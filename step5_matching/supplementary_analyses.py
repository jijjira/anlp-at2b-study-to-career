"""Supplementary analyses reported in Sections 4.3 and 4.4 and Appendix A of the report.

Everything here is computed from outputs already saved in the repository:
  step1_data/job_cleaned.csv                                   (688 advertisements)
  step4_semantic/results/hybrid_job_skills/job_skills_hybrid_long.csv
  step4_semantic/results/details/curriculum_all_hits.csv       (unit evidence)

Analyses
  A. Exact versus hybrid fit per career, with a paired bootstrap over advertisements
     of the hybrid-minus-exact difference.
  B. Leave-one-skill-out check of the semantic gain (the AI Agents false match),
     and the effect of halving the weight of semantic evidence.
  C. Share of uncovered top-30 demand by skill category (exact coverage).
  D. Greedy unit selection: how many units reproduce each career's 20-unit fit.
  E. Sensitivity of hybrid fit to the top-N cut-off (N = 10 to 50; report Table A2).
  F. Precision of exact hits and semantic additions in the blinded human audits (Wilson 95% intervals; report Figure 4).
  G. Hybrid fit after removing only the match the blinded audit judged false (AI Agents in USYD COMP5310,
     evidence "Ethical AI usage"); the other AI Agents match (USYD COMP5046, "Models - Agents") was judged
     correct and stays (report Table 6 note and Section 4.4).

Run:  python supplementary_analyses.py            (writes CSVs to ./outputs/supplementary)
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from matching import build_career_profiles, match_careers, study_coverage_from_hits

SEED = 36118
TOP_N = 30


def load(root: Path):
    jobs = pd.read_csv(root / "step1_data" / "job_cleaned.csv")
    job_hits = pd.read_csv(root / "step4_semantic" / "results" / "hybrid_job_skills" / "job_skills_hybrid_long.csv")
    unit_hits = pd.read_csv(root / "step4_semantic" / "results" / "details" / "curriculum_all_hits.csv")
    return jobs, job_hits, unit_hits


def fit_table(job_hits, jobs, unit_hits, *, exact_only=False, semantic_discount=1.0,
              drop_skill=None, units=None) -> pd.Series:
    """Fit (0 to 100) per career under one configuration."""
    jh, uh = job_hits, unit_hits
    if exact_only:
        jh = jh[jh["source"].eq("exact")]
        uh = uh[uh["source"].eq("exact")]
    profiles = build_career_profiles(jh, jobs, semantic_discount=semantic_discount)
    study = study_coverage_from_hits(uh, unit_ids=units, semantic_discount=semantic_discount)
    if drop_skill is not None:
        study = study[study["skill"] != drop_skill]
    ranking, _ = match_careers(study, profiles, top_n=TOP_N)
    return ranking.set_index("career")["match_percent"]


def paired_bootstrap(jobs, job_hits, unit_hits, n_boot=1000, seed=SEED) -> pd.DataFrame:
    """Resample advertisements within each career; recompute hybrid minus exact."""
    rng = np.random.default_rng(seed)
    rows = []
    study_h = study_coverage_from_hits(unit_hits)
    study_e = study_coverage_from_hits(unit_hits[unit_hits["source"].eq("exact")])
    exact_hits = job_hits[job_hits["source"].eq("exact")]
    for career, jgroup in jobs.groupby("career_category"):
        ids = jgroup["job_id"].to_numpy()
        diffs = []
        for _ in range(n_boot):
            draw = rng.choice(ids, size=len(ids), replace=True)
            # relabel duplicates so each resampled copy counts as its own advertisement
            new_ids = [f"{i}#{k}" for k, i in enumerate(draw)]
            jb = pd.DataFrame({"job_id": new_ids, "career_category": career})
            mapping = pd.DataFrame({"job_id": draw, "new_id": new_ids})

            def resample(h):
                m = h[h["career_category"].eq(career)].merge(mapping, on="job_id")
                return m.drop(columns="job_id").rename(columns={"new_id": "job_id"})

            vals = []
            for hits, study in ((job_hits, study_h), (exact_hits, study_e)):
                prof = build_career_profiles(resample(hits), jb)
                r, _ = match_careers(study, prof, top_n=TOP_N)
                vals.append(float(r.loc[r["career"].eq(career), "match_percent"].iloc[0]))
            diffs.append(vals[0] - vals[1])
        lo, hi = np.percentile(diffs, [2.5, 97.5])
        rows.append({"career": career, "mean_gain": float(np.mean(diffs)),
                     "ci_low": float(lo), "ci_high": float(hi), "excludes_zero": bool(lo > 0 or hi < 0)})
    return pd.DataFrame(rows).sort_values("career").reset_index(drop=True)


def leave_one_skill_out(jobs, job_hits, unit_hits) -> pd.DataFrame:
    """Hybrid fit after removing each semantically added unit skill, one at a time."""
    hybrid = fit_table(job_hits, jobs, unit_hits)
    exact = fit_table(job_hits, jobs, unit_hits, exact_only=True)
    exact_skills = set(unit_hits.loc[unit_hits["source"].eq("exact"), "skill"])
    added = sorted(set(unit_hits.loc[unit_hits["source"].eq("semantic"), "skill"]) - exact_skills)
    rows = []
    for skill in added:
        without = fit_table(job_hits, jobs, unit_hits, drop_skill=skill)
        for career in hybrid.index:
            rows.append({"dropped_skill": skill, "career": career, "hybrid": hybrid[career],
                         "exact": exact[career], "without_skill": without[career],
                         "points_from_skill": hybrid[career] - without[career]})
    return pd.DataFrame(rows)


def audit_wrong_match_only(jobs, job_hits, unit_hits) -> pd.DataFrame:
    """Hybrid fit with only the audit-wrong AI Agents match (USYD COMP5310) removed."""
    hybrid = fit_table(job_hits, jobs, unit_hits)
    wrong = unit_hits["skill"].eq("AI Agents") & unit_hits["unit_id"].str.contains("COMP5310") & unit_hits["source"].eq("semantic")
    only_false = fit_table(job_hits, jobs, unit_hits[~wrong])
    no_agents = fit_table(job_hits, jobs, unit_hits, drop_skill="AI Agents")
    out = pd.DataFrame({"hybrid": hybrid, "false_match_removed": only_false, "ai_agents_removed_entirely": no_agents})
    out["points_from_false_match"] = out["hybrid"] - out["false_match_removed"]
    return out


def uncovered_by_category(jobs, job_hits, unit_hits) -> pd.DataFrame:
    """Uncovered top-30 demand by skill category, using exact coverage."""
    profiles = build_career_profiles(job_hits[job_hits["source"].eq("exact")], jobs)
    study = study_coverage_from_hits(unit_hits[unit_hits["source"].eq("exact")])
    _, details = match_careers(study, profiles, top_n=TOP_N)
    details = details.assign(uncovered=details["demand_weight"] * (1 - details["coverage"]))
    out = details.groupby("skill_category").agg(
        uncovered_demand=("uncovered", "sum"), total_demand=("demand_weight", "sum")).reset_index()
    out["share_of_uncovered_pct"] = 100 * out["uncovered_demand"] / out["uncovered_demand"].sum()
    out["covered_pct"] = 100 * (1 - out["uncovered_demand"] / out["total_demand"])
    return out.sort_values("share_of_uncovered_pct", ascending=False).reset_index(drop=True)


def greedy_units(jobs, job_hits, unit_hits) -> pd.DataFrame:
    """Per career, add the unit that raises exact fit most until the 20-unit fit is reached."""
    exact_jobs = job_hits[job_hits["source"].eq("exact")]
    exact_units = unit_hits[unit_hits["source"].eq("exact")]
    profiles = build_career_profiles(exact_jobs, jobs)
    all_units = sorted(exact_units["unit_id"].unique())

    def score(units, career):
        study = study_coverage_from_hits(exact_units, unit_ids=units)
        r, _ = match_careers(study, profiles, top_n=TOP_N)
        return float(r.loc[r["career"].eq(career), "match_percent"].iloc[0])

    rows = []
    for career in sorted(jobs["career_category"].unique()):
        full = score(all_units, career)
        chosen, remaining, current = [], list(all_units), 0.0
        while remaining and current < full - 1e-9:
            best = max(remaining, key=lambda u: score(chosen + [u], career))
            chosen.append(best)
            remaining.remove(best)
            current = score(chosen, career)
            rows.append({"career": career, "step": len(chosen), "unit_added": best,
                         "fit_percent": current, "full_20_unit_fit": full})
    return pd.DataFrame(rows)


def sensitivity_top_n(jobs, job_hits, unit_hits, cutoffs=(10, 20, 30, 40, 50)) -> pd.DataFrame:
    """Hybrid fit (%) per career for several top-N cut-offs."""
    profiles = build_career_profiles(job_hits, jobs)
    study = study_coverage_from_hits(unit_hits)
    out = {}
    for n in cutoffs:
        ranking, _ = match_careers(study, profiles, top_n=n)
        out[n] = ranking.set_index("career")["match_percent"]
    return pd.DataFrame(out).rename_axis(columns="top_n")


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return centre - half, centre + half


def audit_precision(root: Path) -> pd.DataFrame:
    """Join each blinded audit sheet to its key and compute precision by producing method."""
    audit = root / "step4_semantic" / "results" / "audit"
    rows = []
    for name, sheet, key in (("advertisements", "job_audit_sheet.csv", "job_audit_key.csv"),
                             ("units", "curriculum_label_sheet.csv", "curriculum_label_key.csv")):
        m = pd.read_csv(audit / sheet).merge(pd.read_csv(audit / key)[["item_id", "source"]], on="item_id")
        for source, g in m.groupby("source"):
            k, n = int((g["human_label"] == 1).sum()), len(g)
            lo, hi = wilson(k, n)
            rows.append({"corpus": name, "method": source, "n": n, "correct": k,
                         "precision_pct": 100 * k / n, "wilson_low": 100 * lo, "wilson_high": 100 * hi})
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "outputs" / "supplementary")
    ap.add_argument("--n-boot", type=int, default=1000)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    jobs, job_hits, unit_hits = load(args.root)

    exact = fit_table(job_hits, jobs, unit_hits, exact_only=True)
    hybrid = fit_table(job_hits, jobs, unit_hits)
    half = fit_table(job_hits, jobs, unit_hits, semantic_discount=0.5)
    base = pd.DataFrame({"exact": exact, "hybrid": hybrid, "hybrid_half_semantic_weight": half})
    base["gain"] = base["hybrid"] - base["exact"]
    base["gain_half_weight"] = base["hybrid_half_semantic_weight"] - base["exact"]
    base.round(2).to_csv(args.output / "A_exact_vs_hybrid.csv")
    print("\nA. Exact vs hybrid fit\n", base.round(1).to_string())

    boot = paired_bootstrap(jobs, job_hits, unit_hits, n_boot=args.n_boot)
    boot.round(2).to_csv(args.output / "A_paired_bootstrap_gain.csv", index=False)
    print("\nA. Paired bootstrap of hybrid minus exact\n", boot.round(1).to_string(index=False))

    loo = leave_one_skill_out(jobs, job_hits, unit_hits)
    loo.round(2).to_csv(args.output / "B_leave_one_skill_out.csv", index=False)
    top = loo[loo["career"].eq("AI Engineer")].sort_values("points_from_skill", ascending=False).head(3)
    print("\nB. Largest single-skill contributions for AI Engineer\n", top.round(1).to_string(index=False))

    g = audit_wrong_match_only(jobs, job_hits, unit_hits)
    g.round(2).to_csv(args.output / "G_false_match_only.csv")
    print("\nG. Removing only the audit-wrong AI Agents match\n", g.round(1).to_string())

    unc = uncovered_by_category(jobs, job_hits, unit_hits)
    unc.round(2).to_csv(args.output / "C_uncovered_by_category.csv", index=False)
    print("\nC. Uncovered demand by skill category\n", unc.round(1).to_string(index=False))

    greedy = greedy_units(jobs, job_hits, unit_hits)
    greedy.round(2).to_csv(args.output / "D_greedy_unit_selection.csv", index=False)
    steps = greedy.groupby("career")["step"].max()
    print("\nD. Units needed to reach each career's full 20-unit fit\n", steps.to_string())
    sens = sensitivity_top_n(jobs, job_hits, unit_hits)
    sens.round(2).to_csv(args.output / "E_sensitivity_top_n.csv")
    print("\nE. Hybrid fit by top-N cut-off\n", sens.round(1).to_string())

    aud = audit_precision(args.root)
    aud.round(1).to_csv(args.output / "F_audit_precision.csv", index=False)
    print("\nF. Blinded audit precision\n", aud.round(1).to_string(index=False))

    print(f"\nWritten to {args.output}")


if __name__ == "__main__":
    main()
