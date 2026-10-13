# User testing

Three classmates completed a short formative usability test of the first version of the Streamlit application (version 1).

## Tasks
1. Upload a university study-material PDF.
2. Select the exact baseline or hybrid semantic matching method.
3. Generate career matches.
4. Review career rankings, skills covered, priority gaps, explanations and suggested skills to develop.
5. Complete a five-item Likert questionnaire plus one open-ended question.

Scale: 1 = Strongly disagree, 5 = Strongly agree.

## Results

| Item | Mean / 5 |
|---|---:|
| Q1 Ease of upload and analysis | 3.33 |
| Q2 Clarity of career results | 5.00 |
| Q3 Usefulness of matched skills and gaps | 4.33 |
| Q4 Clarity of recommendation explanations | 5.00 |
| Q5 Usefulness for exploring study-to-career alignment | 4.33 |
| **Overall mean across all 15 ratings** | **4.40** |

## Open feedback
- P1: Hybrid mode was slow, and the distinction between the two matching modes was unclear.
- P2: Career suitability also depends on work experience and education, not only skill overlap.
- P3: The application was viewed positively, but the participant remained concerned about finding a good job.

No participant reported a task-blocking usability issue. The feedback was then used to revise the interface (version 2), and the revised version was then tested with five students (see the second test below):
- P1 (slow hybrid mode, unclear difference between modes): the modes now have plain-language names with a one-line explanation, the spinner says the first hybrid run loads a model, and a "how to read the results" panel was added.
- P2 (experience and education also matter): the responsible-use notice now says this explicitly.
- P3 (worry about finding a job): the notice states that a score is not the chance of getting a job.
- Other changes: a sample outline button, a tie warning for scores within two points, "possibly covered" marking for semantic-only skills, and a CSV download of the gaps.

## Second test (five students)

Five students used the application and rated the same five statements on the same 1 to 5 scale. Each participant's ratings are in `user_testing_round2.csv`. No comments were recorded for this round, and its participants differ from the pilot, so the change from the pilot is indicative, not a measured effect.

| Item | Mean / 5 | Pilot mean (n = 3) |
|---|---:|---:|
| Q1 Ease of upload and analysis | 4.20 | 3.33 |
| Q2 Clarity of career results | 4.40 | 5.00 |
| Q3 Usefulness of matched skills and gaps | 4.40 | 4.33 |
| Q4 Clarity of recommendation explanations | 3.80 | 5.00 |
| Q5 Usefulness for exploring study-to-career alignment | 4.60 | 4.33 |
| **Overall mean across all 25 ratings** | **4.28** | 4.40 |

Explanation clarity was rated lowest (two ratings of 3), so the explanation panel is the first part to evaluate next.
