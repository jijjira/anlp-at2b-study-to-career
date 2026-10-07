"""Main evaluation of the semantic layer on the 30 gold ads (Step 3 protocol, plus leave-one-ad-out cross-validation).

Honest protocol (n = 30 is tiny, so tuning must never see the ad it is scored on)
-------------------------------------------------------------------------------
* The decision rule (threshold tau, optional margin delta) is chosen by LEAVE-ONE-AD-OUT cross-validation:
  for each ad, tau/delta are picked on the other 29 ads (maximising lenient micro-F1) and then applied to the held-out
  ad. The pooled out-of-fold predictions are what every reported number and bootstrap uses.
* The "in-sample best" row (tuned on all 30) is shown only as an optimistic reference and is the setting used to
  run the unlabelled 688-ad corpus and the curriculum PDFs.
* All models are reported; MAIN_MODEL (config.py) was fixed in advance as the headline.
* Comparisons use the paired bootstrap over ads (2,000 resamples, seed 36118), as in Step 3.
"""
from __future__ import annotations

import json
import random
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

import config
import metrics
from data_access import Context
from semantic_extractor import (Decision, SkillSpace, TextScores, get_encoder, make_units, score_text)

S0, S5 = "S0 Baseline (PhraseMatcher)", "S5 Baseline++"


def grid(norm: str, delta_grid=None) -> list[Decision]:
    taus = config.TAU_GRID_RAW if norm == "raw" else config.TAU_GRID_Z
    deltas = delta_grid if delta_grid is not None else (config.DELTA_GRID_RAW if norm == "raw" else config.DELTA_GRID_Z)
    return [Decision(t, d, k, norm) for t in taus for d in deltas for k in config.TOPK_GRID]


class Runner:
    """Holds encoders / spaces / per-ad score matrices so ablations reuse embeddings."""

    def __init__(self, ctx: Context, device: str | None = None):
        self.ctx, self.device = ctx, device
        self._enc, self._space, self._scores, self._ref = {}, {}, {}, {}

    def encoder(self, key):
        if key not in self._enc:
            self._enc[key] = get_encoder(key, device=self.device) if key != "hashing" else get_encoder(key)
        return self._enc[key]

    def space(self, key, proto_mode, pool, categories, min_alias_len) -> SkillSpace:
        k = (key, proto_mode, pool, categories, min_alias_len)
        if k not in self._space:
            self._space[k] = SkillSpace(self.ctx.table, self.encoder(key), proto_mode, pool, categories, min_alias_len)
        return self._space[k]

    def scores(self, key, granularity, space: SkillSpace, min_words, max_words) -> dict[int, TextScores]:
        k = (key, granularity, id(space), min_words, max_words)
        if k not in self._scores:
            enc, jobs = self.encoder(key), self.ctx.jobs
            self._scores[k] = {r: score_text(jobs.job_description[r], self.ctx.s5, space, enc, granularity,
                                             min_words, max_words) for r in self.ctx.rows}
        return self._scores[k]

    def ensure_reference(self, key, granularity, space: SkillSpace, min_words, max_words):
        """Fit per-skill z-normalisation on unlabelled ad units (gold ads excluded)."""
        k = (key, granularity, min_words, max_words)
        if k not in self._ref:
            rng = random.Random(config.SEED)
            gold = set(self.ctx.rows)
            pool = [r for r in range(len(self.ctx.jobs)) if r not in gold]
            rng.shuffle(pool)
            texts, seen = [], set()
            for r in pool:
                for u in make_units(self.ctx.s5.segment(self.ctx.jobs.job_description[r]), granularity,
                                    min_words, max_words):
                    if u.text.lower() not in seen:
                        seen.add(u.text.lower()), texts.append(u.text)
                if len(texts) >= config.REFERENCE_UNITS:
                    break
            self._ref[k] = self.encoder(key).encode(texts[:config.REFERENCE_UNITS])
        space.fit_reference(self._ref[k])

    def save(self):
        for e in self._enc.values():
            e.save()


# --------------------------------------------------------------------------- #
def predictions(scores: dict, space: SkillSpace, d: Decision, base_pred: dict, rows, semantic_only=False) -> dict:
    pred = {}
    for r in rows:
        adds = scores[r].additions(space, d, exclude=set() if semantic_only else set(base_pred[r]))
        pred[r] = (set(adds) if semantic_only else base_pred[r] | set(adds))
    return pred


