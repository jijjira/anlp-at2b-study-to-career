# Handoff: Member 4 (Semantic NLP) to Member 5

## Use the semantic skills without touching NLP code
`step4_semantic/results/handoff/` (created by `python run_all.py corpus`):
* `job_skills_hybrid_extracted.csv`: same columns as Step 3's `job_skills_extracted.csv`
  (job_id, career_category, job_title, extracted_skills), including semantically found skills.
* `job_skills_hybrid_long.csv`: one row per (ad, skill) with `source` (exact | semantic), `strength`
  (required/duty/preferred/unlabelled), `weight`, similarity `score` and the `evidence` sentence.
  Every row (exact or semantic) has its `evidence` line and `line_no`. Filter `source == "exact"` to get Step 3's
  Baseline++ output.

## Use it as an extractor (same interface as Step 3)
```python
import sys; sys.path.append("../step3_baseline_nlp"); sys.path.append("../step4_semantic")
import experiments as ex, corpus_extract as ce
from data_access import load_context
runner = ex.Runner(load_context())
hy = ce.build_hybrid(runner, ce.load_final())      # tuned HybridExtractor
hy.extract_weighted(text)       # {skill: demand weight}   (same as RequirementAwareExtractor)
hy.skill_strengths(text)        # {skill: strength class}  -> alignment.job_strengths / DemandModel work unchanged
hy.explain(text)                # DataFrame with source, similarity and the evidence sentence
```
Semantic skills get the weight of the section their evidence came from (required 1.0, duty 0.75, preferred 0.5);
`sem_weight` in `config.DEFAULTS` can discount them if you want a more conservative profile.

## What to be careful about
* Semantic additions are probabilistic: precision 0.64 on gold ads and on unseen ads (blinded audit), against 0.96 for
  exact hits. Quote these numbers if you describe the app's reliability, and show semantic skills as "possibly" present.
* First use downloads the embedding model (about 0.4 GB for the default); the app should load it once.
* The threshold was tuned on job ads; on unit text the semantic additions scored precision 0.77 in the blinded audit.
