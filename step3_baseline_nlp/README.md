# Step 3: Baseline NLP, PDF reader, curriculum alignment and sector lens

## Task
Extract skills with a spaCy PhraseMatcher over the Step 2 dictionary, then improve it into Baseline++: each advertisement is read by section, skills are weighted by how strongly the advertisement asks for them (required 1.00, duty 0.75, preferred 0.50, company text 0), ambiguous words are guarded, and 45 human-reviewed aliases are added. A PyMuPDF reader turns unit PDFs into skills with a coverage level (assessed, taught, mentioned) and page evidence. An alignment layer scores each career against 20 real unit documents with bootstrap intervals, and a sector lens tests whether demand depends on the employer's sector. A 30-advertisement gold set evaluates extraction.

## Work in this folder
| Path | Purpose |
|---|---|
| `skill_extractor.py`, `skill_extractor_v2.py` | Baseline and Baseline++ extractors |
| `extraction.py`, `curriculum.py`, `real_units.py` | PDF reader and unit-document handling |
| `alignment.py`, `analysis.py` | Career fit, gaps and uncertainty |
| `sectors.py`, `sector_analysis.py`, `company_sector_map.csv` | Sector lens |
| `evaluate.py`, `gold_annotations.py`, `gold_split.json` | Gold set and metrics |
| `make_sheet.py`, `human_annotation_sheet.xlsx`, `human_annotation_sheet_FILLED.xlsx`, `pass2_filled.xlsx`, `human_merged.xlsx`, `human_annotation_key_PRIVATE.csv` | Second-annotator check on 10 of the 30 gold ads: blank sheet, human pass 1 and pass 2, merged human labels and the answer key |
| `ai_second_annotator_FILLED.xlsx` | A second AI pass (Claude) on the same blank sheet; not a human annotation (see `docs/ai_annotator_provenance.md`) |
| `annotator_agreement.py`, `human_agreement.py` | Three-rater agreement, extractor-vs-rater scores and Figure 7; `human_agreement.py` is the original gold-vs-human kappa script |
| `annotator_agreement_results.csv`, `annotator_confusions.csv`, `extractor_vs_annotators.csv`, `human_agreement_results.csv`, `figures/fig7_annotator_agreement.png` | Outputs of those scripts |
| `docs/annotation_agreement_report.md` | Full write-up and interpretation |
| `discover.py`, `discovery_candidates_raw.csv`, `extra_aliases_reviewed.csv` | Alias discovery and the reviewed aliases |
| `03_` to `08_*.ipynb` | Extraction, experiments, PDF pipeline, alignment, sector lens, 20-unit case study |
| `data/` | The 20 unit PDFs (`curriculum_pdfs/`) and their manifest |
| `figures/` | Charts used in the report |
| `test_*.py` | 40 automated tests |
| `docs/references_and_data_sources.md` | Data description, unit-page sources and references |
| `job_cleaned.csv`, `skills_dictionary.csv`, `normalisation.py` | Copies of the Step 1 and 2 inputs so this folder runs on its own |
| `job_skills_extracted.csv`, `job_skills_long.csv` | Extraction output for the 688 advertisements |
| `run.command` (Mac), `run.bat` (Windows) | One-click install, tests and notebook launch |

## How to run
```
pip install -r requirements.txt
python -m pytest -q          # 40 tests
jupyter lab                  # run notebooks 03 to 08 with Restart & Run All
```
The notebooks also run in Google Colab: upload one, run the first cell and follow the prompt.

## Key results
* Extraction on the 30-advertisement gold set: strict F1 0.872 (plain matcher) to 0.943 (Baseline++), +0.071, 95% CI [0.039, 0.104]; most of the gain comes from the reviewed aliases.
* Curriculum fit with exact matching: Data Scientist 65.4%, Data Engineer 59.3%, Data Analyst 58.1%, ML Engineer 58.2%, AI Engineer 32.6%.
* Sector profiles differ (permutation p = 0.004) but only borderline after adjusting for career mix (p = 0.06).

## Limitations
The gold set (30 advertisements) was labelled by one AI annotator. On 10 of them a single human annotator and a second AI pass also labelled the same candidates: the human agrees only fairly with the gold (kappa 0.33 for named-and-demanded skills, 0.25 over four classes), while the second AI pass agrees closely (0.85) but is not independent. The implicit-skill tier is unreliable (kappa at most 0.12), so conclusions rest on named skills. See `docs/annotation_agreement_report.md`. Unit handbook pages are shorter than full outlines, the extractor was validated on advertisements and not on unit text, and exact matching misses skills taught without being named.
