# Step 5: Career profiles, matching and explanations

Folder owner: **Tengxiao Nong**.

## What I did

This module converts the hybrid job-skill output from Step 4 into transparent career skill profiles. It compares the skills covered by study materials with the 30 most demanded skills for each career, ranks the five careers, identifies matched skills and priority gaps, and produces a JSON-safe explanation payload for the Streamlit app.

## Method

For career `c` and skill `s`, demand is the mean requirement weight across every advertisement in that career:

`demand(c,s) = sum of requirement weights / number of career advertisements`

The supplied job-side weights are required = 1.0, duty = 0.75, preferred = 0.5 and unlabelled = 0.5. Study-material coverage is assessed = 1.0, taught = 0.75 and mentioned = 0.5.

For the top 30 skills in a career:

`match = sum(demand * coverage) / sum(demand)`

The score represents coverage of skills found in the sampled advertisements. It is not a probability of employment or proof that a student has mastered a skill.

## Run

From the repository root:

```bash
python step5_matching/matching.py
pytest -q step5_matching/test_matching.py
```

Windows users can also double-click `run_matching.bat`. macOS users can run `bash step5_matching/run_matching.command`.

For Google Colab, upload `05_career_matching_colab.ipynb`, run the cells in order, and upload the complete project ZIP when the first code cell asks for it.

To analyse selected units, repeat `--unit` with the exact IDs in Step 4's curriculum result:

```bash
python step5_matching/matching.py \
  --unit "UTS 36118 Applied NLP" \
  --unit "UTS 36120 Adv ML Application"
```

## Inputs

- `step1_data/job_cleaned.csv`: all advertisements, including ads where no skill was extracted.
- `step4_semantic/results/handoff/job_skills_hybrid_long.csv`: exact and semantic job-skill hits with requirement weights.
- `step4_semantic/results/details/curriculum_all_hits.csv`: exact and semantic skills found in the 20 curriculum PDFs.
- A live Step 3 or Step 4 `StudyProfile` can also be converted with `study_coverage_from_profile()`.

## Outputs

Running the demo creates `outputs/`:

- `career_profiles.csv`: skill demand and rank within each career.
- `demo_career_ranking.csv`: ranked careers, score, matched skills and gaps.
- `demo_skill_explanations.csv`: contribution and remaining gain for each top skill.
- `demo_sensitivity.csv`: rankings under top-20, top-30 and top-40 cutoffs.
- `demo_learning_recommendations.csv`: ranked skill-development actions for every career.
- `demo_study_profile.json`: merged curriculum skill evidence.
- `demo_app_payload.json`: nested, JSON-safe output for Member 6.

Member 6 can import `build_career_profiles`, `study_coverage_from_profile`, `match_careers`, `learning_recommendations` and `app_payload` from `matching.py`.

### Dynamic frontend interface

`demo_app_payload.json` is only the fixed 20-PDF demonstration. For a new PDF,
Member 6 should call the dynamic API instead:

```python
from step5_matching.frontend_api import match_uploaded_pdf

results = match_uploaded_pdf(uploaded_pdf)
```

The call runs Step 3 exact extraction and recalculates Step 5 for that PDF. Pass
`use_semantic=True` to optionally add Step 4 semantic matches. It then
returns the same five-career JSON structure as the 20-PDF demo. A runnable
example is provided in `step5_matching/frontend_demo.py`:

```bash
pip install -r step5_matching/frontend_requirements.txt
streamlit run step5_matching/frontend_demo.py
```

## Limitations

- The ranking reflects 688 sampled U.S. advertisements and five career labels; Data Analyst has only 27 ads.
- The top-30 cutoff is transparent but remains a modelling choice. The included sensitivity table shows that Data Scientist remains first at top-30 and top-40, while ML Engineer narrowly ranks first at top-20.
- Semantic additions are probabilistic. Step 4 reports precision of 0.64 on unseen job ads and 0.77 on unit PDFs, so the interface should label semantic evidence as “possible”.
- Coverage in a PDF means that the material mentions, teaches or assesses a skill. It does not prove student mastery.
