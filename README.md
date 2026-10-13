# From Study Materials to Career Recommendations

**UTS 36118 Applied NLP: Assessment 2 Part B, Group 6**

**Research question:** Are Australian university curricula aligned with the skills demanded by the U.S. Data/AI labour market?

We extract skills from Data/AI job advertisements (the U.S. benchmark) and from unit outlines (the study material) into one shared skill vocabulary, compare the two, and recommend careers and the skills to learn next. The final report is submitted separately on Canvas.

![From job advertisements and unit documents to career recommendations](images/pipeline.png)

## Headline results

* **Data:** 688 U.S. advertisements from 106 employers, five careers; 20 unit outlines from UTS, USYD and UNSW.
* **Extraction:** strict F1 rises from 0.872 (plain matcher) to 0.943 (Baseline++), mostly from the human-reviewed dictionary; the semantic layer lifts implicit-skill recall from 0.023 to 0.349 at about 64% precision on what it adds.
* **Alignment:** curriculum fit is highest for Data Scientist and lowest for AI Engineer (exact matching 65.4% and 32.6%; hybrid 68.5% and 40.8%). Gaps are in applied, production-oriented skills (causal inference, experimentation, dbt, observability, APIs, agents).
* **Application:** upload a unit outline and get ranked career fits, covered skills, priority gaps and page-level evidence. A pilot test (n = 3) rated it 4.40 out of 5.

![Career fit under exact and hybrid matching](images/career_fit_exact_vs_hybrid.png)

*Curriculum fit for each career (share of the 30 most demanded skills covered by the 20 units), exact matching versus hybrid matching.*

![The Streamlit application](images/app_screenshot.png)

*The Streamlit application: upload a unit PDF and get ranked career matches, covered skills, gaps and evidence.*

## Team and tasks

| Step | Member | Task | Folder |
|---|---|---|---|
| 1 | Zheke Yi | Collect and clean the job advertisements: 688 U.S. ads, five careers | `step1_data/` |
| 2 | Wancheng Liu | Build the skills dictionary: 132 skills, 232 aliases, 12 categories | `step2_dictionary/` |
| 3 | Jirawan Pedersen | Baseline NLP, PDF reader, curriculum alignment, 20-unit case study, sector lens | `step3_baseline_nlp/` |
| 4 | Tao Lou | Semantic layer (Sentence Transformers), main evaluation and blinded audits | `step4_semantic/` |
| 5 | Tengxiao Nong | Career profiles, matching scores, skill gaps and recommendations | `step5_matching/` |
| 6 | Chongyan Tang | Streamlit application and user testing | `step6_app/` |

Every step folder follows the same layout: a `README.md` (task, files, how to run, key results, limitations), a `requirements.txt`, the numbered notebook(s), the code, and the step's outputs or results.

## How to run

On your own computer, clone the repo and create an environment:

```
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
jupyter lab
```

Then open a step folder and run its notebook with Restart & Run All. The quickest checks are:

* Tests: `cd step3_baseline_nlp && python -m pytest -q` (40), `cd step4_semantic && python -m pytest -q` (18), `cd step5_matching && python -m pytest -q` (6).
* Career ranking: `cd step5_matching && python matching.py`.
* App: `pip install -r step6_app/requirements.txt` then `streamlit run step6_app/app.py`.
* Step 3 also has one-click launchers (`run.command` on Mac, `run.bat` on Windows). The Step 3 notebooks and `step5_matching/10_career_matching_colab.ipynb` are built for Google Colab: upload one, run the first cell, and follow the prompt.

## Where to find each part of the report

