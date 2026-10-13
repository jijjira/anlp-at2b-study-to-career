"""Career profiles, ranking, skill gaps and explanations for Step 5."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Mapping

import numpy as np
import pandas as pd

LEVEL_WEIGHTS = {"assessed": 1.0, "taught": 0.75, "mentioned": 0.5}
DEFAULT_TOP_N = 30
DEFAULT_GAP_K = 8
GENERIC_GAP_SKILLS = {"Artificial Intelligence"}


def _learning_action(skill: str) -> str:
    """Return a short, practical learning action for a priority skill gap."""
    actions = {
        "Causal Inference": "Analyse an observational dataset and explain assumptions, treatment effects and limitations.",
        "Experiment Design": "Design a controlled experiment with hypotheses, metrics, sample-size reasoning and bias checks.",
        "A/B Testing": "Run an end-to-end A/B test analysis and report statistical and business conclusions.",
        "Forecasting": "Build and evaluate a time-series forecast against a simple baseline.",
        "Dashboarding": "Build an interactive dashboard that communicates decisions, filters and key metrics.",
        "Tableau": "Create a Tableau dashboard with calculated fields, filters and a short data story.",
        "Power BI": "Create a Power BI report with a data model, DAX measures and interactive visuals.",
        "Looker": "Build a small governed analytics model and dashboard in Looker or Looker Studio.",
        "dbt": "Create a tested dbt transformation project with documentation and lineage.",
        "ETL": "Build a reproducible extract-transform-load pipeline with validation and error handling.",
        "Observability": "Add logging, monitoring and data or model quality checks to a deployed pipeline.",
        "AWS": "Deploy one small data or ML workload using core AWS storage and compute services.",
        "Azure": "Deploy one small data or ML workload using core Azure services.",
        "GCP": "Deploy one small data or ML workload using core Google Cloud services.",
        "Kubernetes": "Containerise an application and deploy it to a local or managed Kubernetes cluster.",
        "CI/CD": "Create an automated test and deployment workflow for a data or ML project.",
        "PyTorch": "Train, evaluate and document a PyTorch model with a reproducible experiment.",
        "Fine-tuning": "Fine-tune a small pretrained model and compare it with a baseline.",
        "RAG": "Build and evaluate a retrieval-augmented generation pipeline with cited sources.",
        "APIs": "Expose a model or data service through a documented REST API with tests.",
        "Data Governance": "Document data ownership, quality rules, lineage, privacy and access controls.",
    }
    return actions.get(skill, f"Complete a small practical project demonstrating {skill} and document the evidence.")


def build_career_profiles(job_skill_hits: pd.DataFrame, jobs: pd.DataFrame,
                          semantic_discount: float = 1.0) -> pd.DataFrame:
    """Build demand weights using every ad, including ads with no skill hit."""
    required = {"job_id", "career_category", "canonical_skill", "weight", "source"}
    missing = required - set(job_skill_hits.columns)
    if missing:
        raise ValueError(f"job_skill_hits is missing columns: {sorted(missing)}")
    if not {"job_id", "career_category"}.issubset(jobs.columns):
        raise ValueError("jobs must contain job_id and career_category")
    if not 0 <= semantic_discount <= 1:
        raise ValueError("semantic_discount must be between 0 and 1")

    hits = job_skill_hits.copy()
    hits["effective_weight"] = pd.to_numeric(hits["weight"], errors="coerce").fillna(0.0)
    hits.loc[hits["source"].eq("semantic"), "effective_weight"] *= semantic_discount
    hits = hits.groupby(["job_id", "career_category", "canonical_skill"], as_index=False).agg(
        effective_weight=("effective_weight", "max"),
        source=("source", lambda x: "exact" if "exact" in set(x) else "semantic"),
        skill_category=("skill_category", "first"),
    )
    totals = jobs.groupby("career_category")["job_id"].nunique().rename("career_job_total")
    summary = hits.groupby(["career_category", "canonical_skill"], as_index=False).agg(
        job_count=("job_id", "nunique"),
        weight_sum=("effective_weight", "sum"),
        skill_category=("skill_category", "first"),
        semantic_only_jobs=("source", lambda x: int((x == "semantic").sum())),
    ).merge(totals, on="career_category", how="left", validate="many_to_one")
    summary["job_pct"] = 100 * summary["job_count"] / summary["career_job_total"]
    summary["demand_weight"] = summary["weight_sum"] / summary["career_job_total"]
    summary["rank_within_career"] = summary.groupby("career_category")["demand_weight"].rank(
        method="first", ascending=False).astype(int)
    cols = ["career_category", "canonical_skill", "skill_category", "job_count",
            "career_job_total", "job_pct", "demand_weight", "semantic_only_jobs",
            "rank_within_career"]
    return summary[cols].sort_values(["career_category", "rank_within_career"]).reset_index(drop=True)


def study_coverage_from_hits(study_hits: pd.DataFrame, unit_ids: Iterable[str] | None = None,
                             semantic_discount: float = 1.0) -> pd.DataFrame:
    """Merge curriculum hits into one profile, keeping the best evidence per skill."""
    required = {"unit_id", "skill", "source", "page", "level", "evidence"}
    missing = required - set(study_hits.columns)
    if missing:
        raise ValueError(f"study_hits is missing columns: {sorted(missing)}")
    if not 0 <= semantic_discount <= 1:
        raise ValueError("semantic_discount must be between 0 and 1")
    hits = study_hits.copy()
    if unit_ids is not None:
        selected = set(unit_ids)
        hits = hits[hits["unit_id"].isin(selected)].copy()
        absent = selected - set(hits["unit_id"])
        if absent:
            raise ValueError(f"Unknown or empty unit_ids: {sorted(absent)}")
    if hits.empty:
        return pd.DataFrame(columns=["skill", "coverage", "level", "source", "units",
                                     "pages", "evidence", "semantic_score"])
    hits["coverage"] = hits["level"].map(LEVEL_WEIGHTS).fillna(0.0)
    hits.loc[hits["source"].eq("semantic"), "coverage"] *= semantic_discount
    hits["semantic_score"] = pd.to_numeric(hits.get("score"), errors="coerce")
    hits = hits.sort_values(["skill", "coverage", "source"], ascending=[True, False, True])
    rows = []
    for skill, group in hits.groupby("skill", sort=True):
        best = group.iloc[0]
        rows.append({"skill": skill, "coverage": float(best["coverage"]), "level": best["level"],
                     "source": best["source"],
                     "units": sorted(group["unit_id"].dropna().astype(str).unique().tolist()),
                     "pages": sorted({int(p) for p in group["page"].dropna()}),
                     "evidence": str(best["evidence"]),
                     "semantic_score": None if pd.isna(best["semantic_score"]) else float(best["semantic_score"])})
    return pd.DataFrame(rows).sort_values(["coverage", "skill"], ascending=[False, True]).reset_index(drop=True)


def study_coverage_from_profile(profile) -> pd.DataFrame:
    """Convert a Step 3/4 StudyProfile into the table accepted by match_careers."""
    rows = []
    for skill, detail in profile.skills.items():
        rows.append({"skill": skill,
                     "coverage": float(detail.get("weight", LEVEL_WEIGHTS.get(detail.get("level"), 0.0))),
                     "level": detail.get("level", "mentioned"), "source": detail.get("source", "exact"),
                     "units": [], "pages": list(detail.get("pages", [])),
                     "evidence": detail.get("evidence", ""), "semantic_score": detail.get("score")})
    return pd.DataFrame(rows)


def _normalise_study(study) -> pd.DataFrame:
    if isinstance(study, pd.DataFrame):
        if not {"skill", "coverage"}.issubset(study.columns):
            raise ValueError("study DataFrame must contain skill and coverage")
        out = study.copy()
    elif isinstance(study, Mapping):
        out = pd.DataFrame({"skill": list(study), "coverage": list(study.values())})
    else:
        out = pd.DataFrame({"skill": list(study), "coverage": 1.0})
    out["coverage"] = pd.to_numeric(out["coverage"], errors="coerce").fillna(0.0).clip(0.0, 1.0)
    return out.sort_values("coverage", ascending=False).drop_duplicates("skill")


def match_careers(study, career_profiles: pd.DataFrame, top_n: int = DEFAULT_TOP_N,
                  gap_k: int = DEFAULT_GAP_K,
                  exclude_gaps: Iterable[str] = GENERIC_GAP_SKILLS) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Rank careers and return per-skill contributions and remaining gaps."""
    if top_n <= 0 or gap_k <= 0:
        raise ValueError("top_n and gap_k must be positive")
    needed = {"career_category", "canonical_skill", "demand_weight"}
    missing = needed - set(career_profiles.columns)
    if missing:
        raise ValueError(f"career_profiles is missing columns: {sorted(missing)}")
    student = _normalise_study(study)
    coverage = dict(zip(student["skill"], student["coverage"]))
    study_lookup = student.set_index("skill").to_dict("index")
    excluded = set(exclude_gaps)
    rankings, detail_rows = [], []
    for career, group in career_profiles.groupby("career_category", sort=True):
        top = group.nlargest(top_n, "demand_weight").copy()
        top["coverage"] = top["canonical_skill"].map(coverage).fillna(0.0)
        top["contribution"] = top["demand_weight"] * top["coverage"]
        top["remaining_gain"] = top["demand_weight"] * (1.0 - top["coverage"])
        denom = float(top["demand_weight"].sum())
        score = float(top["contribution"].sum() / denom) if denom else 0.0
        matched = top[top["coverage"] > 0].sort_values("contribution", ascending=False)
        gaps = top[~top["canonical_skill"].isin(excluded)].sort_values("remaining_gain", ascending=False)
        top_matched = matched.head(5)["canonical_skill"].tolist()
        top_gaps = gaps.head(gap_k)["canonical_skill"].tolist()
        rankings.append({"career": career, "match_score": score, "match_percent": round(score * 100, 1),
                         "n_ads": int(group["career_job_total"].max()) if "career_job_total" in group else None,
                         "n_top_skills": len(top), "n_covered_top_skills": int((top["coverage"] > 0).sum()),
                         "matched_skills": top_matched, "priority_gaps": top_gaps,
                         "explanation": f"The materials cover {', '.join(top_matched) if top_matched else 'none of the top skills detected'}; the largest remaining gaps are {', '.join(top_gaps[:3]) if top_gaps else 'none'}."})
        for _, row in top.iterrows():
            evidence = study_lookup.get(row["canonical_skill"], {})
            detail_rows.append({"career": career, "skill": row["canonical_skill"],
                                "skill_category": row.get("skill_category", ""),
                                "demand_weight": float(row["demand_weight"]), "coverage": float(row["coverage"]),
                                "contribution": float(row["contribution"]),
                                "remaining_gain": float(row["remaining_gain"]),
                                "status": "covered" if row["coverage"] > 0 else "gap",
                                "coverage_level": evidence.get("level"),
                                "evidence_source": evidence.get("source"),
                                "units": evidence.get("units", []),
                                "pages": evidence.get("pages", []),
                                "evidence": evidence.get("evidence"),
                                "semantic_score": evidence.get("semantic_score")})
    ranking = pd.DataFrame(rankings).sort_values(["match_score", "career"], ascending=[False, True]).reset_index(drop=True)
    ranking.insert(0, "rank", np.arange(1, len(ranking) + 1))
    return ranking, pd.DataFrame(detail_rows)


