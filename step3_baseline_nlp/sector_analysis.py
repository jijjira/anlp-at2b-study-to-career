"""Sector lens: do the skills the market demands depend on the employer's sector?

All uncertainty is **company-clustered**: ads from one company are not independent (one company writes many
similar ads), so bootstrap and permutation steps resample or shuffle whole companies, never single ads.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from skill_extractor_v2 import DEFAULT_WEIGHTS


class SectorModel:
    def __init__(self, strengths: list[dict], companies, sector_of: dict, careers=None, weights=None):
        w = dict(DEFAULT_WEIGHTS if weights is None else weights)
        self.skills = sorted({s for d in strengths for s in d})
        self.sidx = {s: i for i, s in enumerate(self.skills)}
        self.W = np.zeros((len(strengths), len(self.skills)))
        for r, d in enumerate(strengths):
            for s, st in d.items():
                self.W[r, self.sidx[s]] = w.get(st, 0.0)
        self.companies_per_ad = np.asarray(companies)
        self.company_names = sorted(set(self.companies_per_ad))
        cidx = {c: i for i, c in enumerate(self.company_names)}
        self.ad_company = np.array([cidx[c] for c in self.companies_per_ad])
        nC, nS = len(self.company_names), len(self.skills)
        self.C_sum = np.zeros((nC, nS)); self.C_n = np.zeros(nC)
        np.add.at(self.C_sum, self.ad_company, self.W); np.add.at(self.C_n, self.ad_company, 1)
        self.sectors = sorted(set(sector_of[c] for c in self.company_names))
        self.company_sector = np.array([self.sectors.index(sector_of[c]) for c in self.company_names])
        self.onehot = np.eye(len(self.sectors))[self.company_sector]            # companies x sectors
        self.careers = None if careers is None else np.asarray(careers)

    # ---- basic tables ------------------------------------------------------
    def _sector_means(self, weight=None):
        w = np.ones(len(self.company_names)) if weight is None else weight
        A = self.onehot * w[:, None]
        n = A.T @ self.C_n
        return (A.T @ self.C_sum) / np.maximum(n, 1)[:, None], n

    def demand_table(self) -> pd.DataFrame:
        m, _ = self._sector_means()
        return pd.DataFrame(m, index=self.sectors, columns=self.skills)

    # ---- distinctive skills with company-cluster bootstrap ----------------------
    def distinctive(self, sector: str, n_boot: int = 1000, seed: int = 36118, min_ads_with_skill: int = 5,
                    k: int = 8) -> pd.DataFrame:
        """Skills whose demand in `sector` exceeds demand elsewhere, with a company-cluster 95% interval."""
        si = self.sectors.index(sector)
        rng = np.random.default_rng(seed)
        nC = len(self.company_names)

        def diff(w):
            A = self.onehot * w[:, None]
            n_all = (w * self.C_n).sum(); s_all = (w[:, None] * self.C_sum).sum(0)
            n_in = A[:, si] @ self.C_n; s_in = A[:, si] @ self.C_sum
            if n_in == 0 or n_all - n_in == 0:
                return np.zeros(len(self.skills))
            return s_in / n_in - (s_all - s_in) / (n_all - n_in)

        point = diff(np.ones(nC))
        draws = np.array([diff(np.bincount(rng.integers(0, nC, nC), minlength=nC).astype(float)) for _ in range(n_boot)])
        lo, hi = np.quantile(draws, [0.025, 0.975], axis=0)
        in_ads = self.W[self.sector_of_ad() == si]
        n_with = (in_ads > 0).sum(0)
        m, _ = self._sector_means()
        rest = (self.C_sum.sum(0) - self.onehot[:, si] @ self.C_sum) / (self.C_n.sum() - self.onehot[:, si] @ self.C_n)
        df = pd.DataFrame({"skill": self.skills, "demand_in_sector": m[si], "demand_elsewhere": rest, "difference": point,
                           "ci_low": lo, "ci_high": hi, "ads_with_skill": n_with})
        df = df[(df.ads_with_skill >= min_ads_with_skill)]
        df["robust"] = df.ci_low > 0                              # interval excludes zero
        return df.sort_values("difference", ascending=False).head(k).reset_index(drop=True)

    def sector_of_ad(self) -> np.ndarray:
        return self.company_sector[self.ad_company]

    # ---- does sector matter? company-level permutation test ----------------------
    def _spread(self, labels: np.ndarray, adjust: bool, main: np.ndarray) -> float:
        """Mean pairwise Euclidean distance between sector demand vectors (optionally career-adjusted)."""
        oh = np.eye(len(self.sectors))[labels][:, main]
        if adjust:
            base = self._career_adjusted_sums()
            sums, n = base
        else:
            sums, n = self.C_sum, self.C_n
        A = oh
        nn = A.T @ n
        keep = nn > 0
        m = ((A.T @ sums) / np.maximum(nn, 1)[:, None])[keep]
        d = np.sqrt(((m[:, None, :] - m[None, :, :]) ** 2).sum(-1))
        iu = np.triu_indices(len(m), 1)
        return float(d[iu].mean())

    def _career_adjusted_sums(self):
        """Company sums of (ad demand minus the career-average demand): removes the effect of career mix."""
        if self.careers is None:
            raise ValueError("careers are needed for the career-adjusted test")
        R = self.W.copy()
        for c in set(self.careers):
            rows = self.careers == c
            R[rows] -= self.W[rows].mean(0)
        sums = np.zeros_like(self.C_sum); np.add.at(sums, self.ad_company, R)
        return sums, self.C_n

    def permutation_test(self, main_sectors, n_perm: int = 2000, seed: int = 36118, adjust_career: bool = False) -> dict:
        """Shuffle sector labels among companies; compare observed spread between sector profiles to the shuffled spread."""
        main = np.array([s in set(main_sectors) for s in self.sectors])
        # restrict to companies in main sectors
        cmask = main[self.company_sector]
        rng = np.random.default_rng(seed)
        obs_labels = self.company_sector.copy()
        sub = np.where(cmask)[0]
        saved = (self.C_sum, self.C_n, self.company_sector)
        try:
            self.C_sum, self.C_n = saved[0][sub], saved[1][sub]
            if adjust_career:
                full_sums, _ = self._career_adjusted_sums_full(saved)
                self.C_sum = full_sums[sub]
            obs = self._spread(obs_labels[sub], False, main)
            null = np.array([self._spread(rng.permutation(obs_labels[sub]), False, main) for _ in range(n_perm)])
        finally:
            self.C_sum, self.C_n, self.company_sector = saved
        p = (1 + (null >= obs).sum()) / (1 + n_perm)
        return {"observed_spread": obs, "null_mean": float(null.mean()), "null_95": float(np.quantile(null, 0.95)), "p_value": float(p),
                "null": null, "career_adjusted": adjust_career}

    def _career_adjusted_sums_full(self, saved):
        old = (self.C_sum, self.C_n)
        self.C_sum, self.C_n = saved[0], saved[1]
        try:
            return self._career_adjusted_sums()
        finally:
            self.C_sum, self.C_n = old

    # ---- curriculum fit per sector, company-cluster bootstrap ----------------------
    def fit(self, student, topn: int = 30, n_boot: int = 500, seed: int = 36118) -> pd.DataFrame:
        cov = np.zeros(len(self.skills))
        items = student.items() if isinstance(student, dict) else ((s, 1.0) for s in student)
        for s, c in items:
            if s in self.sidx:
                cov[self.sidx[s]] = c
        rng = np.random.default_rng(seed)
        nC = len(self.company_names)

        def fit_from(w):
            A = self.onehot * w[:, None]
            n = A.T @ self.C_n
            m = (A.T @ self.C_sum) / np.maximum(n, 1)[:, None]
            out = np.zeros(len(self.sectors))
            for i in range(len(self.sectors)):
                top = np.argsort(-m[i])[:topn]
                den = m[i][top].sum()
                out[i] = (m[i][top] * cov[top]).sum() / den if den > 0 else 0.0
            return out

        point = fit_from(np.ones(nC))
        draws = np.array([fit_from(np.bincount(rng.integers(0, nC, nC), minlength=nC).astype(float)) for _ in range(n_boot)])
        lo, hi = np.quantile(draws, [0.025, 0.975], axis=0)
        n_ads = (self.onehot.T @ self.C_n).astype(int)
        return pd.DataFrame({"sector": self.sectors, "ads": n_ads, "fit": point, "ci_low": lo, "ci_high": hi}
                            ).sort_values("fit", ascending=False).reset_index(drop=True)

    def gaps(self, student, sector: str, k: int = 8, exclude=()) -> pd.DataFrame:
        m, _ = self._sector_means(); si = self.sectors.index(sector)
        cov = np.zeros(len(self.skills))
        items = student.items() if isinstance(student, dict) else ((s, 1.0) for s in student)
        for s, c in items:
            if s in self.sidx:
                cov[self.sidx[s]] = c
        gain = m[si] * (1 - cov)
        for s in exclude:
            if s in self.sidx:
                gain[self.sidx[s]] = -1
        order = np.argsort(-gain)[:k]
        return pd.DataFrame({"skill": [self.skills[i] for i in order], "demand": m[si][order].round(3),
                             "current_coverage": cov[order], "marginal_gain": gain[order].round(3)})
