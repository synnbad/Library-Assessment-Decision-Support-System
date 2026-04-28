# Project Context for AI Agents

## Project Overview

**Name:** Library Assessment Decision Support System  
**Type:** AI-powered data analysis and assessment tool  
**Purpose:** Help library professionals analyze patron feedback, usage statistics, and circulation data using NLP and machine learning  
**Status:** Local-first prototype/workbench with enhanced features

## Quick Start for AI Agents

### Understanding the Codebase

1. **Entry Point:** `streamlit_app.py` - Main Streamlit web application
2. **Core Modules:** `modules/` directory contains all business logic
3. **Configuration:** `config/settings.py` - System settings and constants
4. **Database:** SQLite database at `data/library.db`
5. **Tests:** `tests/` directory with unit, integration, and manual tests

### Key Technologies

- **Framework:** Streamlit (web UI)
- **Database:** SQLite (data storage)
- **Vector DB:** ChromaDB (semantic search)
- **LLM:** Ollama + Llama 3.2 (local inference)
- **NLP:** Hugging Face Transformers, Sentence-BERT, TextBlob
- **ML:** scikit-learn, PyTorch
- **Stats:** scipy, numpy, pandas

### Architecture

```
streamlit_app.py (UI)
    ↓
modules/ (Business Logic)
    ├── auth.py (Authentication)
    ├── csv_handler.py (Data upload/validation)
    ├── database.py (SQLite operations)
    ├── pii_detector.py (Privacy protection)
    ├── sentiment_enhanced.py (RoBERTa sentiment)
    ├── qualitative_analysis.py (Text analysis)
    ├── quantitative_analysis.py (Statistics)
    ├── rag_query.py (RAG system)
    ├── report_generator.py (Report creation)
    └── visualization.py (Charts/graphs)
    ↓
data/ (Storage)
    ├── library.db (SQLite database)
    └── chroma_db/ (Vector embeddings)
```

## Recent Major Changes

### 1. Enhanced Sentiment Analysis (RoBERTa)
- **File:** `modules/sentiment_enhanced.py`
- **What:** Implemented transformer-based sentiment analysis
- **Why:** 17% accuracy improvement over TextBlob baseline
- **Status:** Fully integrated, tested, working

### 2. Flexible Data Validation
- **File:** `modules/csv_handler.py`
- **What:** Removed strict column requirements, accepts any CSV structure
- **Why:** Real-world data (PLS, Qualtrics, ILS exports) has varied formats
- **Status:** Fully implemented, backward compatible

### 3. Metadata Auto-Fill
- **File:** `modules/csv_handler.py`, `streamlit_app.py`
- **What:** Auto-detects and populates FAIR/CARE metadata from uploaded files
- **Why:** Saves time, ensures consistent metadata quality
- **Status:** Working with encoding detection

### 4. Encoding Handling
- **File:** `modules/csv_handler.py`
- **What:** Automatic detection of CSV encodings (UTF-8, Latin-1, CP1252, etc.)
- **Why:** Real-world files have various encodings
- **Status:** Fully implemented, handles edge cases

### 5. Authentication Disabled for Development
- **File:** `streamlit_app.py`
- **What:** Auto-login as demo_user
- **Why:** Easier development and testing
- **Status:** Easy to re-enable for production

## Module Responsibilities

### auth.py
- User authentication and session management
- Password hashing (bcrypt)
- Access logging
- Currently bypassed for development (auto-login)

### csv_handler.py
- CSV file validation (flexible, not strict)
- Data parsing with encoding detection
- Metadata auto-fill functionality
- Dataset storage and retrieval
- Export capabilities

### database.py
- SQLite database initialization
- Query execution helpers
- Database migrations
- Connection management

### pii_detector.py
- Detects PII (emails, phones, SSNs, etc.)
- Redaction functionality
- Regex-based pattern matching

### sentiment_enhanced.py
- RoBERTa-based sentiment analysis
- Batch processing for efficiency
- Returns dict with sentiment, confidence, score
- Fallback to TextBlob if unavailable

