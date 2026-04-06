# Library Assessment Decision Support System

An AI-augmented assessment tool that helps library professionals analyze patron feedback, usage patterns, and service effectiveness through a **human-in-the-loop** approach. The system combines quantitative and qualitative analysis with natural language querying to support data-driven decision-making while keeping humans at the center of the assessment process.

## Overview

This system is designed to **augment, not replace** human expertise in library assessment. It provides:

- **Multi-Source Data Integration**: Combine survey responses, usage statistics, circulation data, and other sources for comprehensive analysis
- **Cross-Dataset Insights**: Identify patterns and relationships across different data sources
- **Intelligent Analysis**: AI-powered insights that synthesize information from multiple datasets
- **Natural Language Interaction**: Ask questions that span multiple data sources and get unified, contextual answers
- **Human-Centered Workflow**: All AI-generated insights are presented as recommendations for human review and validation
- **Transparent Reasoning**: Every answer includes citations and confidence scores so you can verify the analysis
- **Local Processing**: Complete data privacy with no external API calls - your data never leaves your infrastructure

## Key Features

### Multi-Source Data Integration
- **Flexible Data Upload**: Import data from multiple sources - survey responses, usage statistics, circulation records, and more
- **Cross-Dataset Analysis**: Correlate patterns across different data sources (e.g., link satisfaction scores with usage trends)
- **Unified Querying**: Ask questions that span multiple datasets and get synthesized answers
- **Relationship Discovery**: Automatically identify connections between different data sources
- **Temporal Integration**: Analyze how different metrics evolve together over time

### Analysis Capabilities
- **Quantitative Analysis**: Correlation analysis, trend forecasting, comparative statistics, and distribution analysis with LLM-powered interpretations
- **Qualitative Analysis**: Automated sentiment analysis and theme identification from open-ended survey responses
- **RAG-Powered Queries**: Ask questions in natural language and get answers grounded in your actual data with citations
- **Statistical Insights**: Advanced statistical methods with plain-language explanations for non-technical stakeholders
- **Cross-Source Synthesis**: Generate insights that combine quantitative metrics with qualitative feedback

### Human-in-the-Loop Design
- **Review & Validate**: All AI-generated insights are presented for human review before action
- **Contextual Recommendations**: Actionable suggestions based on your data, not generic advice
- **Audit Trail**: Complete logging of all analyses and queries for transparency and accountability
- **Expert Augmentation**: Designed to enhance librarian expertise, not replace professional judgment

### Data Management & Visualization
- **Flexible Data Upload**: Support for any CSV format - no column restructuring required! Works with Qualtrics, ILS exports, PLS data, and custom formats
- **Auto-Fill Metadata**: Automatically detect and populate FAIR/CARE metadata fields from uploaded datasets
- **Interactive Visualizations**: Create accessible charts (bar, line, pie, heatmaps, trend charts) with WCAG AA compliant colors
- **Comprehensive Reports**: Generate reports combining statistics, narrative insights, and visualizations
- **FAIR & CARE Metadata**: Rich metadata support for responsible data governance

### Privacy & Compliance Features
- **FERPA Compliant**: All processing happens locally via Ollama - no external API calls or cloud services
- **PII Detection & Redaction**: Automatic detection and redaction of personally identifiable information
- **Local-Only Processing**: Your data stays on your infrastructure at all times
- **FAIR Principles**: Findable, Accessible, Interoperable, and Reusable data practices
- **CARE Principles**: Collective benefit, Authority to control, Responsibility, and Ethics in data governance

## System Requirements

- **Python**: 3.10 or higher
- **RAM**: 16GB minimum (8GB for LLM, 8GB for application)
- **Storage**: 50GB (20GB for models, 30GB for data)
- **CPU**: 4 cores minimum
- **GPU**: Optional but recommended for faster LLM inference
- **Ollama**: Must be installed and running locally

## Quick Start

### 1. Install Ollama

