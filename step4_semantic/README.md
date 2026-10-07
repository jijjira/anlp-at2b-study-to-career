# Step 4: Semantic NLP (Sentence Transformers) and main evaluation (Tao Lou)

UTS 36118 Applied NLP, AT2 Part B, Group 6. Builds on `step3_baseline_nlp/` (Member 3).

**Question for this step:** can sentence embeddings recover skills that a job ad *implies* but never names, without
hurting precision, compared with Step 3's exact-phrase matcher (Baseline++)?

## Quick start
```bash
# from the repo root: step3_baseline_nlp/ and step4_semantic/ side by side
cd step4_semantic
pip install -r requirements.txt -r ../step3_baseline_nlp/requirements.txt
python -m pytest -q                       # 18 offline tests (no model download)
python run_all.py verify                  # our metrics reproduce Step 3 (S0 0.872, S5 0.943)
python run_all.py compare ablate errors figures corpus curriculum report
# or:  python run_all.py all              (first run downloads the models; --quick = 2 models, 300 resamples)
```
If Step 3 lives elsewhere: `export STEP3_DIR=/path/to/step3_baseline_nlp` (or `--step3 PATH`).
Everything is cached in `cache/` (git-ignored), so re-runs and ablations are fast.

## Method in one paragraph
Hybrid = Baseline++ (exact) + semantic additions. Each ad is cut into units (lines and clauses) with Step 3's section
segmenter, so company/benefit text is never evidence and every added skill inherits a requirement strength. Each dictionary
skill is represented by its name and aliases, averaged into one centroid vector; the skill score for a unit is its
cosine to that vector. A skill is
added when a unit scores above a threshold (optional margin below the unit's best skill; optional per-skill z-score
against unlabelled ad units, a hubness correction). Only *concept* categories may be added (named tools and languages
stay with the exact matcher). Details and justification: `docs/report_section_semantic_method.md`.

## Evaluation protocol
* **Same 30 gold ads and definitions as Step 3**; `verify` checks the baseline numbers are reproduced.
* **Two views**: *strict* (gold = R+P, Step 3's metric; implicit skills found count as errors) and *lenient*
  (gold = R+P+I; an implicit skill the ad demands is correct), plus **I-recall** and the precision of the **additions**.
* **Leave-one-ad-out CV** picks the threshold/margin on 29 ads and applies it to the 30th; only pooled
  out-of-fold predictions are reported. The "tuned on all 30" row is optimistic and only used to run the corpus.
* **Paired bootstrap** over ads (2,000 resamples, seed 36118) for differences to Baseline++ and Baseline. Strict F1 is also
  computed with **Step 3's own `evaluate.bootstrap`** (row "strict_F1 (Step 3 evaluate.bootstrap)" in `model_bootstrap.csv`)
  and must agree with our implementation, which adds lenient F1, precision and I-recall.
* **Controls**: a character-hashing *lexical* encoder (is the gain more than fuzzy string matching?), a semantic-only
  control (run once, for the main model only), and a pre-specified headline model (`config.MAIN_MODEL`); all models are reported.
* **Ablations** (one factor at a time): granularity, prototypes, pooling, allowed skills, z-normalisation, margin rule.
* **Pooling choice re-checked inside CV**: centroid pooling became the default after the first ablation, so
  `compare` also reports `mpnet hybrid (pool chosen in CV)`, where max vs centroid is picked inside each fold.
* **Beyond 30 ads**: `corpus` runs all 688 ads and writes a **blinded** audit sheet (50 semantic additions + 50 exact
  hits from non-gold ads, shuffled, source hidden in `job_audit_key.csv`); `curriculum` runs the 20 real unit PDFs, checks
  Step 3's two test cases (COMP9311 "SQL", 36103 "Statistics") and writes a blinded sheet for unit text (all semantic
  additions + 30 exact hits). Both sheets were labelled with `label_tool.py` (see `docs/audit_instructions.md`).

## Files
| File | Purpose |
|---|---|
| `config.py` | paths, model registry, a-priori design decisions, grids |
| `semantic_extractor.py` | encoders, units, skill space, decision rule, `HybridExtractor` (the method) |
| `metrics.py` | strict/lenient P/R/F1, I-recall, additions precision, paired bootstrap, Wilson CI |
| `data_access.py` | loads Step 3 assets, `verify_against_step3` |
| `experiments.py` | sweeps, LOOCV, model comparison, ablations |
| `error_analysis.py`, `figures.py` | error tables, report figures |
| `corpus_extract.py` | 688-ad run, blinded audit sheet (`blind_job_audit`), `evaluate_job_audit` |
| `label_tool.py` | label a blinded sheet one item at a time in the terminal (resumable) |
| `curriculum_semantic.py` | unit PDFs, label sheet, `evaluate_unit_labels`, career-fit comparison |
| `make_report.py` | writes `results/summary.md` and `docs/README_section_student4.md` from the results |
| `run_all.py` | one command for every stage |
| `tests/test_semantic.py` | 18 offline tests |
| `docs/` | report section, root-README section, handoff to Student 5, audit instructions |

## What is in `results/`
```
results/summary.md      all headline tables (start here)
results/audit/          labelled blinded audit sheets and their keys (job ads, unit PDFs)
results/handoff/        job_skills_hybrid_*.csv for Student 5
results/details/        every other table behind summary.md
figures/                3 report figures (model comparison, ablation, threshold sweep)
```

## Results
All tables are generated from the result files, not typed by hand: start with `results/summary.md`. Headline numbers
(30 gold ads, out-of-fold, MPNet hybrid vs Baseline++): lenient F1 0.874 to 0.889 (+0.015, 95% CI [0.003, 0.028]),
implicit-skill recall 0.023 to 0.349, precision of added skills 0.636. Blinded human audit: semantic additions 0.64
(job ads) and 0.77 (unit PDFs) vs exact hits 0.96 and 0.97.
