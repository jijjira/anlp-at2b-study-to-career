# Step 5: Career matching and recommendations

## Task
Turn skills into career recommendations. Demand-weighted profiles are built for five careers from the 688 advertisements, and a study profile (from the 20 units or one uploaded PDF) is scored against each career's 30 most demanded skills: `match(c) = sum(demand(c,s) x coverage(s)) / sum(demand(c,s))`. Coverage weights are assessed 1.0, taught 0.75 and mentioned 0.5. The module also returns the skill gaps with the most to gain, learning recommendations, evidence (unit and page) and a sensitivity analysis over the top 20, 30 and 40 skills, and exposes a JSON interface for the app.

## Work in this folder
| Path | Purpose |
|---|---|
| `matching.py` | Career profiles, scoring, gaps, recommendations, sensitivity |
| `frontend_api.py`, `frontend_demo.py` | JSON interface for the app and a minimal upload demo |
| `10_career_matching.ipynb`, `10_career_matching_colab.ipynb` | Walkthrough, local and Google Colab |
| `test_matching.py` | 6 automated tests |
| `outputs/` | Profiles, ranking, per-skill explanations, recommendations, sensitivity and app payload for the 20-unit case study |
| `figures/` | Career-match chart |
| `run_matching.command` (Mac), `run_matching.bat` (Windows) | One-click run |

## How to run
```
pip install -r requirements.txt
python matching.py                        # prints the five ranked careers, writes outputs/
python -m pytest -q test_matching.py      # 6 tests
pip install -r frontend_requirements.txt && python -m streamlit run frontend_demo.py    # upload a new PDF
```

## Key results
* Fit on the 20 real units with hybrid evidence: Data Scientist 68.5%, Data Engineer 62.9%, Data Analyst 61.7%, ML Engineer 61.0%, AI Engineer 40.8%.
* The order depends on how many skills are scored: ML Engineer is first at the top 20 (69.8%), Data Scientist at the top 30 and 40.

## Limitations
Data Analyst has only 27 advertisements, so its profile is the least stable. Scores measure how much of a career's demanded skills the documents cover, not mastery or employability, and semantic additions are probabilistic.
