# AI-Powered Library Assessment Decision Support System

## A Local-First Multi-Source Data Integration Approach Using Natural Language Processing, Retrieval-Augmented Generation, and Human-in-the-Loop Analysis

**Authors:** [Your Names], [Degrees]  
**Institution:** [Your Institution], [City], [State], [Country]  
**Repository:** https://github.com/synnbad/Library-Assessment-Decision-Support-System  
**Last updated:** 2026-04-27

## Abstract

This report presents the design, implementation, and evaluation framework for a
local-first AI-powered decision support system for library assessment. The system
integrates multiple library assessment data sources, including survey responses,
usage statistics, circulation records, e-resource metrics, instruction data,
reference interactions, event attendance, spaces data, collection data, and
benchmark information. Rather than functioning as a single predictive model, the
application is a human-in-the-loop assessment workbench that combines data
validation, metadata governance, statistical analysis, natural language processing
(NLP), semantic retrieval, Retrieval-Augmented Generation (RAG), and leadership
report generation.

The system uses SQLite as the local system of record, ChromaDB as a local vector
index, sentence-transformer embeddings for semantic search, TextBlob and optional
transformer-based sentiment analysis for qualitative feedback, TF-IDF with K-Means
for theme extraction, and Ollama-hosted local language models for narrative
drafting and cited question answering. Privacy and governance are central design
constraints: core data remains on the local workstation or institution-controlled
infrastructure, PII detection and redaction are applied to sensitive text, and
human review is required before AI-generated findings become decision artifacts.

This report maps the system to a formal evaluation checklist covering data and
preprocessing, dataset characteristics, modeling approach, evaluation metrics,
results and interpretation, error analysis, visualizations, practical impact, and
limitations. Because the current project is a system implementation rather than a
completed supervised model validation study, unverified performance claims are
treated as future evaluation targets rather than completed results.

## 1. Introduction

Library assessment teams routinely work with heterogeneous evidence: open-ended
survey comments, Likert-scale responses, circulation data, gate counts, electronic
resource usage, instruction statistics, reference interactions, study room
bookings, event attendance, and benchmark comparisons. These sources are valuable,
but they are difficult to synthesize manually. Qualitative feedback requires
coding and theme development, quantitative analysis requires statistical fluency,
and leadership reporting requires concise interpretation grounded in evidence.

At the same time, library assessment data can include sensitive information about
students, staff, services, spaces, and institutional behavior. Sending raw data to
external AI services can create privacy, compliance, and governance concerns,
especially in educational settings subject to FERPA or similar local policies.

This system addresses those constraints by providing a local-first assessment
workbench. Its purpose is not to replace professional judgment. Its purpose is to
make evidence easier to prepare, search, analyze, interpret, and report while
keeping humans responsible for conclusions and recommendations.

## 2. Study Framing

The major framing shift for this report is that the project should not be
described primarily as a predictive machine learning model. The application does
not currently train a supervised classifier such as logistic regression, random
forest, XGBoost, or LSTM on an outcome label. Instead, it combines multiple applied
AI and analytics components:

- data import and normalization
- PII review and redaction
- metadata readiness checks
- qualitative sentiment and theme analysis
- quantitative statistical analysis
- semantic indexing and retrieval
- RAG-based natural language question answering
- AI-assisted interpretation and recommendation drafting
- leadership-ready report assembly

The appropriate evaluation unit is therefore the full decision-support workflow:
whether the system helps library staff move from raw assessment data to
trustworthy, cited, reviewable findings.

## 3. Research Questions

1. How can NLP and semantic retrieval improve the efficiency and consistency of
   library assessment workflows?
2. How can a local-first architecture support AI-assisted analysis while
   preserving privacy and institutional control?
3. How can RAG improve natural-language access to multi-source assessment data
   while maintaining citations and evidence traceability?
4. Which workflow and quality controls are needed so AI-generated interpretations
   support, rather than replace, professional judgment?
5. What evaluation metrics are appropriate for an assessment workbench that
   combines deterministic statistics, NLP, retrieval, and narrative generation?

## 4. System Objectives

The system was designed to:

- import common library assessment file types
- normalize heterogeneous data into analysis-ready structures
- detect missing metadata and data readiness gaps
- identify and redact personally identifiable information
- support qualitative analysis of text feedback
- support quantitative analysis of usage and metric data
- index uploaded rows for semantic search
- answer natural-language questions with citations
- generate draft interpretations, insights, and recommendations
- assemble leadership-ready reports with methods, evidence, and limitations
- maintain local-first data custody
- support named local user accounts and role-aware workflows

## 5. Checklist Mapping Summary

