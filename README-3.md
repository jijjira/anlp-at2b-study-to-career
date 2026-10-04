# From Study Materials to Career Recommendations
**UTS 36118 Applied NLP — AT2 Part B, Group 6**

We match the skills in a student's study materials against the skills demanded in Data/AI job advertisements, and recommend careers and the skills to learn next.

## Pipeline
| Step | What | Owner | Folder |
|---|---|---|---|
| 1 | Job-ad collection & cleaning (US data) | Member 1 | `step1_data/` |
| 2 | Skill dictionary & normalisation | Member 2 | `step2_dictionary/` |
| 3 | **Baseline NLP skill extraction (spaCy PhraseMatcher) + innovation experiments** | Member 3 | `step3_baseline_nlp/` |
| 4 | Semantic matching (Sentence Transformers) | Member 4 | `step4_semantic/` |
| 5 | User interface / recommendations | Member 5 | `step5_ui/` |
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

## Step 3 — run order (`step3_baseline_nlp/`)
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
