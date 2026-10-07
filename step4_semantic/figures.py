"""Figures for the report/slides (saved to figures/ as PNG, dpi 200). Inputs are the CSVs written by run_all.py."""
from __future__ import annotations


import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config

BLUE, ORANGE, GREY, INK = "#2a78d6", "#d6732a", "#b9b8b2", "#0b0b0b"


def _save(fig, name):
    config.FIGURES.mkdir(exist_ok=True)
    fig.savefig(config.FIGURES / f"{name}.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def fig_threshold_sweep(sweep: pd.DataFrame, model: str, base_lenient_f1: float, base_i_recall: float):
    """Metrics vs threshold (margin rule off) - shows the precision/recall trade-off and how flat the optimum is."""
    d = sweep[sweep.delta.isna()] if "delta" in sweep else sweep
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
    ax[0].plot(d.tau, d.lenient_F1, color=BLUE, label="lenient F1 (R+P+I gold)")
    ax[0].plot(d.tau, d.strict_F1, color=ORANGE, label="strict F1 (R+P gold)")
    ax[0].axhline(base_lenient_f1, color=BLUE, ls=":", lw=1, label="Baseline++ lenient F1")
    ax[0].set_xlabel("similarity threshold"); ax[0].set_ylabel("micro F1"); ax[0].legend(fontsize=8)
    ax[0].set_title(f"{model}: F1 vs threshold (in-sample sweep)")
    ax[1].plot(d.tau, d.I_recall, color=BLUE, label="I-recall")
    ax[1].plot(d.tau, d.added_precision, color=ORANGE, label="precision of additions")
    ax[1].axhline(base_i_recall, color=GREY, ls=":", label="Baseline++ I-recall")
    ax[1].set_xlabel("similarity threshold"); ax[1].legend(fontsize=8)
    ax[1].set_title("Implicit-skill recall vs precision of additions")
    _save(fig, f"fig_s4_threshold_sweep_{model}")


def fig_model_comparison(table: pd.DataFrame, boots: pd.DataFrame, base_row: pd.Series):
    """Lenient F1 and I-recall (out-of-fold) per model, with paired-bootstrap 95% CI of the difference to Baseline++."""
    t = table[~table.semantic_only].reset_index(drop=True)
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
    for a, metric, label, base in ((ax[0], "lenient_F1", "lenient F1", base_row["lenient_F1"]),
                                   (ax[1], "I_recall", "I-recall", base_row["I_recall"])):
        b = boots[(boots.vs == "S5 Baseline++") & (boots.metric == metric)].set_index("system")
        vals = [t.loc[i, metric] for i in t.index]
        lo = [b.loc[s, "delta_lo"] - b.loc[s, "delta"] for s in t.system]
        hi = [b.loc[s, "delta_hi"] - b.loc[s, "delta"] for s in t.system]
        x = np.arange(len(t))
        a.bar(x, vals, color=[GREY if m == "hashing" else BLUE for m in t.model])
        a.errorbar(x, vals, yerr=[-np.array(lo), hi], fmt="none", ecolor=INK, capsize=3, lw=1)
        a.axhline(base, color=ORANGE, ls="--", lw=1, label="Baseline++")
        names = [s.replace(" hybrid", "").replace("(pool chosen in CV)", "(CV pool)") for s in t.system]
        a.set_xticks(x); a.set_xticklabels(names, rotation=20); a.set_ylabel(label); a.legend(fontsize=8)
        a.set_title(f"{label}: out-of-fold; bars = 95% CI of difference to Baseline++")
        a.set_ylim(min(vals + [base]) - 0.1, 1.0)
    _save(fig, "fig_s4_model_comparison")


def fig_ablation(abl: pd.DataFrame):
    labels = [f"{r.factor}: {r.setting}" for r in abl.itertuples()]
    y = np.arange(len(abl))[::-1]
    fig, ax = plt.subplots(figsize=(8, 0.38 * len(abl) + 1.2))
    ax.barh(y, abl.lenient_F1, color=[ORANGE if d else BLUE for d in abl.is_default])
    ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=8); ax.set_xlabel("lenient F1 (out-of-fold)")
    ax.set_xlim(abl.lenient_F1.min() - 0.05, min(1.0, abl.lenient_F1.max() + 0.03))
    ax.set_title("Ablation around the default configuration (orange = default)")
    _save(fig, "fig_s4_ablation")
