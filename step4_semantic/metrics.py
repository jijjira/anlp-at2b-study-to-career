"""Evaluation metrics for Step 4 (same definitions as Step 3's evaluate.py, plus tier-aware extensions).

Gold tiers (gold_annotations.py): R explicit required, P explicit preferred, I implicit (no dictionary alias),
OTHER outside the dictionary. Universe = base dictionary + reviewed extra aliases (Step 3 "extended" scope).

Two scoring views, always reported together:
  strict   gold = (R | P) & universe        <- Step 3's headline metric. Valid implicit skills found by a semantic
                                               method count as false positives here, so strict precision is a
                                               deliberately pessimistic view for this method.
  lenient  gold = (R | P | I) & universe     <- an ad that demands a skill implicitly does demand it, so finding it
                                               is correct. This is the fair view for the semantic layer.
Plus I-recall = share of the implicit (I) labels recovered, and the precision of the semantic ADDITIONS alone.
"""
from __future__ import annotations

import math
import random
from typing import Callable, Mapping

import numpy as np


def gold_views(GOLD: Mapping, rows, universe: set) -> dict:
    return dict(
        strict={r: (GOLD[r]["R"] | GOLD[r]["P"]) & universe for r in rows},
        lenient={r: (GOLD[r]["R"] | GOLD[r]["P"] | GOLD[r]["I"]) & universe for r in rows},
        I={r: GOLD[r]["I"] & universe for r in rows},
        RP={r: (GOLD[r]["R"] | GOLD[r]["P"]) & universe for r in rows},
    )


def counts(pred: Mapping, gold: Mapping, rows) -> tuple[int, int, int]:
    tp = sum(len(pred[r] & gold[r]) for r in rows)
    fp = sum(len(pred[r] - gold[r]) for r in rows)
    fn = sum(len(gold[r] - pred[r]) for r in rows)
    return tp, fp, fn


def prf(pred: Mapping, gold: Mapping, rows) -> dict:
    """Micro precision / recall / F1 (identical to evaluate.prf when gold = strict view)."""
    tp, fp, fn = counts(pred, gold, rows)
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return dict(TP=tp, FP=fp, FN=fn, P=p, R=r, F1=2 * p * r / (p + r) if p + r else 0.0)


def i_recall(pred: Mapping, I: Mapping, rows) -> float:
    hit = sum(len(pred[r] & I[r]) for r in rows)
    tot = sum(len(I[r]) for r in rows)
    return hit / tot if tot else 0.0


def additions_precision(pred: Mapping, base_pred: Mapping, lenient: Mapping, I: Mapping, rows) -> dict:
    """Precision of what the semantic layer ADDED on top of base_pred."""
    added = {r: pred[r] - base_pred[r] for r in rows}
    n = sum(len(a) for a in added.values())
    ok = sum(len(added[r] & lenient[r]) for r in rows)
    ok_i = sum(len(added[r] & I[r]) for r in rows)
    return dict(n_added=n, added_per_ad=n / max(1, len(rows)), added_correct=ok, added_I=ok_i,
                added_precision=ok / n if n else float("nan"))


def summarise(pred: Mapping, base_pred: Mapping, views: Mapping, rows) -> dict:
    s, l = prf(pred, views["strict"], rows), prf(pred, views["lenient"], rows)
    out = {f"strict_{k}": v for k, v in s.items()}
    out.update({f"lenient_{k}": v for k, v in l.items()})
    out["I_recall"] = i_recall(pred, views["I"], rows)
    out.update(additions_precision(pred, base_pred, views["lenient"], views["I"], rows))
    return out


# --------------------------------------------------------------------------- #
# Paired bootstrap over ads (same resampling idea and seed as evaluate.bootstrap)
# --------------------------------------------------------------------------- #
def metric_fn(name: str, views: Mapping) -> Callable:
    def f1(pred, rows, g):
        tp, fp, fn = counts(pred, g, rows)
        return 2 * tp / (2 * tp + fp + fn) if tp else 0.0

    def prec(pred, rows, g):
        tp, fp, _ = counts(pred, g, rows)
        return tp / (tp + fp) if tp + fp else 0.0

    table = {
        "strict_F1": lambda p, rows: f1(p, rows, views["strict"]),
        "lenient_F1": lambda p, rows: f1(p, rows, views["lenient"]),
        "lenient_P": lambda p, rows: prec(p, rows, views["lenient"]),
        "strict_P": lambda p, rows: prec(p, rows, views["strict"]),
        "I_recall": lambda p, rows: i_recall(p, views["I"], rows),
    }
    return table[name]


def paired_bootstrap(pred_a: Mapping, pred_b: Mapping, f: Callable, rows, n: int = 2000, seed: int = 36118) -> dict:
    """Delta = f(b) - f(a) over ad resamples. Returns point estimate, 95% percentile CI and one-sided p(delta<=0)."""
    rng, rows = random.Random(seed), list(rows)
    fa, fb, d = [], [], []
    for _ in range(n):
        sample = [rng.choice(rows) for _ in rows]
        x, y = f(pred_a, sample), f(pred_b, sample)
        fa.append(x), fb.append(y), d.append(y - x)
    q = lambda v: tuple(np.percentile(v, [2.5, 97.5]).round(3))
    point = f(pred_b, rows) - f(pred_a, rows)
    return dict(a=round(f(pred_a, rows), 3), b=round(f(pred_b, rows), 3), delta=round(point, 3),
                delta_CI=q(d), a_CI=q(fa), b_CI=q(fb), p_delta_le_0=float(np.mean(np.array(d) <= 0)))


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a proportion (used for the manual audits)."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, centre - half), min(1.0, centre + half))
