# Step 2: Skills dictionary and normalisation (Wancheng Liu)

This step builds the controlled skill dictionary and normalisation layer used by the downstream NLP pipeline.

## What I did

- Built a controlled Data/AI skill dictionary from the cleaned U.S. job dataset.
- Defined **132 canonical skills**, **232 aliases**, and **12 skill categories**.
- Added alias-to-canonical normalisation rules, for example:
  - `ML` → `Machine Learning`
  - `LLM` / `LLMs` → `Large Language Models`
  - `Amazon Web Services` → `AWS`
  - `PowerBI` → `Power BI`
- Added safer matching rules for short or ambiguous skills such as `R`, `C++`, and `C#`.
- Validated the dictionary against the cleaned job descriptions.
- Calculated overall skill frequencies and career-level skill frequencies for later career-profile construction.

## Key results

| Metric | Result |
|---|---:|
| Job ads analysed | 688 |
| Canonical skills | 132 |
| Aliases | 232 |
| Skill categories | 12 |
| Conflicting aliases | 0 |
| Zero-match canonical skills | 7 |

High-frequency skills in the current U.S. Data/AI job sample included:

- Python: **66.3%**
- Large Language Models: **46.7%**
- Machine Learning: **43.6%**
- SQL: **34.7%**

Career-level profiles also showed clear differences:

- **Data Scientist:** SQL, Python, Statistics, Causal Inference, Machine Learning
- **ML Engineer:** Machine Learning, Python, Large Language Models, PyTorch, TensorFlow

These differences support the use of career-specific skill profiles in later alignment stages.

## Files and how to run them

### Main notebook

`02_skill_dictionary_normalisation.ipynb`
1. loads `job_cleaned.csv`
2. defines the skill taxonomy
3. builds alias-to-canonical mappings
4. validates the dictionary
5. calculates overall skill frequencies
6. calculates career-level skill frequencies
7. exports the Step 2 outputs

## Inputs and outputs

### Input from Step 1

- `job_cleaned.csv`

### Outputs

- `skills_dictionary.csv`  
  Canonical skills, aliases, categories, and frequency information.

- `skill_frequency_by_career.csv`  
  Skill frequencies for each career category.

- `normalisation.py`  
  Reusable alias-to-canonical normalisation functions.

- `skill_taxonomy.md`  
  Documentation of the skill categories and normalisation rules.

## Downstream use

Student 3 can use:

- `job_cleaned.csv`
- `skills_dictionary.csv`
- `normalisation.py`

to build the spaCy `PhraseMatcher` skill-extraction pipeline.

Recommended flow:

```text
job_description
→ PhraseMatcher
→ matched alias
→ canonical skill
→ remove duplicates

## Limitations

- The dictionary is a controlled vocabulary and may not cover every emerging or uncommon technical skill.
- Explicit phrase matching may miss skills that are described indirectly.
- Short or ambiguous aliases still require careful downstream validation.
- Seven canonical skills were not found in the current job sample, but were retained for future data and curriculum analysis.
- Skill frequency reflects how often a skill is mentioned in job advertisements, not its importance, required proficiency, or hiring probability.
- The current dataset represents a selected sample of U.S. Data/AI jobs rather than the entire U.S. labour market.
- Final job-level skill extraction is handled in Step 3.

## Extra libraries

No additional libraries beyond the shared `requirements.txt`.

Main dependencies used in this step:

- `pandas`
- `re`
- `pathlib`

## Dictionary design notes

The 132 canonical skills and aliases were selected using:

1. common Data/AI technical skills
2. terminology observed in the cleaned U.S. job advertisements
3. alternative spellings and abbreviations requiring normalisation

The skills were grouped into 12 categories to make later extraction, analysis, and alignment more interpretable.

If the dictionary is updated later, Students 3–5 should be notified so that downstream extraction and alignment remain consistent.
