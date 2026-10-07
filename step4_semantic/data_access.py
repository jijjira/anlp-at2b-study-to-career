"""Load Step 3 assets (jobs, gold labels, dictionary, baseline extractors) without depending on the working dir.

Step 3's evaluate.py reads "job_cleaned.csv" with a relative path at import time, so we do NOT import it for the
numbers; metrics.py re-implements its definitions and `verify_against_step3` checks the two agree on the
baseline numbers reported in Step 3 (S0 F1 0.872, S5 F1 0.943).
"""
from __future__ import annotations

import contextlib
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

import config
import metrics
from semantic_extractor import load_skill_table


@contextlib.contextmanager
def in_dir(path):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


@dataclass
class Context:
    step3: Path
    jobs: pd.DataFrame
    GOLD: dict
    rows: list
    table: pd.DataFrame
    universe: set
    v1: object                      # S0: Step 3 PhraseMatcher baseline
    s5: object                      # S5: Baseline++ (reviewed aliases + plural variants)
    views: dict
    base_preds: dict = field(default_factory=dict)      # system name -> {row: set}


def load_context(step3_dir=None) -> Context:
    step3 = config.find_step3(step3_dir)
    if str(step3) not in sys.path:
        sys.path.insert(0, str(step3))
    from skill_extractor import SkillExtractor                              # noqa: E402
    from skill_extractor_v2 import RequirementAwareExtractor                # noqa: E402
    from gold_annotations import GOLD                                       # noqa: E402

    jobs = pd.read_csv(step3 / "job_cleaned.csv", encoding="utf-8-sig")
    table = load_skill_table(step3)
    universe = set(table.canonical_skill)
    rows = sorted(GOLD)
    v1 = SkillExtractor()
    s5 = RequirementAwareExtractor(extra_aliases_path=str(step3 / "extra_aliases_reviewed.csv"), expand_morphology=True)
    ctx = Context(step3, jobs, GOLD, rows, table, universe, v1, s5, metrics.gold_views(GOLD, rows, universe))
    ctx.base_preds = {
        "S0 Baseline (PhraseMatcher)": {r: set(v1.extract_skills(jobs.job_description[r])) & universe for r in rows},
        "S5 Baseline++": {r: set(s5.extract_skills(jobs.job_description[r])) & universe for r in rows},
    }
    return ctx


def verify_against_step3(ctx: Context, tol: float = 0.002) -> dict:
    """Check our metric code reproduces the Step 3 headline numbers (S0 0.872, S5 0.943) and, when possible,
    Step 3's own evaluate.py. Raises AssertionError on mismatch."""
    out = {}
    for name, ref in (("S0 Baseline (PhraseMatcher)", 0.872), ("S5 Baseline++", 0.943)):
        res = metrics.prf(ctx.base_preds[name], ctx.views["strict"], ctx.rows)
        out[name] = res
        assert abs(res["F1"] - ref) <= tol, f"{name}: F1 {res['F1']:.3f} differs from Step 3 value {ref}"
    try:                                           # optional cross-check against Step 3's own code
        with in_dir(ctx.step3):
            import evaluate as ev                  # noqa: E402
            _, table = ev.run()
        key = [k for k in table.index if k[0].startswith("extended") and k[1].startswith("S5")][0]
        assert abs(table.loc[key, "F1"] - out["S5 Baseline++"]["F1"]) <= 1e-9
        out["evaluate_py_agrees"] = True
    except (ImportError, FileNotFoundError, KeyError, IndexError) as e:   # cross-check is optional
        out["evaluate_py_agrees"] = f"skipped ({type(e).__name__})"
    return out


def step3_bootstrap(ctx: Context, preds_a: dict, preds_b: dict, n: int = config.N_BOOT, seed: int = config.SEED):
    """Strict-F1 paired bootstrap computed by Step 3's OWN `evaluate.bootstrap` (the same function Member 3 used).

    preds_a / preds_b: {row: set(skills)} for the 30 gold ads. Returns Step 3's dict (F1_a, F1_b, delta, delta_CI,
    p_delta_le_0), or None if Step 3's evaluate.py cannot be imported (e.g. in the offline unit tests).
    """
    try:
        with in_dir(ctx.step3):
            import evaluate as ev                                           # noqa: E402
            if Path(getattr(ev, "__file__", "")).resolve().parent != Path(ctx.step3).resolve():
                return None                                                 # a different `evaluate` package was imported
            return ev.bootstrap({"a": preds_a, "b": preds_b}, "a", "b", universe=ctx.universe, n=n, seed=seed)
    except (ImportError, FileNotFoundError, KeyError, OSError):
        return None
