# Course Project Summary: Library Assessment Decision Support System

> Historical course-project summary. Model improvement percentages are retained as
> proposed enhancement targets or course-context assumptions, not current validated
> system metrics.

## Project Overview

A comprehensive AI-powered decision support system for library assessment that combines multiple NLP techniques with a human-in-the-loop approach. The system processes multi-source data (surveys, usage statistics, circulation data) to provide actionable insights while supporting privacy-conscious local processing.

---

## NLP Techniques Utilized

### 1. Text Preprocessing and Tokenization
- **Purpose**: Clean and normalize raw text data
- **Implementation**: NLTK tokenization, lowercasing, stop word removal
- **Location**: `modules/qualitative_analysis.py`, `modules/rag_query.py`

### 2. Sentiment Analysis
- **Current**: Lexicon-based using TextBlob
- **Technique**: Polarity scoring (-1 to +1 scale)
- **Classification**: Positive, Neutral, Negative
- **Location**: `modules/qualitative_analysis.py`
- **Enhancement Available**: RoBERTa-based model (see `HUGGINGFACE_QUICK_START.md`)

### 3. Topic Modeling / Theme Extraction
- **Technique**: TF-IDF + K-Means Clustering
- **Process**:
  1. Convert text to TF-IDF vectors
  2. Cluster similar responses using K-Means
  3. Extract top keywords per cluster as themes
- **Output**: Themes with keywords, frequency, sentiment distribution, representative quotes
- **Location**: `modules/qualitative_analysis.py`

### 4. Text Embeddings
- **Model**: Sentence-BERT (`all-MiniLM-L6-v2`)
- **Dimensions**: 384
- **Purpose**: Convert text to dense vectors for semantic similarity
- **Use Case**: RAG retrieval, semantic search
- **Location**: `modules/rag_query.py`

### 5. Retrieval-Augmented Generation (RAG)
- **Architecture**: Retrieval → Context Assembly → Generation → Citation
- **Components**:
  - Vector database: ChromaDB
  - Embedding model: Sentence-BERT
  - LLM: Llama 3.2 (3B parameters via Ollama)
- **Features**: Conversation context, citation tracking, suggested follow-ups
- **Location**: `modules/rag_query.py`

### 6. Text Generation
- **Model**: Llama 3.2 (3B)
- **Use Cases**:
  - Statistical interpretation
  - Insight generation
  - Recommendation generation
  - Executive summaries
- **Location**: `modules/quantitative_analysis.py`, `modules/report_generator.py`

### 7. Named Entity Recognition (Pattern-Based)
- **Technique**: Regex pattern matching
- **Entities**: Email, phone, SSN, student IDs
- **Purpose**: PII detection and redaction (privacy-conscious governance)
- **Location**: `modules/pii_detector.py`

### 8. Statistical Text Analysis
- **Metrics**: Word counts, response lengths, frequency distributions
- **Purpose**: Quantitative insights about text characteristics
- **Location**: `modules/quantitative_analysis.py`

---

## Statistical Techniques Utilized

### 1. Correlation Analysis
- **Methods**: Pearson, Spearman, Kendall
- **Purpose**: Identify relationships between numeric variables
- **Output**: Correlation matrix, significance tests, top correlations

### 2. Trend Analysis
- **Technique**: Linear regression with time series
- **Features**: Trend direction, R-squared, seasonal patterns, forecasting
- **Purpose**: Identify patterns over time

### 3. Comparative Analysis
- **Tests**: t-test, Mann-Whitney U, ANOVA, Kruskal-Wallis
- **Purpose**: Compare metrics across groups
- **Features**: Automatic test selection based on normality and group count

### 4. Distribution Analysis
- **Techniques**: Normality tests, outlier detection (IQR, Z-score)
- **Metrics**: Mean, median, std dev, skewness, kurtosis
- **Purpose**: Understand data distributions

---

## Machine Learning Techniques

