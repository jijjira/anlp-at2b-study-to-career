import numpy as np
from alignment import DemandModel, curriculum_coverage
from extraction import analyse_text

# tiny synthetic market: 2 careers, 10 ads each
S = ([{"Python": "required", "SQL": "required", "Docker": "preferred"}] * 6 + [{"Python": "required"}] * 4 +
     [{"Tableau": "required", "SQL": "required"}] * 10)
C = ["DS"] * 10 + ["DA"] * 10
M = DemandModel(S, C)

def test_demand_weights():
    d = dict(zip(M.skills, M.demand("DS")))
    assert d["Python"] == 1.0 and abs(d["Docker"] - 0.6 * 0.5) < 1e-9 and d["Tableau"] == 0.0

def test_fit_ranges_and_order():
    f = M.fit({"Python", "SQL"}, topn=3, n_boot=200).set_index("career")
    assert f.loc["DS", "fit"] > f.loc["DA", "fit"]
    assert (f.ci_low <= f.ci_high).all()
    assert ((f[["fit", "ci_low", "ci_high"]] >= 0) & (f[["fit", "ci_low", "ci_high"]] <= 1)).all().all()

def test_stronger_coverage_gives_higher_fit():
    weak = M.fit({"Python": 0.5, "SQL": 0.5}, topn=3, n_boot=50).set_index("career").loc["DS", "fit"]
    strong = M.fit({"Python": 1.0, "SQL": 1.0}, topn=3, n_boot=50).set_index("career").loc["DS", "fit"]
    assert strong > weak

def test_bootstrap_is_reproducible():
    a = M.fit({"Python"}, topn=3, n_boot=100); b = M.fit({"Python"}, topn=3, n_boot=100)
    assert a.equals(b)

def test_gaps_exclude_covered_skills():
    g = M.gaps({"Python": 1.0}, "DS", k=3)
    assert g.iloc[0].skill != "Python" and (g.marginal_gain >= 0).all()

def test_curriculum_takes_strongest_level():
    a = analyse_text("Week 1: Basics\nWe use Docker in the lab."); b = analyse_text("Assessment\nA Docker project.")
    cur = curriculum_coverage({"Unit A": a, "Unit B": b})
    assert cur["Docker"]["best_level"] == "assessed" and set(cur["Docker"]["units"]) == {"Unit A", "Unit B"}
