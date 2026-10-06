from skill_extractor_v2 import RequirementAwareExtractor, REQUIRED, PREFERRED, COMPANY
X = RequirementAwareExtractor(extra_aliases_path="extra_aliases_reviewed.csv", expand_morphology=True)

def test_required_vs_preferred():
    s = X.skill_strengths("Requirements:\n- 3 years of Python\nNice to have:\n- Kafka")
    assert s["Python"] == REQUIRED and s["Kafka"] == PREFERRED

def test_company_boilerplate_not_demand():
    t = "About us:\nFounded by the creators of Apache Spark.\nRequirements:\n- SQL"
    assert X.extract_skills(t) == ["SQL"] and "Apache Spark" in X.extract_skills(t, mode="all")

def test_ambiguous_verb_guard():
    assert "Apache Spark" not in X.extract_skills("Requirements:\n- You will spark curiosity in teams")
    assert "Apache Spark" in X.extract_skills("Requirements:\n- Experience with Python and Spark")

def test_url_removed():
    assert "GitHub" not in X.extract_skills("Requirements:\n- Apply at https://github.com/acme/jobs")

def test_morphology_and_weights():
    assert "A/B Testing" in X.extract_skills("Requirements:\n- Design A/B tests")
    assert X.extract_weighted("Requirements:\n- Python\nPreferred:\n- Kafka") == {"Python": 1.0, "Kafka": 0.5}