### Supervised Learning
- **Sentiment Classification**: Pre-trained models (TextBlob baseline, RoBERTa recommended)
- **Named Entity Recognition**: Pattern-based (regex) with ML enhancement available

### Unsupervised Learning
- **K-Means Clustering**: Theme extraction from survey responses
- **TF-IDF Vectorization**: Feature extraction for text clustering

### Transfer Learning
- **Sentence Embeddings**: Pre-trained Sentence-BERT model
- **LLM**: Pre-trained Llama 3.2 for text generation
- **Benefit**: Leverage models trained on billions of tokens without training data

### Retrieval-Augmented Generation
- **Hybrid Approach**: Combines retrieval (information retrieval) with generation (NLP)
- **Advantage**: Grounds responses in actual data, reduces hallucination

---

## System Architecture

### Data Flow

```
Raw Data (CSV) → Preprocessing → Storage (SQLite) → Analysis
                                      ↓
                                  Embeddings → Vector DB (ChromaDB)
                                      ↓
User Query → RAG Engine → Retrieval → LLM → Response + Citations
```

### Key Components

1. **Data Layer**: SQLite database with FAIR/CARE metadata
2. **Processing Layer**: NLP modules for analysis
3. **Vector Store**: ChromaDB for semantic search
4. **LLM Layer**: Ollama (local Llama 3.2)
5. **UI Layer**: Streamlit web interface
6. **Export Layer**: Report generation (Markdown, PDF)

---

## Hugging Face Models - Enhancement Opportunities

### Immediate Impact (Recommended for Course Project)

#### 1. Enhanced Sentiment Analysis
- **Model**: `cardiffnlp/twitter-roberta-base-sentiment-latest`
- **Improvement**: +17% accuracy over TextBlob
- **Benefit**: Better understanding of student feedback
- **Implementation Time**: 2-3 hours
- **See**: `HUGGINGFACE_QUICK_START.md`

#### 2. Zero-Shot Classification
- **Model**: `facebook/bart-large-mnli`
- **Use Case**: Automatically categorize responses by topic
- **Benefit**: Organize feedback without manual labeling
- **Example**: Classify into "study spaces", "hours", "resources", "staff"

#### 3. Better Embeddings
- **Model**: `BAAI/bge-base-en-v1.5`
- **Improvement**: +15% retrieval accuracy
- **Benefit**: More relevant RAG responses
- **Dimensions**: 768 (vs. current 384)

### Advanced Enhancements

#### 4. Named Entity Recognition
- **Model**: `dslim/bert-base-NER`
- **Benefit**: Better PII detection beyond regex
- **Entities**: Person, Organization, Location

#### 5. Topic Modeling
- **Library**: BERTopic with `all-mpnet-base-v2`
- **Improvement**: +35% topic coherence
- **Features**: Automatic topic naming, hierarchical topics

#### 6. Summarization
- **Model**: `facebook/bart-large-cnn`
- **Use Case**: Summarize long survey responses
- **Benefit**: Handle longer documents efficiently

#### 7. Extractive QA
- **Model**: `deepset/roberta-base-squad2`
- **Use Case**: Fast factual question answering
- **Benefit**: Complement generative QA with extraction

### Complete Details
See `NLP_TECHNIQUES_AND_MODELS.md` for:
- Detailed model comparisons
- Implementation guides
- Performance benchmarks
- Integration examples

---

## Key Features for Course Documentation

### 1. Multi-Source Data Integration
- Combines surveys, usage stats, circulation data
- Unified querying across datasets
- Cross-dataset analysis and insights

### 2. Human-in-the-Loop Design
- AI augments, doesn't replace human judgment
- Provides interpretations and recommendations
- Users make final decisions

### 3. Privacy-First Architecture
- All processing happens locally (no external APIs)
- FERPA-conscious design consideration
- PII detection and redaction
- Audit logging for accountability