def learning_recommendations(details: pd.DataFrame, career: str, k: int = 5) -> pd.DataFrame:
    """Turn the largest actionable gaps for one career into a ranked learning plan."""
    if career not in set(details["career"]):
        raise ValueError(f"Unknown career: {career}")
    gaps = (details[(details["career"] == career) & (details["status"] == "gap")]
            .sort_values(["remaining_gain", "demand_weight"], ascending=False)
            .head(k).copy())
    gaps.insert(0, "priority", np.arange(1, len(gaps) + 1))
    gaps["why_recommended"] = gaps.apply(
        lambda r: f"High career demand ({r.demand_weight:.3f}) with no detected coverage in the selected materials.",
        axis=1,
    )
    gaps["suggested_action"] = gaps["skill"].map(_learning_action)
    return gaps[["priority", "career", "skill", "skill_category", "demand_weight",
                 "coverage", "why_recommended", "suggested_action"]].rename(
        columns={"coverage": "current_coverage"}
    )


def app_payload(ranking: pd.DataFrame, details: pd.DataFrame) -> list[dict]:
    """Create a JSON-safe result for the Streamlit app."""
    payload = json.loads(ranking.to_json(orient="records"))
    for record in payload:
        relevant = details[details["career"].eq(record["career"])]
        record["skill_details"] = json.loads(
            relevant.sort_values("demand_weight", ascending=False).to_json(orient="records")
        )
        record["learning_recommendations"] = json.loads(
            learning_recommendations(details, record["career"]).to_json(orient="records")
        )
    return payload


