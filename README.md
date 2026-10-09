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
| 1 | Zheke Yi | Job-ad data collection and cleaning | `step1_data/` |
| 2 | Wancheng Liu | Skills dictionary and normalisation | `step2_dictionary/` |
| 3 | Jirawan Pedersen | Baseline NLP (PhraseMatcher), PDF reader, curriculum alignment, sector lens | `step3_baseline_nlp/` |
| 4 | Tao Lou | Semantic NLP (Sentence Transformers) and main evaluation | `step4_semantic/` |
| 5 | Tengxiao Nong | Career profiles and matching | `step5_matching/` |
| 6 | Chongyan Tang | Streamlit app and user testing | `step6_app/` |

*(Roles follow our team division document. Correct anything that has changed, and rename folders if the group prefers other names.)*

## Quick start (everyone, including the instructor)

Easiest, no install: open `step3_baseline_nlp/08_real_curriculum_case_study.ipynb` in Google Colab (File > Upload notebook), run the first cell, then Runtime > Run all. The first cell downloads the project zip from our shared Drive folder (https://drive.google.com/drive/folders/1itmHAXH4dyXbm1icJ1ip7RrRvXkMj9UK) and finds every file by itself. The other Step 3 notebooks work the same way. If the download fails, drag `Member3_Baseline_NLP.zip` from that Drive folder into Colab's Files panel and run the cell again.

On your own computer: download or clone the repo, open `step3_baseline_nlp/`, then right-click `run.command` and choose Open (Mac) or double-click `run.bat` (Windows). It installs what it needs, runs the 40 tests and opens the main notebook. Or by hand: `python -m venv .venv`, activate it, `pip install -r requirements.txt`, `jupyter lab`, and use Restart & Run All inside each step folder.

---

## Student 1: Job-ad data collection and cleaning (Zheke Yi)

*To be added by Student 1.*

* What I did:
* Key results (for example number of ads, companies, date range):
* Files and how to run them:
* Limitations:

---

## Student 2: Skills dictionary and normalisation (Wancheng Liu)

Folder: `step2_dictionary/`. Data input: `job_cleaned.csv` from Student 1.

**What I did**

1. **Controlled skill dictionary:** built a structured vocabulary for Data and AI job advertisements, containing 132 canonical skills and 232 reviewed aliases across 12 technical skill categories.
2. **Skill taxonomy:** grouped skills into Programming, Data Analysis & Statistics, Machine Learning & AI, NLP / Generative AI, ML Frameworks & Libraries, Data Engineering, Databases, Cloud, MLOps / Deployment, Data Visualisation / BI, Development Tools, and Methods / Architecture.
3. **Alias normalisation:** mapped different expressions of the same skill to one canonical representation, for example `ML` → `Machine Learning`, `LLM/LLMs` → `Large Language Models`, `Amazon Web Services` → `AWS`, and `PowerBI` → `Power BI`.
4. **Safe matching rules:** added stricter matching logic for short or ambiguous terms such as `R`, `C++`, `C#`, `AWS`, `GCP`, `LLM`, `NLP` and `SQL`, so that later extraction does not rely on unsafe substring matching.
5. **Dictionary validation:** checked for aliases mapped to multiple canonical skills, canonical skills with no matches in the current corpus, and short aliases requiring special treatment.
6. **Overall skill frequency:** used the 688 cleaned U.S. Data/AI job advertisements to estimate how frequently each canonical skill appeared in the current dataset.
7. **Career-level skill frequency:** calculated skill frequencies separately for each career category so later students could construct career-specific skill profiles rather than using one generic Data/AI profile.
8. **Reusable outputs:** exported the dictionary, career-level frequencies, taxonomy documentation and a reusable normalisation module for Student 3.

**Run order**

1. `02_skill_dictionary_normalisation.ipynb`: loads `job_cleaned.csv`, creates the taxonomy and alias mappings, validates matching rules, calculates skill frequencies and exports all Step 2 outputs.
2. Output: `skills_dictionary.csv`
3. Output: `skill_frequency_by_career.csv`
4. Output: `normalisation.py`
5. Output: `skill_taxonomy.md`

**Reusable API for other students**

```python
from normalisation import normalise_skill

normalise_skill("ML")
# "Machine Learning"

normalise_skill("LLMs")
# "Large Language Models"

normalise_skill("amazon web services")
# "AWS"
```

Student 3 can use the `alias` field in `skills_dictionary.csv` as spaCy PhraseMatcher patterns and then convert detected aliases into their canonical forms using `normalise_skill()`.

Recommended downstream flow:

```text
job_description
→ phrase matching
→ matched alias
→ canonical skill
→ remove duplicates
```

**Main files:** `02_skill_dictionary_normalisation.ipynb`, `skills_dictionary.csv`, `skill_frequency_by_career.csv`, `normalisation.py`, `skill_taxonomy.md`.

**Key results**

* **Skill vocabulary:** the final controlled vocabulary contains 132 canonical skills, 232 aliases and 12 technical categories.
* **Dictionary consistency:** validation found 0 aliases mapped to multiple canonical skills, indicating that the current alias-to-canonical mapping is internally consistent.
* **Zero-match skills:** 7 canonical skills were not found in the current U.S. job corpus: AWS Lambda, Cassandra, Data Cleaning, NLTK, Oracle, SciPy and spaCy. They were retained because they may still appear in future job data or student study materials.
* **Ambiguous aliases:** short terms such as `R`, `C++`, `C#`, `EDA`, `ETL`, `AWS`, `GCP`, `LLM`, `NLP`, `SQL` and `dbt` were explicitly identified as requiring careful phrase/token matching rather than simple substring matching.
* **Career-specific demand:** the skill-frequency analysis showed clear differences between career categories. For Data Scientist advertisements, the most frequent skills included SQL (89.76%), Python (88.98%), Statistics (65.35%), Causal Inference (51.18%) and Machine Learning (43.31%).
* **ML Engineer profile:** Machine Learning (82.67%), Python (64.36%), Large Language Models (52.48%), PyTorch (42.08%) and TensorFlow (29.21%) were among the strongest signals for ML Engineer advertisements.
* These differences support the use of career-specific skill profiles in the later alignment stage instead of treating all Data/AI jobs as having the same skill requirements.

**Limitations:** the dictionary is a controlled vocabulary and may not cover every emerging or uncommon technical skill; explicit phrase matching may miss skills expressed indirectly; short or ambiguous aliases still require additional validation in Step 3; 7 skills were not observed in the current job sample; frequency represents how often a skill is mentioned, not its importance, required proficiency or hiring probability; and the dataset represents a selected sample of U.S. Data/AI advertisements rather than the entire U.S. labour market.

**Handoffs**: Student 3 receives `job_cleaned.csv`, `skills_dictionary.csv` and `normalisation.py` and uses the aliases as spaCy PhraseMatcher patterns for job-level skill extraction. The same canonical vocabulary should also be used when extracting skills from Australian university study materials so that curriculum skills and U.S. job-demand skills remain directly comparable.

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
7. Optional: `pytest` (40 tests)

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

## Student 4: Semantic NLP (Sentence Transformers) and main evaluation (Tao Lou)

Folder: `step4_semantic/` (full detail in its own README). Builds on Student 3's `step3_baseline_nlp/`: the Baseline++
extractor, the 30-ad gold set and `evaluate.py`.

**What I did**

1. **Hybrid extractor:** keeps every Baseline++ match and adds skills an ad *implies* but never names, using Sentence
   Transformers (`all-mpnet-base-v2`). Ad text is cut into lines and clauses (company text skipped via Student 3's section
   segmenter); each skill's name and aliases are averaged into one centroid vector; a skill is added when a unit's cosine
   similarity passes a threshold and is close to that unit's best skill. Only concept skills can be added; tools and
   languages stay with exact matching.
2. **Main evaluation:** the same 30 gold ads and definitions as Step 3, scored strict (R+P gold) and lenient (R+P+I gold),
   plus implicit-skill recall and the precision of the added skills. Thresholds are chosen by leave-one-ad-out
   cross-validation, so every number is out-of-fold; 95% paired-bootstrap intervals (strict F1 also with Step 3's own
   `evaluate.bootstrap`).
3. **Model comparison and controls:** MiniLM, MPNet (pre-specified) and BGE-base, a character-hashing lexical control and
   a semantic-only control.
4. **Ablation and error analysis:** six design factors one at a time; errors by skill. The pooling choice was re-checked
   by selecting it inside each cross-validation fold.
5. **Blinded human audit:** 50 semantic additions and 50 exact hits from non-gold ads, plus all 22 semantic additions
   and 30 exact hits on unit PDFs, shuffled with the source hidden, labelled with `label_tool.py`.
6. **Student side:** the hybrid on the 20 real unit PDFs, Student 3's two test cases, and career fit exact vs hybrid.

**Run order** (`step4_semantic/`)

1. `pip install -r requirements.txt -r ../step3_baseline_nlp/requirements.txt`
2. Optional: `python -m pytest -q` (18 offline tests)
3. `python run_all.py verify` (reproduces Step 3: F1 0.872 and 0.943)
4. `python run_all.py compare ablate errors figures corpus curriculum report` (first run downloads the models)
5. `09_semantic_evaluation.ipynb` runs and shows the same steps

**Reusable API for other students**

```python
import sys; sys.path += ["../step3_baseline_nlp", "../step4_semantic"]
import experiments as ex, corpus_extract as ce
from data_access import load_context
hy = ce.build_hybrid(ex.Runner(load_context()), ce.load_final())   # tuned hybrid extractor
hy.extract_weighted(text)    # {skill: demand weight}, same as RequirementAwareExtractor
hy.explain(text)             # source (exact | semantic), similarity and evidence sentence per skill
```

**Figures:** `step4_semantic/figures/` (model comparison, ablation, threshold sweep).

**Main files:** `semantic_extractor.py`, `experiments.py`, `metrics.py`, `error_analysis.py`, `corpus_extract.py`,
`curriculum_semantic.py`, `label_tool.py`, `run_all.py`, `make_report.py`, `results/summary.md` (all tables),
`results/audit/` (blinded audit sheets and keys), `results/handoff/` (for Student 5), and `docs/` (report section,
handoff note, audit instructions).

**Key results**

* **Gold ads (30 ads, out-of-fold, MPNet hybrid vs Baseline++):** lenient F1 0.874 to 0.889, delta +0.015, 95% CI
  [0.003, 0.028]; implicit-skill recall 0.023 to 0.349 (about one in three unnamed skills recovered); lenient precision
  0.908 to 0.888. 64% of added skills are correct. Strict F1 falls from 0.943 to 0.904 because Baseline++ already has R+P
  recall 0.984, so the strict view can only count newly found implicit skills as errors.
* **Controls:** the lexical control adds nothing, so the gain is semantic, not fuzzy matching; MPNet alone (no exact
  matcher) finds the most implicit skills (0.605) but precision collapses to 0.585. Embeddings complement the dictionary;
  they do not replace it.
* **Ablation:** pooling matters most (centroid 0.889 vs max 0.873); centroid was chosen in 30 of 30 cross-validation folds.
* **Unseen ads (blinded human audit):** precision 0.64 for semantic additions [0.50, 0.76] vs 0.96 for exact hits
  [0.87, 0.99]. The semantic figure matches the gold-ad estimate (0.636), so the result generalises. Most errors are a
  related but different skill, for example "data infrastructure" read as Data Warehousing.
* **Unit PDFs:** UTS 36103 now gets Statistics; UNSW COMP9311 still misses SQL. Blinded audit on unit text: precision
  0.77 for semantic additions [0.57, 0.90] vs 0.97 for exact hits [0.83, 0.99]; Data Warehousing is the main error (0 of 3)
  in both audits. Hybrid career fit is higher for every career (AI Engineer 0.33 to 0.41); these are exploratory
  estimates that may be inflated by false-positive skill predictions.

**Limitations:** gold labels are Student 3's single AI annotator (n = 30, 43 implicit labels, wide intervals); the 30 ads
were used for tuning, comparison and ablation; centroid pooling was adopted after the first ablation (re-checked inside
cross-validation); one human annotator for the audit, with ambiguous items resolved with an AI assistant under a fixed
rule; skills outside the dictionary cannot be found; English-only models and US ads.

**Handoffs:** Student 5 can use `results/handoff/job_skills_hybrid_long.csv` (one row per ad and skill, with `source`,
strength, weight and evidence; filter `source == "exact"` for Step 3's output) or call `hy.extract_weighted`. Student 6
can call `curriculum_semantic.analyse_study_material_semantic` for an uploaded PDF and should show added skills as
"possibly covered" with their evidence; load the model once (about 0.4 GB).

---

## Student 5: Career profiles and matching (Tengxiao Nong)

## Run it (easiest way)

**Windows:** unzip the complete repository, open `step5_matching`, then double-click `run_matching.bat`.

**Mac:** unzip the complete repository, open `step5_matching`, then run `bash run_matching.command` in Terminal.

**Google Colab (no local setup):** go to [Google Colab](https://colab.research.google.com/), choose **File > Upload notebook**, upload `05_career_matching_colab.ipynb`, and run the cells in order. When prompted, upload the complete project ZIP so the notebook can access the Step 1, Step 3 and Step 4 inputs.

The standard run installs the small Step 5 dependencies, runs the career-matching pipeline, prints the five ranked careers in the terminal, and saves the detailed results in `outputs/`. Six automated tests are included to check the demand denominator, score bounds, monotonicity, evidence preservation, gap ranking and frontend payload.

This module converts the hybrid job-skill and curriculum-skill outputs into interpretable career recommendations. It builds demand-weighted profiles for five careers, compares them with the skills covered by course PDFs, calculates matching scores, identifies important gaps, recommends priority skills to learn, and provides a JSON-safe interface for the Streamlit app.

## Run order (local, Google Colab or frontend demo)

1. Run `matching.py` to build the five career profiles from 688 job advertisements and evaluate the 20-PDF curriculum case study.
2. The script calculates career rankings with the top 30 demanded skills per career and writes the ranking, explanations, sensitivity analysis and learning recommendations to `outputs/`.
3. Run `pytest -q test_matching.py` to execute the six automated tests.
4. Use `05_career_matching.ipynb` for a local Jupyter walkthrough or `05_career_matching_colab.ipynb` for Google Colab.
5. Run `frontend_demo.py` to upload a new PDF and recalculate the five career matches dynamically:

```bash
pip install -r frontend_requirements.txt
python -m streamlit run frontend_demo.py
```

For one or more selected curriculum units, repeat `--unit` with the exact unit IDs from Step 4:

```bash
python matching.py \
  --unit "UTS 36118 Applied NLP" \
  --unit "UTS 36120 Adv ML Application"
```

The matching score for career `c` uses its top 30 demanded skills:

`match(c) = sum(demand(c,s) * coverage(s)) / sum(demand(c,s))`

Job-side requirement weights are required = 1.0, duty = 0.75, preferred = 0.5 and unlabelled = 0.5. Study-material coverage weights are assessed = 1.0, taught = 0.75 and mentioned = 0.5. The result measures coverage of skills found in the sampled advertisements; it is not a probability of employment or proof of personal mastery.

## Main files

* `matching.py`: builds career demand profiles, calculates matching scores, ranks careers, preserves evidence, identifies skill gaps and generates learning recommendations.
* `frontend_api.py`: dynamic interface for Member 6; accepts a newly uploaded PDF or a Step 3/4 `StudyProfile` and returns five JSON-safe career records.
* `frontend_demo.py`: minimal Streamlit demonstration for uploading one new course PDF and displaying career, match percentage, matched skills and priority learning skills.
* `05_career_matching.ipynb`: local notebook walkthrough of the Step 5 method and outputs.
* `05_career_matching_colab.ipynb`: Google Colab version that accepts the complete repository ZIP.
* `test_matching.py`: six automated tests for the profile, scoring, explanation, recommendation and frontend logic.
* `requirements.txt`: lightweight dependencies for the standard 20-PDF matching pipeline.
* `frontend_requirements.txt`: additional dependencies for live PDF extraction and the Streamlit demonstration.
* `run_matching.bat`, `run_matching.command`: one-click Windows and Mac launchers.
* `outputs/career_profiles.csv`: demand weight and skill rank within each career.
* `outputs/demo_career_ranking.csv`: five ranked careers, scores, matched skills and priority gaps.
* `outputs/demo_skill_explanations.csv`: per-skill contribution, remaining gain and supporting course evidence.
* `outputs/demo_learning_recommendations.csv`: five priority learning actions for every career.
* `outputs/demo_sensitivity.csv`: rankings under top-20, top-30 and top-40 skill cut-offs.
* `outputs/demo_app_payload.json`: nested output for the fixed 20-PDF demonstration.

For a newly uploaded PDF, the frontend should call the dynamic interface instead of reading the fixed demonstration JSON:

```python
from step5_matching.frontend_api import match_uploaded_pdf

results = match_uploaded_pdf(uploaded_pdf)
```

Pass `use_semantic=True` only when the Step 4 Sentence-Transformer model is available. The default exact-matching path runs without downloading the semantic model.

## Headline results

* On the 20 real curriculum PDFs, the top-30 configuration ranks Data Scientist first at 68.5%, followed by Data Engineer at 62.9%, Data Analyst at 61.7%, ML Engineer at 61.0% and AI Engineer at 40.8%.
* The sensitivity analysis shows that ML Engineer ranks first at the top-20 cut-off (69.8%), while Data Scientist ranks first at top-30 (68.5%) and top-40 (67.1%). This indicates that the ordering is partly sensitive to the number of demanded skills included.
* The output explains each recommendation through matched skills, demand-weighted gaps, course units, PDF pages and evidence text.
* A live PDF upload returns the same five-career structure and can be consumed directly by the Streamlit frontend without reusing the fixed 20-PDF result.

## Limitations

* The career profiles are based on 688 sampled U.S. advertisements and only five career labels; Data Analyst has 27 advertisements, so its profile is less stable than the larger categories.
* The top-30 cut-off is an interpretable modelling choice rather than a universal threshold; the included top-20 and top-40 sensitivity results should be reported with the main ranking.
* Semantic additions are probabilistic. Step 4 reports precision of 0.64 on unseen job advertisements and 0.77 on unit PDFs, so semantic evidence should be presented as possible rather than certain.
* A skill mentioned, taught or assessed in a PDF indicates curriculum coverage, not that an individual student has mastered the skill.
* A single uploaded course normally receives lower scores than the combined 20-course curriculum because it covers a smaller share of a career's top skills.

## Student 6: Streamlit app and user testing (Chongyan Tang)

**What I did**

1. Integrated the existing NLP and career-matching pipeline into a Streamlit application.
2. Added PDF upload, exact-baseline and hybrid-semantic modes, configurable Top-N career results, ranked match visualisation, matched skills, priority gaps, recommendation explanations, PDF evidence, learning suggestions and JSON export.
3. Added responsible-use wording so skill detections are presented as study-material coverage rather than personal mastery, and career scores as skill alignment rather than job-success probabilities.
4. Conducted formative user testing with three classmates.

**Key results**

- Exact baseline on `sample_unit_outline.pdf`: Data Scientist 41.9%, Data Analyst 40.1%, ML Engineer 39.0%, Data Engineer 23.1%, AI Engineer 21.8%.
- Hybrid semantic on the same PDF: Data Scientist 41.9%, ML Engineer 41.7%, Data Analyst 40.1%, Data Engineer 23.1%, AI Engineer 21.8%.
- User testing (n=3): ease 3.33/5; result clarity 5.00/5; skills/gaps usefulness 4.33/5; explanation clarity 5.00/5; overall usefulness 4.33/5. Overall mean = 4.40/5.

**Files and how to run**

```bash
pip install -r step6_app/requirements.txt
streamlit run step6_app/app.py
```

Main files: `step6_app/app.py`, `step6_app/README.md`, `step6_app/user_testing/user_testing_results.csv`.

**Limitations**

Hybrid semantic matching is slower than the exact baseline and the distinction between modes may not be obvious to all users. The current recommendations are skill-overlap results and do not model work experience, education or other hiring factors. User testing was formative and small (n=3).


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
README.md                  this page: the whole team, one section per student
CONTRIBUTING.md            how we work (read this first, 2 minutes)
requirements.txt           shared libraries (extra ones go in your own folder)
.gitignore
.github/                   pull request checklist
data/                      shared inputs and notes (see its README)
step1_data/                Student 1, Zheke Yi
step2_dictionary/          Student 2, Wancheng Liu
step3_baseline_nlp/        Student 3, Jirawan Pedersen (notebooks 03 to 08, code, 20 unit PDFs, figures)
step4_semantic/            Student 4, Tao Lou
step5_matching/            Student 5, Tengxiao Nong
step6_app/                 Student 6, Chongyan Tang
report/                    one Markdown file per student, plus references
```

Each step folder has a README template (what I did, key results, files, inputs and outputs, limitations). Fill it in, and copy the key lines into your section above.

## Team conventions

* **Work only in your own folder** and your file in `report/`. Shared files (this README, `requirements.txt`, `data/`) need a message to the group or a pull request. Full rules and the Terminal-free way to upload are in `CONTRIBUTING.md`.
* Run `git pull` before you push.
* Commit notebooks **with outputs**. Do not commit `.venv/`, `__pycache__/`, big files, passwords or tokens.
* Dictionary changes: Student 2 merges proposals (for example `extra_aliases_reviewed.csv`) and tells Students 3 to 5.
* Every notebook starts with a setup cell that works for anyone, with no personal paths (copy the one in the Step 3 notebooks).

## Checklist before the report is due (14 Oct)

- [ ] Each student fills in their section above, their step folder README, and their file in `report/` (see `report/README.md`)
- [ ] Students 1 and 2: dataset and dictionary notes (collection date, categories, terms of use); check `company_sector_map.csv`
- [ ] Student 4: run the semantic model on the same 30 gold ads and compare with Step 3
- [ ] Students 5 and 6: plug in the alignment output and test the app with a few users
- [ ] Everyone: references checked, and every notebook runs from a clean start
