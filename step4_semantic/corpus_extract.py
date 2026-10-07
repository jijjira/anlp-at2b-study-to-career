"""Run the tuned hybrid extractor on all 688 job ads (unlabelled) and prepare a human precision audit.

Outputs:
  results/handoff/job_skills_hybrid_long.csv        job_id | career_category | canonical_skill | skill_category | source | strength | weight | score | evidence
  results/handoff/job_skills_hybrid_extracted.csv   same format as Step 3's job_skills_extracted.csv
  results/details/semantic_additions_by_skill.csv   which skills the semantic layer adds, how often, in which careers
  results/audit/job_audit_sheet.csv                 BLINDED sheet for human labelling: 50 random semantic additions + 50 random
                                                    exact hits from non-gold ads, shuffled, no source/score column
                                                    (human_label: 1 = the ad demands the skill, 0 = not)
  results/audit/job_audit_key.csv                   hidden item_id -> source mapping (do NOT open before labelling is finished)

The decision rule comes from results/details/final_config.json (tuned on all 30 gold ads). Because those 30 ads are only 4%
of the corpus, treat the audit - not the gold F1 - as the estimate of precision on unseen ads.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

import pandas as pd

import config
from experiments import Runner
from semantic_extractor import Decision, HybridExtractor


def load_final(path: Path | None = None) -> dict:
    p = Path(path) if path else config.DETAILS / "final_config.json"
    if not p.exists():
        raise FileNotFoundError(f"{p} not found - run `python run_all.py compare` first")
    return json.loads(p.read_text())


def build_hybrid(runner: Runner, final: dict) -> HybridExtractor:
    cfg, dec = {**config.DEFAULTS, **final["cfg"]}, Decision(**final["decision"])
    space = runner.space(final["model"], cfg["proto_mode"], cfg["pool"], cfg["categories"], cfg["min_alias_len"])
    if dec.norm == "z":
        runner.ensure_reference(final["model"], cfg["granularity"], space, cfg["min_words"], cfg["max_words"])
    return HybridExtractor(runner.ctx.s5, space, runner.encoder(final["model"]), dec, cfg["granularity"],
                           cfg["sem_weight"], cfg["min_words"], cfg["max_words"])


def run(runner: Runner, final: dict, n_audit: int = 50) -> dict:
    ctx, jobs = runner.ctx, runner.ctx.jobs
    hy = build_hybrid(runner, final)
    cat = ctx.table.drop_duplicates("canonical_skill").set_index("canonical_skill")["category"].to_dict()
    long_rows, wide_rows, adds = [], [], []
    for r in range(len(jobs)):
        ev = hy.analyse(jobs.job_description[r])
        for e in ev:
            rec = dict(row=r, job_id=jobs.job_id[r], career_category=jobs.career_category[r], canonical_skill=e.skill,
                       skill_category=cat.get(e.skill, ""), source=e.source, strength=e.strength, weight=e.weight,
                       score=e.score, evidence=e.unit, line_no=e.line_no)
            long_rows.append(rec)
            if e.source == "semantic":
                adds.append(rec)
        wide_rows.append(dict(job_id=jobs.job_id[r], career_category=jobs.career_category[r], job_title=jobs.job_title[r],
                              extracted_skills=", ".join(e.skill for e in ev)))
    runner.save()
    config.ensure_dirs()
    long = pd.DataFrame(long_rows)
    long.drop(columns="row").to_csv(config.HANDOFF / "job_skills_hybrid_long.csv", index=False)
    pd.DataFrame(wide_rows).to_csv(config.HANDOFF / "job_skills_hybrid_extracted.csv", index=False)
    a = pd.DataFrame(adds)
    if len(a):
        by = (a.groupby("canonical_skill").agg(n_ads=("job_id", "nunique"), mean_score=("score", "mean"))
              .join(a.pivot_table(index="canonical_skill", columns="career_category", values="job_id",
                                  aggfunc="nunique", fill_value=0)).sort_values("n_ads", ascending=False))
        by.to_csv(config.DETAILS / "semantic_additions_by_skill.csv")
        sheet_path, key_path = config.AUDIT / "job_audit_sheet.csv", config.AUDIT / "job_audit_key.csv"
        if _has_labels(sheet_path):
            print(f"  NOTE: {sheet_path.name} already has labels - not overwritten (delete it to make a new sheet)")
        else:
            sheet, key = blind_job_audit(long, jobs, set(ctx.rows), n_sem=n_audit, n_exact=n_audit)
            sheet.to_csv(sheet_path, index=False)
            key.to_csv(key_path, index=False)                       # do NOT show this file to the annotator
    return dict(n_ads=len(jobs), n_exact=int((long.source == "exact").sum()), n_semantic=int((long.source == "semantic").sum()),
                ads_with_addition=int(a.row.nunique()) if len(a) else 0)


def _has_labels(path: Path) -> bool:
    if not Path(path).exists():
        return False
    df = pd.read_csv(path)
    return "human_label" in df and df.human_label.astype(str).isin(["0", "1", "0.0", "1.0"]).any()


def blind_job_audit(long: pd.DataFrame, jobs: pd.DataFrame, gold_rows: set, n_sem: int = 100, n_exact: int = 100,
                    seed: int = config.SEED) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Blinded precision audit on UNSEEN ads, designed for a single annotator (the method developer).

    `long` has one row per (ad, skill) with columns row, job_id, canonical_skill, source, strength, evidence, score.
    The sheet mixes a random sample of semantic additions with a random sample of exact hits (gold ads excluded),
    shuffled, with NO source or score column, so the annotator cannot tell which method found an item and cannot favour
    the semantic layer. Both methods are scored on the same footing. Returns (sheet, key); `key` maps item_id -> source
    and is only read by `evaluate_job_audit` after labelling.
    """
    long = long.copy()
    if "line_no" in long:     # show the FULL ad line for both sources (a semantic unit may be a clause fragment,
        from semantic_extractor import _clean                     # which would otherwise give its source away)
        def full_line(r, ln, ev):
            if pd.isna(ln):
                return ev
            lines = str(jobs.job_description[r]).split("\n")
            return _clean(lines[int(ln)]) if 0 <= int(ln) < len(lines) else ev
        long["evidence"] = [full_line(r, ln, ev) for r, ln, ev in zip(long.row, long.line_no, long.evidence)]
    pool = long[~long.row.isin(gold_rows) & long.evidence.notna() & (long.evidence.astype(str).str.len() > 0)]
    sem, exa = pool[pool.source == "semantic"], pool[pool.source == "exact"]
    sem = sem.sample(n=min(n_sem, len(sem)), random_state=seed)
    exa = exa.sample(n=min(n_exact, len(exa)), random_state=seed)
    items = pd.concat([sem, exa]).sample(frac=1.0, random_state=seed).reset_index(drop=True)
    items.insert(0, "item_id", [f"J{i:04d}" for i in range(len(items))])
    items["job_title"] = [jobs.job_title[r] for r in items.row]
    key = items[["item_id", "row", "job_id", "canonical_skill", "source", "score"]]
    sheet = (items.rename(columns={"canonical_skill": "skill", "strength": "section"})
             [["item_id", "job_id", "job_title", "skill", "section", "evidence"]]
             .assign(human_label="", annotator=""))
    return sheet, key


def evaluate_job_audit(sheet_path: Path | None = None, key_path: Path | None = None) -> pd.DataFrame:
    """Precision of semantic additions vs exact hits on unseen ads (Wilson 95% CI), from the filled blinded sheet."""
    import curriculum_semantic as cs                       # same scoring code as the unit-PDF label sheet
    return cs.evaluate_unit_labels(sheet_path or config.AUDIT / "job_audit_sheet.csv",
                                   key_path or config.AUDIT / "job_audit_key.csv")
