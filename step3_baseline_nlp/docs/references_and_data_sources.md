# References, dataset and curriculum sources 

APA 7.

## 1. Job-ad dataset (U.S. benchmark)
| Item | Detail |
|---|---|
| File | `job_cleaned.csv` (from Step 1) |
| Size | 688 ads, 106 companies, 5 career categories (AI Engineer 275, ML Engineer 202, Data Scientist 127, Data Engineer 57, Data Analyst 27) |
| Source | Public company job boards read through the Greenhouse (489 ads) and Ashby (199 ads) job-posting interfaces; every ad keeps its `source_url` |
| Dates | `date_posted` from 2021-08-27 to 2026-10-01 (591 ads from 2026); all collected on 2026-10-01 (`collected_at`) |
| Fields | job_id, career_category, job_title, company, job_description, date_posted, year, date_basis, location, source, source_url, collected_at |
| Not included | The 14 Australian ads are a separate small set and are not in this file |
| Content | Public job postings only, no personal data about applicants |

The collection script and dates are in `step1_data/`. The raw ads belong to the employers; the data are public postings used for coursework.

Dataset citations:
* Greenhouse Software. (n.d.). *Job Board API*. https://developers.greenhouse.io/job-board.html
* Ashby. (n.d.). *Public job posting API*. https://developers.ashbyhq.com/docs/public-job-posting-api

## 2. Curriculum sources (20 public unit documents, accessed 4 October 2026)
None of the three universities publishes a ready-made PDF of these unit descriptions; each is a web page with a print option, so the PDFs in `data/curriculum_pdfs/` are browser print-outs saved on 4 Oct 2026 (UTS and UNSW handbook pages, USYD outlines with every section expanded). `group` is "core" for the first 7 (all machine learning) and "added" for 13 units covering databases, big-data engineering, statistics, visualisation, foundations, NLP and software architecture. The UTS handbook shows only the description and learning outcomes (topics and assessment are on Canvas), so UTS coverage is a lower bound. `UTS_36106.pdf` and `UTS_36120.pdf` are earlier, thinner print-outs and could be replaced.

| Unit | Group | File | Page used |
|---|---|---|---|
| UTS 36100 Data Science for Innovation | added | UTS_36100.pdf | https://handbook.uts.edu.au/subjects/details/36100.html |
| UTS 36103 Statistical Thinking | added | UTS_36103.pdf | https://handbook.uts.edu.au/subjects/details/36103.html |
| UTS 36104 Data Visualisation and Narratives | added | UTS_36104.pdf | https://handbook.uts.edu.au/subjects/details/36104.html |
| UTS 36106 ML Algorithms | core | UTS_36106.pdf | https://handbook.uts.edu.au/subjects/details/36106.html |
| UTS 36117 Data Visualisation | added | UTS_36117.pdf | https://handbook.uts.edu.au/subjects/36117.html |
| UTS 36118 Applied NLP | core | UTS_36118.pdf | https://handbook.uts.edu.au/subjects/details/36118.html |
| UTS 36120 Adv ML Application | core | UTS_36120.pdf | https://handbook.uts.edu.au/subjects/details/36120.html |
| UTS 36124 Applied Data Science for Innovation | added | UTS_36124.pdf | https://handbook.uts.edu.au/subjects/details/36124.html |
| UTS 41091 Data Systems | added | UTS_41091.pdf | https://handbook.uts.edu.au/subjects/details/41091.html |
| UTS 94693 Big Data Engineering | added | UTS_94693.pdf | https://handbook.uts.edu.au/subjects/details/94693.html |
| USYD COMP5046 NLP | added | USYD_COMP5046.pdf | https://www.sydney.edu.au/units/COMP5046/2026-S1C-NE-CC |
| USYD COMP5310 Principles of Data Science | added | USYD_COMP5310.pdf | https://www.sydney.edu.au/units/COMP5310/2026-S2C-NE-CC |
| USYD COMP5318 ML and Data Mining | core | USYD_COMP5318.pdf | https://www.sydney.edu.au/units/COMP5318/2026-S2C-NE-CC |
| USYD COMP5348 Enterprise Software Architecture | added | USYD_COMP5348.pdf | https://www.sydney.edu.au/units/COMP5348/2026-S2C-NE-CC |
| USYD DATA5207 Data Analysis | core | USYD_DATA5207.pdf | https://www.sydney.edu.au/units/DATA5207/2026-S1C-ND-CC |
| UNSW COMP6713 NLP | added | UNSW_COMP6713_handbook.pdf | https://www.handbook.unsw.edu.au/postgraduate/courses/2027/COMP6713 |
| UNSW COMP9311 Database Systems | added | UNSW_COMP9311_handbook.pdf | https://www.handbook.unsw.edu.au/postgraduate/courses/2027/COMP9311 |
| UNSW COMP9321 Data Services Engineering | added | UNSW_COMP9321_handbook.pdf | https://www.handbook.unsw.edu.au/postgraduate/courses/2027/COMP9321 |
| UNSW COMP9417 ML and Data Mining | core | UNSW_COMP9417_handbook.pdf | https://www.handbook.unsw.edu.au/postgraduate/courses/2027/COMP9417 |
| UNSW COMP9444 Deep Learning | core | UNSW_COMP9444_handbook.pdf | https://www.handbook.unsw.edu.au/postgraduate/courses/2027/COMP9444 |

Manual review: `data/curriculum_manifest.csv` records the few false matches removed (server clustering read as machine-learning clustering in COMP5348, a cost note read as cloud computing in COMP5046, and an AI-usage policy sentence in COMP5310), each with a reason.