| Checklist Area | Adapted System-Evaluation Mapping |
|---|---|
| Data and preprocessing | Import, validation, schema normalization, missing data checks, PII review, metadata, indexing |
| Dataset characteristics | Library assessment source types, row counts, variables, text fields, date fields, metric fields |
| Modeling approach | NLP, sentiment, themes, embeddings, ChromaDB retrieval, RAG, local LLM drafting, deterministic statistics |
| Evaluation metrics | Retrieval metrics, citation accuracy, sentiment agreement, theme interpretability, report usefulness, usability |
| Results and interpretation | Implemented system capabilities, demonstration outputs, readiness signals, leadership report generation |
| Error analysis | Misretrieval, weak citations, missing metadata, PII risks, sparse data, ambiguous questions, local LLM failures |
| Visualizations | Trends, distributions, comparison charts, correlation heatmaps, sentiment/theme summaries |
| Practical impact | Faster evidence synthesis, privacy-preserving AI, better reporting, more consistent assessment workflows |
| Limitations and future work | External validation, stronger models, benchmark datasets, multilingual support, predictive modeling extensions |

## 6. Data And Preprocessing

### 6.1 Data Sources And Cohort Definition

The system supports library assessment datasets rather than a clinical cohort. A
"cohort" in this context is the set of records included in a specific assessment
project, report, query scope, or analysis run.

Supported source categories include:

- survey responses and open-ended feedback
- usage statistics
- circulation records
- e-resource usage reports
- instruction session data
- reference interaction data
- event attendance data
- study room and space usage data
- collection and holdings data
- peer benchmark data

Each imported dataset receives a local dataset identifier, metadata fields, upload
date, row count, source description, analysis capability flags, and indexing state.

### 6.2 Inclusion Criteria

Records are included when they:

- come from a supported file type such as CSV, TSV, TXT, Excel, or JSON
- can be parsed into a tabular or text-like structure
- include the minimum fields required for the detected dataset type
- pass basic validation checks
- are not blocked by configured PII or governance rules
- are associated with an active dataset in the local SQLite database

For RAG and semantic search, records are included in the searchable corpus after
they have been converted to text passages and indexed into ChromaDB.

### 6.3 Exclusion Criteria

Records or files may be excluded when they:

- are malformed or cannot be parsed
- lack required columns for the selected or inferred dataset type
- are duplicate uploads detected by file hash
- contain high-risk PII that administrators choose to block
- are archived or deleted
- cannot be transformed into a meaningful analysis or retrieval passage

The system should report exclusions clearly so users understand whether a problem
is caused by file structure, missing fields, privacy policy, or unsupported data.

### 6.4 Missing Data Handling

The system does not silently erase uncertainty. Missing data is handled through:

- validation warnings during import
- metadata readiness checks
- profiling of missing fields
- modeling-readiness checks for missingness, outliers, numeric columns, and date columns
- analysis-specific safeguards when columns are insufficient
- report language that can describe limitations and incomplete evidence

For statistical workflows, missing values are handled according to the specific
analysis function. For qualitative and retrieval workflows, empty or low-content
text can reduce sentiment quality, theme quality, and retrieval usefulness.

### 6.5 Feature Engineering And Normalization

The system creates analysis-ready representations rather than training a single
prediction model. Important transformations include:

- standardizing survey responses into question and response text
- normalizing usage-like records into date, metric, value, and category fields
- deriving sentiment polarity and sentiment labels for text records
- extracting TF-IDF features for theme clustering
- generating representative keywords for themes
- converting rows into retrieval passages
- embedding retrieval passages as dense vectors
- storing vector metadata such as dataset ID, row ID, source type, and citation fields
- producing dataset profiles used for question suggestions and analysis guidance

## 7. Dataset Characteristics

### 7.1 Sample Size

Sample size is dataset-specific and should be reported per study, project, or
demonstration. In this system, sample size may refer to:

- number of uploaded datasets
- number of rows per dataset
- number of text responses
- number of usage records
- number of indexed retrieval passages
- number of records included in a specific analysis

The current report should avoid fixed sample size claims unless they come from a
specific exported dataset or study run.

### 7.2 Class Distribution And Imbalance

The current system is not centered on supervised class prediction. However, class
or category distributions are still relevant for:

- sentiment labels: positive, neutral, negative
- dataset type
- patron or user category, where appropriate and privacy-safe
- resource type
- service category
- theme cluster
- time period

Imbalance should be reported when it affects interpretation. For example, a survey
with very few negative comments may not support reliable conclusions about
dissatisfaction themes.

### 7.3 Key Variables

Clinical variables and social determinants of health are not the relevant frame.
For this system, key variables include:

- response text
- survey question
- response date
- metric name
- metric value
- date or time period
- resource or service category
- circulation material type
- patron group, when available and appropriate
- location or space category
- event or instruction session type
- benchmark institution or comparison group
- metadata fields such as title, source, description, usage notes, and ethical considerations

