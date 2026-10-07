# Human audit instructions (one annotator, blinded)

Status: both sheets are labelled (100 job-ad items, 52 unit items); results are in `results/summary.md`.

The 30 gold ads were labelled by one AI annotator and are also the tuning set. These two sheets give an independent,
**human** estimate of precision on text the method was NOT tuned on. They are designed so that one person (the method
developer) can label them without favouring the semantic method: every sheet mixes semantic additions with exact-match
hits, shuffled, and hides which method produced each item.

## Order
1. Run the pipeline first, so the sheets match the final configuration: `python run_all.py compare corpus curriculum`.
   (A sheet that already contains labels is never overwritten; delete it yourself if you really want a new one.)
2. Label with the terminal tool (one item at a time, saved after every answer, resumable):
   ```bash
   python label_tool.py                                          # job ads:   results/audit/job_audit_sheet.csv
   python label_tool.py results/audit/curriculum_label_sheet.csv # unit PDFs: results/audit/curriculum_label_sheet.csv
   ```
   Answer `1`, `0`, `a` (show the whole ad), `s` (skip) or `q` (save and quit). You can also fill the `human_label`
   column in Excel instead; the tool and the scorer read the same file.
3. Only after BOTH sheets are finished, score them and rebuild the report:
   ```bash
   python -c "import corpus_extract as ce; print(ce.evaluate_job_audit())"
   python -c "import curriculum_semantic as cs; print(cs.evaluate_unit_labels())"
   python make_report.py        # adds both audit tables to results/summary.md and the README section
   ```

## Sheet 1: `results/audit/job_audit_sheet.csv` (unseen job ads)
50 random semantic additions + 50 random exact hits from the 658 non-gold ads, shuffled. The `evidence` column is the
full ad line the item came from; `section` is the part of the ad (required / duty / preferred).

`human_label` **1** = the ad really demands or uses this skill (even if it is worded differently), **0** = it does not
(different meaning, only loosely related, company text). Judge the skill, not the wording: "measure how well models
generalise" demands Model Evaluation even though those words never appear.

## Sheet 2: `results/audit/curriculum_label_sheet.csv` (20 unit PDFs)
All semantic additions + 30 random exact hits. `human_label` **1** = this unit really teaches, assesses or covers the
skill as course content, **0** = no (for example a prerequisite, a tool name in a policy table, or a different meaning).

## Rules that keep the audit honest
* Do **not** open `job_audit_key.csv` or `curriculum_label_key.csv` until labelling is finished. The tool never reads them.
* Do not try to guess which method found an item; label only what the ad / unit says.
* Label every item (skipping hard ones biases precision upward). If unsure after reading the whole ad (`a`), decide by
  whether a recruiter would expect a candidate to have that skill.
* Do not change labels after seeing the scores.

Ambiguous items were resolved with an AI assistant applying the written rule above; this is stated in the report.
