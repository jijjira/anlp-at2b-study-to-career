"""Hand annotation of the 30-job held-out sample (single annotator: Claude, blind to extractor output).
R = explicitly named skill the ad requires or says the role uses (requirements or responsibilities)
P = explicitly named, preferred / nice-to-have
I = implicit: concept clearly demanded but not named with any dictionary alias (target for the semantic method)
OTHER = explicitly demanded skills outside the dictionary (dictionary coverage gap)
Skills only mentioned in company description, benefits or legal text are NOT labelled."""
GOLD = {}
def g(row, R=(), P=(), I=(), OTHER=()): GOLD[row] = dict(R=set(R), P=set(P), I=set(I), OTHER=set(OTHER))
g(5,  R=["SQL","Pandas","Data Analysis"], P=["Python"], I=["Data Pipelines"], OTHER=["Polars"])
g(9,  R=["SQL","Dashboarding","Data Pipelines"], P=["Apache Spark","Python","Artificial Intelligence"], I=["Statistics"], OTHER=["Business Intelligence"])
g(57, R=["SQL","Python","A/B Testing","Dashboarding"], P=["Causal Inference"], I=["Experiment Design","Statistics"], OTHER=["Uplift Modeling"])
g(58, R=["A/B Testing","Dashboarding","SQL","Python","Experiment Design","Causal Inference"], P=["Natural Language Processing","Large Language Models"], I=["Model Evaluation"])
g(65, R=["dbt","ETL","Airflow","GitHub","SQL","Python","Dashboarding","Data Pipelines"], I=["Data Modeling","Data Visualization"], OTHER=["Hex"])
g(83, R=["Data Governance","Data Quality","Data Analysis"], P=["Tableau","Power BI","Data Visualization","SQL","Python","R","Data Warehousing"], I=["Data Cleaning"], OTHER=["Excel","ERP Systems","Master Data Management"])
g(106, R=["Machine Learning","RAG","Large Language Models","Model Context Protocol","Model Monitoring","Time Series","Deep Learning","PyTorch","TensorFlow","JAX","Python","SQL","Apache Spark","Ray","Model Training","Artificial Intelligence","Forecasting"],
       P=["Causal Inference"], I=["Recommendation Systems","Cloud Computing","Experiment Design","Model Evaluation","Model Deployment"], OTHER=["Federated Learning","Differential Privacy","Foundation Models"])
g(141, R=["Statistics","Dashboarding","Data Governance","Data Quality","SQL","Python","R","Data Analysis","Tableau","Data Warehousing","Data Modeling"], I=["Data Visualization"], OTHER=["Survey Design","Data Wrangling"])
g(142, R=["Data Visualization","Looker","Dashboarding","Data Pipelines","Data Quality","Python","SQL","Data Analysis","Generative AI","Large Language Models","Tableau"],
       P=["Snowflake","BigQuery","Databricks","dbt","Airflow","Data Modeling"], OTHER=["Hex","Business Intelligence"])
g(158, R=["Machine Learning","Python","SQL","Pandas","scikit-learn","XGBoost","Keras","TensorFlow","Artificial Intelligence"], P=["Deep Learning"], I=["Model Deployment"],
       OTHER=["Operations Research","Mathematical Programming","Combinatorial Optimization"])
g(170, R=["Distributed Systems","Reinforcement Learning","Machine Learning"], P=["JAX","PyTorch"], I=["Model Training"])
g(182, R=["Data Pipelines","Dashboarding","Python","Machine Learning"], P=["C++","GCP","BigQuery","PostgreSQL"], I=["Distributed Systems","Data Warehousing"], OTHER=["Data Engineering","Google Cloud Storage"])
g(208, R=["Machine Learning","Classification","Feature Engineering","Large Language Models","AI Agents","Knowledge Graphs","Feature Store","Model Training","Model Serving","Artificial Intelligence"],
       OTHER=["Entity Resolution","Weak Supervision","Fraud Detection"])
g(215, R=["Python","PostgreSQL","AWS","Fine-tuning","Machine Learning"], P=["Large Language Models"], I=["Prompt Engineering","Model Evaluation","RAG"], OTHER=["Temporal","LiteLLM","Active Learning"])
g(218, R=["Distributed Systems","Large Language Models","Artificial Intelligence","Machine Learning","Kubernetes","Python","Go","Java","C++","Observability"], I=["Model Serving"], OTHER=["Site Reliability Engineering"])
g(302, R=["Data Pipelines","Apache Spark","SQL","dbt","Python","AWS","Azure","GCP","Tableau","CI/CD","Data Lake","Apache Iceberg"], I=["Data Modeling","Data Visualization"],
       OTHER=["SQLMesh","Palantir Foundry","Flyte","Amazon Athena","Containerization"])
g(303, R=["Causal Inference","Machine Learning","Recommendation Systems","Python","R","SQL","Hive","Apache Spark","Airflow","Deep Learning"], I=["Experiment Design"], OTHER=["Ranking Systems"])
g(312, R=["Artificial Intelligence","Machine Learning","Python","Observability","Data Governance"], P=["JavaScript","TypeScript"], I=["AI Agents","RAG","Model Evaluation"])
g(320, R=["Machine Learning","A/B Testing","Artificial Intelligence","Large Language Models","SQL","EDA"], I=["Recommendation Systems","Deep Learning","Statistics"], OTHER=["Ranking Systems","Ads Conversion Modeling"])
g(329, R=["SQL","Python","Statistics","Artificial Intelligence"], I=["Experiment Design"], OTHER=["Attribution Analytics"])
g(338, R=["Python","SQL","R"], I=["Data Quality"], OTHER=["OCaml"])
g(339, R=["SQL","Python","Statistics"], P=["Artificial Intelligence"], I=["Experiment Design","AI Agents","Prompt Engineering"])
g(411, R=["Tableau","Dashboarding","SQL","dbt","Forecasting","Artificial Intelligence"], I=["Data Pipelines","Data Modeling"], OTHER=["Business Intelligence","Dataform","Fraud Analytics"])
g(441, R=["TypeScript","Python","Distributed Systems","Data Pipelines","Artificial Intelligence","Machine Learning","Large Language Models","Vector Databases","AI Agents","Embeddings"], I=["Cloud Computing"], OTHER=["Full-stack Engineering"])
g(519, R=["SQL","Data Visualization","Tableau","Dashboarding","Data Analysis","Forecasting"], P=["dbt","Python","Artificial Intelligence"], OTHER=["Sigma"])
g(527, R=["Artificial Intelligence","Large Language Models"], P=["Model Context Protocol","Data Pipelines","APIs"], I=["Model Evaluation","Prompt Engineering"], OTHER=["Human-in-the-loop"])
g(537, R=["Observability","Java","C++","Generative AI"], OTHER=["Low-latency Systems","Market Data Protocols"])
g(545, R=["Data Pipelines","Machine Learning","Python","APIs","Data Governance","SQL","Data Analysis","AWS","GCP","Azure","Artificial Intelligence","Large Language Models","Microservices","Distributed Systems","Generative AI"], I=["Cloud Computing"], OTHER=["Data Engineering"])
g(597, R=["Vector Search","RAG","Vector Databases","AI Agents","Large Language Models","Microservices","Observability","Distributed Systems","APIs","Go","Java","Python","Kubernetes","Data Pipelines","Artificial Intelligence","Machine Learning"],
       P=["SQL"], I=["Model Evaluation"], OTHER=["Context Engineering","FoundationDB"])
g(606, R=["MATLAB","Python"], OTHER=["Thermal Engineering","CAD"])
