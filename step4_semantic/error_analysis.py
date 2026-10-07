"""Error analysis of the hybrid method on the 30 gold ads (uses the out-of-fold decisions).

Outputs (results/details/):
  error_analysis.csv     one row per implicit (I) label and per semantic addition, with the evidence sentence
  error_by_skill.csv     per skill: implicit labels recovered / missed, false additions (finds "hub" skills)
"""
from __future__ import annotations

import pandas as pd

import config
from experiments import Runner, S5


def error_table(runner: Runner, res: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    ctx, cfg, model = runner.ctx, res["cfg"], res["model"]
    space = runner.space(model, cfg["proto_mode"], cfg["pool"], "all" if res["semantic_only"] else cfg["categories"],
                         cfg["min_alias_len"])
    scores = runner.scores(model, cfg["granularity"], space, cfg["min_words"], cfg["max_words"])
    if cfg["norm"] == "z":
        runner.ensure_reference(model, cfg["granularity"], space, cfg["min_words"], cfg["max_words"])
    base, v, recs = ctx.base_preds[S5], ctx.views, []
    for r in ctx.rows:
        ts, d, pred = scores[r], res["chosen"][r], res["oof"][r]
        adds = ts.additions(space, d, exclude=set(base[r]))
        for s in sorted(v["I"][r]):
            if s in pred:
                kind = "I_recovered_by_semantic" if s in adds else "I_found_by_exact"
                h = adds.get(s)
                recs.append(dict(row=r, skill=s, kind=kind, cosine=h.cosine if h else None,
                                 strength=h.strength if h else None, evidence=h.unit if h else None, tau=d.tau))
            else:
                if s in space.skills and len(ts.units):
                    k = space.skills.index(s)
                    col = ts.S[:, k]
                    u = int(col.argmax())
                    rank_in_unit = int((ts.S[u] > ts.S[u, k]).sum()) + 1
                    recs.append(dict(row=r, skill=s, kind="I_missed", cosine=float(col[u]), strength=ts.units[u].strength,
                                     evidence=ts.units[u].text, tau=d.tau, best_unit_rank_of_skill=rank_in_unit))
                else:
                    recs.append(dict(row=r, skill=s, kind="I_missed_not_candidate", tau=d.tau))
        for s, h in adds.items():
            kind = ("addition_correct_I" if s in v["I"][r] else
                    "addition_correct_RP" if s in v["strict"][r] else "addition_wrong")
            recs.append(dict(row=r, skill=s, kind=kind, cosine=h.cosine, strength=h.strength, evidence=h.unit, tau=d.tau))
    df = pd.DataFrame(recs)
    by = (df.assign(n=1).pivot_table(index="skill", columns="kind", values="n", aggfunc="sum", fill_value=0)
          .reset_index()) if len(df) else pd.DataFrame()
    return df, by


def save(df, by):
    config.ensure_dirs()
    df.to_csv(config.DETAILS / "error_analysis.csv", index=False)
    by.to_csv(config.DETAILS / "error_by_skill.csv", index=False)