Follow instructions at [https://ollama.ai](https://ollama.ai) to install Ollama for your operating system.

### 2. Download LLM Model

```bash
# Download Llama 3.2 3B (recommended for MVP)
ollama pull llama3.2:3b

# Alternative: Phi-3 Mini
ollama pull phi3:mini
```

### 3. Clone Repository

```bash
git clone <repository-url>
cd <repository-name>
```

### 4. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt

# Download NLTK data for TextBlob
python -m textblob.download_corpora
```

### 6. Initialize Application

```bash
# Initialize database and create default admin user
python scripts/init_app.py
```

This will:
- Create the SQLite database with all required tables
- Create a default admin user (username: `admin`, password: `admin123`)
-  **Important**: Change the default password after first login!

### 7. Run Application

```bash
streamlit run streamlit_app.py
```

The application will open in your browser at `http://localhost:8501`

## Project Structure

```
.
├── streamlit_app.py          # Main Streamlit application
├── modules/                   # Core Python modules
│   ├── auth.py               # Authentication
│   ├── csv_handler.py        # CSV upload and validation
│   ├── database.py           # Multi-source data storage
│   ├── rag_query.py          # Cross-dataset RAG query engine
│   ├── qualitative_analysis.py  # Sentiment and theme analysis
│   ├── quantitative_analysis.py # Statistical analysis with LLM interpretations
│   ├── report_generator.py  # Multi-source report generation
│   ├── visualization.py      # Chart generation
│   └── pii_detector.py       # PII detection and redaction
├── config/                    # Configuration
│   └── settings.py           # System settings
├── data/                      # Data storage
│   ├── library.db            # SQLite database
│   └── chroma_db/            # ChromaDB vector store
├── tests/                     # Test suite
│   ├── unit/                 # Unit tests
│   ├── property/             # Property-based tests
│   └── integration/          # Integration tests
├── requirements.txt           # Python dependencies
└── README.md                 # This file
```

## Usage Workflow

The system follows a human-centered assessment workflow:

### 1. Login & Authentication

Use the credentials you created during setup. The system maintains an audit trail of all access for accountability.

### 2. Upload & Curate Data

- Navigate to "Data Upload" page
- Select dataset type (survey, usage, circulation)
- Upload CSV file with your library data
- Add FAIR/CARE metadata (title, description, source, ethical considerations)
- Review automated PII detection warnings
- Preview and confirm upload

### 3. Explore with Natural Language Queries

- Navigate to "Query Interface" page
- Ask questions about your data in plain English, including cross-dataset queries:
  - "What are the main themes in patron feedback?"
  - "How has circulation changed over the past year?"
  - "Which services have the highest satisfaction scores?"
  - "Is there a correlation between program attendance and satisfaction ratings?"
  - "How do usage patterns differ across branches?"
- Review answers with citations to verify against source data
- Ask follow-up questions (conversation context is maintained)
- Validate AI responses against your domain expertise
- Query across multiple datasets simultaneously for comprehensive insights

### 4. Perform Quantitative Analysis

- Navigate to "Quantitative Analysis" page
- Select analysis type:
  - **Correlation**: Identify relationships between metrics
  - **Trend**: Analyze patterns over time with forecasting
  - **Comparative**: Compare performance across branches, time periods, or categories
  - **Distribution**: Detect outliers and analyze data distributions
- Review statistical results and LLM-generated interpretations
- Validate recommendations against operational context
- Export results for further analysis

### 5. Analyze Qualitative Feedback

- Navigate to "Qualitative Analysis" page
- Select dataset with text responses (surveys, comments)
- Review automated sentiment analysis
- Explore identified themes and representative quotes
- Validate theme accuracy and relevance
- Export analysis results

### 6. Generate Assessment Reports

- Navigate to "Report Generation" page
- Select multiple datasets and analyses to include
- Choose report components (statistics, visualizations, qualitative insights, quantitative analysis)
- System automatically synthesizes insights across data sources
- Preview AI-generated narrative sections that integrate findings
- Edit and refine report content based on your expertise
- Export as PDF or Markdown for stakeholder distribution

### 7. Create Custom Visualizations

- Navigate to "Visualization" page
- Select dataset and chart type
- Choose columns and configure display options
- Review accessibility compliance (WCAG AA)
- Export charts for presentations or reports

## CSV Format Requirements

### Survey Responses
Required columns: `response_date`, `question`, `response_text`

### Usage Statistics
Required columns: `date`, `metric_name`, `metric_value`

### Circulation Data
Required columns: `checkout_date`, `material_type`, `patron_type`

See USER_GUIDE.md for detailed format specifications.

## Multi-Source Integration Examples

The system is designed to integrate and analyze data from multiple sources simultaneously:

### Example 1: Satisfaction + Usage Correlation
- Upload survey data with satisfaction scores
- Upload usage statistics with visit counts
- Run correlation analysis to identify if satisfaction correlates with usage
- Generate insights: "Higher satisfaction scores are associated with increased program attendance"

### Example 2: Cross-Branch Comparison
- Upload circulation data from multiple branches
- Upload survey responses by branch
- Compare performance across locations
- Identify best practices: "Branch A has higher satisfaction - what are they doing differently?"

### Example 3: Temporal Pattern Analysis
- Upload monthly usage statistics over 2 years
- Upload quarterly survey responses
- Analyze trends across both datasets
- Forecast future needs: "Usage is increasing but satisfaction is declining - capacity issue?"

### Example 4: Service Impact Assessment
- Upload pre-program and post-program survey data
- Upload usage statistics before and after service changes
- Perform comparative analysis
- Measure impact: "New hours increased usage by 25% and satisfaction by 15%"

### Example 5: Comprehensive Assessment
- Combine survey responses, circulation data, program attendance, and digital resource usage
- Ask: "What factors most influence patron satisfaction?"
- System analyzes correlations across all datasets
- Generate holistic recommendations based on multi-source insights

The RAG query engine automatically searches across all uploaded datasets to provide comprehensive answers grounded in your complete data landscape.

## Data Privacy & Compliance

### FERPA Compliance
- **Local Processing Only**: All AI/LLM processing happens on your local infrastructure via Ollama
- **No External APIs**: Zero external API calls - your data never leaves your control
- **PII Protection**: Automatic detection and redaction of personally identifiable information
- **Audit Logging**: Complete audit trail of all data access and analysis operations

### FAIR Data Principles
- **Findable**: Rich metadata fields, searchable datasets, data manifest generation
- **Accessible**: Multiple export formats (CSV, JSON, PDF, Markdown), clear documentation
- **Interoperable**: Standard formats, documented schema, API-ready structure
- **Reusable**: Provenance tracking, usage notes, source attribution, clear licensing

### CARE Data Principles
- **Collective Benefit**: Usage notes document how data serves community interests
- **Authority to Control**: Users maintain complete control over data lifecycle and access
- **Responsibility**: Provenance tracking, ethical considerations documentation, responsible use guidelines
- **Ethics**: Privacy protections, ethical use documentation, transparent AI decision-making

These principles are implemented as **features** to support responsible data governance, not as constraints on functionality.

## Testing

### Test Coverage
- **Unit Tests**: 241 tests covering core functionality
- **Integration Tests**: 7 tests for end-to-end workflows
- **Property-Based Tests**: Planned for data integrity validation
- **Coverage**: ~75% code coverage across critical modules

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=modules --cov-report=html

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run specific test file
pytest tests/unit/test_ollama_crash_handling.py

# Run tests with verbose output
pytest -v
```

### Recent Test Additions (2026-04-06)
- ✅ Ollama crash handling tests (13 tests, all passing)
- ✅ RAG-PII end-to-end tests (7 tests, all passing)
- ✅ Authentication rate limiting tests
- ✅ Secure session ID tests
- ✅ Database-ChromaDB synchronization tests

### Test Categories

**Unit Tests** (`tests/unit/`):
- Authentication and authorization
- CSV validation and error handling
- PII detection and redaction
- Database operations
- RAG query processing
- Ollama crash handling
- Visualization generation

**Integration Tests** (`tests/integration/`):
- End-to-end data upload flow
- RAG query with PII protection
- Report generation workflow
- Multi-dataset analysis
- Session collision resistance

**Manual Tests** (`tests/manual/`):
- UI/UX validation
- Accessibility compliance (WCAG AA)
- Cross-browser compatibility
- Performance under load

## Development

```bash
# Format code
black .

# Lint code
ruff check .

# Type checking (if using mypy)
mypy modules/
```

## System Status & Reliability

### Production Readiness: 90% Complete

**Phase 1 (P0) Critical Security & Data Integrity**: 9/10 tasks complete
- ✅ Database-ChromaDB synchronization
- ✅ SQLite WAL mode for concurrent operations
- ✅ Metadata validation & SQL injection prevention
- ✅ Duplicate column detection
- ✅ ChromaDB indexing status tracking
- ✅ PII redaction in RAG context (defense-in-depth)
- ✅ Authentication rate limiting (5 attempts/60s)
- ✅ Cryptographically secure session IDs
- ✅ Ollama crash handling with 30s timeout
- ⚠️ NULL sentiment handling (minor edge case)

**Recent Improvements** (2026-04-06):
- Fixed Ollama crash handling - application no longer hangs when Ollama is unavailable
- Fixed Plotly visualization colorbar configuration
- Fixed report generation page variable scope issue
- Added comprehensive error handling with user-friendly messages
- All critical security vulnerabilities addressed

### Error Handling & Resilience

The system now includes robust error handling:

**Ollama Connection Issues**:
- Automatic detection of Ollama crashes or unavailability
- 30-second timeout prevents application hangs
- Clear error messages with recovery instructions
- Graceful degradation - system remains functional

**Database Resilience**:
- WAL mode enables concurrent read/write operations
- Automatic retry logic with exponential backoff
- Database-ChromaDB synchronization prevents data inconsistencies

**Security Hardening**:
- Rate limiting prevents brute force attacks
- Cryptographically secure session management
- PII detection at multiple layers (input, context, output)
- SQL injection prevention through parameterized queries

## Troubleshooting

### Ollama Connection Error
**Symptoms**: "Ollama Connection Error" message in query interface

**Solutions**:
1. Ensure Ollama is running: `ollama serve`
2. Check Ollama is accessible: `curl http://localhost:11434`
3. Verify model is available: `ollama list`
4. Pull model if missing: `ollama pull llama3.2:3b`

**Note**: The system now handles Ollama crashes gracefully with clear error messages and recovery instructions.

### ChromaDB Error
**Symptoms**: Vector search errors or indexing failures

**Solutions**:
- Delete `data/chroma_db/` directory and restart application
- ChromaDB will reinitialize automatically
- Check indexing status in dataset management page

### Import Errors
**Symptoms**: Module not found errors

**Solutions**:
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`
- Verify Python version: `python --version` (3.10+ required)

### Database Errors
**Symptoms**: "Database is locked" or corruption errors

**Solutions**:
- System now uses WAL mode to prevent most locking issues
- If corruption occurs, delete `data/library.db` and reinitialize
- Run: `python scripts/init_app.py`
- Restore from backup if available

### Rate Limiting Lockout
**Symptoms**: "Too many login attempts" message

**Solutions**:
- Wait 60 seconds before retrying
- Verify correct username and password
- Check for caps lock or typing errors
- Contact administrator if account is locked

## Human-in-the-Loop Philosophy

This system is designed around the principle that **AI should augment human expertise, not replace it**:

### AI as Assistant, Not Authority
- All AI-generated insights are presented as **recommendations** for human review
- Statistical interpretations include confidence levels and limitations
- Citations and source data are always provided for verification
- Professional librarian judgment remains central to decision-making

### Transparency & Explainability
- Every AI response includes citations to source data
- Statistical methods and assumptions are clearly explained
- Confidence scores help you assess reliability
- Complete audit trail of all analyses and queries

### Validation Workflow
1. **AI Analyzes**: System processes data and generates insights
2. **Human Reviews**: You examine results, check citations, validate against context
3. **Human Decides**: You make final decisions based on AI insights + your expertise
4. **System Documents**: All decisions and rationale are logged for accountability

### When to Trust AI vs. Human Judgment
- **Trust AI for**: Pattern detection, statistical calculations, large-scale text analysis, citation retrieval
- **Trust Humans for**: Contextual interpretation, policy decisions, stakeholder communication, ethical considerations
- **Best Together**: AI finds patterns, humans determine meaning and action

## Security & Best Practices

### Initial Setup
- ✅ Change default admin password immediately after first login
- ✅ Store database file (`data/library.db`) securely with appropriate file permissions
- ✅ Regularly backup data directory to prevent data loss
- ✅ Review access logs in `access_logs` table periodically

### Operational Security
- ✅ All data processing happens locally - no external API calls
- ✅ PII detection runs automatically on all text inputs and outputs (multi-layer protection)
- ✅ Audit trail captures all data access and analysis operations
- ✅ User authentication required for all system access
- ✅ Rate limiting prevents brute force attacks (5 attempts per 60 seconds)
- ✅ Cryptographically secure session management prevents session hijacking
- ✅ SQL injection prevention through parameterized queries
- ✅ Graceful error handling prevents information leakage

### Data Governance
- Document data sources and provenance in FAIR/CARE metadata
- Review and validate AI-generated insights before acting on them
- Maintain ethical considerations documentation for sensitive datasets
- Follow your institution's data retention and deletion policies

### System Monitoring
- Monitor application logs in `logs/app.log` for operational issues
- Review error logs in `logs/errors.log` for system errors
- Check database size and growth rate regularly
- Monitor ChromaDB indexing status for failed operations
- Review authentication logs for suspicious activity

### Backup Strategy
**Critical Files to Backup**:
- `data/library.db` - Main database (includes all metadata and user data)
- `data/chroma_db/` - Vector embeddings (can be regenerated but time-consuming)
- `config/settings.py` - System configuration
- `.env` - Environment variables (if used)

**Backup Frequency**:
- Daily: Database file
- Weekly: Full data directory
- Before major updates: Complete system backup

**Recovery Testing**:
- Test backup restoration quarterly
- Document recovery procedures
- Maintain off-site backup copies



## Acknowledgments

This system demonstrates a human-centered approach to AI-augmented library assessment, incorporating:
- **Local LLM deployment** (Ollama with Llama 3.2)
- **RAG implementation** (ChromaDB + sentence-transformers)
- **Advanced statistical analysis** (scipy, statsmodels) with LLM-powered interpretations
- **NLP analysis** (TextBlob for sentiment, TF-IDF for themes)
- **Accessible data visualization** (Plotly with WCAG AA compliance)
- **Privacy-preserving AI** (FERPA-compliant local processing)
- **Responsible data governance** (FAIR & CARE principles)
- **Human-in-the-loop design** (AI augmentation, not replacement)

Built to demonstrate that AI can enhance library assessment while keeping human expertise and judgment at the center of decision-making.

