# Skill Taxonomy — Step 2

This taxonomy supports explainable skill extraction from U.S. Data/AI job advertisements and Australian students' study materials.

## Summary
- Canonical skills: 132
- Aliases: 232
- Categories: 12

## Categories

### Cloud
AWS, AWS Lambda, Azure, GCP, SageMaker, Vertex AI

### Data Analysis & Statistics
A/B Testing, Causal Inference, Classification, Clustering, Data Analysis, Data Cleaning, EDA, Experiment Design, Feature Engineering, Forecasting, Hypothesis Testing, Regression, Statistics, Time Series

### Data Engineering
Airflow, Apache Spark, Data Lake, Data Pipelines, Data Warehousing, Databricks, ELT, ETL, Flink, Hadoop, Hive, Kafka, Lakehouse, Presto, Snowflake, Trino, dbt

### Data Visualisation / BI
Dashboarding, Data Visualization, Looker, Matplotlib, Plotly, Power BI, Seaborn, Tableau

### Databases
BigQuery, Cassandra, DynamoDB, Elasticsearch, MongoDB, MySQL, Oracle, PostgreSQL, Redis, Redshift, SQL Server, Vector Databases

### Development Tools
APIs, Git, GitHub, Jupyter, Linux, REST APIs, VS Code

### ML Frameworks & Libraries
JAX, Keras, LightGBM, NLTK, NumPy, Pandas, PyTorch, SciPy, TensorFlow, XGBoost, scikit-learn, spaCy

### MLOps / Deployment
CI/CD, Docker, GitHub Actions, Jenkins, Kubeflow, Kubernetes, MLflow, Model Deployment, Model Monitoring, Model Serving, Terraform

### Machine Learning & AI
Artificial Intelligence, Computer Vision, Deep Learning, Feature Store, Generative AI, Machine Learning, Model Evaluation, Model Training, Predictive Modeling, Recommendation Systems, Reinforcement Learning

### Methods / Architecture
Cloud Computing, Data Governance, Data Modeling, Data Quality, Distributed Systems, Graph Neural Networks, Knowledge Graphs, Microservices

### NLP / Generative AI
Embeddings, Fine-tuning, Hugging Face, LangChain, Large Language Models, LlamaIndex, Named Entity Recognition, Natural Language Processing, Prompt Engineering, RAG, Text Classification, Tokenization, Transformers, Vector Search

### Programming
Bash, C#, C++, Go, Java, JavaScript, MATLAB, Python, R, SQL, Scala, TypeScript

## Normalisation principle

Aliases are mapped to a single canonical representation.

Short or ambiguous aliases such as `R` require strict token or phrase matching. Step 3 should use spaCy PhraseMatcher rather than arbitrary substring matching.

## Interpretation

Skill frequencies represent mentions in job advertisements. They are not measures of candidate mastery, employability, or hiring probability.