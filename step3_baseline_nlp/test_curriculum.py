from curriculum import load_curriculum

def test_manifest_loads_all_units_and_exclusions_apply():
    profs, man = load_curriculum()
    assert len(profs) == 20 and set(man.group) == {"core", "added"}
    assert "Clustering" not in profs["USYD COMP5348 Enterprise Software Architecture"].skills
    assert "SQL" in profs["UTS 94693 Big Data Engineering"].skills
    assert "Large Language Models" in profs["UNSW COMP6713 NLP"].skills