### 7.4 Train, Validation, And Test Split

The production system does not currently require a train, validation, and test
split because it primarily uses pre-trained models, deterministic statistics, and
retrieval over user-provided data.

Splits become relevant for future supervised evaluation tasks, such as:

- validating sentiment predictions against manually labeled responses
- benchmarking retrieval against a curated question-answer set
- testing a future predictive model for usage forecasting or service demand
- comparing theme extraction against human-coded themes

For future validation, a recommended design is:

- training set: used only if a supervised or fine-tuned model is introduced
- validation set: used for prompt, threshold, and hyperparameter tuning
- test set: held out for final evaluation
- temporal split: used when evaluating forecasting or time-sensitive workflows

## 8. Modeling And NLP Approach

### 8.1 Baseline And Advanced Components

The system uses a layered approach:

| Component | Current Role | Current/Planned Method |
|---|---|---|
| Sentiment analysis | Estimate tone of text feedback | TextBlob baseline, optional RoBERTa enhancement |
| Theme extraction | Group similar open-ended responses | TF-IDF plus K-Means |
| Semantic search | Retrieve relevant rows by meaning | Sentence-transformer embeddings with ChromaDB |
| Question answering | Answer user questions with cited evidence | RAG with local Ollama model |
| Statistical analysis | Analyze numeric and time-series data | Correlation, trend, comparison, distribution methods |
| Narrative drafting | Explain results in plain language | Local LLM prompts with human review |
| Report generation | Assemble leadership-ready outputs | Structured report workflow and export |

### 8.2 Sentiment Analysis

The baseline sentiment path uses TextBlob. TextBlob is fast and simple, making it
useful for lightweight exploratory analysis. It produces polarity and subjectivity
signals that can be summarized across responses and within themes.

The repository also contains an enhanced sentiment module designed around a
transformer model such as `cardiffnlp/twitter-roberta-base-sentiment-latest`.
This should be described as optional or configurable unless it is enabled and
evaluated in a specific run.

Appropriate evaluation:

- manually label a representative set of library feedback responses
- compare TextBlob and RoBERTa predictions against human labels
- report accuracy, precision, recall, F1-score, and confusion matrices
- examine low-confidence and disagreement cases

### 8.3 Theme Extraction

Theme extraction uses TF-IDF vectorization and K-Means clustering. TF-IDF converts
text responses into weighted term features. K-Means groups responses with similar
feature patterns. For each theme, the system can provide:

- top keywords
- representative responses
- theme frequency
- sentiment distribution within the theme

This is best described as automated theme discovery, not final qualitative coding.
Human review remains necessary because clusters may merge unrelated issues, split
the same issue across multiple groups, or overemphasize repeated terms.

### 8.4 Semantic Embeddings And ChromaDB

For retrieval, rows are converted into text passages and embedded using a
sentence-transformer model such as `sentence-transformers/all-MiniLM-L6-v2`.
Embeddings allow the system to match user questions to semantically related records
even when exact keywords differ.

ChromaDB stores the local vector index. SQLite remains the system of record, while
ChromaDB serves as the retrieval layer. The Streamlit Data workflow exposes
indexing status so users can tell whether datasets are ready for Ask.

### 8.5 Retrieval-Augmented Generation

The RAG workflow follows this sequence:

1. The user asks a natural-language question.
2. The question is embedded.
3. ChromaDB retrieves the most relevant indexed passages.
4. Retrieved passages are assembled into a bounded context.
5. PII redaction and safety checks are applied.
6. A local Ollama-hosted language model drafts an answer from the retrieved context.
7. The answer includes citations or source references.
8. The user reviews the answer before promoting it into a report.

RAG is appropriate because it grounds generated answers in uploaded assessment
data. It is preferable to unconstrained chatbot use because it preserves a link
between claims and evidence.

### 8.6 Statistical Analysis

The quantitative analysis layer supports:

- correlation analysis
- trend analysis
- comparative analysis
- distribution analysis
- chart generation
- LLM-assisted interpretation, insights, and recommendations

These are deterministic or statistical computations first. The LLM is used to help
explain results in accessible language, not to invent statistical findings.

### 8.7 Hyperparameter Tuning Strategy

Because the system currently uses pre-trained and deterministic methods, tuning is
workflow-specific:

- TF-IDF: maximum features, n-gram range, stop words
- K-Means: number of themes, initialization, random seed
- Retrieval: top-k passages, embedding model, chunk size, metadata filters
- LLM: model name, temperature, context size, prompt templates
- Statistics: method selection rules and significance thresholds

Future validation should document any parameter choices before final testing.

### 8.8 Temporal And Cross-Validation Setup

