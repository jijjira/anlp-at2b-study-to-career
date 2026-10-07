"""Step 4 configuration: paths, model registry and a-priori design decisions.

Everything that was decided BEFORE looking at results is fixed here, so the report can say so honestly:
  * MAIN_MODEL is the pre-specified headline model. Every other model is reported too; if another model
    wins on the 30 ads, say so as an exploratory (post-hoc) finding, do not silently swap the headline.
  * CONCEPT_CATEGORIES decides which dictionary skills the semantic layer may add (concept-like skills that
    ads often imply). Named products and languages (Python, Snowflake, React ...) are always named explicitly,
    and embeddings of rare brand names are noise, so they are left to the exact matcher.

One decision was changed AFTER seeing results (say so in the report):
  * DEFAULTS["pool"] was "max" in the first run and is now "centroid", because the one-factor ablation showed
    centroid pooling was the only setting that significantly improved lenient F1 (0.873 -> 0.889, 95% CI of the
    difference [0.003, 0.028]). Because that choice was made on the 30 gold ads, experiments.model_comparison also
    reports "<main> hybrid (pool chosen in CV)": max vs centroid is selected INSIDE each leave-one-ad-out fold, so that
    row checks the choice without letting the held-out ad influence it (it cannot undo the optimism of having
    examined these 30 ads repeatedly).
"""
from __future__ import annotations

import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
DETAILS = RESULTS / "details"          # every table behind summary.md
AUDIT = RESULTS / "audit"              # sheets that humans label
HANDOFF = RESULTS / "handoff"          # files for Student 5
FIGURES = HERE / "figures"
CACHE = HERE / "cache"
SEED = 36118                      # same seed as Step 3 (gold set, bootstrap)

# --------------------------------------------------------------------------- #
# Locate the Step 3 code/data (step3_baseline_nlp/ in the group repo)
# --------------------------------------------------------------------------- #
_MARKER = "skill_extractor_v2.py"


def find_step3(explicit: str | os.PathLike | None = None) -> Path:
    """Find the folder holding skill_extractor_v2.py, job_cleaned.csv, gold_annotations.py ...

    Order: explicit argument, env STEP3_DIR, ../step3_baseline_nlp, ./Member3_Baseline_NLP, then any
    sibling/parent folder containing skill_extractor_v2.py.
    """
    cands = []
    if explicit:
        cands.append(Path(explicit))
    if os.environ.get("STEP3_DIR"):
        cands.append(Path(os.environ["STEP3_DIR"]))
    cands += [HERE.parent / "step3_baseline_nlp", HERE.parent / "Member3_Baseline_NLP",
              HERE / "step3_baseline_nlp", HERE / "Member3_Baseline_NLP"]
    for c in cands:
        if (c / _MARKER).exists():
            return c.resolve()
    for root in (HERE.parent, HERE.parent.parent):
        for hit in root.glob(f"*/{_MARKER}"):
            return hit.parent.resolve()
    raise FileNotFoundError(
        "Could not find the Step 3 folder (needs skill_extractor_v2.py). Put this folder next to "
        "step3_baseline_nlp/ or set the environment variable STEP3_DIR=/path/to/step3_baseline_nlp")


# --------------------------------------------------------------------------- #
# Sentence-embedding models (all symmetric sentence-similarity use)
# `prefix` is prepended to BOTH skill phrases and ad text.
# --------------------------------------------------------------------------- #
MODELS = {
    "minilm":   dict(hf="sentence-transformers/all-MiniLM-L6-v2", prefix=""),
    "mpnet":    dict(hf="sentence-transformers/all-mpnet-base-v2", prefix=""),
    "bge-base": dict(hf="BAAI/bge-base-en-v1.5", prefix=""),
    # lexical control (no neural model): character n-gram hashing. If a neural model does not beat this,
    # its "semantic" gain is only fuzzy string matching.
    "hashing":  dict(hf=None, prefix=""),
}
MAIN_MODEL = "mpnet"
COMPARE_MODELS = ["hashing", "minilm", "mpnet", "bge-base"]

# Dictionary categories whose skills the semantic layer may ADD (a priori, see module docstring).
CONCEPT_CATEGORIES = {
    "Data Analysis & Statistics", "Data Engineering", "Data Visualisation / BI", "Machine Learning & AI",
    "Methods / Architecture", "MLOps / Deployment", "NLP / Generative AI",
}

# --------------------------------------------------------------------------- #
# Default method settings (the ablation changes one factor at a time around these)
# --------------------------------------------------------------------------- #
DEFAULTS = dict(
    granularity="line+clause",    # line | clause | line+clause | line+window
    proto_mode="aliases",         # canonical | aliases | aliases_ctx
    pool="centroid",              # max | centroid  (was "max" in the first run; see module docstring)
    norm="raw",                   # raw (cosine) | z (per-skill z-score vs. a reference corpus)
    categories="concept",         # concept | all
    min_alias_len=4,              # aliases shorter than this stay with the exact matcher
    min_words=3,                  # shortest ad unit (words) that is embedded
    max_words=60,                 # longer lines are split into sentences
    sem_weight=1.0,               # weight multiplier for semantically found skills
)

# Threshold grids (cosine for raw, z-score for z-norm) and optional margin / top-k rules
TAU_GRID_RAW = [round(x, 2) for x in [0.20 + 0.01 * i for i in range(0, 61)]]      # 0.20 .. 0.80
TAU_GRID_Z = [round(x, 2) for x in [1.0 + 0.25 * i for i in range(0, 33)]]         # 1.0 .. 9.0
DELTA_GRID_RAW = [None, 0.03, 0.06]
DELTA_GRID_Z = [None, 0.5, 1.0]
TOPK_GRID = [None]

N_BOOT = 2000
REFERENCE_UNITS = 4000            # unlabelled ad units used for per-skill z-normalisation


# --------------------------------------------------------------------------- #
# Output folders
# --------------------------------------------------------------------------- #

def ensure_dirs():
    for d in (RESULTS, DETAILS, AUDIT, HANDOFF, FIGURES, CACHE):
        d.mkdir(parents=True, exist_ok=True)
