# Member 3: Baseline NLP, alignment layer and sector lens (UTS 36118 AT2 Part B, Group 6)

## Run it (easiest way)

**Mac:** unzip, open the folder, right-click `run.command`, choose Open (or in Terminal: `bash run.command`).
**Windows:** unzip, double-click `run.bat`.
**Google Colab (no install):** go to colab.research.google.com, File > Upload notebook and choose `08_real_curriculum_case_study.ipynb`, then drag `Member3_Baseline_NLP.zip` into the left Files panel (folder icon). Run the first cell, then Runtime > Run all. If you skip the drag, the first cell downloads the zip from the shared Drive folder (https://drive.google.com/drive/folders/1itmHAXH4dyXbm1icJ1ip7RrRvXkMj9UK) or asks you to choose it.

The first run installs what it needs (a minute or two), checks the code (40 tests pass), then opens the main notebook. In the notebook use Kernel > Restart Kernel and Run All Cells. Nothing needs editing.

Skill extraction with a spaCy PhraseMatcher, an improved requirement-aware version, a PDF study-material pipeline, an alignment layer (coverage strength, uncertainty ranges, curriculum heatmap) and a sector lens (does skill demand depend on the employer's sector?).

## Run order (Google Colab or local Jupyter)
1. Put this whole folder in Google Drive (for example `My Drive/ANLP AT2B`), keeping the files flat, or run locally with `pip install -r requirements.txt`.
2. `03_skill_extraction.ipynb`: baseline extraction on 688 job ads.
3. `04_innovation_experiments.ipynb`: held-out evaluation, ablation, error analysis.
4. `05_study_material_pipeline.ipynb`: PDF study material to skills, with coverage level (assessed, taught, mentioned).
5. `06_curriculum_alignment.ipynb`: career fit with bootstrap ranges and the curriculum heatmap (synthetic demo units; the real units are in 08).
6. `07_sector_lens.ipynb`: sector profiles, permutation test, universal core vs sector-specific skills, curriculum fit by sector.
7. `08_real_curriculum_case_study.ipynb`: the reframed question on 20 real unit PDFs from UTS, USYD and UNSW (career fit, gaps, fit by sector, sensitivity checks).
Each notebook starts with a setup cell that mounts Drive and lists any missing file. If your Drive path differs, change the `FOLDER` line in that cell.

**Figures:** every chart is shown inside its notebook and also saved as a PNG in `figures/` (for the report and slides): `fig0` demand and extraction, `fig1` unit-by-skill heatmap, `fig2` career fit, `fig3` top gaps, `fig4` by university, `fig5` by sector, `fig6` effect of unit selection.

## Main files
* `skill_extractor.py`, `skill_extractor_v2.py`: baseline and requirement-aware extractors.
* `extraction.py`: PDF pipeline (PyMuPDF) with coverage levels, same matcher as the job side.
* `alignment.py`: demand model, career fit with bootstrap ranges, gap ranking.
* `curriculum.py`, `data/curriculum_manifest.csv`, `data/curriculum_pdfs/`: the 20 real unit PDFs, with source URLs and the manual-review list of removed false matches.
* `real_units.py`: condensed page text of the first 7 units (sensitivity check only).
* `sectors.py`, `company_sector_map.csv`: company-to-sector labels (manual, please review).
* `sector_analysis.py`: company-clustered bootstrap and permutation tests by sector.
* `docs/references_and_data_sources.md`: dataset description, unit-page sources (with PDF instructions) and APA references
* `evaluate.py`, `gold_annotations.py`, `gold_split.json`: 30-ad evaluation set and metrics (for Member 4).
* `extra_aliases_reviewed.csv`: 45 proposed dictionary aliases (for Member 2 to review).
* `job_cleaned.csv`, `skills_dictionary.csv`, `normalisation.py`: inputs from Steps 1 and 2.
* `test_*.py`: 40 automated tests (`pytest`).
* `docs/`: report section, contribution statement, handoff note for Member 4.

## Headline results
* Extraction (30 held-out ads): F1 0.872 to 0.943, +0.071, 95% CI 0.039 to 0.104.
* Sector lens (688 ads, 106 companies): sector profiles differ (p = 0.004) but only borderline after removing career mix (p = 0.06).
Limitations: single annotator, n = 30, US ads only, manual sector labels, PDF and curriculum demos use synthetic outlines.
