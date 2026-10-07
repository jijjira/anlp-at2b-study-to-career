### Student 4: Semantic NLP (Sentence Transformers) and main evaluation (Tao Lou)

Folder: `step4_semantic/` (full detail in its own README). Builds on Student 3's `step3_baseline_nlp/`: the Baseline++
extractor, the 30-ad gold set and `evaluate.py`.

**What I did**

1. **Hybrid extractor:** keeps every Baseline++ match and adds skills an ad *implies* but never names, using Sentence
   Transformers (`all-mpnet-base-v2`). Ad text is cut into lines and clauses (company text skipped via Student 3's section
   segmenter); each skill's name and aliases are averaged into one centroid vector; a skill is added when a unit's cosine
   similarity passes a threshold and is close to that unit's best skill. Only concept skills can be added; tools and
   languages stay with exact matching.
2. **Main evaluation:** the same 30 gold ads and definitions as Step 3, scored strict (R+P gold) and lenient (R+P+I gold),
   plus implicit-skill recall and the precision of the added skills. Thresholds are chosen by leave-one-ad-out
   cross-validation, so every number is out-of-fold; 95% paired-bootstrap intervals (strict F1 also with Step 3's own
   `evaluate.bootstrap`).
3. **Model comparison and controls:** MiniLM, MPNet (pre-specified) and BGE-base, a character-hashing lexical control and
   a semantic-only control.
4. **Ablation and error analysis:** six design factors one at a time; errors by skill. The pooling choice was re-checked
   by selecting it inside each cross-validation fold.
5. **Blinded human audit:** 50 semantic additions and 50 exact hits from non-gold ads, plus all 22 semantic additions
   and 30 exact hits on unit PDFs, shuffled with the source hidden, labelled with `label_tool.py`.
6. **Student side:** the hybrid on the 20 real unit PDFs, Student 3's two test cases, and career fit exact vs hybrid.

**Run order** (`step4_semantic/`)

1. `pip install -r requirements.txt -r ../step3_baseline_nlp/requirements.txt`
2. Optional: `python -m pytest -q` (18 offline tests)
3. `python run_all.py verify` (reproduces Step 3: F1 0.872 and 0.943)
4. `python run_all.py compare ablate errors figures corpus curriculum report` (first run downloads the models)
5. `09_semantic_evaluation.ipynb` runs and shows the same steps

**Reusable API for other students**

```python
import sys; sys.path += ["../step3_baseline_nlp", "../step4_semantic"]
import experiments as ex, corpus_extract as ce
from data_access import load_context
hy = ce.build_hybrid(ex.Runner(load_context()), ce.load_final())   # tuned hybrid extractor
hy.extract_weighted(text)    # {skill: demand weight}, same as RequirementAwareExtractor
hy.explain(text)             # source (exact | semantic), similarity and evidence sentence per skill
```

**Figures:** `step4_semantic/figures/` (model comparison, ablation, threshold sweep).

**Main files:** `semantic_extractor.py`, `experiments.py`, `metrics.py`, `error_analysis.py`, `corpus_extract.py`,
`curriculum_semantic.py`, `label_tool.py`, `run_all.py`, `make_report.py`, `results/summary.md` (all tables),
`results/audit/` (blinded audit sheets and keys), `results/handoff/` (for Student 5), and `docs/` (report section,
handoff note, audit instructions).

**Key results**

* **Gold ads (30 ads, out-of-fold, MPNet hybrid vs Baseline++):** lenient F1 0.874 to 0.889, delta +0.015, 95% CI
  [0.003, 0.028]; implicit-skill recall 0.023 to 0.349 (about one in three unnamed skills recovered); lenient precision
  0.908 to 0.888. 64% of added skills are correct. Strict F1 falls from 0.943 to 0.904 because Baseline++ already has R+P
  recall 0.984, so the strict view can only count newly found implicit skills as errors.
* **Controls:** the lexical control adds nothing, so the gain is semantic, not fuzzy matching; MPNet alone (no exact
  matcher) finds the most implicit skills (0.605) but precision collapses to 0.585. Embeddings complement the dictionary;
  they do not replace it.
* **Ablation:** pooling matters most (centroid 0.889 vs max 0.873); centroid was chosen in 30 of 30 cross-validation folds.
* **Unseen ads (blinded human audit):** precision 0.64 for semantic additions [0.50, 0.76] vs 0.96 for exact hits
  [0.87, 0.99]. The semantic figure matches the gold-ad estimate (0.636), so the result generalises. Most errors are a
  related but different skill, for example "data infrastructure" read as Data Warehousing.
* **Unit PDFs:** UTS 36103 now gets Statistics; UNSW COMP9311 still misses SQL. Blinded audit on unit text: precision
  0.77 for semantic additions [0.57, 0.90] vs 0.97 for exact hits [0.83, 0.99]; Data Warehousing is the main error (0 of 3)
  in both audits. Hybrid career fit is higher for every career (AI Engineer 0.33 to 0.41); these are exploratory
  estimates that may be inflated by false-positive skill predictions.

**Limitations:** gold labels are Student 3's single AI annotator (n = 30, 43 implicit labels, wide intervals); the 30 ads
were used for tuning, comparison and ablation; centroid pooling was adopted after the first ablation (re-checked inside
cross-validation); one human annotator for the audit, with ambiguous items resolved with an AI assistant under a fixed
rule; skills outside the dictionary cannot be found; English-only models and US ads.

**Handoffs:** Student 5 can use `results/handoff/job_skills_hybrid_long.csv` (one row per ad and skill, with `source`,
strength, weight and evidence; filter `source == "exact"` for Step 3's output) or call `hy.extract_weighted`. Student 6
can call `curriculum_semantic.analyse_study_material_semantic` for an uploaded PDF and should show added skills as
"possibly covered" with their evidence; load the model once (about 0.4 GB).