Temporal validation is relevant for trend analysis, forecasting, and longitudinal
assessment. Cross-validation is relevant only if future supervised models are
introduced. For the current system, a better evaluation design is scenario-based:

- curated datasets
- curated user questions
- expected citations
- expected statistical outputs
- human-rated report quality

## 9. Evaluation Metrics

### 9.1 Primary Metrics

The appropriate primary metrics depend on component:

| Component | Recommended Metrics |
|---|---|
| Sentiment | Accuracy, precision, recall, F1-score, confusion matrix |
| Theme extraction | Topic coherence, topic diversity, human interpretability rating |
| Retrieval | Precision@K, Recall@K, Mean Reciprocal Rank |
| RAG answers | Relevance, faithfulness, completeness, citation correctness |
| Statistical analysis | Correct method selection, calculation accuracy, interpretation accuracy |
| Reports | Completeness, clarity, evidence traceability, leadership usefulness |
| Usability | Task completion rate, time on task, user satisfaction |

### 9.2 Calibration

Calibration is not a core metric for the current system because the application is
not primarily producing calibrated risk probabilities. Calibration would become
relevant if the system adds supervised predictive models, such as forecasting high
demand for study rooms or classifying responses into operational risk categories.

### 9.3 Statistical Tests And Confidence Intervals

For future evaluation, the report should include:

- confidence intervals for accuracy, F1-score, and retrieval metrics
- paired comparisons when evaluating two methods on the same examples
- inter-rater agreement for human-labeled sentiment or theme evaluation
- bootstrap confidence intervals for small evaluation sets
- correction for multiple comparisons when testing many variables

## 10. Results And Interpretation

### 10.1 Implemented System Results

The current system implements the following capabilities:

- local Streamlit workflow shell organized as Home, Data, Analyze, Ask, Reports,
  Governance, and Admin
- named local users with role-aware access
- dataset import, validation, duplicate detection, and normalization
- metadata fields aligned with FAIR/CARE-oriented governance
- PII detection and redaction utilities
- indexing workflow that marks datasets ready for Ask when rows are present in ChromaDB
- qualitative sentiment and theme analysis
- quantitative correlation, trend, comparison, and distribution analysis
- semantic search over indexed records
- RAG question answering with local Ollama generation
- report generation with executive-summary style output
- admin and governance surfaces for local-first deployment

### 10.2 Demonstration Results

A coherent demonstration should report only what was actually run. For example:

- number of datasets imported
- number of rows per dataset
- number of datasets indexed
- number of Ask queries tested
- example retrieved citations
- example qualitative themes
- example trend or comparison outputs
- report sections generated

Demonstration results should not claim model accuracy, retrieval accuracy, time
savings, or user satisfaction unless those were measured using a documented method.

### 10.3 Interpretation Of System Behavior

The system is strongest when:

- uploaded data has clear text, date, metric, and category fields
- dataset metadata is complete
- rows can be converted into meaningful retrieval passages
- users ask scoped questions that map to available data
- generated narratives are reviewed before use

The system is weaker when:

- files are sparse or poorly structured
- metadata is missing
- questions require data not present in the corpus
- text fields are too short for semantic retrieval
- local LLM resources are unavailable
- users treat generated text as final rather than draft evidence

## 11. Error Analysis

### 11.1 Common Failure Modes

Common failure scenarios include:

- a dataset exists in SQLite but is not indexed in ChromaDB
- ChromaDB contains rows but the UI indexing state is stale
- a user asks a broad question that retrieves weakly related passages
- a question asks for a comparison that requires fields not present in the data
- a file has missing or inconsistent date and metric columns
- qualitative feedback contains very short or ambiguous text
- theme clusters group responses that share words but not meaning
- the local Ollama service is unavailable or too slow
- PII patterns over-redact harmless text or miss unusual identifiers

### 11.2 Bias And Subgroup Performance

Bias evaluation should be adapted to library assessment. Important questions
include:

- Does sentiment analysis perform differently for different writing styles?
- Are comments from smaller groups underrepresented in themes?
- Does retrieval favor longer responses over shorter but important ones?
- Are patron categories, if present, interpreted ethically and with enough context?
- Are recommendations sensitive to privacy, equity, and institutional policy?

Subgroup analysis should only be performed when categories are available,
appropriate, and privacy-safe.

### 11.3 Data Or Model Limitations

The system depends on the quality of local data. It cannot infer facts that are not
present in uploaded records. It can retrieve semantically similar records, but it
cannot guarantee that those records are sufficient for a strong conclusion.

Local models also have limits. A small local LLM is useful for drafting and
summarization, but it may produce weaker prose or reasoning than larger hosted
models. This tradeoff is intentional because privacy and local custody are core
requirements.

### 11.4 Edge Cases

Edge cases that should be included in test plans:

