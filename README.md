# From Study Materials to Career Recommendations
**UTS 36118 Applied NLP: AT2 Part B, Group 6**

We match the skills in a student's study material# From Study Materials to Career Recommendations

**UTS 36118 Applied NLP: AT2 Part B, Group 6**

**Research question:** Are Australian university curricula aligned with the skills demanded by the U.S. Data/AI labour market?

We extract skills from Data/AI job advertisements (the U.S. benchmark) and from a student's study materials (unit outlines), compare the two, and recommend careers and the skills to learn next.

```
job ads -> skills -> career and sector demand profiles
unit outline PDFs -> skills covered (with page evidence)
                         \-> alignment score, biggest gaps, recommendations
```

## Pipeline

| Step | What | Owner | Folder |
|---|---|---|---|
| 1 | Job-ad collection and cleaning (U.S. data) | Member 1 | `step1_data/` |
| 2 | Skill dictionary and normalisation | Member 2 | `step2_dictionary/` |
| 3 | **Baseline NLP (spaCy PhraseMatcher), PDF study-material pipeline, curriculum alignment, sector lens** | Jirawan Pedersen | `step3_baseline_nlp/` |
| 4 | Semantic matching (Sentence Transformers) | Member 4 | `step4_semantic/` |
| 5 | User interface and recommendations | Tengxiao Nong | `step5_ui/` |
| 6 | Report and poster | Member 6 | `report/` |

*(Edit names and owners to match the team division.)*

## Quick start

```bash
git clone <repo-url> && cd <repo>
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
jupyter lab
```

Run notebooks from inside their own step folder (they import local `.py` files). Use **Restart & Run All**. In Google Colab, put the step folder in Drive (for example `My Drive/ANLP AT2B`) and run the first cell of each notebook, which mounts Drive and lists any missing file.

## Step 3: run order (`step3_baseline_nlp/`)

Required input files in the same folder: `job_cleaned.csv`, `skills_dictionary.csv`, `normalisation.py` (copies from Steps 1 and 2).

1. `03_skill_extraction.ipynb`: baseline extraction on 688 job ads, outputs `job_skills_extracted.csv` and `job_skills_long.csv`
2. `04_innovation_experiments.ipynb`: held-out evaluation, ablation, requirement-aware profiles, error analysis
3. `05_study_material_pipeline.ipynb`: PDF study material to skills (PyMuPDF), with coverage level (assessed, taught, mentioned)
4. `06_curriculum_alignment.ipynb`: career fit with bootstrap ranges, skill gaps and curriculum heatmap (synthetic demo units)
5. `07_sector_lens.ipynb`: does skill demand depend on the employer's sector? (company-clustered tests)
6. `08_real_curriculum_case_study.ipynb`: the research question on 7 real public units from UTS, USYD and UNSW
7. Optional: `python run_step3.py` (regenerate outputs), `pytest` (33 tests)

### Reusable API (also for student study material)

```python
from skill_extractor import extract_skills                 # baseline
from skill_extractor_v2 import RequirementAwareExtractor    # requirement-aware, demand weights
from extraction import analyse_study_material, analyse_text # PDF (path, bytes or Streamlit upload) or text -> skills + pages
from alignment import DemandModel, job_strengths, curriculum_coverage
x = RequirementAwareExtractor("skills_dictionary.csv", extra_aliases_path="extra_aliases_reviewed.csv", expand_morphology=True)
x.extract_weighted(text)   # {skill: demand weight}
```

### Main files

* `skill_extractor.py`, `skill_extractor_v2.py`: baseline and requirement-aware extractors
* `extraction.py`: PDF pipeline with coverage levels (same matcher as the job side)
* `alignment.py`: demand model, career fit with bootstrap ranges, gap ranking
* `sectors.py`, `company_sector_map.csv`, `sector_analysis.py`: company-to-sector labels (manual, please review) and company-clustered tests
* `real_units.py`: the 7 real public unit descriptions with source URLs
* `evaluate.py`, `gold_annotations.py`, `gold_split.json`: 30-ad evaluation set and metrics (for Member 4)
* `extra_aliases_reviewed.csv`: 45 proposed dictionary aliases (for Member 2 to review)

## Key results

**Extraction (30-ad held-out gold set, seed 36118).** Micro-F1 0.872 (baseline) to 0.943 (Baseline++), delta F1 +0.071, 95% CI [0.039, 0.104]. The gain comes from human-reviewed dictionary expansion. The section-aware filter is not significant on F1, but it yields demand-weighted career profiles. About 27% of the skills a human reads are implicit or out of the dictionary, which is the target for the semantic method (Step 4).

