# Step 2: Skills dictionary and normalisation

## Task
Build the shared skill vocabulary that lets job advertisements and unit documents be compared. The dictionary has 132 canonical skills, 232 reviewed aliases and 12 categories. Aliases map to one canonical name (for example `ML` to `Machine Learning`), and short or ambiguous terms such as `R`, `C++`, `SQL` and `dbt` get strict token matching instead of substring matching. The dictionary was validated for conflicts and used to compute skill frequencies for each career.

## Work in this folder
| File | Purpose |
|---|---|
| `02_skill_dictionary_normalisation.ipynb` | Builds, validates and exports everything below |
| `outputs/skills_dictionary.csv` | Canonical skills, aliases and categories |
| `outputs/normalisation.py` | `normalise_skill()` alias-to-canonical function |
| `outputs/skill_frequency_by_career.csv` | Skill frequency per career |
| `outputs/skill_taxonomy.md` | The 12 categories and their skills |

## How to run
```
jupyter lab 02_skill_dictionary_normalisation.ipynb    # reads ../step1_data/job_cleaned.csv; Run All
```

## Key results
* 132 skills, 232 aliases, 12 categories, 0 aliases mapped to more than one skill.
* 7 skills do not occur in the current corpus (AWS Lambda, Cassandra, Data Cleaning, NLTK, Oracle, SciPy, spaCy) and were kept for future data and unit text.
* Career-level frequencies differ clearly between careers, which is why Step 5 builds a profile per career.

## Output used next
`skills_dictionary.csv` and `normalisation.py` feed the Step 3 extractor (copies sit in `step3_baseline_nlp/`).

## Limitations
A controlled vocabulary misses skills outside it. Frequency counts mentions, not importance or required proficiency.
