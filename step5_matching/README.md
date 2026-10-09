# Step 5: Career matching, skill-gap ranking and learning recommendations 

## Run it (easiest way)

**Windows:** unzip the complete repository, open `step5_matching`, then double-click `run_matching.bat`.

**Mac:** unzip the complete repository, open `step5_matching`, then run `bash run_matching.command` in Terminal.

**Google Colab (no local setup):** go to [Google Colab](https://colab.research.google.com/), choose **File > Upload notebook**, upload `05_career_matching_colab.ipynb`, and run the cells in order. When prompted, upload the complete project ZIP so the notebook can access the Step 1, Step 3 and Step 4 inputs.

The standard run installs the small Step 5 dependencies, runs the career-matching pipeline, prints the five ranked careers in the terminal, and saves the detailed results in `outputs/`. Six automated tests are included to check the demand denominator, score bounds, monotonicity, evidence preservation, gap ranking and frontend payload.

This module converts the hybrid job-skill and curriculum-skill outputs into interpretable career recommendations. It builds demand-weighted profiles for five careers, compares them with the skills covered by course PDFs, calculates matching scores, identifies important gaps, recommends priority skills to learn, and provides a JSON-safe interface for the Streamlit app.

## Run order (local, Google Colab or frontend demo)

1. Run `matching.py` to build the five career profiles from 688 job advertisements and evaluate the 20-PDF curriculum case study.
2. The script calculates career rankings with the top 30 demanded skills per career and writes the ranking, explanations, sensitivity analysis and learning recommendations to `outputs/`.
3. Run `pytest -q test_matching.py` to execute the six automated tests.
4. Use `05_career_matching.ipynb` for a local Jupyter walkthrough or `05_career_matching_colab.ipynb` for Google Colab.
5. Run `frontend_demo.py` to upload a new PDF and recalculate the five career matches dynamically:

```bash
pip install -r frontend_requirements.txt
python -m streamlit run frontend_demo.py
```

For one or more selected curriculum units, repeat `--unit` with the exact unit IDs from Step 4:

```bash
python matching.py \
  --unit "UTS 36118 Applied NLP" \
  --unit "UTS 36120 Adv ML Application"
```

The matching score for career `c` uses its top 30 demanded skills:

`match(c) = sum(demand(c,s) * coverage(s)) / sum(demand(c,s))`

Job-side requirement weights are required = 1.0, duty = 0.75, preferred = 0.5 and unlabelled = 0.5. Study-material coverage weights are assessed = 1.0, taught = 0.75 and mentioned = 0.5. The result measures coverage of skills found in the sampled advertisements; it is not a probability of employment or proof of personal mastery.

## Main files

* `matching.py`: builds career demand profiles, calculates matching scores, ranks careers, preserves evidence, identifies skill gaps and generates learning recommendations.
* `frontend_api.py`: dynamic interface for Member 6; accepts a newly uploaded PDF or a Step 3/4 `StudyProfile` and returns five JSON-safe career records.
* `frontend_demo.py`: minimal Streamlit demonstration for uploading one new course PDF and displaying career, match percentage, matched skills and priority learning skills.
* `05_career_matching.ipynb`: local notebook walkthrough of the Step 5 method and outputs.
* `05_career_matching_colab.ipynb`: Google Colab version that accepts the complete repository ZIP.
* `test_matching.py`: six automated tests for the profile, scoring, explanation, recommendation and frontend logic.
* `requirements.txt`: lightweight dependencies for the standard 20-PDF matching pipeline.
* `frontend_requirements.txt`: additional dependencies for live PDF extraction and the Streamlit demonstration.
* `run_matching.bat`, `run_matching.command`: one-click Windows and Mac launchers.
* `outputs/career_profiles.csv`: demand weight and skill rank within each career.
* `outputs/demo_career_ranking.csv`: five ranked careers, scores, matched skills and priority gaps.
* `outputs/demo_skill_explanations.csv`: per-skill contribution, remaining gain and supporting course evidence.
* `outputs/demo_learning_recommendations.csv`: five priority learning actions for every career.
* `outputs/demo_sensitivity.csv`: rankings under top-20, top-30 and top-40 skill cut-offs.
* `outputs/demo_app_payload.json`: nested output for the fixed 20-PDF demonstration.

For a newly uploaded PDF, the frontend should call the dynamic interface instead of reading the fixed demonstration JSON:

```python
from step5_matching.frontend_api import match_uploaded_pdf

results = match_uploaded_pdf(uploaded_pdf)
```

Pass `use_semantic=True` only when the Step 4 Sentence-Transformer model is available. The default exact-matching path runs without downloading the semantic model.

## Headline results

* On the 20 real curriculum PDFs, the top-30 configuration ranks Data Scientist first at 68.5%, followed by Data Engineer at 62.9%, Data Analyst at 61.7%, ML Engineer at 61.0% and AI Engineer at 40.8%.
* The sensitivity analysis shows that ML Engineer ranks first at the top-20 cut-off (69.8%), while Data Scientist ranks first at top-30 (68.5%) and top-40 (67.1%). This indicates that the ordering is partly sensitive to the number of demanded skills included.
* The output explains each recommendation through matched skills, demand-weighted gaps, course units, PDF pages and evidence text.
* A live PDF upload returns the same five-career structure and can be consumed directly by the Streamlit frontend without reusing the fixed 20-PDF result.

## Limitations

* The career profiles are based on 688 sampled U.S. advertisements and only five career labels; Data Analyst has 27 advertisements, so its profile is less stable than the larger categories.
* The top-30 cut-off is an interpretable modelling choice rather than a universal threshold; the included top-20 and top-40 sensitivity results should be reported with the main ranking.
* Semantic additions are probabilistic. Step 4 reports precision of 0.64 on unseen job advertisements and 0.77 on unit PDFs, so semantic evidence should be presented as possible rather than certain.
* A skill mentioned, taught or assessed in a PDF indicates curriculum coverage, not that an individual student has mastered the skill.
* A single uploaded course normally receives lower scores than the combined 20-course curriculum because it covers a smaller share of a career's top skills.
