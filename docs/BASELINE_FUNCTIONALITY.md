# Baseline Functionality Documentation

> Historical note: this file captures the pre-refactor baseline from 2026-04-13.
> It intentionally mentions legacy FastAPI/code-organization issues that have
> since been cleaned up. Use `README.md` and `docs/DEPENDENCY_STRATEGY.md` for
> current runtime guidance.

**Date:** 2026-04-13
**Branch:** refactor/library-assessment-repo-cleanup
**Purpose:** Document baseline functionality before refactoring

## Application Status

**Python Version:** 3.14.3
**Git Branch:** refactor/library-assessment-repo-cleanup (newly created)
**Working Directory:** Clean

## Core Features (Pre-Refactoring)

### 1. Authentication
- Login page with username/password
- Session management via Streamlit session state
- Rate limiting (5 attempts/60s)
- Audit logging

### 2. Data Upload
- CSV file upload with validation
- Support for survey, usage, and circulation data types
- FAIR/CARE metadata collection
- Duplicate detection via file hash
- Dataset management (view, edit, delete, export)

### 3. Ask
- RAG-powered natural language queries
- ChromaDB vector store for document retrieval
- Ollama LLM integration for answer generation
- Conversation context management
- PII redaction on outputs
- Citation tracking

### 4. Qualitative Analysis
- Sentiment analysis using TextBlob
- Theme extraction using TF-IDF + K-means
- Representative quote identification
- Analysis result storage and export

### 5. Quantitative Analysis
- Correlation analysis (Pearson, Spearman, Kendall)
- Trend analysis with forecasting
- Comparative analysis (t-tests, ANOVA)
- Distribution analysis with outlier detection
- LLM-powered interpretations

### 6. Visualization
- Bar charts, line charts, pie charts
- WCAG AA compliant color palette
- Export to PNG/HTML

### 7. Report Generation
- Statistical summaries
- LLM-generated narratives
- Visualization embedding
- Export to PDF/Markdown

### 8. Data Governance
- FAIR principles documentation
- CARE principles documentation
- Data provenance tracking

### 9. Logs & Monitoring
- Access logs
- Query logs
- System status monitoring

## Known Issues

### Identity Drift
- pyproject.toml identifies project as "sentiment-analysis"
- README.md describes Library Assessment Decision Support System
- Mixed dependencies (Streamlit + FastAPI)
- Legacy FastAPI code in src/ directory

### Code Organization
- streamlit_app.py is 3042 lines (monolithic)
- No modular UI structure
- Difficult to maintain and test

### Testing Gaps
- No property-based tests for CSV round-trip
- No RAG retrieval quality evaluation
- Limited UI testing

## Dependencies (Current)

### From requirements.txt:
- streamlit>=1.31.0
- chromadb>=0.4.22
- sentence-transformers>=2.3.1
- textblob>=0.17.1
- scikit-learn>=1.6.1
- transformers>=4.36.0
- torch>=2.1.0
- ollama>=0.1.6
- pandas>=2.2.3
- numpy>=2.1.3
- scipy>=1.11.0
- statsmodels>=0.14.0
- plotly>=5.18.0
- kaleido>=0.2.1
- reportlab>=4.0.9
- markdown>=3.5.2
- bcrypt>=4.1.2
- pytest>=8.0.0
- pytest-cov>=4.1.0
- hypothesis>=6.98.3
- black>=24.1.1
- ruff>=0.2.1

### From pyproject.toml (legacy):
- fastapi>=0.104.1
- uvicorn[standard]>=0.24.0
- pydantic>=2.5.0
- transformers>=4.57.0
- torch>=2.9.0
- python-dotenv>=1.0.0
- python-multipart>=0.0.6

## Refactoring Goals

1. Remove legacy FastAPI code
2. Modularize streamlit_app.py into 10 UI modules
3. Align metadata and dependencies
4. Add RAG retrieval quality evaluation
5. Add CSV round-trip validation with property tests
6. Update documentation
7. Achieve 80% test coverage

## Verification Checklist

Before refactoring:
- [x] Git branch created
- [x] Python version verified (3.14.3)
- [x] Baseline documentation created
- [ ] Application runs successfully (requires dependencies)
- [ ] Core features tested manually

Note: Full application testing requires installing dependencies, which will be done after metadata alignment.
