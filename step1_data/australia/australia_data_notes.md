# Australian job advertisements: data notes

The earlier `public_jobs_2020_2026.csv` is a multinational dataset and cannot serve as an Australian sample. This set was selected by the location of the vacancy, not by where the company is headquartered.

Re-collected on 2026-10-03. Total advertisements: 14. Careers: AI Engineer 8, Data Analyst 2, ML Engineer 3, Data Engineer 1. Years: all 14 are from 2026.

Sources are the public Greenhouse, Ashby and SmartRecruiters job-board interfaces. Every record has its actual advertisement link and description. The 12 fields are the same as in the main CSV; no columns were added. NLP Engineer is still excluded, records missing any output field are dropped, and duplicates are removed by company, title, location and posting date.

A location must explicitly contain Australia/AU/AUS or a recognisable Australian city or state. Advertisements located only as Global, Remote or APAC were not counted as Australian. The posting date comes from the date field supplied by each interface; for SmartRecruiters it is `releasedDate`, which may be a re-release date and does not guarantee the first historical posting date.

This batch is small and contains 2026 records only. The `2020_2026` in the file name is the date-filter range, not a claim that every year has data. It is not a complete seven-year history, and the absence of a career category must not be read as that career not existing in the Australian market. The source list is dominated by international technology companies and its coverage is incomplete.

To reproduce, run `collect_australia_jobs.py` and then `supplement_australia_jobs.py` (needs `requests` and `beautifulsoup4`). Interface failures are listed in the JSON summary. Later runs will return different data.
