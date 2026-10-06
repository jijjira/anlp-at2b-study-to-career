# Handoff: Member 3 (Baseline NLP) to Member 4 (Semantic NLP and Evaluation)

## What you can use straight away
1. **Baseline extractor (the thing to beat).** `from skill_extractor import extract_skills` takes raw text and returns canonical skills. `skill_extractor_v2.RequirementAwareExtractor(extra_aliases_path="extra_aliases_reviewed.csv", expand_morphology=True)` is the improved version (Baseline++).
2. **Gold evaluation set (30 job ads).** `gold_annotations.py` holds `GOLD[row] = {R, P, I, OTHER}` and `gold_split.json` lists which rows. Row numbers index into `job_cleaned.csv`.
   * R = explicit required skill, P = explicit preferred skill
   * I = implicit skill with no dictionary alias (43 labels): the target for your semantic method
   * OTHER = real skill missing from the dictionary (49 labels)
3. **Evaluation code.** `evaluate.py` has `prf()` for precision, recall and F1, and `bootstrap()` for paired confidence intervals. Add your method as a new function and compare it with the same code.
4. **Baseline numbers to compare against** (extended dictionary scope, 30 ads): baseline F1 0.872 (P .902, R .844); Baseline++ F1 0.943 (P .904, R .984). Difference +0.071, 95% CI 0.039 to 0.104.
5. **Student side.** `extraction.py` reads a PDF (`analyse_study_material`) and returns skills with pages, using the same matcher.

6. **Real curriculum data.** `curriculum.load_curriculum()` loads 20 unit PDFs (UTS, USYD, UNSW) listed in `data/curriculum_manifest.csv`, and notebook 08 gives career fit, gaps and sector fit against the U.S. benchmark (Data Scientist 0.65, Data Engineer 0.59, ML Engineer 0.58, Data Analyst 0.58, AI Engineer 0.33).
7. **A ready-made test for your method.** UNSW COMP9311 (Database Systems) finds zero skills with exact matching because its handbook text never says "SQL", and UTS 36103 says "statistical" but not "Statistics". If embeddings recover these without hurting precision, that is a clear, visible win for the semantic method. Unit text has no gold labels yet, so label a few units by hand if you want to measure it.

## Suggested next steps for you
* Run your Sentence-Transformer method on the same 30 ads and report P, R and F1 on R+P labels, then separately recall on the I labels.
* Check whether embeddings recover I-tier skills without hurting precision. Report both.
* Use the same bootstrap function so the comparison is fair.
* Label some study-material PDFs yourself, because only job ads are labelled so far.

## Caveats you should repeat in the report
* Gold labels come from one annotator (an AI model, blind to system output), so they are silver-standard. A second human annotator on about 10 ads would help (compute Cohen's kappa).
* n = 30 ads, so confidence intervals are wide.
* One rule (header parsing) was fixed after looking at a gold ad, a small source of optimism.
* US ads only; the Australian set has 14 ads, too few to evaluate.
* Sentence Transformers have not been run by Member 3, so no semantic results exist yet.

## Files to open first
`04_innovation_experiments.ipynb` (results), `gold_annotations.py`, `evaluate.py`, `extraction.py`.