def sweep(scores, space, decisions, base_pred, views, rows, semantic_only=False):
    recs, preds = [], []
    for d in decisions:
        p = predictions(scores, space, d, base_pred, rows, semantic_only)
        preds.append(p)
        recs.append({**{k: v for k, v in asdict(d).items()}, **metrics.summarise(p, base_pred, views, rows)})
    return pd.DataFrame(recs), preds


def _counts_lenient(preds, lenient, rows):
    tp = np.array([[len(p[r] & lenient[r]) for r in rows] for p in preds])
    fp = np.array([[len(p[r] - lenient[r]) for r in rows] for p in preds])
    fn = np.array([[len(lenient[r] - p[r]) for r in rows] for p in preds])
    return tp, fp, fn


def _pick(tp, fp, fn, taus) -> int:
    """argmax micro-F1; ties -> higher precision, then higher tau (the more conservative rule)."""
    tp_s, fp_s, fn_s = tp.sum(1), fp.sum(1), fn.sum(1)
    f1 = np.where(tp_s > 0, 2 * tp_s / np.maximum(2 * tp_s + fp_s + fn_s, 1), 0.0)
    prec = np.where(tp_s + fp_s > 0, tp_s / np.maximum(tp_s + fp_s, 1), 0.0)
    order = np.lexsort((np.asarray(taus), prec, f1))        # last key = primary
    return int(order[-1])


def loocv(decisions, preds, views, rows):
    """Leave-one-ad-out selection of the decision rule. Returns (oof predictions, chosen decision per ad)."""
    tp, fp, fn = _counts_lenient(preds, views["lenient"], rows)
    taus = [d.tau for d in decisions]
    oof, chosen = {}, {}
    for j, r in enumerate(rows):
        keep = [i for i in range(len(rows)) if i != j]
        best = _pick(tp[:, keep], fp[:, keep], fn[:, keep], taus)
        oof[r], chosen[r] = preds[best][r], decisions[best]
    return oof, chosen


def best_in_sample(decisions, preds, views, rows) -> tuple[Decision, dict]:
    tp, fp, fn = _counts_lenient(preds, views["lenient"], rows)
    i = _pick(tp, fp, fn, [d.tau for d in decisions])
    return decisions[i], preds[i]


# --------------------------------------------------------------------------- #
def run_config(runner: Runner, model: str, cfg: dict | None = None, semantic_only: bool = False,
               delta_grid=None) -> dict:
    """One full configuration: sweep -> LOOCV -> summary (+ tuned-on-all reference)."""
    cfg = {**config.DEFAULTS, **(cfg or {})}
    ctx = runner.ctx
    categories = "all" if semantic_only else cfg["categories"]
    space = runner.space(model, cfg["proto_mode"], cfg["pool"], categories, cfg["min_alias_len"])
    scores = runner.scores(model, cfg["granularity"], space, cfg["min_words"], cfg["max_words"])
    if cfg["norm"] == "z":
        runner.ensure_reference(model, cfg["granularity"], space, cfg["min_words"], cfg["max_words"])
    decisions = grid(cfg["norm"], delta_grid)
    base = ctx.base_preds[S5]
    sw, preds = sweep(scores, space, decisions, base, ctx.views, ctx.rows, semantic_only)
    oof, chosen = loocv(decisions, preds, ctx.views, ctx.rows)
    d_all, p_all = best_in_sample(decisions, preds, ctx.views, ctx.rows)
    taus = [c.tau for c in chosen.values()]
    return dict(model=model, cfg=cfg, semantic_only=semantic_only, sweep=sw, oof=oof, chosen=chosen,
                oof_summary=metrics.summarise(oof, base, ctx.views, ctx.rows),
                insample_decision=d_all, insample_pred=p_all,
                insample_summary=metrics.summarise(p_all, base, ctx.views, ctx.rows),
                tau_median=float(np.median(taus)), tau_iqr=tuple(np.percentile(taus, [25, 75])),
                decisions=decisions, preds=preds)