**Sector lens (6 main sectors, 688 ads).** Demand profiles differ by sector (permutation test p = 0.004, but only p = 0.06 after adjusting for career mix, so we call it suggestive). Python, AI, Machine Learning and LLMs are demanded in every sector, while some skills are sector-specific (for example Statistics and Causal Inference for consumer firms, Distributed Systems for infrastructure).

**Case study: 7 public Australian units (UTS 36118, 36106, 36120; USYD COMP5318, DATA5207; UNSW COMP9444, COMP9417).** The units cover the machine learning core. Career fit is highest for ML Engineer (0.43) and Data Scientist (0.37) and lowest for Data Engineer (0.12). The biggest gaps are SQL, Causal Inference, Dashboarding, A/B Testing and LLMs. These are ML-focused units taken from handbook pages, so a gap may be taught in another unit. Treat this as a case study, not a claim about whole degrees.

## Limitations

* Gold labels come from a single (AI) annotator, n = 30.
* U.S.-only job data, mostly large tech employers and mostly 2026 ads. The Australian set is too small (14 ads) for separate tests.
* Sector labels are manual (17 borderline companies), and health tech (22 ads) is exploratory only.
* Unit descriptions are shorter than full outlines, and the extractor was validated on job ads, not unit text.
* Exact-phrase matching misses skills taught without naming them (the target of Step 4).

See the report section for details.

## Repo layout

```
data/                 shared inputs (check course rules before making the repo public)
step1_data/ ... step5_ui/
report/               draft sections, figures
requirements.txt
```

## Team conventions

* Work in your own step folder and open a pull request for changes to shared files (`data/`, `skills_dictionary.csv`).
* Commit notebooks **with outputs**. Do not commit `.venv/` or `__pycache__/`.
* Dictionary changes: Member 2 merges proposals (for example `extra_aliases_reviewed.csv`) and tells Members 3 to 5.
s against the skills demanded in Data/AI job advertisements, and recommend careers and the skills to learn next.

## Pipeline
| Step | What | Owner | Folder |
|---|---|---|---|
| 1 | Job-ad collection & cleaning (US data) | Member 1 | `step1_data/` |
| 2 | Skill dictionary & normalisation | Member 2 | `step2_dictionary/` |
| 3 | Baseline NLP skill extraction (spaCy PhraseMatcher) + innovation experiments | Jirawan Pedersen | `step3_baseline_nlp/` |
| 4 | Semantic matching (Sentence Transformers) | Member 4 | `step4_semantic/` |
| 5 | User interface / recommendations | Tengxiao Nong | `step5_ui/` |
| 6 | Report & poster | Member 6 | `report/` |

*(Edit names/owners to match the team division.)*

## Quick start
```bash
git clone <repo-url> && cd <repo>
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
jupyter lab
```
Run notebooks from inside their own step folder (they import local `.py` files). Use **Restart & Run All**.

## Step 3 - run order (`step3_baseline_nlp/`)
Required input files in the same folder: `job_cleaned.csv`, `skills_dictionary.csv`, `normalisation.py` (copies from Step 1/2).
1. `03_skill_extraction.ipynb` — baseline extraction → `job_skills_extracted.csv`, `job_skills_long.csv`
2. `04_innovation_experiments.ipynb` — held-out evaluation, ablation, requirement-aware profiles, error analysis
3. Optional: `python run_step3.py` (regenerate outputs), `pytest` (tests)

Reusable API (also for student study material):
```python
from skill_extractor import extract_skills              # baseline
from skill_extractor_v2 import RequirementAwareExtractor # requirement-aware, demand weights
x = RequirementAwareExtractor("skills_dictionary.csv", extra_aliases_path="extra_aliases_reviewed.csv", expand_morphology=True)
x.extract_weighted(text)   # {skill: demand weight}
```

### Key results (30-ad held-out gold set, seed 36118)
Micro-F1 0.872 (baseline) → 0.943 (Baseline++), ΔF1 +0.071, 95% CI [0.039, 0.104]. The gain comes from human-reviewed dictionary expansion; the section-aware filter is not significant on F1 but yields demand-weighted career profiles. About 27% of skills a human reads are implicit or out-of-dictionary — the target for the semantic method (Step 4).

**Limitations:** gold labels from a single (AI) annotator, n = 30; US-only data; Australian set too small (14 ads). See the report section for details.

## Repo layout
```
data/                 shared inputs (check course rules before making the repo public)
step1_data/ ... step5_ui/
report/               draft sections, figures
requirements.txt
```

## Team conventions
- Work in your own step folder; open a pull request for changes to shared files (`data/`, `skills_dictionary.csv`).
- Commit notebooks **with outputs**. Don't commit `.venv/` or `__pycache__/`.
- Dictionary changes: Member 2 merges proposals (e.g. `extra_aliases_reviewed.csv`) and tells Members 3–5.
