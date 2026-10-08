import pandas as pd

from matching import build_career_profiles, learning_recommendations, match_careers, recommend_for_frontend


def _profiles():
    jobs = pd.DataFrame({"job_id": ["a", "b", "c"], "career_category": ["Data", "Data", "ML"]})
    hits = pd.DataFrame({
        "job_id": ["a", "b", "c"], "career_category": ["Data", "Data", "ML"],
        "canonical_skill": ["Python", "SQL", "Python"], "skill_category": ["Programming"] * 3,
        "source": ["exact", "exact", "semantic"], "weight": [1.0, 0.5, 1.0],
    })
    return build_career_profiles(hits, jobs)


def test_profile_uses_all_ads_as_denominator():
    row = _profiles().query("career_category == 'Data' and canonical_skill == 'Python'").iloc[0]
    assert row.demand_weight == 0.5


def test_more_relevant_coverage_cannot_reduce_score():
    profiles = _profiles()
    before, _ = match_careers({"Python": 0.5}, profiles, top_n=10)
    after, _ = match_careers({"Python": 1.0, "SQL": 1.0}, profiles, top_n=10)
    assert after.set_index("career").loc["Data", "match_score"] > before.set_index("career").loc["Data", "match_score"]


def test_full_and_empty_coverage_have_expected_bounds():
    profiles = _profiles()
    empty, _ = match_careers({}, profiles, top_n=10)
    full, _ = match_careers({"Python": 1.0, "SQL": 1.0}, profiles, top_n=10)
    assert empty.match_score.eq(0).all()
    assert full.match_score.eq(1).all()


def test_explanation_preserves_study_evidence():
    study = pd.DataFrame([{"skill": "Python", "coverage": 0.75, "level": "taught",
                           "source": "semantic", "units": ["Unit A"], "pages": [2],
                           "evidence": "build predictive models", "semantic_score": 0.82}])
    _, details = match_careers(study, _profiles(), top_n=10)
    row = details.query("career == 'Data' and skill == 'Python'").iloc[0]
    assert row.evidence_source == "semantic"
    assert row.pages == [2]


def test_learning_plan_prioritises_largest_gap():
    _, details = match_careers({"Python": 1.0}, _profiles(), top_n=10)
    plan = learning_recommendations(details, "Data", k=1)
    assert plan.iloc[0].skill == "SQL"
    assert plan.iloc[0].priority == 1


def test_frontend_payload_is_dynamic_and_limited_to_top_k():
    profiles = _profiles()
    python_result = recommend_for_frontend({"Python": 1.0}, profiles, top_k=1)
    sql_result = recommend_for_frontend({"SQL": 1.0}, profiles, top_k=1)
    assert len(python_result) == len(sql_result) == 1
    assert python_result[0]["career"] != sql_result[0]["career"]
    assert "learning_recommendations" in python_result[0]