| Report section | Where in the repo |
|---|---|
| Data sources (job advertisements) | `step1_data/` (`job_cleaned.csv`, raw snapshot, collection script, `australia/`) |
| Data sources (unit documents) | `step3_baseline_nlp/data/curriculum_pdfs/` and `step3_baseline_nlp/docs/references_and_data_sources.md` |
| Skill vocabulary and normalisation | `step2_dictionary/` (`outputs/skills_dictionary.csv`, `outputs/normalisation.py`) |
| Baseline and Baseline++ extraction | `step3_baseline_nlp/skill_extractor.py`, `skill_extractor_v2.py`, `discover.py`, `extra_aliases_reviewed.csv` |
| Reading unit PDFs | `step3_baseline_nlp/extraction.py`, `curriculum.py` |
| Semantic layer | `step4_semantic/semantic_extractor.py`, `corpus_extract.py`, `curriculum_semantic.py` |
| Career matching and recommendations | `step5_matching/matching.py`, `frontend_api.py` |
| Evaluation, gold set and uncertainty | `step3_baseline_nlp/evaluate.py`, `gold_annotations.py`; `step4_semantic/experiments.py`, `metrics.py` |
| Findings: extraction accuracy | `step3_baseline_nlp/04_innovation_experiments.ipynb`; `step4_semantic/results/summary.md` |
| Findings: curriculum alignment and sectors | `step3_baseline_nlp/06_curriculum_alignment.ipynb`, `07_sector_lens.ipynb`, `08_real_curriculum_case_study.ipynb`, `figures/` |
| Findings: exact versus hybrid career fit | `step4_semantic/results/details/curriculum_fit_exact_vs_hybrid.csv`; `step5_matching/outputs/` |
| Blinded audits | `step4_semantic/results/audit/` |
| Application and user test | `step6_app/app.py`; `step6_app/user_testing/` |
| Reproducibility | `requirements.txt` in every step; tests in Steps 3, 4 and 5 |

## Data and references

* Job ads: 688 public postings from 106 companies (Greenhouse and Ashby job boards), collected 1 Oct 2026. The 14 Australian ads are a separate, small set.
* Curriculum sources: 20 public unit pages (UTS, USYD, UNSW handbooks), saved as PDFs in `step3_baseline_nlp/data/curriculum_pdfs/` and listed with URLs and APA references in `step3_baseline_nlp/docs/references_and_data_sources.md`.

## Group limitations

* U.S.-only job data, mostly large tech employers and mostly 2026 ads. The Australian set is too small (14 ads) for separate tests.
* Twenty selected units is a case study, not all of Australian higher education or whole degrees.
* Gold labels come from a single AI annotator; a second human annotator on about 10 ads would help.

## Repo layout

```
README.md                  this page
requirements.txt           shared libraries (each step folder also has its own)
images/                    figures shown in this README
step1_data/                raw and cleaned job ads, collection script, Australian set
step2_dictionary/          skills dictionary, taxonomy, normalisation module
step3_baseline_nlp/        notebooks 03 to 08, extractor and PDF code, 20 unit PDFs, figures, tests
step4_semantic/            semantic model, evaluation, blinded audit sheets, results, tests
step5_matching/            career matching code, notebooks, outputs, tests
step6_app/                 Streamlit app and user-testing data
```

## Reproducibility

* Automated tests: 40 (Step 3), 18 (Step 4), 6 (Step 5), all passing.
* Re-running `step1_data/01_data_cleaning.ipynb` reproduces the 688 cleaned advertisements exactly.
* Fixed random seed 36118 for the gold-set split and bootstrap intervals.
* Checked with Python 3.13, spaCy 3.8, pandas 3.0, NumPy 2.5, SciPy 1.18, PyMuPDF 1.28, sentence-transformers 6.1, PyTorch 2.14, Streamlit 1.65 and pytest 9.1.

## Run times

* Step 3 tests take under a minute; Steps 4 and 5 tests take a few seconds.
* `python matching.py` in Step 5 takes a few seconds and needs no model download.
* The first run of Step 4's model comparison, and the first use of hybrid mode in the app, downloads the language models (about 0.4 GB for the main model); allow roughly 10 to 30 minutes on a CPU for the full Step 4 run.
