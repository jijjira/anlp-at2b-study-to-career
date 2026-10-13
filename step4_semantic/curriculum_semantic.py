"""Semantic layer on the STUDENT side: 20 real unit PDFs (UTS, USYD, UNSW) from Step 3.

This addresses Step 3's stated limitation "extractor validated on job ads, not unit text" and the ready-made test in
the two test cases: UNSW COMP9311 (Database Systems) yields zero skills with exact matching because the handbook text never
says "SQL", and UTS 36103 says "statistical" but never "Statistics".

Unit text has no gold labels, so we (a) report what the semantic layer ADDS with the evidence sentence and page,
(b) check the two named cases, and (c) write a blinded label sheet for human labelling; `evaluate_unit_labels` then gives the
precision of exact vs semantic hits with Wilson 95% intervals. Recall on unit text is NOT measured (no full labels).

The same coverage levels as Step 3 are used (assessed 1.0 / taught 0.75 / mentioned 0.5), and the same filters keep
requisites, "further study" sentences, course codes and AI-policy tables from counting as coverage.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import config
import metrics
from semantic_extractor import Decision, SkillSpace, detect, make_units

LEVEL_RANK = {"assessed": 0, "taught": 1, "mentioned": 2}


def _step3_modules(step3: Path):
    if str(step3) not in sys.path:
        sys.path.insert(0, str(step3))
    import extraction                                                       # noqa: E402
    return extraction


def semantic_additions_for_pages(pages: list[str], exact_skills: set[str], space: SkillSpace, encoder,
                                 decision: Decision, ext, granularity: str = "line+clause",
                                 min_words: int = 3, max_words: int = 60) -> dict:
    """Best semantic evidence per skill over all pages: {skill: dict(level, page, score, cosine, evidence)}."""
    best: dict[str, dict] = {}
    for pno, text in enumerate(pages, start=1):
        levels = ext.tag_lines(text)
        segs = []
        for i, line in enumerate(text.split("\n")):
            line = line.strip()
            if not line or ext._NOT_COVERED.search(line) or ext._COURSE_CODE.search(line):
                continue                                              # catalogue reference, not coverage
            segs.append((i, line, levels.get(i, ext.MENTIONED)))
        units = make_units(segs, granularity, min_words, max_words)
        if not units:
            continue
        S = space.similarity(encoder.encode([u.text for u in units]))
        for k, (score, row) in detect(space.normalise(S, decision.norm), decision).items():
            sk = space.skills[k]
            if sk in exact_skills:
                continue
            u = units[row]
            cur = best.get(sk)
            cand = dict(level=u.strength, page=pno, score=score, cosine=float(S[row, k]), evidence=u.text[:200])
            if cur is None or (LEVEL_RANK[cand["level"]], -cand["score"]) < (LEVEL_RANK[cur["level"]], -cur["score"]):
                cand["pages"] = sorted({pno} | set(cur["pages"] if cur else []))
                best[sk] = cand
            else:
                cur["pages"] = sorted(set(cur["pages"]) | {pno})
    return best


def load_curriculum_hybrid(step3: Path, space: SkillSpace, encoder, decision: Decision, granularity="line+clause",
                           min_words=3, max_words=60):
    """-> (profiles_exact, profiles_hybrid, manifest, additions DataFrame). Profiles are Step 3 StudyProfile objects
    (hybrid ones carry extra keys source/score), so alignment.curriculum_coverage / DemandModel work unchanged."""
    ext = _step3_modules(step3)
    man = pd.read_csv(Path(step3) / "data" / "curriculum_manifest.csv").fillna("")
    exact_p, hyb_p, found, add_rows = {}, {}, [], []
    cat = space.category
    for _, r in man.iterrows():
        path = Path(step3) / "data" / "curriculum_pdfs" / r.file
        if not path.exists():
            continue
        pages = ext.clean_pages(ext.read_pdf_pages(str(path)))
        prof = ext.analyse_pages(pages)
        excluded = [x.strip() for x in r.excluded_skills.split(";") if x.strip()]
        for s in excluded:
            prof.skills.pop(s, None)
        for d in prof.skills.values():
            d["source"] = "exact"
        hyb = copy.deepcopy(prof)
        adds = semantic_additions_for_pages(pages, set(prof.skills) | set(excluded), space, encoder, decision, ext,
                                            granularity, min_words, max_words)
        for sk, a in adds.items():
            hyb.skills[sk] = dict(mentions=len(a["pages"]), pages=a["pages"], level=a["level"],
                                  category=cat.get(sk, ""), evidence=a["evidence"],
                                  weight=ext.COVERAGE_WEIGHTS[a["level"]], source="semantic", score=a["score"])
            add_rows.append(dict(unit_id=r.unit_id, skill=sk, page=a["page"], level=a["level"],
                                 score=round(a["score"], 3), cosine=round(a["cosine"], 3), evidence=a["evidence"]))
        exact_p[r.unit_id], hyb_p[r.unit_id] = prof, hyb
        found.append(r)
    return exact_p, hyb_p, pd.DataFrame(found), pd.DataFrame(add_rows)


def analyse_study_material_semantic(source, step3: Path, hybrid_space: SkillSpace, encoder, decision: Decision,
                                    granularity="line+clause"):
    """One uploaded PDF -> StudyProfile with semantic additions (for the Streamlit app)."""
    ext = _step3_modules(step3)
    pages = ext.clean_pages(ext.read_pdf_pages(source))
    prof = ext.analyse_pages(pages)
    for d in prof.skills.values():
        d["source"] = "exact"
    adds = semantic_additions_for_pages(pages, set(prof.skills), hybrid_space, encoder, decision, ext, granularity)
    for sk, a in adds.items():
        prof.skills[sk] = dict(mentions=len(a["pages"]), pages=a["pages"], level=a["level"],
                               category=hybrid_space.category.get(sk, ""), evidence=a["evidence"],
                               weight=ext.COVERAGE_WEIGHTS[a["level"]], source="semantic", score=a["score"])
    return prof


NAMED_CHECKS = [("UNSW COMP9311", "SQL"), ("UTS 36103", "Statistics")]


def named_checks(exact_p: dict, hyb_p: dict, man: pd.DataFrame) -> list[dict]:
    """The two named test cases. Unit ids are matched by substring on the manifest unit_id / code."""
    out = []
    for key, skill in NAMED_CHECKS:
        uni, code = key.split()
        ids = [u for u in exact_p if code in u and uni in u] or [u for u in exact_p if code in u]
        for u in ids:
            h = hyb_p[u].skills.get(skill)
            out.append(dict(unit=u, skill=skill, exact_found=skill in exact_p[u].skills, hybrid_found=h is not None,
                            n_exact_skills=len(exact_p[u].skills), n_hybrid_skills=len(hyb_p[u].skills),
                            evidence=(h or {}).get("evidence"), page=((h or {}).get("pages") or [None])[0],
                            score=(h or {}).get("score")))
    return out


def all_hits(exact_p: dict, hyb_p: dict) -> pd.DataFrame:
    """Every (unit, skill) the hybrid reports, with its source (exact | semantic). For reference, not for labelling."""
    recs = []
    for u, p in hyb_p.items():
        for sk, d in p.skills.items():
            recs.append(dict(unit_id=u, skill=sk, source=d.get("source", "exact"), page=(d["pages"] or [None])[0],
                             level=d["level"], score=d.get("score"), evidence=d["evidence"]))
    return pd.DataFrame(recs).sort_values(["source", "unit_id", "skill"]).reset_index(drop=True)


def label_sheet(exact_p: dict, hyb_p: dict, n_exact: int = 30, seed: int = config.SEED):
    """Blinded, sampled sheet for human labelling of unit-text precision.

    Contains ALL semantic additions plus a random sample of `n_exact` (default 30) exact-match hits, shuffled, WITHOUT the source or
    score columns, so annotators cannot tell which method found what. Returns (sheet, key); `key` maps item_id -> source
    and is only used by `evaluate_unit_labels`. Labelling every hit (hundreds of rows) is not needed to estimate precision.
    """
    hits = all_hits(exact_p, hyb_p)
    sem = hits[hits.source == "semantic"]
    exa = hits[hits.source == "exact"]
    exa = exa.sample(n=min(n_exact, len(exa)), random_state=seed)
    pool = pd.concat([sem, exa]).sample(frac=1.0, random_state=seed).reset_index(drop=True)
    pool.insert(0, "item_id", [f"U{i:04d}" for i in range(len(pool))])
    key = pool[["item_id", "unit_id", "skill", "source", "score"]]
    sheet = pool[["item_id", "unit_id", "skill", "page", "level", "evidence"]].assign(human_label="", annotator="")
    return sheet, key


def evaluate_unit_labels(sheet_path: Path | None = None, key_path: Path | None = None) -> pd.DataFrame:
    """Precision of exact vs semantic hits on unit text from the filled sheet (Wilson 95% CI).

    Exact hits are a random SAMPLE, so their precision is an estimate for all exact hits; semantic hits are all labelled.
    Recall on unit text is not measured (no complete labels).
    """
    sp = Path(sheet_path) if sheet_path else config.AUDIT / "curriculum_label_sheet.csv"
    kp = Path(key_path) if key_path else config.AUDIT / "curriculum_label_key.csv"
    df = pd.read_csv(sp).merge(pd.read_csv(kp)[["item_id", "source"]], on="item_id", how="left")
    df = df[df.human_label.astype(str).isin(["0", "1", "0.0", "1.0"])]
    recs = []
    for src, g in df.groupby("source"):
        k, n = int((g.human_label.astype(float) == 1).sum()), len(g)
        lo, hi = metrics.wilson(k, n)
        recs.append(dict(source=src, n_labelled=n, correct=k, precision=k / n if n else np.nan, ci_lo=lo, ci_hi=hi))
    return pd.DataFrame(recs)


def career_fit_comparison(step3: Path, jobs: pd.DataFrame, base_extractor, hybrid_extractor, exact_p, hyb_p,
                          n_boot: int = 200) -> pd.DataFrame:
    """Career fit of the whole 20-unit catalogue, exact vs hybrid on BOTH sides (demand from jobs, coverage from units)."""
    if str(step3) not in sys.path:
        sys.path.insert(0, str(step3))
    from alignment import DemandModel, curriculum_coverage, job_strengths   # noqa: E402
    out = {}
    for name, ex, profs in (("exact", base_extractor, exact_p), ("hybrid", hybrid_extractor, hyb_p)):
        D = DemandModel(job_strengths(jobs.job_description, ex), jobs.career_category)
        cov = {s: d["weight"] for s, d in curriculum_coverage(profs).items()}
        fit = D.fit(cov, n_boot=n_boot).set_index("career")
        out[f"{name}_fit"], out[f"{name}_lo"], out[f"{name}_hi"] = fit.fit, fit.ci_low, fit.ci_high
        out[f"{name}_n_skills_covered"] = pd.Series(len(cov), index=fit.index)
    return pd.DataFrame(out).round(3).reset_index()