def run_pool_cv(runner: Runner, model: str, pools=("max", "centroid")) -> dict:
    """Check of the pooling choice: the pool (max | centroid) is selected INSIDE each leave-one-ad-out
    fold together with tau/delta, by pooling the candidate rules of both settings into one list. The held-out ad
    therefore never influences which pool is used for it."""
    ctx, base = runner.ctx, runner.ctx.base_preds[S5]
    cands = []                                                # (pool, decision, predictions)
    for pool in pools:
        r = run_config(runner, model, {"pool": pool})
        cands += [(pool, d, p) for d, p in zip(r["decisions"], r["preds"])]
    preds = [p for _, _, p in cands]
    taus = [d.tau for _, d, _ in cands]
    tp, fp, fn = _counts_lenient(preds, ctx.views["lenient"], ctx.rows)
    oof, chosen, pool_of = {}, {}, {}
    for j, row in enumerate(ctx.rows):
        keep = [i for i in range(len(ctx.rows)) if i != j]
        best = _pick(tp[:, keep], fp[:, keep], fn[:, keep], taus)
        pool_of[row], chosen[row], oof[row] = cands[best][0], cands[best][1], cands[best][2][row]
    i_all = _pick(tp, fp, fn, taus)
    picked = pd.Series(pool_of).value_counts()
    t = [d.tau for d in chosen.values()]
    return dict(model=model, cfg={**config.DEFAULTS, "pool": "chosen in CV"}, semantic_only=False, oof=oof,
                chosen=chosen, pool_chosen=pool_of,
                pool_note=", ".join(f"{k} {v}/{len(ctx.rows)}" for k, v in picked.items()),
                oof_summary=metrics.summarise(oof, base, ctx.views, ctx.rows),
                insample_decision=cands[i_all][1], insample_pred=cands[i_all][2],
                insample_summary=metrics.summarise(cands[i_all][2], base, ctx.views, ctx.rows),
                tau_median=float(np.median(t)), tau_iqr=tuple(np.percentile(t, [25, 75])))


def compare_to_baselines(ctx: Context, oof: dict, n_boot: int = config.N_BOOT) -> pd.DataFrame:
    rows, recs = ctx.rows, []
    for base_name in (S5, S0):
        for m in ("strict_F1", "lenient_F1", "lenient_P", "I_recall"):
            res = metrics.paired_bootstrap(ctx.base_preds[base_name], oof, metrics.metric_fn(m, ctx.views), rows,
                                           n_boot, config.SEED)
            recs.append(dict(vs=base_name, metric=m, **res))
        # same comparison with Member 3's own evaluate.bootstrap (strict F1), and a check that both agree
        from data_access import step3_bootstrap
        ref = step3_bootstrap(ctx, ctx.base_preds[base_name], oof, n_boot, config.SEED)
        if ref is not None:
            own = next(r for r in recs if r["vs"] == base_name and r["metric"] == "strict_F1")
            recs.append(dict(vs=base_name, metric="strict_F1 (Step 3 evaluate.bootstrap)", a=own["a"], b=own["b"],
                             delta=ref["delta"], delta_CI=ref["delta_CI"], a_CI=ref["F1_a"], b_CI=ref["F1_b"],
                             p_delta_le_0=ref["p_delta_le_0"]))
            if tuple(ref["delta_CI"]) != tuple(own["delta_CI"]) and n_boot == 2000:
                print(f"  !! WARNING: own bootstrap CI {own['delta_CI']} differs from Step 3 evaluate.bootstrap "
                      f"{ref['delta_CI']} for {base_name}")
    return pd.DataFrame(recs)


def baseline_table(ctx: Context) -> pd.DataFrame:
    recs = []
    for name, p in ctx.base_preds.items():
        recs.append(dict(system=name, **metrics.summarise(p, ctx.base_preds[S5], ctx.views, ctx.rows)))
    return pd.DataFrame(recs)


def row_for(name: str, res: dict) -> dict:
    s = res["oof_summary"]
    return dict(system=name, model=res["model"], semantic_only=res["semantic_only"], tau_median=res["tau_median"],
                tau_q25=res["tau_iqr"][0], tau_q75=res["tau_iqr"][1], **s,
                insample_tau=res["insample_decision"].tau, insample_delta=res["insample_decision"].delta,
                insample_lenient_F1=res["insample_summary"]["lenient_F1"],
                insample_I_recall=res["insample_summary"]["I_recall"])


