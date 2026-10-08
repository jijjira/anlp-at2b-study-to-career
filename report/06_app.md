## 6. Web Application, User Testing and Discussion

### 6.1 Streamlit application

The final pipeline was exposed through a Streamlit interface so that a student can interact with the NLP and matching components without running notebooks or code. The application accepts a university course or unit PDF and calls the existing Step 5 `CareerMatchingAPI`, which integrates the upstream PDF skill extraction and career-profile matching. Users can select either **Exact keyword matching (Baseline)** or **Hybrid semantic matching**, and can request the top three to five career results.

The output is designed to be explainable rather than presenting only a single recommendation. The interface shows (1) ranked career match percentages, (2) a comparison bar chart, (3) skills covered by the uploaded material, (4) priority skill gaps, (5) a short explanation of why the career matched, (6) page-level evidence returned by the study-material pipeline, and (7) suggested skills to develop. Results can also be downloaded as JSON. A responsible-use notice states that detected skills represent coverage in the uploaded material rather than evidence that the student has personally mastered them, and that the career match is a skill-alignment result rather than a definitive career decision.

A small display-layer consistency check was added so that a skill already shown as covered is not simultaneously displayed as a priority gap. This does not alter the upstream matching result or the downloadable raw JSON; it only avoids contradictory presentation in the user interface. Career-demand weights are displayed as percentages to make them easier for non-technical users to interpret.

Both available matching modes were successfully integrated. On the sample unit outline used during interface testing, the exact baseline returned Data Scientist (41.9%), Data Analyst (40.1%) and ML Engineer (39.0%) as the top three careers. With hybrid semantic matching, Data Scientist remained first at 41.9%, while ML Engineer increased to 41.7% and moved from third to second; Data Analyst remained at 40.1%. This single example is useful for demonstrating that semantic additions can affect downstream ranking, but it should not be interpreted as evidence that the hybrid method is always better.

### 6.2 User testing

A small formative user test was conducted with **three classmates** after the application was functional. Participants used the interface and then rated five statements on a five-point Likert scale (1 = strongly disagree, 5 = strongly agree). The questions covered ease of use, clarity of career results, usefulness of matched skills and gaps, clarity of explanations, and overall usefulness for exploring study-to-career alignment. One open-ended improvement question was also included.

| Measure | P1 | P2 | P3 | Mean |
|---|---:|---:|---:|---:|
| Ease of PDF upload and analysis | 3 | 3 | 4 | 3.33 |
| Career match results were easy to understand | 5 | 5 | 5 | 5.00 |
| Matched skills and priority gaps were useful | 4 | 4 | 5 | 4.33 |
| Explanations clarified why careers were recommended | 5 | 5 | 5 | 5.00 |
| Would use the app to explore study-to-career alignment | 5 | 4 | 4 | 4.33 |

The overall mean across all 15 ratings was **4.40/5**. The strongest result was clarity: all three participants gave the maximum score for both the career-result presentation and the recommendation explanations. The lowest mean was for ease of use (3.33/5). The corresponding qualitative feedback from P1 identified two reasons: hybrid semantic matching took noticeably longer to run, and the difference between the exact and hybrid modes was not fully clear. P2 noted a conceptual limitation of the system: real recruitment decisions depend on additional factors such as work experience and educational background. P3 described the application positively but remained concerned about their ability to obtain a good job, illustrating that a career-alignment tool cannot remove the broader uncertainty associated with employment outcomes.

No further interface changes were made after this small test because none of the participants reported a task-blocking usability problem. Instead, the feedback was retained as evidence for the limitations and future-work discussion.

### 6.3 Discussion and limitations

The user test suggests that the main strength of the application is **interpretability**. Participants consistently understood the ranked career results and the explanation of why a career was recommended. Showing both covered skills and priority gaps, together with source evidence, makes the recommendation easier to inspect than a black-box career label.

However, the test also highlights several limitations. First, semantic matching has greater computational cost than the exact baseline, particularly when the Sentence Transformer model is loaded for the first time. A future deployment could reduce this friction through model caching, pre-loading or a hosted service. Second, although the interface labels the two methods, a user may still not understand why they should choose one over the other; a future version could provide a short plain-language comparison or automatically select the recommended mode. Third, the current career score is based primarily on skill alignment. It does not include work experience, degree level, portfolio quality, location, salary expectations, interview performance or labour-market competition. Consequently, a 41.9% match should be interpreted only as alignment with the skills represented in the project's job-ad profiles, not as a 41.9% probability of obtaining that job.

Finally, the usability study involved only three classmates and was intended as a formative check rather than a representative evaluation. Future work should test a larger and more diverse student sample, collect task-completion times, and evaluate whether recommendations remain understandable when users upload a wider range of study documents.