- empty files
- malformed CSV files
- duplicate uploads
- all-missing text columns
- very large datasets
- mixed-language feedback
- sensitive free-text comments
- ambiguous metric names
- date formats from multiple systems
- archived datasets
- interrupted indexing jobs
- unavailable Ollama service
- ChromaDB and SQLite status mismatch

## 12. Visualizations

The visualization checklist should be adapted as follows:

| Original Visualization Item | Applicability To This System |
|---|---|
| ROC curves | Future supervised classifiers only |
| Precision-recall curves | Future supervised classifiers or retrieval benchmarking |
| Calibration plots | Future probability-producing predictive models only |
| SHAP or feature importance | Future supervised models only |
| Temporal trends | Current trend analysis and usage/circulation workflows |
| Subgroup plots | Current comparative analysis when privacy-safe groups exist |
| Correlation heatmaps | Current quantitative analysis |
| Distribution charts | Current quantitative analysis |
| Theme summaries | Current qualitative analysis |
| Sentiment distributions | Current qualitative analysis |
| Citation/evidence tables | Current RAG and reporting workflow |

Recommended current visuals:

- dataset inventory and readiness table
- missing metadata table
- indexing status table
- sentiment distribution bar chart
- theme frequency chart
- representative quote table
- metric trend line chart
- comparison box plot
- distribution histogram
- correlation heatmap
- report evidence table

## 13. Practical Impact

This system's practical value is in assessment operations and decision support,
not clinical deployment.

### 13.1 How Results Can Be Used

Library teams can use the system to:

- identify major themes in open-ended feedback
- summarize user sentiment across services or spaces
- detect usage trends over time
- compare usage or feedback across groups, periods, or categories
- ask natural-language questions about uploaded evidence
- produce leadership-ready briefs
- document data sources, limitations, and methods
- support planning, resource allocation, service improvement, and communication

### 13.2 Thresholds For Decision-Making

The system should not enforce universal thresholds. Instead, thresholds should be
locally configured and documented. Examples include:

- minimum number of responses before reporting a theme
- minimum number of records before comparing groups
- minimum retrieval score or citation count before promoting an answer
- significance threshold for statistical tests
- threshold for flagging high missingness
- threshold for requiring additional human review

### 13.3 Comparison To Current Practice

Compared with manual assessment workflows, the system can reduce repetitive work in
importing, profiling, searching, summarizing, and drafting. Compared with generic
cloud AI tools, it offers stronger local data custody and better evidence
traceability. Compared with traditional statistical tools, it provides a more
accessible workflow for non-specialists while preserving statistical outputs.

The tradeoff is that the system requires local setup, careful review, and explicit
validation before claims about model accuracy or workflow time savings can be made.

## 14. Privacy, Governance, And Human Review

The system is designed around local-first governance:

- SQLite stores core records locally.
- ChromaDB stores retrieval vectors locally.
- Ollama runs language generation locally.
- PII detection and redaction are applied before sensitive text is displayed or generated.
- Named local users support accountability.
- Admin controls govern users, PII rules, logs, and system health.
- Generated narratives are treated as drafts.

FAIR principles are reflected through metadata, identifiers, provenance, and export
support. CARE principles are reflected through local control, responsible use,
ethical considerations, and human review.

## 15. Limitations And Future Work

### 15.1 Data Limitations

- Real-world library datasets vary widely in structure and completeness.
- Small datasets may not support reliable theme or subgroup analysis.
- Missing metadata can weaken interpretation.
- Free-text feedback may include sensitive information.
- Evaluation results from one institution may not generalize to another.

### 15.2 Model Limitations

- TextBlob is fast but limited for domain-specific sentiment.
- TF-IDF plus K-Means can miss nuanced or overlapping themes.
- Sentence embeddings improve retrieval but can still return weak matches.
- Small local LLMs can draft plausible but incomplete interpretations.
- RAG reduces hallucination risk but does not eliminate it.
- The system does not currently provide a full supervised predictive modeling pipeline.

### 15.3 External Validation Plans

Recommended validation steps:

1. Create a benchmark set of manually labeled library feedback responses.
2. Compare TextBlob and enhanced transformer sentiment predictions.
3. Create a curated set of assessment questions with expected supporting records.
4. Evaluate retrieval using Precision@K, Recall@K, and Mean Reciprocal Rank.
5. Evaluate RAG answers for relevance, faithfulness, completeness, and citation correctness.
6. Ask librarians to rate theme interpretability and report usefulness.
7. Run usability testing with representative assessment workflows.
8. Test the system on datasets from multiple library contexts.

### 15.4 Future Enhancements

Short-term enhancements:

- strengthen indexing confirmation and retry controls
- improve report review and approval workflows
- expand PII rule configuration
- add explicit evidence-confidence labels for Ask responses
- add benchmark evaluation scripts for RAG and sentiment