### 4. FAIR and CARE Principles
- **Findable**: Rich metadata, unique IDs, keywords
- **Accessible**: Export capabilities, authentication
- **Interoperable**: Standard formats (CSV, JSON)
- **Reusable**: Complete provenance tracking
- **Collective Benefit**: Improves library services
- **Authority to Control**: User controls data lifecycle
- **Responsibility**: Audit logs, ethical guidelines
- **Ethics**: Privacy by design, no external transmission

### 5. Comprehensive Analysis Pipeline
- Qualitative: Sentiment, themes, quotes
- Quantitative: Statistics, correlations, trends
- Visualization: Interactive charts
- Reporting: Automated report generation

---

## Technical Stack

### Core Technologies
- **Language**: Python 3.9+
- **Web Framework**: Streamlit
- **Database**: SQLite
- **Vector Store**: ChromaDB
- **LLM Runtime**: Ollama

### NLP Libraries
- **Transformers**: Hugging Face transformers
- **Embeddings**: Sentence-Transformers
- **Text Processing**: NLTK, TextBlob
- **ML**: scikit-learn (clustering, TF-IDF)
- **Statistics**: scipy, numpy, pandas

### Visualization
- **Charts**: Plotly
- **Reports**: Markdown, reportlab (PDF)

---

## Evaluation Metrics

### NLP Performance
- **Sentiment Analysis**: Accuracy, precision, recall, F1-score
- **Topic Coherence**: Coherence score, topic diversity
- **RAG Quality**: Retrieval accuracy, answer relevance, citation accuracy
- **Embedding Quality**: Retrieval@K, MRR (Mean Reciprocal Rank)

### System Performance
- **Response Time**: Query latency, analysis time
- **Throughput**: Queries per second, batch processing speed
- **Resource Usage**: Memory, CPU, disk space

### User Experience
- **Usability**: Task completion rate, time on task
- **Accuracy**: User satisfaction with results
- **Trust**: Citation usage, result verification

---

## Comparison with Alternatives

### Why Local LLM (Llama) vs. Cloud APIs (OpenAI)?
- **Privacy**: Data never leaves institution (FERPA requirement)
- **Cost**: No per-query fees
- **Control**: Full control over model and data
- **Offline**: Works without internet
- **Trade-off**: Smaller model, slightly lower quality

### Why RAG vs. Fine-Tuning?
- **No Training Data**: RAG works with existing documents
- **Up-to-Date**: New data immediately available
- **Explainable**: Citations show data sources
- **Flexible**: Easy to add/remove data
- **Trade-off**: Requires good retrieval

### Why Sentence-BERT vs. Word2Vec?
- **Context**: Sentence-level embeddings capture meaning
- **Quality**: Better semantic similarity
- **Pre-trained**: No training needed
- **Modern**: State-of-the-art approach
- **Trade-off**: Larger model size

---

## Learning Outcomes Demonstrated

### NLP Concepts
1. Text preprocessing and normalization
2. Feature extraction (TF-IDF, embeddings)
3. Sentiment analysis (lexicon and ML-based)
4. Topic modeling and clustering
5. Semantic similarity and vector search
6. Text generation and summarization
7. Named entity recognition
8. Retrieval-augmented generation

### Machine Learning
1. Supervised learning (classification)
2. Unsupervised learning (clustering)
3. Transfer learning (pre-trained models)
4. Model evaluation and comparison
5. Hyperparameter tuning
6. Batch processing and optimization

### Software Engineering
1. Modular architecture design
2. Database design and management
3. API integration (Ollama, Hugging Face)
4. Error handling and validation
5. Testing and quality assurance
6. Documentation and code organization

### Data Science
1. Exploratory data analysis
2. Statistical testing
3. Data visualization
4. Report generation
5. Reproducibility and provenance

---

## Future Enhancements

### Short-Term (1-2 weeks)
1. Implement RoBERTa sentiment analysis
2. Add zero-shot classification
3. Enhance PII detection with NER
4. Improve error handling

