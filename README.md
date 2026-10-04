# From Study Materials to Career Recommendations

**UTS 36118 Applied NLP: AT2 Part B, Group 6**

**Research question:** Are Australian university curricula aligned with the skills demanded by the U.S. Data/AI labour market?

We extract skills from Data/AI job advertisements (the U.S. benchmark) and from a student's study materials (unit outlines), compare the two, and recommend careers and the skills to learn next.

```
job ads (Student 1) -> skills dictionary (Student 2) -> skill extraction (Students 3 and 4)
unit outline PDFs -> skills covered, with page evidence (Student 3) ---------^
        \-> career profiles and matching (Student 5) -> app and user testing (Student 6)
```

## Team

Each student fills in their own section below (and keeps their code in their own folder). Please add your name and update your section before 14 Oct.

| Student | Name | Role | Folder |
|---|---|---|---|
| 1 | (add name) | Job-ad data collection and cleaning | `step1_data/` |
| 2 | (add name) | Skills dictionary and normalisation | `step2_dictionary/` |
| 3 | Jirawan Pedersen | Baseline NLP (PhraseMatcher), PDF reader, curriculum alignment, sector lens | `step3_baseline_nlp/` |
| 4 | (add name) | Semantic NLP (Sentence Transformers) and main evaluation | `step4_semantic/` |
| 5 | (add name) | Career profiles and matching | `step5_matching/` |
| 6 | Tengxiao Nong | Streamlit app and user testing | `step6_app/` |

*(Roles follow our team division document. Correct anything that has changed, and rename folders if the group prefers other names.)*

## Quick start (everyone, including the instructor)

```bash
git clone <repo-url> && cd <repo>
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
jupyter lab
```

Run each notebook from inside its own step folder (they import local `.py` files) and use **Restart & Run All**. In Google Colab, open a notebook and run its first cell. The Step 3 notebooks find the project files automatically (current folder, then this repo, then a shared Drive folder, then a zip upload) and list anything missing. If the repo is private, upload the submission zip when asked.

---

## Student 1: Job-ad data collection and cleaning

*To be added by Student 1.*

* What I did:
* Key results (for example number of ads, companies, date range):
* Files and how to run them:
* Limitations:

---

## Student 2: Skills dictionary and normalisation

*To be added by Student 2.*

* What I did:
* Key results (for example number of skills, aliases, categories):
* Files and how to run them:
* Limitations:

---

## Student 3: Baseline NLP, PDF reader, curriculum alignment and sector lens (Jirawan Pedersen)

Folder: `step3_baseline_nlp/` (full detail in its own README). Data input: `job_cleaned.csv`, `skills_dictionary.csv`, `normalisation.py` from Students 1 and 2.

**What I did**

1. **Baseline extractor:** a spaCy PhraseMatcher over the shared skills dictionary (case-insensitive, with a case-sensitive rule for the language "R").
2. **Improved extractor ("Baseline++"):** reads each job ad by section (required, duty, preferred, company text), weights skills by how strongly the ad asks for them, guards ambiguous words (for example "R&D" is not R, "spark discussion" is not Apache Spark), and adds 45 reviewed aliases mined from the ads.
3. **Evaluation:** a 30-ad stratified gold set, an ablation (S0 to S5), bootstrap confidence intervals and an error analysis.
4. **PDF reader:** PyMuPDF text extraction from unit outlines, with header, footer, hyphenation and table-column clean-up, a coverage level per skill (assessed, taught, mentioned) with page evidence, and filters so requisites, "further study" sentences and AI-policy tables are not counted as coverage. Tested on 20 real PDFs, which exposed and fixed four bugs.
5. **Curriculum alignment:** a career fit score with confidence ranges and a ranked list of the biggest skill gaps.
6. **Sector lens:** companies grouped into sectors, tested with company-clustered methods to see whether skill demand depends on the employer's sector.
7. **Case study:** the research question run on 20 real unit PDFs from UTS, USYD and UNSW (saved in `step3_baseline_nlp/data/curriculum_pdfs/`).

**Run order** (`step3_baseline_nlp/`)

1. `03_skill_extraction.ipynb`: baseline extraction on 688 ads, outputs `job_skills_extracted.csv`, `job_skills_long.csv`
2. `04_innovation_experiments.ipynb`: held-out evaluation, ablation, error analysis
3. `05_study_material_pipeline.ipynb`: PDF study material to skills
4. `06_curriculum_alignment.ipynb`: career fit, gaps and heatmap (synthetic demo units)
5. `07_sector_lens.ipynb`: sector profiles, permutation test, universal and sector-specific skills
6. `08_real_curriculum_case_study.ipynb`: the 20 real unit PDFs against the U.S. benchmark
7. Optional: `python run_step3.py`, `pytest` (40 tests)

**Reusable API for other students**

```python
from skill_extractor import extract_skills                 # baseline
from skill_extractor_v2 import RequirementAwareExtractor    # requirement-aware, demand weights
from extraction import analyse_study_material, analyse_text # PDF (path, bytes or Streamlit upload) or text -> skills + pages
from alignment import DemandModel, job_strengths, curriculum_coverage
x = RequirementAwareExtractor("skills_dictionary.csv", extra_aliases_path="extra_aliases_reviewed.csv", expand_morphology=True)
x.extract_weighted(text)   # {skill: demand weight}
```