Medium-term enhancements:

- enable transformer-based sentiment as a tested optional mode
- add BERTopic or another neural topic modeling option
- evaluate BGE or other embedding models for retrieval quality
- add multilingual text handling
- improve deterministic routing for statistical questions

Long-term enhancements:

- add supervised predictive workflows where appropriate
- add temporal forecasting for demand planning
- support institution-controlled VM inference
- support multi-institution benchmarking with strong governance controls
- create formal external validation reports

## 16. Conclusion

The AI-Powered Library Assessment Decision Support System is best understood as a
local-first, human-in-the-loop assessment workbench. Its contribution is not a
single trained predictive model. Its contribution is the integration of data
validation, metadata governance, NLP, semantic retrieval, RAG, statistical
analysis, and report generation into a coherent workflow for library assessment.

The checklist can be applied successfully when translated from a clinical
predictive-model frame into an assessment decision-support frame. Data and
preprocessing become import, normalization, metadata, PII review, and indexing.
Modeling becomes a layered NLP and retrieval architecture. Evaluation becomes a
combination of retrieval metrics, citation checks, sentiment agreement, theme
interpretability, statistical correctness, report usefulness, and usability.
Practical impact becomes better evidence synthesis, faster assessment workflows,
and privacy-preserving AI adoption.

The system is already positioned to support real library assessment work, but
future reports should distinguish clearly between implemented functionality,
demonstration outputs, and formally validated performance claims.

## References

1. Devlin J, Chang MW, Lee K, Toutanova K. BERT: Pre-training of deep
   bidirectional transformers for language understanding. arXiv:1810.04805. 2018.
2. Reimers N, Gurevych I. Sentence-BERT: Sentence embeddings using Siamese
   BERT-networks. arXiv:1908.10084. 2019.
3. Lewis P, Perez E, Piktus A, et al. Retrieval-augmented generation for
   knowledge-intensive NLP tasks. arXiv:2005.11401. 2020.
4. Grootendorst M. BERTopic: Neural topic modeling with a class-based TF-IDF
   procedure. arXiv:2203.05794. 2022.
5. Wilkinson MD, Dumontier M, Aalbersberg IJ, et al. The FAIR Guiding Principles
   for scientific data management and stewardship. Scientific Data. 2016;3:160018.
6. Carroll SR, Garba I, Figueroa-Rodriguez OL, et al. The CARE Principles for
   Indigenous Data Governance. Data Science Journal. 2020;19:43.
7. Family Educational Rights and Privacy Act, 20 U.S.C. 1232g; 34 CFR Part 99.
8. Loria S. TextBlob: Simplified Text Processing. https://textblob.readthedocs.io/
9. Pedregosa F, Varoquaux G, Gramfort A, et al. Scikit-learn: Machine learning in
   Python. Journal of Machine Learning Research. 2011;12:2825-2830.
10. Wolf T, Debut L, Sanh V, et al. Transformers: State-of-the-art natural
    language processing. EMNLP System Demonstrations. 2020.

## Appendix A. Evaluation Against Checklist

This appendix evaluates the system directly against the checklist. The checklist is
retained as report content, but each item is interpreted for a local-first library
assessment decision-support system rather than a clinical predictive model.

Status labels:

- **Implemented:** Supported by the current system.
- **Partially implemented:** Present, but needs stronger evaluation, UI support, or documentation.
- **Future validation:** Requires a formal evaluation dataset or study protocol.
- **Not applicable:** Not appropriate unless the system adds supervised predictive modeling.

### 1. Data And Preprocessing

| Checklist Item | System-Specific Evaluation | Metric Or Evidence | Status |
|---|---|---|---|
| Data source(s) and cohort definition | The system supports library assessment sources: surveys, usage statistics, circulation, e-resource, instruction, reference, spaces, events, collection, and benchmark data. The "cohort" is the selected dataset set used for a project, analysis, report, or Ask query scope. | Dataset inventory; dataset type; row count; source metadata; selected report/query scope. | Implemented |
| Inclusion / exclusion criteria | Files are included when they are supported, parseable, valid for a known dataset type, not duplicates, and not blocked by PII/governance controls. Files or rows are excluded when malformed, unsupported, duplicate, archived, deleted, or privacy-blocked. | Import validation results; duplicate hash detection; PII review result; archive/delete state; import error logs. | Implemented |
| Missing data handling | The system surfaces missing required columns, incomplete metadata, missing values, low-content text, and modeling-readiness gaps. Statistical workflows should describe missingness before interpretation. | Missing-field warnings; metadata readiness table; modeling-readiness checks; analysis limitations in reports. | Partially implemented |
| Feature engineering / normalization | The system normalizes uploaded records into survey and usage-like tables, derives sentiment labels, extracts TF-IDF features, clusters themes, converts rows into text passages, and creates embeddings for retrieval. | Stored normalized records; generated sentiment fields; theme records; ChromaDB indexed passages; dataset profile output. | Implemented |

