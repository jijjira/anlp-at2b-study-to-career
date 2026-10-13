# Step 1: Job-ad collection and cleaning

## Task
Collect Data and AI job advertisements from public job boards and clean them into the U.S. benchmark used by every later step. 1,083 advertisements were collected on 1 October 2026 from public Greenhouse, Ashby, Remote OK and Remotive feeds. Career labels and dates were standardised, duplicates and records with missing values were removed, only identifiable U.S. locations were kept, and NLP Engineer was dropped (one advertisement, located in India). Original descriptions and source links were kept for traceability.

## Work in this folder
| File | Purpose |
|---|---|
| `collect_public_jobs.py` | Collection script |
| `requirements.txt` | Libraries for the script and the notebook |
| `public_jobs_2020_2026.csv` | Raw snapshot (1,083 records, 12 columns) |
| `01_data_cleaning.ipynb` | Cleaning, U.S. filtering and descriptive statistics |
| `job_cleaned.csv` | Cleaned benchmark (688 advertisements), used by Steps 2, 3 and 5 |
| `australia/` | Separate 14-advertisement Australian set with its collection scripts and notes; not part of the benchmark |

## How to run
```
pip install -r requirements.txt
python collect_public_jobs.py                    # optional: listings change, so results would differ
jupyter lab 01_data_cleaning.ipynb               # Run All; reproduces job_cleaned.csv exactly
```

## Key results
* 688 cleaned U.S. advertisements from 106 employers (Greenhouse 489, Ashby 199), posted 2021 to 2026 (591 from 2026); 395 of the 1,083 raw records were removed.
* Five careers: AI Engineer 275, ML Engineer 202, Data Scientist 127, Data Engineer 57, Data Analyst 27.
* 12 columns kept unchanged, no missing values.

## Limitations
A convenience sample from selected public boards, dominated by large technology employers. Careers were assigned by job-title keyword rules, city-only locations were not geocoded, and source terms of use apply to any redistribution.
