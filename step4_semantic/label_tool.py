"""Label a blinded audit sheet one item at a time in the terminal (single annotator, resumable).

    python label_tool.py                                        # job-ad sheet: results/audit/job_audit_sheet.csv
    python label_tool.py results/audit/curriculum_label_sheet.csv   # unit-PDF sheet

For each item you see the skill and the evidence line (plus the job title / unit), and answer:
    1  the ad demands this skill / the unit really teaches or assesses it
    0  it does not (wrong meaning, only loosely related, company text, prerequisite ...)
    a  show the whole ad (job sheet) for more context        s  skip for now        q  save and quit
The file is saved after every answer, so you can stop and continue later. The tool never opens the *_key.csv file,
so you cannot see which method (exact or semantic) produced an item. Do not open the key until you have finished.
"""
from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pandas as pd

import config

LABELS = {"1", "0"}


def _done(v) -> bool:
    return str(v) in {"0", "1", "0.0", "1.0"}


def _show_ad(job_id: str):
    try:
        jobs = pd.read_csv(config.find_step3() / "job_cleaned.csv", encoding="utf-8-sig")
        text = jobs.loc[jobs.job_id == job_id, "job_description"].iloc[0]
        print("\n" + "-" * 100 + "\n" + str(text)[:6000] + "\n" + "-" * 100)
    except Exception as e:                                    # context is optional
        print(f"  (could not load the ad: {type(e).__name__})")


def main(path: str | None = None):
    p = Path(path) if path else config.AUDIT / "job_audit_sheet.csv"
    if not p.exists():
        raise SystemExit(f"{p} not found - run `python run_all.py corpus` (or `curriculum`) first")
    if "key" in p.name:
        raise SystemExit("that is the hidden key file - open the *_sheet.csv file instead")
    df = pd.read_csv(p, dtype={"human_label": "object", "annotator": "object"})
    try:
        name = input("Your name (written to the annotator column): ").strip() or "annotator"
    except (EOFError, KeyboardInterrupt):
        return
    todo = [i for i in df.index if not _done(df.at[i, "human_label"])]
    print(f"{len(df) - len(todo)} of {len(df)} already labelled. {len(todo)} to go. Answer 1 / 0 / a / s / q.\n")
    for n, i in enumerate(todo, 1):
        r = df.loc[i]
        where = r.get("job_title", r.get("unit_id", ""))
        print(f"[{n}/{len(todo)}] {r['item_id']}  |  {where}  |  section/level: {r.get('section', r.get('level', ''))}")
        print(f"  SKILL:    {r['skill']}")
        print("  EVIDENCE: " + textwrap.fill(str(r["evidence"]), 100, subsequent_indent=" " * 12))
        while True:
            try:
                ans = input("  label > ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                ans = "q"
            if ans == "a" and "job_id" in df:
                _show_ad(r["job_id"])
                continue
            if ans in LABELS | {"s", "q"}:
                break
            print("  type 1, 0, a, s or q")
        if ans == "q":
            break
        if ans in LABELS:
            df.at[i, "human_label"], df.at[i, "annotator"] = ans, name
            df.to_csv(p, index=False)
        print()
    df.to_csv(p, index=False)
    left = int((~df.human_label.map(_done)).sum())
    print(f"saved {p}  ({len(df) - left} labelled, {left} left)")
    if left == 0:
        print("All done. Now score it:  python -c \"import corpus_extract as ce; print(ce.evaluate_job_audit())\""
              if "job" in p.name else
              "All done. Now score it:  python -c \"import curriculum_semantic as cs; print(cs.evaluate_unit_labels())\"")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