**Figures:** charts appear inside each notebook and are saved as PNGs in `step3_baseline_nlp/figures/` for the report and slides.

**Main files:** `skill_extractor.py`, `skill_extractor_v2.py`, `extraction.py`, `alignment.py`, `sectors.py`, `sector_analysis.py`, `company_sector_map.csv`, `real_units.py`, `evaluate.py`, `gold_annotations.py`, `gold_split.json`, `extra_aliases_reviewed.csv`, and `docs/` (report section, handoff note, references and data sources).

**Key results**

* **Extraction (30-ad held-out gold set, seed 36118):** micro-F1 0.872 (baseline) to 0.943 (Baseline++), delta F1 +0.071, 95% CI [0.039, 0.104]. The gain comes from the reviewed dictionary expansion. The section-aware filter is not significant on F1, but it gives demand-weighted career profiles. About 27% of the skills a human reads are implicit or missing from the dictionary, which is the target for Student 4.
* **Sector lens (6 main sectors, 688 ads):** demand profiles differ by sector (permutation test p = 0.004, but p = 0.06 after adjusting for career mix, so we call it suggestive). Python, AI, Machine Learning and LLMs are demanded in every sector.
* **Case study (20 real unit PDFs from UTS, USYD and UNSW):** taking the best coverage across all 20 units, career fit is highest for Data Scientist (0.65), then Data Engineer (0.59), ML Engineer (0.58) and Data Analyst (0.58), and lowest for AI Engineer (0.33). Selection mattered: with only 7 ML units Data Engineer fit was 0.13, and adding database, big-data engineering and statistics units closed the SQL, Spark and Snowflake gaps. Gaps that remain: Causal Inference, A/B testing, experiment design, dashboarding, observability, dbt, cloud platforms, agents. This is a case study of 20 chosen units, and handbook PDFs are shorter than full outlines (UTS shows only description and learning outcomes), so a gap may be taught elsewhere.

**Limitations:** single (AI) annotator, n = 30; handbook pages are shorter than full outlines; extractor validated on job ads, not unit text; exact-phrase matching misses skills taught without naming them; sector labels are manual (17 borderline); health tech (22 ads) is exploratory only.

**Handoffs:** Student 4 runs the semantic model on the same 30 gold ads (see `docs/HANDOFF_to_member4.md`). Students 5 and 6 can call the alignment functions above.

---

## Student 4: Semantic NLP (Sentence Transformers) and main evaluation

*To be added by Student 4.*

* What I did:
* Key results (compare against the Step 3 baseline on the same 30 gold ads):
* Files and how to run them:
* Limitations:

---

## Student 5: Career profiles and matching

*To be added by Student 5.*

* What I did:
* Key results:
* Files and how to run them:
* Limitations:

---

## Student 6: Streamlit app and user testing (Tengxiao Nong)

*To be added by Tengxiao.*

* What I did:
* Key results (for example user testing findings):
* Files and how to run them:
* Limitations:

---

## Data and references

* Job ads: 688 public postings from 106 companies (Greenhouse and Ashby job boards), collected 1 Oct 2026. The 14 Australian ads are a separate, small set.
* Curriculum sources: 20 public unit pages (UTS, USYD, UNSW handbooks), saved as PDFs in `step3_baseline_nlp/data/curriculum_pdfs/` and listed with URLs and APA references in `step3_baseline_nlp/docs/references_and_data_sources.md`.
* Please add your own data sources and references there, or in `report/`.

## Group limitations (keep in the report)

* U.S.-only job data, mostly large tech employers and mostly 2026 ads. The Australian set is too small (14 ads) for separate tests.
* Twenty selected units is a case study, not all of Australian higher education or whole degrees.
* Gold labels come from a single AI annotator; a second human annotator on about 10 ads would help.

## Repo layout

```
data/                 shared inputs (check course rules before making the repo public)
step1_data/ ... step6_app/
report/               draft sections, figures, references
requirements.txt
```

## Team conventions

* Work in your own step folder and open a pull request for changes to shared files (`data/`, `skills_dictionary.csv`).
* Commit notebooks **with outputs**. Do not commit `.venv/` or `__pycache__/`.
* Dictionary changes: Student 2 merges proposals (for example `extra_aliases_reviewed.csv`) and tells Students 3 to 5.
* Every notebook should start with a setup cell that works for anyone, with no personal paths.

## Checklist before the report is due (14 Oct)

- [ ] Each student fills in their section above and adds their part to `report/`
- [ ] Students 1 and 2: dataset and dictionary notes (collection date, categories, terms of use); check `company_sector_map.csv`
- [ ] Student 4: run the semantic model on the same 30 gold ads and compare with Step 3
- [ ] Students 5 and 6: plug in the alignment output and test the app with a few users
- [ ] Everyone: references checked, and every notebook runs from a clean start
