# Step 6: Streamlit app and user testing (Chongyan Tang)

Folder owner: **Chongyan Tang**.

## What I did

I integrated the team's existing study-material extraction and career-matching pipeline into a Streamlit web application. The interface accepts a course/unit PDF, lets the user choose exact keyword matching or hybrid semantic matching, and presents ranked career matches with matched skills, priority skill gaps, PDF evidence and suggested skills to develop. I also conducted a small formative user test with three classmates and documented the usability findings and limitations.

## Key results

The application successfully ran both available extraction modes on the team's sample unit outline.

- Exact baseline: Data Scientist 41.9%, Data Analyst 40.1%, ML Engineer 39.0%, Data Engineer 23.1%, AI Engineer 21.8%.
- Hybrid semantic: Data Scientist 41.9%, ML Engineer 41.7%, Data Analyst 40.1%, Data Engineer 23.1%, AI Engineer 21.8%.
- In this example, semantic matching increased the ML Engineer score from 39.0% to 41.7% and changed its rank from third to second. This is an illustrative case, not evidence that the hybrid method is always superior.

User testing (n=3):
- Ease of upload/analysis: 3.33/5
- Career-result clarity: 5.00/5
- Usefulness of skills/gaps: 4.33/5
- Explanation clarity: 5.00/5
- Overall usefulness: 4.33/5
- Overall mean across all ratings: 4.40/5

The strongest ratings were for clarity of the career results and explanations (both 5.00/5). The main usability concern was hybrid-model latency and uncertainty about the difference between the two extraction modes.

## Files and how to run them

- `app.py`: final Streamlit user interface.
- `requirements.txt`: Step 6 dependencies.
- `user_testing/user_testing_results.csv`: participant ratings and open feedback.
- `user_testing/README.md`: testing procedure and summary.

From the repository root:

```bash
pip install -r step6_app/requirements.txt
streamlit run step6_app/app.py
```

The first hybrid-semantic run may take longer because the Sentence Transformer model may need to load/download.

## Inputs and outputs

**Inputs from other steps**
- Step 3: PDF study-material extraction, exact skill matches and page-level evidence.
- Step 4: semantic skill additions for hybrid matching.
- Step 5: `CareerMatchingAPI`, career profiles, match scores, priority gaps and learning recommendations.

**Outputs**
- Interactive ranked career matches.
- Matched skills and priority gaps.
- Evidence from the uploaded PDF.
- Suggested skills to develop.
- Downloadable JSON results.
- User-testing results for the final report.

## Limitations

The hybrid semantic mode has higher latency than the exact baseline, especially on first use. One tester was still uncertain about the distinction between the two modes. The recommendation is based mainly on skill overlap and does not model other hiring factors such as work experience, education, interview performance or labour-market competition. Match percentages should therefore be interpreted as skill-alignment scores rather than probabilities of obtaining a job. The user test was also very small (n=3) and should be treated as formative rather than representative.
