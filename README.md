# Library Assessment Decision Support System

An AI-augmented assessment tool for library professionals that combines quantitative and qualitative analysis with natural language querying. All processing happens locally via Ollama for complete data privacy and FERPA compliance.

## Core Features

- Multi-source data integration (surveys, usage statistics, circulation data)
- Natural language queries across datasets with citations
- Quantitative analysis (correlation, trends, comparisons, distributions)
- Qualitative analysis (sentiment, theme identification)
- Report generation with visualizations
- PII detection and redaction
- FAIR and CARE metadata support
- Human-in-the-loop design

## System Requirements

- Python 3.10+
- RAM: 16GB minimum
- Storage: 50GB
- CPU: 4 cores minimum
- Ollama (local LLM server)

## Quick Start

### 1. Install Ollama and Model

```bash
# Install Ollama from https://ollama.ai
ollama pull llama3.2:3b
```

### 2. Setup Application

```bash
git clone <repository-url>
cd <repository-name>
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m textblob.download_corpora
python scripts/init_app.py
```

### 3. Run

```bash
streamlit run streamlit_app.py
```

Default credentials: `admin` / `admin123` (change immediately after first login)

## Project Structure

```
streamlit_app.py          # Main application orchestrator
ui/                       # User interface modules
├── auth_ui.py           # Login/logout interface
├── home_ui.py           # Dashboard and system status
├── data_upload_ui.py    # CSV upload interface
├── query_ui.py          # RAG chat interface
├── qualitative_ui.py    # Qualitative analysis interface
├── quantitative_ui.py   # Quantitative analysis interface
├── visualization_ui.py  # Chart generation interface
├── report_ui.py         # Report generation interface
├── governance_ui.py     # FAIR/CARE documentation
└── logs_ui.py           # Logs and monitoring
modules/                  # Core business logic
├── auth.py              # Authentication
├── csv_handler.py       # Data upload and validation
├── database.py          # Data storage
├── rag_query.py         # Query engine
├── rag_evaluation.py    # RAG quality metrics
├── qualitative_analysis.py
├── quantitative_analysis.py
├── report_generator.py
├── visualization.py
└── pii_detector.py
config/settings.py        # Configuration
data/                     # Data storage
tests/                    # Test suite
```

## Usage

1. **Upload Data**: Navigate to Data Upload, select CSV file, add metadata
2. **Query**: Ask questions in natural language across all datasets
3. **Analyze**: Run quantitative or qualitative analysis
4. **Report**: Generate comprehensive reports with visualizations
5. **Visualize**: Create accessible charts (WCAG AA compliant)

## CSV Format Requirements

**Survey Responses**: `response_date`, `question`, `response_text`  
**Usage Statistics**: `date`, `metric_name`, `metric_value`  
**Circulation Data**: `checkout_date`, `material_type`, `patron_type`

See USER_GUIDE.md for detailed specifications.

## Security & Compliance

- FERPA compliant (local-only processing)
- PII detection and redaction at multiple layers
- Authentication with rate limiting (5 attempts/60s)
- Cryptographically secure session management
- SQL injection prevention
- Complete audit trail

## System Status

**Production Readiness**: 90% (Phase 1: 9/10 tasks complete)

Recent improvements:
- Ollama crash handling with 30s timeout
- Database-ChromaDB synchronization
- SQLite WAL mode for concurrency
- Enhanced error handling
- Security hardening complete

## Testing

```bash
pytest                              # Run all tests
pytest --cov=modules               # With coverage
pytest tests/unit/                 # Unit tests only
pytest tests/integration/          # Integration tests only
```

Coverage: 75% across critical modules  
Unit tests: 241 tests  
Integration tests: 7 tests

## Troubleshooting

**Ollama Connection Error**
```bash
ollama serve
ollama list
ollama pull llama3.2:3b
```

**Database Locked**
- System uses WAL mode to prevent most locking issues
- If corruption occurs: delete `data/library.db` and run `python scripts/init_app.py`

**Import Errors**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Rate Limiting**
- Wait 60 seconds after 5 failed login attempts

## Backup Strategy

**Critical files**: `data/library.db`, `data/chroma_db/`, `config/settings.py`  
**Frequency**: Daily (database), Weekly (full data directory)  
**Testing**: Quarterly restoration tests

## Development

```bash
black .                    # Format code
ruff check .              # Lint
pytest -v                 # Test with verbose output
```

## Human-in-the-Loop Philosophy

AI augments human expertise rather than replacing it:
- All insights presented as recommendations for review
- Citations and confidence scores provided
- Professional judgment remains central
- Complete audit trail maintained

## Technology Stack

- Local LLM: Ollama with Llama 3.2
- RAG: ChromaDB + sentence-transformers
- Statistics: scipy, statsmodels
- NLP: TextBlob, TF-IDF
- Visualization: Plotly (WCAG AA compliant)
- Framework: Streamlit

## Documentation

- USER_GUIDE.md - Detailed usage instructions
- CHANGELOG.md - Version history and updates
- TESTING.md - Testing procedures
- docs/ - Additional documentation

## License

See LICENSE file for details.
