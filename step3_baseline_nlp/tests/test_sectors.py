import numpy as np, pandas as pd, pytest
from sectors import SECTOR_OF, assign_sectors, sector_summary, MAIN_MIN_ADS
from sector_analysis import SectorModel

def test_every_company_has_exactly_one_sector():
    j = pd.read_csv("job_cleaned.csv", encoding="utf-8-sig")
    assert assign_sectors(j).notna().all()
    assert set(j.company) <= set(SECTOR_OF)

def test_unknown_company_raises():
    with pytest.raises(ValueError):
        assign_sectors(pd.DataFrame({"company": ["Nonexistent Corp"]}))

def test_summary_flags_main_sectors():
    j = pd.read_csv("job_cleaned.csv", encoding="utf-8-sig")
    s = sector_summary(j)
    assert s.ads.sum() == len(j) and s[s.main_sector].ads.min() >= MAIN_MIN_ADS

# synthetic market: sector X wants Python, sector Y wants Tableau; companies of 5 ads each
def _toy(n_comp=8):
    S, comp, sec = [], [], {}
    for k in range(n_comp):
        name = f"c{k}"; sec[name] = "X" if k < n_comp // 2 else "Y"
        for _ in range(5):
            S.append({"Python": "required", "SQL": "required"} if sec[name] == "X" else {"Tableau": "required", "SQL": "required"})
            comp.append(name)
    return S, comp, sec

def test_distinctive_finds_the_sector_specific_skill():
    S, comp, sec = _toy()
    m = SectorModel(S, comp, sec)
    d = m.distinctive("X", n_boot=200, min_ads_with_skill=1, k=3)
    assert d.skill.iloc[0] == "Python" and d.difference.iloc[0] == 1.0
    assert "SQL" not in set(d[d.difference > 0.5].skill)          # shared skill is not distinctive

def test_permutation_detects_real_sector_effect():
    S, comp, sec = _toy()
    r = SectorModel(S, comp, sec).permutation_test(["X", "Y"], n_perm=300)
    assert r["p_value"] < 0.05

def test_permutation_no_effect_when_sectors_identical():
    S = [{"Python": "required"}] * 40; comp = [f"c{i//5}" for i in range(40)]
    sec = {f"c{k}": "X" if k % 2 else "Y" for k in range(8)}
    r = SectorModel(S, comp, sec).permutation_test(["X", "Y"], n_perm=200)
    assert r["p_value"] > 0.3

def test_fit_is_ordered_and_reproducible():
    S, comp, sec = _toy()
    m = SectorModel(S, comp, sec)
    a = m.fit({"Python", "SQL"}, topn=2, n_boot=100); b = m.fit({"Python", "SQL"}, topn=2, n_boot=100)
    assert a.equals(b) and a.sector.iloc[0] == "X" and (a.ci_low <= a.ci_high).all()
