"""Load the real unit PDFs listed in data/curriculum_manifest.csv and extract skills.

`group` is "core" for the first seven units collected (all ML-focused) and "added" for the 13 units added later to cover
databases, statistics, visualisation, engineering and NLP. `excluded_skills` is a short human review of false matches, each
with a reason (for example server clustering is not machine-learning clustering).
"""
from pathlib import Path
import pandas as pd
from extraction import analyse_study_material

HERE = Path(__file__).resolve().parent


def load_curriculum(folder=None):
    """-> (profiles dict unit_id -> StudyProfile with exclusions applied, manifest DataFrame of the units found)."""
    folder = Path(folder) if folder else HERE
    man = pd.read_csv(folder / "data" / "curriculum_manifest.csv").fillna("")
    profs, found = {}, []
    for _, r in man.iterrows():
        path = folder / "data" / "curriculum_pdfs" / r.file
        if not path.exists():
            continue
        p = analyse_study_material(str(path))
        for s in [x.strip() for x in r.excluded_skills.split(";") if x.strip()]:
            p.skills.pop(s, None)
        profs[r.unit_id] = p
        found.append(r)
    return profs, pd.DataFrame(found)