def recommend_for_frontend(study, career_profiles: pd.DataFrame, top_k: int = 5,
                           top_n: int = DEFAULT_TOP_N) -> list[dict]:
    """Return a fresh JSON-safe top-k recommendation payload for a frontend.

    ``study`` may be a Step 3/4 coverage DataFrame, a ``skill -> coverage``
    mapping, or an iterable of skill names.  Unlike ``demo_app_payload.json``,
    this function recalculates the result for every uploaded document/profile.
    """
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    ranking, details = match_careers(study, career_profiles, top_n=top_n)
    return app_payload(ranking.head(top_k).copy(), details)


def sensitivity_analysis(study, career_profiles: pd.DataFrame,
                         cutoffs: Iterable[int] = (20, 30, 40)) -> pd.DataFrame:
    """Recalculate scores under alternative top-skill cutoffs."""
    rows = []
    for top_n in cutoffs:
        ranking, _ = match_careers(study, career_profiles, top_n=top_n)
        rows.extend({"top_n": top_n, "rank": int(r.rank), "career": r.career,
                     "match_percent": float(r.match_percent)} for r in ranking.itertuples())
    return pd.DataFrame(rows)


def run_demo(root: Path, output_dir: Path, unit_ids: list[str] | None = None,
             top_n: int = DEFAULT_TOP_N) -> pd.DataFrame:
    jobs = pd.read_csv(root / "step1_data" / "job_cleaned.csv")
    job_hits = pd.read_csv(root / "step4_semantic" / "results" / "hybrid_job_skills" / "job_skills_hybrid_long.csv")
    study_hits = pd.read_csv(root / "step4_semantic" / "results" / "details" / "curriculum_all_hits.csv")
    profiles = build_career_profiles(job_hits, jobs)
    study = study_coverage_from_hits(study_hits, unit_ids=unit_ids)
    ranking, details = match_careers(study, profiles, top_n=top_n)
    sensitivity = sensitivity_analysis(study, profiles)
    learning = pd.concat(
        [learning_recommendations(details, career) for career in ranking["career"]],
        ignore_index=True,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    profiles.to_csv(output_dir / "career_profiles.csv", index=False)
    study.to_json(output_dir / "demo_study_profile.json", orient="records", indent=2)
    ranking.to_csv(output_dir / "demo_career_ranking.csv", index=False)
    details.to_csv(output_dir / "demo_skill_explanations.csv", index=False)
    sensitivity.to_csv(output_dir / "demo_sensitivity.csv", index=False)
    learning.to_csv(output_dir / "demo_learning_recommendations.csv", index=False)
    (output_dir / "demo_app_payload.json").write_text(json.dumps(app_payload(ranking, details), indent=2), encoding="utf-8")
    return ranking


def main() -> None:
    parser = argparse.ArgumentParser(description="Build career profiles and run the Step 5 matching demo")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "outputs")
    parser.add_argument("--unit", action="append", dest="units", help="Unit ID to include; repeat for multiple units")
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    args = parser.parse_args()
    ranking = run_demo(args.root, args.output, unit_ids=args.units, top_n=args.top_n)
    print(ranking[["rank", "career", "match_percent", "n_covered_top_skills"]].to_string(index=False))


if __name__ == "__main__":
    main()
