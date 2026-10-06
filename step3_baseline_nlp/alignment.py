"""Career alignment with uncertainty: student/curriculum skills vs demand-weighted career profiles.

Why bootstrap? The job ads are a modest, noisy sample (27 to 275 ads per career). Resampling the ads gives a
range for each career-fit score instead of one falsely precise number.

fit_c(K) = sum over the career's top-N skills s of  d_c(s) * cov(s)  /  sum over the same skills of d_c(s)
  d_c(s)  demand weight of skill s in career c (mean over ads of the requirement-strength weight)
  cov(s)  how strongly the student material covers s (assessed 1.0, taught 0.75, mentioned 0.5, absent 0)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from skill_extractor_v2 import DEFAULT_WEIGHTS


def job_strengths(job_descriptions, extractor) -> list[dict]:
    """Per ad: canonical skill -> strongest evidence class (required/duty/preferred/unlabelled/company)."""
    return [extractor.skill_strengths(t) for t in job_descriptions]


class DemandModel:
    """Demand weights per career, with bootstrap resampling over job ads."""

    def __init__(self, strengths: list[dict], careers, weights=None):
        w = dict(DEFAULT_WEIGHTS if weights is None else weights)
        self.careers = np.asarray(careers)
        self.skills = sorted({s for d in strengths for s in d})
        self.index = {s: i for i, s in enumerate(self.skills)}
        self.W = np.zeros((len(strengths), len(self.skills)))
        for r, d in enumerate(strengths):
            for s, st in d.items():
                self.W[r, self.index[s]] = w.get(st, 0.0)
        self.names = sorted(set(self.careers))
        self.rows = {c: np.where(self.careers == c)[0] for c in self.names}

    def demand(self, career: str, rows=None) -> np.ndarray:
        rows = self.rows[career] if rows is None else rows
        return self.W[rows].mean(axis=0)

    def table(self) -> pd.DataFrame:
        """career x skill demand weights."""
        return pd.DataFrame({c: self.demand(c) for c in self.names}, index=self.skills).T

    def _fit(self, cov: np.ndarray, d: np.ndarray, topn: int) -> float:
        top = np.argsort(-d)[:topn]
        denom = d[top].sum()
        return float((d[top] * cov[top]).sum() / denom) if denom > 0 else 0.0

    def coverage_vector(self, student) -> np.ndarray:
        """student: set of skills (weight 1) or dict skill -> coverage weight."""
        cov = np.zeros(len(self.skills))
        items = student.items() if isinstance(student, dict) else ((s, 1.0) for s in student)
        for s, c in items:
            if s in self.index:
                cov[self.index[s]] = c
        return cov

    def fit(self, student, topn: int = 30, n_boot: int = 500, seed: int = 36118, alpha: float = 0.05) -> pd.DataFrame:
        """Career fit with a bootstrap interval (resampling the ads of each career, recomputing its top-N)."""
        cov = self.coverage_vector(student)
        rng = np.random.default_rng(seed)
        out = []
        for c in self.names:
            rows = self.rows[c]
            point = self._fit(cov, self.demand(c), topn)
            draws = [self._fit(cov, self.demand(c, rng.choice(rows, size=len(rows), replace=True)), topn)
                     for _ in range(n_boot)]
            lo, hi = np.quantile(draws, [alpha / 2, 1 - alpha / 2])
            out.append({"career": c, "n_ads": len(rows), "fit": point, "ci_low": lo, "ci_high": hi})
        return pd.DataFrame(out).sort_values("fit", ascending=False).reset_index(drop=True)

    def gaps(self, student, career: str, k: int = 8, exclude=()) -> pd.DataFrame:
        """Skills with the largest remaining demand-weighted gain, given the current coverage.

        `exclude` drops umbrella terms (e.g. "Artificial Intelligence") that are too generic to act on.
        """
        cov = self.coverage_vector(student)
        d = self.demand(career)
        gain = d * (1.0 - cov)
        for s in exclude:
            if s in self.index:
                gain[self.index[s]] = -1.0
        order = np.argsort(-gain)[:k]
        return pd.DataFrame({"skill": [self.skills[i] for i in order], "demand": d[order].round(3),
                             "current_coverage": cov[order], "marginal_gain": gain[order].round(3)})


def curriculum_coverage(profiles: dict) -> dict:
    """Merge several StudyProfiles (unit name -> profile) into one curriculum: best coverage per skill, plus where."""
    merged = {}
    for unit, prof in profiles.items():
        for s, d in prof.skills.items():
            cur = merged.setdefault(s, {"weight": 0.0, "units": [], "best_level": None})
            cur["units"].append(unit)
            if d["weight"] > cur["weight"]:
                cur["weight"], cur["best_level"] = d["weight"], d["level"]
    return merged
