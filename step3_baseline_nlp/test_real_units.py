from extraction import analyse_text
from real_units import UNITS, SOURCES

def test_sources_match_units():
    assert set(UNITS) == set(SOURCES) and len(UNITS) == 7

def test_known_skills_found():
    p = {u: set(analyse_text(t).skills) for u, t in UNITS.items()}
    assert "PyTorch" in p["UNSW COMP9444 Deep Learning"]
    assert "R" in p["USYD DATA5207 Data Analysis"]
    assert {"Keras", "TensorFlow", "scikit-learn"} <= p["USYD COMP5318 ML and Data Mining"]
    assert "Natural Language Processing" in p["UTS 36118 Applied NLP"]
