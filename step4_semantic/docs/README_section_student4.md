## Student 4: Semantic NLP (Sentence Transformers) and main evaluation (Tao Lou)

**What I did**
- Built a **hybrid extractor** on top of Step 3's Baseline++: exact matches are kept, and a Sentence-Transformer adds
  *implied* skills. Ad text is split into units (lines and clauses; company text excluded via Step 3's section segmenter);
  each dictionary skill is represented by its name and aliases, pooled into one centroid vector; a skill is
  added when a unit's cosine similarity to it passes a threshold (optionally within a margin of the unit's best skill,
  and optionally z-normalised per skill to remove hub skills).
- Compared 4 embedding models (hashing, minilm, mpnet, bge-base), including a
  character-hashing *lexical control*, and a semantic-only control (main model only). Headline model fixed in advance: `mpnet`.
- Evaluated on the **same 30 gold ads** with Step 3's definitions. Threshold selection is **leave-one-ad-out
  cross-validation** (tuned on 29 ads, applied to the 30th), so all numbers are out-of-fold. Paired bootstrap (2,000
  resamples, seed 36118; strict F1 via Step 3's own `evaluate.bootstrap`), one-factor ablations and error
  analysis, then the 688-ad corpus and the 20 real unit PDFs with blinded human precision audits.

**Key results** (30 gold ads, out-of-fold, `mpnet` hybrid vs Baseline++)
- Implicit-skill recall (I-recall): 0.023 -> 0.349
  (delta 0.326, 95% CI [0.204, 0.463]).
- Lenient F1 (gold = R+P+I; an implicit skill an ad demands is correct): 0.874 -> 0.889
  (delta 0.015, 95% CI [0.003, 0.028]); lenient precision 0.908 -> 0.888
  (delta -0.020, CI [-0.038, -0.005]).
- Strict F1 (Step 3's R+P-only gold, where valid implicit skills count as errors): 0.943 ->
  0.904 (delta -0.038, CI [-0.055, -0.023]). Baseline++ already has R+P recall
  0.984, so strict F1 mainly reflects implicit hits scored as errors; it is reported for comparability.
- The semantic layer added 22 skills over the 30 ads (0.73 per ad); precision of
  those additions 0.636.
- Check of the pooling choice (pool chosen inside each fold; centroid 30/30): lenient F1 0.889 (delta to Baseline++ 0.015, 95% CI [0.003, 0.028]), I-recall 0.349, additions precision 0.636.
- Unit PDFs: the semantic layer added skills to 10 of 20 units. Named cases: UNSW COMP9311 Database Systems - SQL: exact missed, hybrid missed; UTS 36103 Statistical Thinking - Statistics: exact missed, hybrid found.
- Blinded human audit, unseen job ads: precision exact 0.960 [0.865, 0.989] (n=50); semantic 0.640 [0.501, 0.759] (n=50).
- Blinded human audit, unit PDFs: precision exact 0.967 [0.833, 0.994] (n=30); semantic 0.773 [0.566, 0.899] (n=22).

**Files and how to run them** (folder `step4_semantic/`; needs `step3_baseline_nlp/` next to it or `STEP3_DIR`)
- `pip install -r requirements.txt`, then `python run_all.py all` (first run downloads the models; add `--quick` for a short test).
- `semantic_extractor.py` (method), `experiments.py` (LOOCV, ablation, bootstrap), `metrics.py`, `error_analysis.py`,
  `corpus_extract.py`, `curriculum_semantic.py`, `figures.py`, `make_report.py`, `tests/`, `results/`, `figures/`, `docs/`.
- Drop-in for Student 5: `from corpus_extract import build_hybrid` then `.extract_weighted(text)` /
  `.skill_strengths(text)`; or read `results/handoff/job_skills_hybrid_long.csv` / `job_skills_hybrid_extracted.csv`.

**Limitations**
- Human audit: one annotator (the method developer), blinded to which method produced each item; ambiguous items were
  resolved with help from an AI assistant (Claude) applying a fixed written rule, so the labels are human-led but
  AI-assisted. No second annotator, so no inter-annotator agreement. Exact-hit evidence lines contain the skill name,
  so blinding is partial.
- Gold labels: one AI annotator, n = 30, 43 implicit labels (wide intervals; the implicit tier is thin).
- The 30 ads were used for comparison, ablation and error analysis, and centroid pooling was adopted after the first
  ablation; cross-validation keeps the threshold from seeing the scored ad but not this design optimism, so results are
  partly exploratory. Inherited from Step 3: one Baseline++ header rule was fixed after looking at a gold ad.
- Unit text has no complete labels: only precision of hits is audited, not recall.
- Embeddings are tied to dictionary skills; skills outside the dictionary (OTHER tier) are not recoverable.
- English-only models; US job ads; Australian unit handbook text is shorter than full outlines.