### 2. Dataset Characteristics

| Checklist Item | System-Specific Evaluation | Metric Or Evidence | Status |
|---|---|---|---|
| Sample size (N) | N should be reported per dataset and per analysis. Relevant counts include number of datasets, rows, text responses, usage records, indexed passages, and records used in a report. | Dataset row count; analysis input count; number of indexed records; report data-source table. | Implemented |
| Class distribution / imbalance | For this system, class distribution applies to sentiment categories, theme clusters, dataset types, patron/service/resource categories, and comparison groups. Imbalance matters when one group dominates interpretation. | Sentiment distribution; theme frequency; category counts; group sizes before comparisons. | Partially implemented |
| Key variables (clinical, SDOH, etc.) | Clinical and SDOH variables are not the right frame. Key variables are response text, question, date, metric name, metric value, category, service/resource type, patron group when appropriate, and governance metadata. | Data dictionary; metadata fields; inferred column roles; dataset profile. | Implemented |
| Train / validation / test split | The current system uses pre-trained NLP models, deterministic statistics, and retrieval rather than training a supervised outcome model. Splits become necessary for future sentiment benchmarking, retrieval benchmarking, or predictive modeling. | Future benchmark protocol with held-out labeled feedback, curated retrieval queries, and temporal splits for forecasting. | Future validation |

### 3. Modeling Approach

| Checklist Item | System-Specific Evaluation | Metric Or Evidence | Status |
|---|---|---|---|
| Models used (e.g., LR, RF, XGBoost, LSTM) | The current system does not center on LR/RF/XGBoost/LSTM. It uses TextBlob sentiment, optional RoBERTa sentiment, TF-IDF + K-Means themes, sentence-transformer embeddings, ChromaDB retrieval, local Ollama/Llama generation, and deterministic statistical methods. | Module implementation; model configuration; dependency settings; generated analysis artifacts. | Implemented |
| Hyperparameter tuning strategy | Relevant parameters include number of themes, TF-IDF max features, n-gram range, top-k retrieval, embedding model, chunk/passage construction, LLM model, temperature, and context size. These are configurable or implementation-level choices but need formal tuning records. | Configuration values; analysis parameters; validation results for alternative settings. | Partially implemented |
| Baseline vs advanced models | Baselines include TextBlob for sentiment and TF-IDF + K-Means for themes. Advanced options include RoBERTa sentiment, BERTopic, stronger embeddings such as BGE, and future supervised/predictive models. | Comparative evaluation table: baseline vs advanced on the same labeled or curated data. | Partially implemented |
| Temporal / cross-validation setup | Temporal validation applies to trend and forecasting workflows. Cross-validation applies only if supervised models are added. For current RAG and analysis workflows, scenario-based validation is more appropriate. | Time-based holdout for forecasting; curated scenario tests for Ask, retrieval, and reports. | Future validation |

### 4. Evaluation Metrics

| Checklist Item | System-Specific Evaluation | Metric Or Evidence | Status |
|---|---|---|---|
| Primary metrics (AUC, Accuracy, F1) | AUC is not currently applicable unless a supervised classifier is added. Accuracy and F1 apply to sentiment if manually labeled feedback exists. RAG should use Precision@K, Recall@K, MRR, citation correctness, faithfulness, relevance, and completeness. Reports should use clarity, evidence traceability, and leadership usefulness ratings. | Sentiment test set; retrieval benchmark; human RAG rubric; report quality rubric; usability study. | Future validation |
| Calibration (if applicable) | Calibration is not applicable to current retrieval, theme extraction, and narrative drafting. It becomes relevant only for future models that output probabilities used in decisions. | Calibration curve; Brier score; reliability diagram for future probability-producing models. | Not applicable |
| Statistical tests / confidence intervals | Statistical tests are implemented for quantitative analysis workflows. Confidence intervals and paired statistical tests should be added to formal model/RAG evaluations. | p-values in quantitative analysis; bootstrap CIs for retrieval and sentiment metrics; inter-rater agreement for human ratings. | Partially implemented |

### 5. Results And Interpretation

