
# Step 1: Job-ad data collection and cleaning (Zheke Yi)

## What I did

I collected job advertisements from public Greenhouse, Ashby, Remote OK and Remotive feeds using Python and stored them in a consistent 12-column CSV format. The original collection did not restrict countries, so it included advertisements from the United States, Canada, the United Kingdom, India, Australia and other countries. I standardised career labels and dates, checked for duplicates, removed records with missing values, and retained identifiable US locations while excluding explicitly mixed-country locations. NLP Engineer was excluded because it had only one advertisement, which was also located in India. Original job descriptions and source links were preserved for subsequent NLP analysis and reproducibility.

## Key results

| Measure | Result |
|---|---:|
| Original multinational records | 1,083 |
| Cleaned US records | 688 |
| Retained columns | 12 |
| Remaining missing values | 0 |
| Retained career categories | 5 |

| Career category | Job advertisements |
|---|---:|
| AI Engineer | 275 |
| ML Engineer | 202 |
| Data Scientist | 127 |
| Data Engineer | 57 |
| Data Analyst | 27 |
| Total | 688 |

Seven records had missing locations. During US filtering, another seven records that matched US locations also explicitly listed non-US locations and were excluded.

The cleaned dataset retained the original 12 columns without adding new fields: job ID, career category, job title, company, job description, publication date, year, date basis, location, source, source URL and collection date.

## Files and how to run them

| File | Purpose |
|---|---|
| `collect_public_jobs.py` | Collects advertisements from public recruitment feeds |
| `public_jobs_requirements.txt` | Dependencies for the collection script |
| `public_jobs_2020_2026.csv` | Fixed raw dataset used for this analysis |
| `clean_jobs.ipynb` | Data cleaning, US filtering and descriptive statistics |
| `jobs.csv` | Cleaned dataset for subsequent steps |

From this folder, install the collection dependencies:

```bash
python3 -m pip install -r public_jobs_requirements.txt
```

Run the collection script:

```bash
python3 collect_public_jobs.py
```

The script overwrites the raw CSV in its directory. Use the saved raw snapshot to reproduce the reported results, and back it up before collecting a new snapshot because online listings change.

To reproduce cleaning, open `clean_jobs.ipynb` and select **Run All**. The notebook should begin with the shared Step 3 setup template and use project-relative paths rather than personal computer paths.

## Inputs and outputs

- **Inputs from other steps:** None. This step starts with public recruitment feeds and the fixed raw CSV.
- **Outputs other steps can use:** `jobs.csv`, containing 688 cleaned US advertisements with career labels, original job descriptions and source information.

Subsequent NLP steps can use `job_description` as the text input and `career_category` for comparisons between careers. Excluding the NLP Engineer career category does not prevent the use of NLP methods to analyse the remaining five categories.

## Limitations

The original data are a multinational convenience sample from selected public feeds. The final US sample was obtained through location filtering and is not a complete or representative sample of the US labour market. Coverage is uneven across companies, platforms and career categories.

US locations were identified using country labels, state names and city names. Explicitly mixed-country locations and ambiguous remote locations were excluded, but city-only labels were not independently geocoded.

NLP Engineer was excluded because it contained only one advertisement and that advertisement was located in India. The findings therefore do not cover this career category. Removing records with missing values may also introduce selection bias.

The filename indicates the intended 2020–2026 publication-date filter. However, the original records cover 2021–2026 and do not constitute a complete historical archive. Annual record counts should not be interpreted as changes in overall market demand.

Descriptions were converted from HTML to plain text during collection. Cleaning preserved the descriptions supplied in the input CSV. A saved advertisement does not guarantee that the vacancy remains open.

Future work could expand employer and platform coverage and manually validate a sample of career labels and locations.

## Extra libraries

This step uses `requests`, `beautifulsoup4` and `pandas`. Check the shared `requirements.txt` before installing dependencies that may already be included.

### Collection method and date

The fixed original dataset used for this analysis was collected on **1 October 2026**. The script requested public JSON endpoints using `requests` and extracted description text using BeautifulSoup.

Company board identifiers were obtained from the public `ConorsCode/open-jobs-data` registry. The script queried the first 120 Greenhouse boards and all Ashby boards in that registry, supplemented by the Remote OK and Remotive public feeds.

Collection is run manually. Each execution retrieves advertisements available through the feeds at that time; the saved CSV does not update automatically.

### Data sources

- Greenhouse: https://boards-api.greenhouse.io
- Ashby: https://api.ashbyhq.com
- Remote OK: https://remoteok.com/api
- Remotive: https://remotive.com/api/remote-jobs
- Company board registry: https://github.com/ConorsCode/open-jobs-data

### Assignment of `career_category`

Career categories were assigned using job-title keyword rules rather than a trained classification model. For example, “Machine Learning Engineer” was mapped to “ML Engineer”, and “Artificial Intelligence Engineer” was mapped to “AI Engineer”.

The original dataset contained six career categories, while the final analysis retained five. Interdisciplinary titles were assigned to a single category, so classification errors remain possible.

### Source-use conditions

Source names and original advertisement URLs were retained for traceability. When sharing Remote OK and Remotive records, their attribution and backlink requirements should be respected. Use and redistribution of other records should follow the relevant platform and employer terms; public accessibility does not imply unrestricted redistribution rights.