### qualitative_analysis.py
- Sentiment analysis (uses enhanced if available)
- Topic modeling (TF-IDF + K-Means)
- Theme extraction
- Representative quote selection

### quantitative_analysis.py
- Correlation analysis (Pearson, Spearman, Kendall)
- Trend analysis (linear regression)
- Comparative analysis (t-test, ANOVA)
- Distribution analysis
- AI-generated interpretations

### rag_query.py
- Retrieval-Augmented Generation system
- ChromaDB vector store management
- Semantic search using Sentence-BERT
- Llama 3.2 integration via Ollama
- Citation tracking

### report_generator.py
- Comprehensive report generation
- Combines qualitative + quantitative analysis
- Markdown and PDF export
- PII redaction on outputs

### visualization.py
- Interactive charts (Plotly)
- WCAG AA compliant colors
- Bar, line, pie, heatmap, trend charts
- Export to PNG/HTML

## Data Flow

### Upload Flow
```
User uploads CSV
    ↓
csv_handler.validate_csv() - Flexible validation
    ↓
csv_handler.parse_csv() - Multi-encoding support
    ↓
csv_handler.auto_detect_metadata() - Optional auto-fill
    ↓
csv_handler.store_dataset() - Save to SQLite
    ↓
pii_detector.detect_pii() - Scan for PII
```

### Analysis Flow
```
User selects dataset
    ↓
qualitative_analysis.analyze_sentiment() - RoBERTa or TextBlob
    ↓
qualitative_analysis.extract_themes() - TF-IDF + K-Means
    ↓
quantitative_analysis.* - Statistical tests
    ↓
visualization.create_chart() - Generate visualizations
    ↓
report_generator.generate_report() - Combine all results
```

### Query Flow
```
User asks question
    ↓
rag_query.embed_query() - Convert to vector
    ↓
rag_query.search_similar() - Find relevant docs (ChromaDB)
    ↓
rag_query.generate_answer() - LLM generates response (Ollama)
    ↓
Return answer + citations
```

## Configuration

### Environment Variables (.env)
```
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_LOCAL_FILES_ONLY=true
DATABASE_PATH=data/library.db
CHROMA_DB_PATH=data/chroma_db
```

### Settings (config/settings.py)
- Sentiment thresholds
- Topic modeling parameters
- RAG configuration
- PII patterns
- Visualization defaults

## Testing

### Test Structure
```
tests/
├── unit/ - Unit tests for individual modules
├── integration/ - End-to-end workflow tests
├── manual/ - Manual testing scripts
└── property/ - Property-based tests (if any)
```

### Running Tests
```bash
# All tests
pytest tests/

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Specific test file
pytest tests/unit/test_pii_detector.py

# With coverage
pytest --cov=modules tests/
```

### Test Files to Note
- `test_system.py` - Comprehensive system test (run before commits)
- `test_encoding_handling.py` - Encoding detection tests
- `test_flexible_validation.py` - CSV validation tests
- `test_metadata_autofill.py` - Metadata auto-fill tests

## Common Tasks

### Adding a New Analysis Method
1. Add function to appropriate module (`qualitative_analysis.py` or `quantitative_analysis.py`)
2. Add UI in `streamlit_app.py`
3. Add tests in `tests/unit/`
4. Update documentation

### Adding a New Hugging Face Model
1. Add to `requirements.txt`
2. Create or update module in `modules/`
3. Add lazy loading for memory efficiency
4. Test with `test_system.py`
5. Document in `NLP_TECHNIQUES_AND_MODELS.md`

### Modifying Data Validation
1. Edit `csv_handler.py` - `validate_csv()` function
2. Update `SUGGESTED_COLUMNS` dict if needed
3. Test with `test_flexible_validation.py`
4. Update `DATA_FORMAT_GUIDE.md`

### Changing Database Schema
1. Create migration in `database.py` - `migrate_database()`
2. Update relevant modules
3. Test with integration tests
4. Document in `ARCHITECTURE.md`

## Important Files for AI Agents