| Checklist Item | System-Specific Evaluation | Metric Or Evidence | Status |
|---|---|---|---|
| Best model performance | The current report should not claim best-model performance without a formal benchmark. Instead, it should report implemented model paths and define how best performance will be selected in future validation. | Future comparison: TextBlob vs RoBERTa; MiniLM vs BGE; TF-IDF/K-Means vs BERTopic; RAG top-k variants. | Future validation |
| Key findings (clinical/technical) | Clinical findings are not applicable. Technical findings should focus on workflow readiness: successful import, metadata completeness, indexing readiness, retrieval behavior, statistical outputs, and report generation. Assessment findings should come from a specific dataset/project. | Demonstration report; dataset readiness metrics; sample Ask citations; analysis outputs. | Partially implemented |
| Feature importance (e.g., SHAP) | SHAP is not relevant to the current system because there is no supervised predictive model. For current analysis, analogous evidence includes theme keywords, representative quotes, correlation pairs, trend slopes, and cited passages. | Theme keyword tables; quote tables; correlation heatmap; trend chart; citation table. | Not applicable now; future if predictive models are added |

### 6. Error Analysis

| Checklist Item | System-Specific Evaluation | Metric Or Evidence | Status |
|---|---|---|---|
| Common misclassifications | For sentiment, misclassifications should be measured against manually labeled feedback. For retrieval, errors include irrelevant passages, missing relevant passages, weak citations, and answers that overgeneralize from limited evidence. | Confusion matrix; failed query log; retrieval adjudication; answer faithfulness review. | Future validation |
| Bias / subgroup performance | Subgroup evaluation should focus on whether sentiment, retrieval, themes, and recommendations behave differently by privacy-safe categories such as service area, user group, resource type, or time period. | Stratified sentiment metrics; group-level retrieval quality; theme coverage by group; review of recommendation language. | Future validation |
| Data or model limitations | The system should document sparse data, missing metadata, short text, ambiguous metric names, local model constraints, retrieval limits, and LLM narrative uncertainty. | Limitations section in reports; metadata readiness; low-confidence or insufficient-evidence labels. | Partially implemented |
| Edge cases / failure scenarios | Edge cases include malformed files, duplicates, all-missing text, interrupted indexing, stale indexing status, archived datasets, unavailable Ollama, PII-heavy comments, and unsupported schemas. | Unit tests; integration tests; manual smoke tests; admin logs; error messages. | Partially implemented |

### 7. Visualizations

| Checklist Item | System-Specific Evaluation | Metric Or Evidence | Status |
|---|---|---|---|
| ROC / PR curves | These are not applicable to current system behavior unless future supervised classifiers are added. For retrieval, PR-style evaluation can be adapted through Precision@K and Recall@K plots. | Future classifier benchmark; future retrieval benchmark curve. | Not applicable now |
| Calibration plots | Not applicable unless future predictive models produce decision probabilities. | Future calibration curve and Brier score. | Not applicable now |
| SHAP / feature importance plots | Not applicable to the current non-predictive workflow. The system should instead show evidence drivers: theme keywords, citations, correlations, and trend slopes. | Theme keyword chart; citation/evidence table; correlation heatmap; trend chart. | Not applicable now |
| Temporal trends / subgroup plots | Highly applicable. The system supports trend analysis, comparison charts, distributions, and subgroup comparisons when the data contains appropriate date, group, and metric fields. | Trend line charts; comparison box plots; grouped bar charts; distribution charts. | Implemented |

### 8. Clinical / Practical Impact

| Checklist Item | System-Specific Evaluation | Metric Or Evidence | Status |
|---|---|---|---|
| How results can be used | Results can support library planning, service improvement, resource allocation, space planning, collection decisions, instruction planning, leadership reporting, and assessment communication. | Leadership report; recommendations; cited Ask answers; analysis summaries. | Implemented |
| Thresholds for decision-making | The system should support locally defined thresholds, such as minimum response count for a theme, minimum group size for comparison, significance threshold, retrieval citation threshold, and missingness threshold. | Documented report methods; configurable analysis settings; warning labels for insufficient evidence. | Partially implemented |
| Comparison to current practice | The system should be evaluated against manual workflows: time to import, time to summarize themes, time to answer evidence questions, report completeness, and reviewer confidence. | Time-on-task study; user rubric; pre/post workflow comparison. | Future validation |

### 9. Limitations And Future Work

| Checklist Item | System-Specific Evaluation | Metric Or Evidence | Status |
|---|---|---|---|
| Data limitations | Library datasets can be sparse, inconsistent, small, biased toward respondents, missing metadata, or privacy-sensitive. The report should explicitly state these limits. | Dataset profile; missingness summary; metadata readiness; PII review. | Implemented |
| Model limitations | TextBlob may miss context; TF-IDF/K-Means may produce shallow themes; embeddings may retrieve semantically plausible but weak evidence; local LLMs may draft incomplete or overconfident text. | Error analysis; human review; evidence confidence; model comparison study. | Implemented as documented limitation |
| External validation plans | The next evaluation should use manually labeled feedback, curated RAG questions, expected citations, human report scoring, and multi-institution datasets where governance allows. | External validation protocol; benchmark dataset; held-out test set; human evaluator rubric. | Future validation |
