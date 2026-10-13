"""LEGACY text snapshot of the 7 core units, kept only for the page-text comparison in notebook 08. The report and the main
case study read the saved PDFs in data/curriculum_pdfs/ (see docs/references_and_data_sources.md); the UTS and UNSW pages in those
PDFs are the 2027 version of each entry, the USYD outlines are 2026 offerings.

Real public unit descriptions (UTS, USYD, UNSW) used for the curriculum alignment case study.

Text was taken from the public handbook / outline pages listed in SOURCES on 4 Oct 2026 (newest offering found: COMP5318 2026 S2, DATA5207 2026 S1, COMP9444 26T2, COMP9417 26T1, UTS current handbook), via a web fetch tool that
returns a processed copy of each page, so wording may be lightly condensed. Section headings are normalised to
Overview / Learning outcomes / Weekly schedule / Assessment so the coverage tagger can read them. Handbook entries are
shorter than full unit outlines, so coverage here is a LOWER bound.
"""
SOURCES = {
 "UTS 36118 Applied NLP": "https://handbook.uts.edu.au/subjects/details/36118.html",
 "UTS 36106 ML Algorithms": "https://handbook.uts.edu.au/subjects/details/36106.html",
 "UTS 36120 Adv ML Application": "https://handbook.uts.edu.au/subjects/details/36120.html",
 "USYD COMP5318 ML and Data Mining": "https://www.sydney.edu.au/units/COMP5318/2026-S2C-NE-CC",
 "USYD DATA5207 Data Analysis": "https://www.sydney.edu.au/units/DATA5207/2026-S1C-ND-CC",
 "UNSW COMP9444 Deep Learning": "https://webcms3.cse.unsw.edu.au/COMP9444/26T2/outline",
 "UNSW COMP9417 ML and Data Mining": "https://webcms3.cse.unsw.edu.au/COMP9417/26T1/outline",
}
UNITS = {
"UTS 36118 Applied NLP": """Overview
Analysis of naturally occurring human language offers significant potential. Students gain practical expertise in automated methods of natural language processing (NLP) and text mining, working with messy unstructured data sets.
Learning outcomes
Understand core concepts of Natural Language Processing and computational linguistics.
Apply text mining techniques on unstructured data sets using advanced NLP programming packages.
Weekly schedule
Unstructured data and natural language text. NLP fundamentals. Python-based text analysis techniques. Advanced NLP and deep learning approaches. Natural language understanding and generation. Practical NLP applications. Ethical best practices in NLP.
Assessment
Assessment 1 is Python code with an analysis report. Assessment 2 is a group end-to-end NLP project with application design.""",
"UTS 36106 ML Algorithms": """Overview
This subject introduces fundamental machine learning algorithms and their practical application. Industry-standard methodologies for data mining and analytics are explored through readings and assignments.
Learning outcomes
Apply an industry standard analytics life cycle methodology for data mining and pattern discovery.
Execute and interpret machine learning approaches available for extracting value from data.
Weekly schedule
Regression and classification models. CRISP-DM. Classification model development. Unstructured data analysis and text analysis.
Assessment
Assessment 1 is regression and classification models with R code. Assessment 2 is a classification model with R code and a Kaggle predictions file, plus a management presentation. Assessment 3 is unstructured data analysis with visualizations.""",
"UTS 36120 Adv ML Application": """Overview
An in-depth exploration of machine learning techniques with a focus on the engineering aspects of model deployment, including fairness, accountability, privacy and transparency.
Learning outcomes
Implement and evaluate advanced machine learning techniques to real-world problems.
Design and implement robust and efficient systems for model deployment.
Weekly schedule
Training advanced machine learning algorithms. Optimising machine learning models. Interpreting machine learning results. Deploying machine learning solutions. Managing lifecycle of machine learning models.
Assessment
Assessment 1 is a Kaggle competition. Assessment 2 is machine learning as a service, from model training through deployment. Assessment 3 is a group data product with machine learning.""",
"USYD COMP5318 ML and Data Mining": """Overview
Machine learning is the process of automatically building mathematical models that explain and generalise datasets. It covers discovering patterns in data, classification, regression, feature extraction and data visualisation, and the analysis, comparison and usage of machine learning and statistical techniques.
Learning outcomes
Apply machine learning software tools and libraries to prepare data, train models, tune parameters, and generate predictions.
Analyse and compare machine learning algorithms using appropriate evaluation metrics.
Design, implement, and evaluate a complete machine learning solution, justifying algorithm choices.
Communicate machine learning methods and results clearly using suitable visualisations.
Weekly schedule
Weeks 1 to 13: data cleaning and similarity measures, nearest neighbour and rule-based algorithms, linear and logistic regression, probability-based learning, decision trees and ensembles, support vector machines, neural networks, deep neural networks (CNN, RNN, Transformer), clustering, Markov models, reinforcement learning.
Assessment
Weekly homeworks, two group assignments with a computer program and report, and a final exam. Textbooks reference Python libraries scikit-learn, Keras and TensorFlow.""",
"USYD DATA5207 Data Analysis": """Overview
Data science is a rapidly expanding field with demand from technology companies, financial services and government. Students apply quantitative research methods to social science questions, cleaning, processing, modelling and visualising data using R.
Learning outcomes
Apply established data analytical methodology in a sophisticated manner using R.
Apply a theoretical understanding of statistical methods to practical problems.
Present data and reports of a high standard using RStudio.
Demonstrate proficiency in the delivery of a small-scale project.
Weekly schedule
Weeks 1 to 13: understanding the social world using data science, visualising data, surveys and probabilities, predicting outcomes, measuring latent variables, validating data, spatial data, data journalism.
Assessment
A research project, a research plan, lecture quizzes and group work, all in R and RStudio.""",
"UNSW COMP9444 Deep Learning": """Overview
Neural networks and deep learning play a critical role in pushing the boundaries of what AI can achieve. The course covers principles and practice of perceptrons, feedforward networks, backpropagation, convolutional networks, image processing, recurrent networks, language processing, deep reinforcement learning, autoencoders, generative models and adversarial training.
Weekly schedule
Week 1: neuroanatomy, perceptrons, multi-layer networks, backpropagation. Week 2: probability, generalisation, overfitting, PyTorch. Week 3: cross entropy, softmax, weight decay, momentum. Week 4: convolutional networks, image processing. Week 5: reinforcement learning, Q-learning, policy learning, deep reinforcement learning. Week 7: word vectors, recurrent networks. Week 8: transformers, large language models. Week 9: autoencoders, adversarial training, multimodal learning. Week 10: generative models, deep learning and ethics.
Assessment
An individual assignment, a group project and a final exam. Software requirements are Python, PyTorch, NumPy and scikit-learn.""",
"UNSW COMP9417 ML and Data Mining": """Overview
Machine learning is the algorithmic approach to learning from data, and the course also covers data mining, the application of machine learning to obtain insight from data. Topics include linear models for regression and classification, nearest neighbour methods, tree learning, kernel machines, neural networks, unsupervised learning, ensemble learning and learning theory. Assumed knowledge includes programming in Python.
Assessment
Two homeworks, a group project and a final exam.""",
}
