# Step 6: Streamlit application and user testing

## Task
Make the pipeline usable without code. The Streamlit app accepts a unit PDF (or the built-in sample outline), lets the user choose a fast exact method or a deeper hybrid method, and shows ranked career matches with covered skills, priority gaps, page-level evidence and learning suggestions, plus JSON and CSV downloads and a responsible-use notice (coverage is not mastery or a job-success probability). A formative usability test with three users evaluated the first version.

## Work in this folder
| Path | Purpose |
|---|---|
| `app.py` | The Streamlit application; calls the Step 5 interface |
| `requirements.txt` | Full libraries, including the hybrid method (includes Step 5's frontend requirements) |
| `requirements-light.txt` | Lighter install for the fast (exact) method only |
| `user_testing/user_testing_results.csv` | The three participants' ratings and comments (version 1) |
| `images/` | Pipeline diagram and application screenshots used in the report and the root README |
| `user_testing/README.md` | Test tasks, mean scores, feedback and the changes made afterwards |

## How to run
Easiest: double-click `run_app.command` (Mac) or `run_app.bat` (Windows) in the repository root. The first run sets up a private environment, then opens the app in your browser.

By hand:
```
pip install -r requirements.txt          # or requirements-light.txt for the fast method only
streamlit run app.py
```
Click **Try the sample outline** or upload any unit PDF. Hybrid mode downloads the language model on first use (about 0.4 GB, plus about 2 GB of libraries if not yet installed); without those libraries the app shows a short message and the fast method still works.

## What the interface offers
* **Plain-language methods:** "Fast: exact skill names" and "Deeper: also finds skills described in other words", each with a one-line explanation.
* **Sample outline button** for a first result in one click.
* **Headline and tie warning:** the closest career is stated with how many of its 30 top skills are covered, and scores within two points are flagged as effectively tied.
* **Possibly covered marking:** skills found only by the semantic layer are marked "?" and listed separately from exact hits, with a warning that about 64% of such additions were correct in the blinded audit.
* **Evidence:** every covered skill shows how strongly it appears (assessed, taught, mentioned), the page and the sentence.
* **Gaps and next steps:** biggest gaps per career, a "what to learn next" table with career demand bars, and downloads of the full results (JSON) and the gaps (CSV).
* **Responsible-use notice** at the top and a "how to read the results" panel in the sidebar.

## Key results
* On the sample outline, exact matching ranks Data Scientist 41.9%, Data Analyst 40.1%, ML Engineer 39.0%, Data Engineer 23.1%, AI Engineer 21.8%; hybrid mode raises ML Engineer to 41.7%.
* User test of version 1 (n = 3), mean out of 5: ease 3.33, result clarity 5.00, usefulness of skills and gaps 4.33, explanation clarity 5.00, overall usefulness 4.33; overall mean 4.40.

## Limitations
The revised interface has not been re-tested with users. Hybrid mode is slower and needs extra libraries and a model download. Recommendations are skill overlap only (no experience or education), and three participants in the first test are too few for firm conclusions.
