import os, subprocess, sys
import pytest
from extraction import (analyse_study_material, analyse_text, clean_pages, read_pdf_pages, extract_skills)

PDF = "sample_unit_outline.pdf"
if not os.path.exists(PDF):
    subprocess.run([sys.executable, "make_sample_pdf.py"], check=True)

@pytest.fixture(scope="module")
def prof():
    return analyse_study_material(PDF)

def test_reads_all_pages():
    assert len(read_pdf_pages(PDF)) == 5

def test_core_skills_found_with_pages(prof):
    for s in ["Python", "SQL", "Pandas", "PyTorch", "Docker", "AWS", "Tableau", "Natural Language Processing"]:
        assert s in prof.skills, s
    assert prof.skills["Python"]["pages"] == [1, 2] and prof.skills["Docker"]["pages"] == [5]

def test_header_footer_and_page_numbers_removed():
    cleaned = clean_pages(read_pdf_pages(PDF))
    assert all("Unit Outline" not in p and "Page " not in p for p in cleaned)

def test_hyphenation_and_soft_wraps_repaired():
    raw = ["We teach machine\nlearning and deep-\nlearning methods.", "x", "y"]
    out = clean_pages(raw)[0]
    assert "machine learning" in out
    assert {"Machine Learning"} <= set(analyse_text(out).skills)

def test_ambiguous_verb_not_counted_but_capitalised_spark_is(prof):
    assert prof.skills["Apache Spark"]["mentions"] == 1       # "Spark ecosystem" yes, "spark discussion" no

def test_r_and_d_is_not_the_language_r():
    assert "R" not in analyse_text("The R&D budget is large. Python is used.").skills
    assert "R" in analyse_text("We use R for statistics and Python.").skills

def test_bytes_and_fileobj_inputs():
    data = open(PDF, "rb").read()
    import io
    assert set(analyse_study_material(data).skills) == set(analyse_study_material(io.BytesIO(data)).skills)

def test_same_logic_as_job_side():
    t = "Experience with Python and SQL on AWS."
    assert set(analyse_text(t).skills) == set(extract_skills(t))

def test_empty_pdf_text_warns():
    assert analyse_text("").warnings

def test_coverage_levels(prof):
    assert prof.skills["Docker"]["level"] == "assessed"          # under the Assessment heading
    assert prof.skills["Python"]["level"] == "assessed"          # also in a learning outcome (strongest evidence wins)
    assert prof.skills["SQL"]["level"] == "taught"               # weekly schedule only
    assert prof.skills["Git"]["level"] == "mentioned"            # overview sentence only
    assert prof.strengths()["Docker"] == 1.0 and prof.strengths()["Git"] == 0.5

def test_assessment_cue_inside_other_section():
    p = analyse_text("Week 2: Tools\nThe assignment requires a Tableau dashboard.\nWe also use Excel.")
    assert p.skills["Tableau"]["level"] == "assessed"


def test_browser_print_header_with_wide_gaps_removed():
    """Real browser 'Save as PDF' pages carry a header with the title and date separated by a long run of spaces."""
    from extraction import clean_pages
    hdr = "Applied Natural Language Processing" + " " * 150 + "04/10/2026, 18:11"
    pages = [f"{hdr}\nBody text about Python and topic {chr(96+i)*3}.\nhttps://example.edu/subject/36118" + " " * 120 + f"Page {i} of 5" for i in range(1, 6)]
    out = clean_pages(pages)
    assert all("Applied Natural Language" not in p and "Page" not in p for p in out)
    assert all("Python" in p for p in out)


def test_requisites_and_later_study_are_not_coverage():
    from extraction import analyse_text
    text = ("Overview\nThis course covers regression and decision trees.\n"
            "It leads to further learning in advanced topics such as deep learning and computer vision.\n"
            "Exclusion Courses\nMATH5836 - Data and Machine Learning\n"
            "Prerequisite: COMP9021 Python programming")
    names = set(analyse_text(text).skills)
    assert "Regression" in names
    assert not ({"Deep Learning", "Computer Vision", "Machine Learning", "Python"} & names)


def test_indented_wrapped_lines_are_joined():
    """Layout PDFs indent each wrapped line; the sentence must still be rejoined so cues and phrases match."""
    from extraction import clean_pages
    out = clean_pages(["    It prepares students for advanced topics such as deep learning,\n        computer vision and robotics.\n    Next sentence."])
    assert "learning, computer vision" in out[0]


def test_topics_covered_sentence_counts_as_taught():
    from extraction import analyse_text
    p = analyse_text("Overview\nTopics covered in the course include regression and clustering.")
    assert p.skills["Regression"]["level"] == "taught"


def test_ai_policy_table_is_not_coverage_and_columns_split():
    from extraction import analyse_text
    gap = " " * 20
    text = ("Assessment\nQuiz" + gap + "AI prohibited" + gap + "Secure\nFinal exam" + gap + "AI allowed\n"
            "Weekly schedule\nWeek 3" + gap + "Clustering" + gap + "Lecture")
    p = analyse_text(text)
    assert "Artificial Intelligence" not in p.skills and "Generative AI" not in p.skills
    assert p.skills["Clustering"]["level"] == "taught"


def test_table_cell_ai_and_field_of_education_code_are_not_coverage():
    from extraction import analyse_text
    p = analyse_text("Overview\nField of Education 020119 Artificial Intelligence\nAssessment\nFinal exam 60% 2 hours\nAI")
    assert "Artificial Intelligence" not in p.skills