def model_comparison(runner: Runner, models=None, n_boot=config.N_BOOT):
    """Hybrid for every model; the semantic-only control is run once, for config.MAIN_MODEL only
    (it is a control showing the layer cannot work alone, so it is not repeated per model)."""
    models = models or config.COMPARE_MODELS
    ctx, results, recs, boots = runner.ctx, {}, [], []
    for m in models:
        for sem_only in ((False, True) if m == config.MAIN_MODEL else (False,)):
            name = f"{m} {'semantic-only (all skills)' if sem_only else 'hybrid'}"
            print("  ->", name, flush=True)
            res = run_config(runner, m, semantic_only=sem_only)
            results[name] = res
            recs.append(row_for(name, res))
            b = compare_to_baselines(ctx, res["oof"], n_boot)
            b.insert(0, "system", name)
            boots.append(b)
        if m == config.MAIN_MODEL and m != "hashing":
            name = f"{m} hybrid (pool chosen in CV)"            # pooling chosen inside each fold
            print("  ->", name, flush=True)
            res = run_pool_cv(runner, m)
            results[name] = res
            recs.append({**row_for(name, res), "pool_chosen": res["pool_note"]})
            b = compare_to_baselines(ctx, res["oof"], n_boot)
            b.insert(0, "system", name)
            boots.append(b)
            print("     pool chosen per held-out ad:", res["pool_note"], flush=True)
        runner.save()
    return pd.DataFrame(recs), pd.concat(boots, ignore_index=True), results


def all_sweeps(results: dict) -> pd.DataFrame:
    """Threshold sweeps of every hybrid model in one table (column `model`)."""
    parts = []
    for res in results.values():
        if not res["semantic_only"] and "sweep" in res:          # the pool-chosen-in-CV row has no single sweep
            parts.append(res["sweep"].assign(model=res["model"]))
    df = pd.concat(parts, ignore_index=True)
    return df[["model"] + [c for c in df.columns if c != "model"]]


ABLATIONS = {
    "granularity": [("granularity", v) for v in ("line", "clause", "line+clause", "line+window")],
    "prototypes": [("proto_mode", v) for v in ("canonical", "aliases", "aliases_ctx")],
    "pooling": [("pool", v) for v in ("max", "centroid")],
    "skills the semantic layer may add": [("categories", v) for v in ("concept", "all")],
    "score normalisation": [("norm", v) for v in ("raw", "z")],
}


def ablation(runner: Runner, model: str = config.MAIN_MODEL, n_boot=config.N_BOOT):
    """One factor at a time around DEFAULTS, plus the 'no margin rule' variant. LOOCV-tuned each time."""
    ctx, recs, boots = runner.ctx, [], []
    jobs = [(f, k, v, None) for f, items in ABLATIONS.items() for k, v in items]
    jobs.append(("margin rule", "delta", "off", [None]))
    jobs.append(("margin rule", "delta", "on (default)", None))
    for factor, key, value, dgrid in jobs:
        cfg = {} if key == "delta" else {key: value}
        print("  ->", factor, value, flush=True)
        res = run_config(runner, model, cfg, delta_grid=dgrid)
        s = res["oof_summary"]
        recs.append(dict(factor=factor, setting=value, is_default=(config.DEFAULTS.get(key) == value or value == "on (default)"),
                         tau_median=res["tau_median"], **{k: s[k] for k in (
                             "strict_P", "strict_R", "strict_F1", "lenient_P", "lenient_R", "lenient_F1",
                             "I_recall", "n_added", "added_precision")}))
        b = metrics.paired_bootstrap(ctx.base_preds[S5], res["oof"], metrics.metric_fn("lenient_F1", ctx.views),
                                     ctx.rows, n_boot, config.SEED)
        boots.append(dict(factor=factor, setting=value, **{f"lenientF1_{k}": v for k, v in b.items()}))
    runner.save()
    return pd.DataFrame(recs), pd.DataFrame(boots)


# --------------------------------------------------------------------------- #
def save_json(obj, path: Path):
    def default(o):
        if isinstance(o, (set, tuple)):
            return sorted(o) if isinstance(o, set) else list(o)
        if isinstance(o, (np.floating, np.integer)):
            return o.item()
        if isinstance(o, Decision):
            return asdict(o)
        raise TypeError(type(o))
    Path(path).write_text(json.dumps(obj, indent=2, default=default, ensure_ascii=False))


def flatten_ci(df: pd.DataFrame) -> pd.DataFrame:
    """Split tuple-valued CI columns (a_CI, b_CI, delta_CI) into *_lo / *_hi so they survive a CSV round trip."""
    df = df.copy()
    for c in [c for c in df.columns if c.endswith("_CI") or c.endswith("CI")]:
        if len(df) and isinstance(df[c].iloc[0], (tuple, list)):
            base = c[:-3] if c.endswith("_CI") else c[:-2]
            df[f"{base}_lo"] = [x[0] for x in df[c]]
            df[f"{base}_hi"] = [x[1] for x in df[c]]
            df = df.drop(columns=c)
    return df
