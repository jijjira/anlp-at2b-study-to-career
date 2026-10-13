# Step 6: Streamlit application and user testing

## Task
Make the pipeline usable without code. The Streamlit app accepts a unit PDF, offers exact or hybrid semantic matching and a Top-N choice, and shows ranked career matches with covered skills, priority gaps, page-level evidence and learning suggestions, plus a JSON download and a responsible-use notice (coverage is not mastery or a job-success probability). A formative usability test with three users evaluated it.

## Work in this folder
| Path | Purpose |
|---|---|
| `app.py` | The Streamlit application; calls the Step 5 interface |
| `requirements.txt` | Libraries (includes Step 5's frontend requirements) |
| `user_testing/user_testing_results.csv` | The three participants' ratings and comments |
| `user_testing/README.md` | Test tasks, mean scores and feedback |

## How to run
```
pip install -r requirements.txt
streamlit run app.py
```
Upload any unit PDF, for example `../step3_baseline_nlp/sample_unit_outline.pdf`. Hybrid mode downloads the language model on first use.

## Key results
* On the sample outline, exact matching ranks Data Scientist 41.9%, Data Analyst 40.1%, ML Engineer 39.0%, Data Engineer 23.1%, AI Engineer 21.8%; hybrid mode raises ML Engineer to 41.7%.
* User test (n = 3), mean out of 5: ease 3.33, result clarity 5.00, usefulness of skills and gaps 4.33, explanation clarity 5.00, overall usefulness 4.33; overall mean 4.40.

## Limitations
Hybrid mode is slower and the difference between the two modes was unclear to some users. Recommendations are skill overlap only (no experience or education), and three participants are too few for firm conclusions.
