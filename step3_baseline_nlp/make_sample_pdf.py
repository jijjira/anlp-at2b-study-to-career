"""Builds a synthetic multi-page 'unit outline' PDF used by the tests (no real student data)."""
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

def build(path="sample_unit_outline.pdf"):
    st = getSampleStyleSheet()
    def hf(c, d):
        c.saveState(); c.setFont("Helvetica", 8)
        c.drawString(40, 810, "UTS 36XXX Machine Learning Foundations - Unit Outline")   # running header
        c.drawString(40, 25, f"Page {d.page}"); c.restoreState()
    body = [
      ["Unit overview", "This unit is an introduction to applied machine learning. Students may have seen Git before.",
       "Learning outcomes", "By the end of this unit students will be able to build and evaluate a regression model in Python."],
      ["Week 1: Introduction", "Students learn Python programming and use pandas and NumPy for data wrangling. "
       "Exploratory data analysis is introduced with matplotlib. SQL queries are used to extract data from relational databases."],
      ["Week 2: Supervised learning", "The unit covers machine learning fundamentals: linear regression, logistic regression and "
       "random forests with scikit-learn. Model evaluation uses cross-validation, precision and recall."],
      ["Week 3: Deep learning", "Neural networks are built with PyTorch. The unit introduces natural language processing, "
       "including transformers and large language models, plus the Spark ecosystem for big data. We will spark discussion about ethics."],
      ["Week 4: Deployment", "Students package models with Docker, deploy on AWS and track experiments with MLflow. "
       "R is optional. Ordinary R&D budgets are out of scope.", "Assessment", "Assessment 1 is a group project presented in Tableau dashboards. Assessment 2 is a model deployed with Docker."],
    ]
    story = []
    for i, item in enumerate(body):
        h, t = item[0], item[1]
        story += [Paragraph(h, st["Heading2"]), Paragraph(t, st["BodyText"]), Spacer(1, 12)]
        if len(item) > 3: story += [Paragraph(item[2], st["Heading2"]), Paragraph(item[3], st["BodyText"]), Spacer(1, 12)]
        if i < len(body) - 1: story.append(PageBreak())
    SimpleDocTemplate(path, pagesize=A4).build(story, onFirstPage=hf, onLaterPages=hf)
    return path

if __name__ == "__main__":
    print(build())