The condensed page text used earlier for the first seven units is kept in `real_units.py` as a sensitivity check only.

APA entries for the unit pages:
* University of Technology Sydney. (2026). *36100 Data Science for Innovation* [Handbook entry]. Retrieved October 4, 2026, from https://handbook.uts.edu.au/subjects/details/36100.html
* University of Technology Sydney. (2026). *36103 Statistical Thinking for Data Science* [Handbook entry]. Retrieved October 4, 2026, from https://handbook.uts.edu.au/subjects/details/36103.html
* University of Technology Sydney. (2026). *36104 Data Visualisation and Narratives* [Handbook entry]. Retrieved October 4, 2026, from https://handbook.uts.edu.au/subjects/details/36104.html
* University of Technology Sydney. (2026). *36106 Machine Learning Algorithms and Applications* [Handbook entry]. Retrieved October 4, 2026, from https://handbook.uts.edu.au/subjects/details/36106.html
* University of Technology Sydney. (2026). *36117 Data Visualisation* [Handbook entry]. Retrieved October 4, 2026, from https://handbook.uts.edu.au/subjects/36117.html
* University of Technology Sydney. (2026). *36118 Applied Natural Language Processing* [Handbook entry]. Retrieved October 4, 2026, from https://handbook.uts.edu.au/subjects/details/36118.html
* University of Technology Sydney. (2026). *36120 Advanced Machine Learning Application* [Handbook entry]. Retrieved October 4, 2026, from https://handbook.uts.edu.au/subjects/details/36120.html
* University of Technology Sydney. (2026). *36124 Applied Data Science for Innovation* [Handbook entry]. Retrieved October 4, 2026, from https://handbook.uts.edu.au/subjects/details/36124.html
* University of Technology Sydney. (2026). *41091 Data Systems* [Handbook entry]. Retrieved October 4, 2026, from https://handbook.uts.edu.au/subjects/details/41091.html
* University of Technology Sydney. (2026). *94693 Big Data Engineering* [Handbook entry]. Retrieved October 4, 2026, from https://handbook.uts.edu.au/subjects/details/94693.html
* The University of Sydney. (2026). *COMP5046 Natural Language Processing* [Unit outline]. Retrieved October 4, 2026, from https://www.sydney.edu.au/units/COMP5046/2026-S1C-NE-CC
* The University of Sydney. (2026). *COMP5310 Principles of Data Science* [Unit outline]. Retrieved October 4, 2026, from https://www.sydney.edu.au/units/COMP5310/2026-S2C-NE-CC
* The University of Sydney. (2026). *COMP5318 Machine Learning and Data Mining* [Unit outline]. Retrieved October 4, 2026, from https://www.sydney.edu.au/units/COMP5318/2026-S2C-NE-CC
* The University of Sydney. (2026). *COMP5348 Enterprise Scale Software Architecture* [Unit outline]. Retrieved October 4, 2026, from https://www.sydney.edu.au/units/COMP5348/2026-S2C-NE-CC
* The University of Sydney. (2026). *DATA5207 Data Analysis in the Social Sciences* [Unit outline]. Retrieved October 4, 2026, from https://www.sydney.edu.au/units/DATA5207/2026-S1C-ND-CC
* UNSW Sydney. (2026). *COMP6713 Natural Language Processing* [Handbook entry]. Retrieved October 4, 2026, from https://www.handbook.unsw.edu.au/postgraduate/courses/2027/COMP6713
* UNSW Sydney. (2026). *COMP9311 Database Systems* [Handbook entry]. Retrieved October 4, 2026, from https://www.handbook.unsw.edu.au/postgraduate/courses/2027/COMP9311
* UNSW Sydney. (2026). *COMP9321 Data Services Engineering* [Handbook entry]. Retrieved October 4, 2026, from https://www.handbook.unsw.edu.au/postgraduate/courses/2027/COMP9321
* UNSW Sydney. (2026). *COMP9417 Machine Learning* [Handbook entry]. Retrieved October 4, 2026, from https://www.handbook.unsw.edu.au/postgraduate/courses/2027/COMP9417
* UNSW Sydney. (2026). *COMP9444 Neural Networks and Deep Learning* [Handbook entry]. Retrieved October 4, 2026, from https://www.handbook.unsw.edu.au/postgraduate/courses/2027/COMP9444

## 3. Methods and tools references
* Decorte, J.-J., Van Hautte, J., Develder, C., & Demeester, T. (2025). *Efficient text encoders for labor market analysis* (arXiv:2505.24640). https://arxiv.org/abs/2505.24640
* Efron, B. (1979). Bootstrap methods: Another look at the jackknife. *The Annals of Statistics, 7*(1), 1-26.
* Fareri, S., Melluso, N., Chiarello, F., & Fantoni, G. (2021). SkillNER: Mining and mapping soft skills from any text. *Expert Systems with Applications, 184*, Article 115544. (preprint arXiv:2101.11431; VERIFY journal details)
* Honnibal, M., Montani, I., Van Landeghem, S., & Boyd, A. (2020). *spaCy: Industrial-strength natural language processing in Python* [Software]. Explosion. https://spacy.io
* Artifex Software. (n.d.). *PyMuPDF* [Software]. https://pymupdf.readthedocs.io
* Lightcast. (n.d.). *Lightcast SkillsMatch*. https://lightcast.io
* Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using Siamese BERT-networks. *Proceedings of EMNLP-IJCNLP 2019*, 3982-3992.