### Medium-Term (1-2 months)
1. Upgrade to BGE embeddings
2. Implement BERTopic for themes
3. Add document summarization
4. Create evaluation framework

### Long-Term (3-6 months)
1. Multilingual support
2. Dynamic topic modeling (track changes over time)
3. Advanced visualizations (network graphs, word clouds)
4. Mobile-responsive UI
5. Batch processing API

---

## How to Document for Course Report

### 1. Introduction
- Problem statement: Library assessment challenges
- Solution: AI-powered decision support system
- Approach: Multi-source integration with human-in-the-loop

### 2. Methodology
- Data collection and preprocessing
- NLP techniques applied (list from this document)
- Statistical methods used
- System architecture

### 3. Implementation
- Technology stack
- Key algorithms (with code snippets)
- Challenges and solutions
- Design decisions and trade-offs

### 4. Evaluation
- Performance metrics
- Comparison with baselines (TextBlob vs. RoBERTa)
- User testing results
- Limitations and edge cases

### 5. Results
- System capabilities demonstrated
- Example analyses and insights
- Visualizations and reports generated
- Impact on library assessment process

### 6. Discussion
- Strengths and weaknesses
- Comparison with existing solutions
- Ethical considerations (privacy, bias)
- Lessons learned

### 7. Future Work
- Hugging Face model enhancements
- Additional features
- Scalability improvements
- Research directions

### 8. Conclusion
- Summary of contributions
- Key takeaways
- Broader impact

---

## Key Talking Points for Presentation

1. **Multi-Source Integration**: Combines diverse data types for comprehensive insights
2. **Privacy-First**: Local processing ensures privacy-conscious governance
3. **Human-in-the-Loop**: AI augments human decision-making
4. **State-of-the-Art NLP**: RAG, embeddings, LLMs
5. **Practical Impact**: Real-world application for libraries
6. **Extensible**: Easy to add Hugging Face models
7. **Open Source**: Built with open-source tools
8. **Ethical Design**: FAIR and CARE principles

---

## Resources

### Documentation Files
- `NLP_TECHNIQUES_AND_MODELS.md`: Complete NLP guide
- `HUGGINGFACE_QUICK_START.md`: Quick implementation guide
- `README.md`: System overview and setup
- `ARCHITECTURE.md`: Technical architecture
- `USER_GUIDE.md`: User documentation

### Code Organization
- `modules/`: Core NLP and analysis modules
- `streamlit_app.py`: Web interface
- `tests/`: Unit and integration tests
- `examples/`: Usage examples

### External Resources
- [Hugging Face Model Hub](https://huggingface.co/models)
- [Sentence-BERT Documentation](https://www.sbert.net/)
- [Ollama Documentation](https://ollama.ai/)
- [RAG Tutorial](https://www.pinecone.io/learn/retrieval-augmented-generation/)

---

## Quick Start for Demo

1. **Start Ollama**: `ollama serve`
2. **Pull Model**: `ollama pull llama3.2:3b`
3. **Run App**: `streamlit run streamlit_app.py`
4. **Upload Data**: Use sample data in `test_data/`
5. **Try Features**:
   - Query Interface: Ask questions
   - Qualitative Analysis: Analyze sentiment and themes
   - Quantitative Analysis: Run statistical tests
   - Report Generation: Create comprehensive reports

---

## Authentication Note

**For Development/Demo**: Authentication has been disabled. The app auto-logs in with a demo user.

**For Production**: Re-enable authentication by modifying `main()` function in `streamlit_app.py`:
```python
def main():
    auth.init_session_state(st.session_state)
    
    if auth.is_authenticated(st.session_state):
        show_main_app()
    else:
        show_login_page()
```

---

## Contact and Support

For questions about implementation or course project documentation, refer to:
- Code comments in modules
- Docstrings in functions
- README files in each directory
- This summary document

Good luck with your course project!
