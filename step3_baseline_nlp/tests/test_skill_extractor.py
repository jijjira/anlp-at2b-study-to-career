"""Test cases for the PhraseMatcher baseline. Run: python -m pytest -q  (or python test_skill_extractor.py)"""
from skill_extractor import extract_skills, get_extractor

CASES = [
    # (text, expected canonical skills in order of first appearance)
    ("Python, SQL, machine learning and AWS", ["Python", "SQL", "Machine Learning", "AWS"]),
    ("We build LLMs and deploy ML models on Amazon Web Services",
     ["Large Language Models", "Machine Learning", "AWS"]),                     # alias -> canonical
    ("PowerBI and Power BI dashboards", ["Power BI", "Dashboarding"]),          # spelling variants dedupe
    ("Strong R skills; R/Python preferred. Knowledge of R.", ["R", "Python"]),  # case-sensitive R
    ("AI R&D team, recommendation systems, research", ["Recommendation Systems"]),  # R&D is not R
    ("Experience in C++,Go or C#.", ["C++", "C#"]),                             # punctuation glued to tokens
    ("Node.js/TypeScript services", ["TypeScript"]),
    ("CI/CD, A/B testing and k8s", ["CI/CD", "A/B Testing", "Kubernetes"]),
    ("fine‑tuning and time‑series forecasting", ["Fine-tuning", "Time Series", "Forecasting"]),
    ("Built on Apache Spark™ and Databricks", ["Apache Spark", "Databricks"]),
    ("RETRIEVAL-AUGMENTED GENERATION with PYTORCH", ["RAG", "PyTorch"]),        # case-insensitive
    ("Extract, transform, load (ETL) pipelines", ["ETL"]),
    ("We love grammar and programming of rare things", []),                      # no substring false positives
    ("", []),
    (None, []),
]


def test_cases():
    for text, expected in CASES:
        assert extract_skills(text) == expected, (text, extract_skills(text), expected)


def test_dedupe_and_evidence():
    ev = get_extractor().extract_with_evidence("ML models, machine learning, and ml model")
    assert {m.canonical for m in ev} == {"Machine Learning"} and len(ev) == 3
    assert extract_skills("ML models, machine learning, and ml model") == ["Machine Learning"]


if __name__ == "__main__":
    test_cases(); test_dedupe_and_evidence(); print("all tests passed")
