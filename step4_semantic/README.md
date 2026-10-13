# Step 4: Semantic NLP and main evaluation

## Task
Recover skills that an advertisement implies but never names, without hurting precision. The hybrid extractor keeps every Baseline++ match and adds concept skills found by Sentence Transformers (`all-mpnet-base-v2`): text is cut into lines and clauses, each skill's name and aliases are averaged into one centroid, and a skill is added when similarity passes a threshold and is close to the unit's best skill. Thresholds are chosen by leave-one-advertisement-out validation, differences use paired bootstrap intervals, and MiniLM, BGE, a hashing control and an embeddings-only control are compared. Blinded audits check precision on unseen advertisements and on unit text.

## Work in this folder
| Path | Purpose |
|---|---|
| `semantic_extractor.py`, `corpus_extract.py`, `curriculum_semantic.py` | Hybrid extractor and its use on advertisements and unit PDFs |
| `experiments.py`, `metrics.py`, `error_analysis.py`, `data_access.py`, `config.py` | Evaluation, ablations, errors and settings |
| `label_tool.py` | Labelling tool for the blinded audit sheets |
| `run_all.py`, `make_report.py`, `figures.py` | One command for every stage; summary tables and charts |
| `09_semantic_evaluation.ipynb` | Runs and shows the whole evaluation |
| `tests/` | 18 offline tests |
| `results/summary.md`, `results/details/` | All result tables |
| `results/audit/` | Blinded audit sheets and keys |
| `results/hybrid_job_skills/` | Hybrid job-skill tables used by Step 5 |
| `figures/` | Model comparison, ablation and threshold charts |

## How to run
```
pip install -r requirements.txt -r ../step3_baseline_nlp/requirements.txt
python -m pytest -q                        # 18 offline tests
python run_all.py verify                   # reproduces Step 3 (0.872 and 0.943)
python run_all.py compare ablate errors figures corpus curriculum report    # first run downloads the models
```

## Key results
* Lenient F1 0.874 to 0.889 (+0.015, 95% CI [0.003, 0.028]) and implicit-skill recall 0.023 to 0.349 on the 30-advertisement gold set.
* About 64% of added skills are correct on advertisements and 77% on unit text; exact hits are 96% to 97% correct. Data Warehousing is the weakest skill (0 of 6).
* The hashing control adds nothing, so the gain is semantic; embeddings alone find more implicit skills but precision falls, so they complement the dictionary and do not replace it.

## Limitations
The gold labels come from one annotator and the same 30 advertisements were used for tuning, so results are partly exploratory. Skills outside the dictionary cannot be found, and the models are English only.