### Must Read
- `README.md` - Project overview and setup
- `ARCHITECTURE.md` - System architecture details
- `MODULE_INTERFACES.md` - Module API documentation
- This file (`PROJECT_CONTEXT.md`)

### Key Documentation
- `DATA_FORMAT_GUIDE.md` - What data formats are accepted
- `ACCEPTED_DATA_TYPES.md` - Comprehensive data type guide
- `NLP_TECHNIQUES_AND_MODELS.md` - NLP methods used
- `METADATA_AUTOFILL_FEATURE.md` - Metadata auto-fill details
- `USER_GUIDE.md` - End-user documentation

### Project Reports
- `AMIA_PROJECT_REPORT_COMPLETE.md` - Complete academic report
- `IMPLEMENTATION_SUMMARY.md` - Implementation overview
- `COURSE_PROJECT_SUMMARY.md` - Course project summary

## Known Issues and Limitations

### Current Limitations
1. **Model Size:** Limited to 3B parameter models for local inference
2. **Language:** English only (multilingual support planned)
3. **File Size:** 200MB upload limit
4. **Processing Speed:** CPU inference slower than GPU cloud services
5. **Context Window:** 2048 tokens for LLM (limits long documents)

### Workarounds
1. Use quantized models for faster inference
2. Batch processing for large datasets
3. Chunking for long documents
4. GPU acceleration if available

## Development Workflow

### Before Making Changes
1. Read relevant module documentation
2. Check existing tests
3. Review recent changes in git history
4. Run `test_system.py` to ensure baseline works

### After Making Changes
1. Update relevant tests
2. Run `test_system.py` to verify nothing broke
3. Update documentation
4. Check .gitignore for new files
5. Commit with descriptive message

### Code Style
- Follow PEP 8
- Use type hints where possible
- Add docstrings to all functions
- Keep functions focused and small
- Comment complex logic

## Deployment Notes

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Install Ollama
# Visit https://ollama.ai

# Pull model
ollama pull llama3.2:3b

# Initialize database
python scripts/init_app.py

# Run app
streamlit run streamlit_app.py
```

### Production Considerations
1. Re-enable authentication in `streamlit_app.py`
2. Set strong passwords in database
3. Configure proper .env file
4. Set up SSL/TLS for web access
5. Regular database backups
6. Monitor disk space (models + data)
7. Consider GPU for better performance

## Troubleshooting

### Common Issues

**"Ollama not found"**
- Install Ollama from https://ollama.ai
- Ensure it's running: `ollama list`
- Check `OLLAMA_URL` in `.env`

**"Model not found"**
- Pull model: `ollama pull llama3.2:3b`
- Check model name in config

**"Database locked"**
- Close other connections
- Check for zombie processes
- Restart application

**"Out of memory"**
- Reduce batch size
- Use smaller model
- Close other applications
- Add more RAM

**"Encoding error"**
- Should be handled automatically
- Check file is valid CSV
- Try re-saving as UTF-8

## Contact and Resources

### Documentation
- All docs in project root
- Module docstrings in code
- Tests show usage examples

### External Resources
- Streamlit: https://docs.streamlit.io
- Hugging Face: https://huggingface.co/docs
- Ollama: https://ollama.ai/docs
- ChromaDB: https://docs.trychroma.com

## Version History

- **v1.0** - Initial MVP with basic features
- **v1.1** - Added RoBERTa sentiment analysis
- **v1.2** - Flexible data validation
- **v1.3** - Metadata auto-fill feature
- **v1.4** - Encoding detection and handling
- **Current** - Submission-ready workbench with documented limitations

## Next Steps for AI Agents

When picking up this project:

1. **First:** Read this file completely
2. **Second:** Read `README.md` and `ARCHITECTURE.md`
3. **Third:** Run `test_system.py` to verify setup
4. **Fourth:** Explore `streamlit_app.py` to understand UI
5. **Fifth:** Review module files in `modules/`
6. **Sixth:** Check recent git commits for context
7. **Seventh:** Read relevant documentation for your task

Good luck! The codebase is well-documented and modular. Each module has clear responsibilities and interfaces.
