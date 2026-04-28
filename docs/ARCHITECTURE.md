# System Architecture

## Overview

The Library Assessment Decision Support System is a single-application Streamlit workbench for library assessment. It provides natural-language query capabilities, qualitative and quantitative analysis, and report generation while keeping core data in local or institution-controlled storage.

**Key Design Principles:**

- Single application architecture (no microservices)
- Local processing only (no external API calls)
- Simple data storage (SQLite + ChromaDB embedded)
- Manual data upload workflow
- Human-in-the-loop decision making
- Multi-source data integration
- Minimal dependencies for prototype/workbench scope

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Web Framework | Streamlit | Single-page application UI |
| Language Model | Llama 3.2 3B via Ollama | Local LLM inference |
| Vector Store | ChromaDB (embedded) | Document embeddings and retrieval |
| Embeddings | all-MiniLM-L6-v2 | Sentence embeddings (384 dimensions) |
| Database | SQLite | Persistent data storage |
| NLP | TextBlob | Sentiment analysis |
| Statistics | scipy, statsmodels | Advanced statistical analysis |
| Visualization | Plotly | Interactive charts |
| Authentication | bcrypt | Password hashing |

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│              Streamlit Application Orchestrator              │
│                      (streamlit_app.py)                      │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  UI Modules  │    │   Business   │    │  Data Layer  │
│    (ui/)     │───▶│   Logic      │───▶│ (database.py)│
│              │    │  (modules/)  │    │              │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                               │
                            ┌──────────────────┼──────────────────┐
                            ▼                  ▼                  ▼
                    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
                    │   SQLite DB  │  │  ChromaDB    │  │    Ollama    │
                    │ (library.db) │  │ (chroma_db/) │  │ (localhost)  │
                    └──────────────┘  └──────────────┘  └──────────────┘
```

## Module Architecture

### Application Structure

The application follows a three-tier architecture:

1. **UI Layer (ui/)**: Streamlit page components for user interaction
2. **Business Logic Layer (modules/)**: Core functionality and data processing
3. **Data Layer (modules/database.py)**: Database access and persistence

### UI Modules (ui/)

The Streamlit application is modularized into 10 UI components, each responsible for a specific page or feature. The main `streamlit_app.py` file serves as an orchestrator (~200 lines), handling routing and initialization.

#### ui/auth_ui.py (Authentication Interface)
**Purpose:** Login and logout UI components

**Key Functions:**
- `show_login_page()` - Display login form with authentication
- `show_logout_button()` - Display logout button in sidebar

**Dependencies:** modules/auth

#### ui/home_ui.py (Dashboard)
**Purpose:** Home page with system status and quick statistics

**Key Functions:**
- `show_home_page()` - Display dashboard
- `display_system_status()` - Check Ollama, ChromaDB, database connectivity
- `display_quick_stats()` - Show dataset counts and recent activity

**Dependencies:** modules/database, modules/rag_query

#### ui/data_upload_ui.py (Data Upload Interface)
**Purpose:** CSV upload and dataset management

**Key Functions:**
- `show_data_upload_page()` - Display upload interface
- `handle_file_upload()` - Process uploaded CSV files
- `display_dataset_list()` - Show uploaded datasets with actions

**Dependencies:** modules/csv_handler, modules/database

#### ui/query_ui.py (RAG Chat Interface)
**Purpose:** Natural language query interface

**Key Functions:**
- `show_query_interface_page()` - Display chat interface
- `handle_query_submission()` - Process and display query results
- `display_conversation_history()` - Show chat history

**Dependencies:** modules/rag_query, modules/database

#### ui/qualitative_ui.py (Qualitative Analysis Interface)
**Purpose:** Sentiment analysis and theme extraction UI

**Key Functions:**
- `show_qualitative_analysis_page()` - Display analysis interface
- `run_sentiment_analysis()` - Execute and display sentiment analysis
- `run_theme_extraction()` - Execute and display theme identification

**Dependencies:** modules/qualitative_analysis, modules/database

#### ui/quantitative_ui.py (Quantitative Analysis Interface)
**Purpose:** Statistical analysis UI

**Key Functions:**
- `show_quantitative_analysis_page()` - Display analysis interface
- `run_correlation_analysis()` - Execute correlation analysis
- `run_trend_analysis()` - Execute trend analysis
- `run_comparative_analysis()` - Execute comparative analysis

**Dependencies:** modules/quantitative_analysis, modules/database

#### ui/visualization_ui.py (Visualization Interface)
**Purpose:** Chart generation UI

**Key Functions:**
- `show_visualizations_page()` - Display visualization interface
- `create_and_display_chart()` - Generate and show charts

**Dependencies:** modules/visualization, modules/database

#### ui/report_ui.py (Report Generation Interface)
**Purpose:** Report creation and export UI

**Key Functions:**
- `show_report_generation_page()` - Display report interface
- `generate_and_download_report()` - Create and provide download

**Dependencies:** modules/report_generator, modules/database

#### ui/governance_ui.py (Data Governance Interface)
**Purpose:** FAIR/CARE documentation display

**Key Functions:**
- `show_data_governance_page()` - Display governance documentation
- `display_fair_principles()` - Show FAIR implementation
- `display_care_principles()` - Show CARE implementation

**Dependencies:** modules/database

#### ui/logs_ui.py (Logs and Monitoring Interface)
**Purpose:** System logs and monitoring UI

**Key Functions:**
- `show_logs_monitoring_page()` - Display logs interface
- `display_access_logs()` - Show access audit trail
- `display_query_logs()` - Show query history

**Dependencies:** modules/database, modules/logging_service

### Core Modules (modules/)

#### 1. streamlit_app.py (Main Orchestrator)
**Purpose:** Application entry point and page routing

**Key Functions:**
- `main()` - Application entry point
- `initialize_session_state()` - Setup session variables
- `route_to_page()` - Navigate to selected page

**Dependencies:** All ui/ modules, modules/auth

**Responsibilities:**
- Session state initialization
- Authentication check
- Page navigation
- Sidebar menu
- Global error handling

#### 2. modules/auth.py (Authentication)
**Purpose:** User authentication and session management

**Key Functions:**
- `create_user(username, password)` - Create new user account
- `authenticate(username, password)` - Verify credentials
- `hash_password(password)` - bcrypt password hashing
- `verify_password(password, hash)` - Password verification
- `log_access(username, action, details)` - Audit logging
- `login_user(session_state, username)` - Session management
- `logout_user(session_state)` - Session cleanup

**Database Tables:** users, access_logs

**Security Features:**
- bcrypt password hashing (salt rounds: 12)
- Session state management
- Audit logging with timestamps
- Rate limiting support (configurable)


#### 3. modules/csv_handler.py (Data Upload)
**Purpose:** CSV file validation, parsing, and storage

**Key Functions:**
- `validate_csv(file, dataset_type)` - Validate CSV structure
- `parse_csv(file)` - Parse CSV to DataFrame
- `store_dataset(df, name, type, hash, metadata)` - Store in SQLite
- `get_datasets()` - List all datasets with metadata
- `update_dataset_metadata(id, metadata)` - Update FAIR/CARE metadata
- `delete_dataset(id)` - Remove dataset
- `export_dataset(id, format)` - Export to CSV/JSON
- `generate_data_manifest()` - Create FAIR manifest
- `check_duplicate(file_hash)` - Detect duplicate uploads
- `calculate_file_hash(content)` - SHA256 hashing

**Database Tables:** datasets, survey_responses, usage_statistics

**Validation Rules:**
- Survey: requires response_date, question, response_text
- Usage: requires date, metric_name, metric_value
- Circulation: requires checkout_date, material_type, patron_type
- Checks for empty files, missing columns, invalid format

**FAIR/CARE Metadata:**
- title, description, source, keywords (Findable)
- usage_notes, ethical_considerations (CARE)
- data_provenance (JSON tracking transformations)

#### 4. modules/rag_query.py (RAG Engine)
**Purpose:** Retrieval-augmented generation for Q&A

**Key Components:**
- `RAGQuery` class - Main RAG engine
- `initialize()` - Setup Ollama + ChromaDB
- `index_documents(texts, metadata)` - Embed and store
- `index_dataset(dataset_id)` - Index dataset in ChromaDB
- `retrieve_relevant_docs(question, k)` - Vector similarity search
- `generate_answer(question, context, history)` - LLM generation
- `query(question, session_id, username)` - End-to-end Q&A

**RAG Pipeline:**
1. User submits question
2. Question embedded using all-MiniLM-L6-v2 (384 dims)
3. ChromaDB retrieves top-k similar documents (default k=5)
4. Context + conversation history sent to Ollama
5. LLM generates answer with citations
6. PII redaction applied to output
7. Answer + citations returned

**Error Handling:**
- No relevant data: Suggests uploading data
- Context too large: Prompts to be more specific
- LLM timeout: Suggests simpler questions
- Ollama connection failed: Provides setup instructions

**Conversation Context:**
- Maintains last N turns (default: 5)
- Stored in memory by session_id
- Included in LLM prompt for follow-ups
- Clearable by user

#### 4a. modules/rag_evaluation.py (RAG Quality Metrics)
**Purpose:** Evaluate retrieval quality for RAG system

**Key Components:**
- `RAGEvaluator` class - Evaluation engine
- `calculate_precision_at_k(query, relevant_doc_ids, k)` - Precision@k metric
- `calculate_recall_at_k(query, relevant_doc_ids, k)` - Recall@k metric
- `calculate_mrr(query, relevant_doc_ids)` - Mean Reciprocal Rank
- `evaluate_query_set(test_queries)` - Batch evaluation
- `generate_synthetic_test_queries(dataset_id, n_queries)` - Create test queries
- `store_evaluation_results(results, test_set_name)` - Save to database
- `get_evaluation_history(limit)` - Retrieve past evaluations

**Evaluation Metrics:**

1. **Precision@k** = (# relevant docs in top k) / k
   - Measures what fraction of retrieved documents are relevant
   - Range: [0, 1], higher is better
   - Example: If 3 out of 5 retrieved docs are relevant, P@5 = 0.6

2. **Recall@k** = (# relevant docs in top k) / (total # relevant docs)
   - Measures what fraction of all relevant documents were retrieved
   - Range: [0, 1], higher is better
   - Example: If 3 out of 10 relevant docs are in top 5, R@5 = 0.3

3. **MRR** = 1 / (rank of first relevant document)
   - Measures how quickly users find a relevant document
   - Range: [0, 1], higher is better
   - Returns 0 if no relevant documents found
   - Example: First relevant doc at rank 3 → MRR = 1/3 = 0.333

**Database Tables:** rag_evaluations

**Usage:**
- Generate synthetic test queries from datasets
- Evaluate retrieval quality with ground truth
- Track evaluation metrics over time
- Compare different RAG configurations


#### 5. modules/qualitative_analysis.py (NLP Analysis)
**Purpose:** Sentiment analysis and theme identification

**Key Functions:**
- `analyze_sentiment(text)` - TextBlob sentiment analysis
- `analyze_dataset_sentiment(dataset_id)` - Batch sentiment analysis
- `extract_themes(dataset_id, n_themes)` - TF-IDF + K-means clustering
- `get_representative_quotes(texts, keyword, n)` - Find example quotes
- `analyze_responses(dataset_id, n_themes)` - Complete analysis
- `generate_summary(analysis_id)` - Text summary with PII redaction
- `export_analysis(analysis_id, format)` - Export to CSV

**Sentiment Analysis:**
- Uses TextBlob polarity scores (-1 to +1)
- Categories: positive (>0.1), negative (<-0.1), neutral (between)
- Handles processing errors gracefully (skips problematic entries)
- Minimum 10 responses required for analysis

**Theme Identification:**
- TF-IDF vectorization (max 100 features, 1-2 grams)
- K-means clustering (default 5 themes)
- Top 5 keywords per theme
- Representative quotes (3 per theme)
- Sentiment distribution per theme

**Database Tables:** themes, qualitative_analyses

**Error Handling:**

- Insufficient data: Clear error with minimum requirements
- TextBlob errors: Skip problematic entries, continue with rest
- TF-IDF/clustering errors: Explain issue with short/homogeneous text

#### 6. modules/quantitative_analysis.py (Statistical Analysis)

**Purpose:** Advanced statistical analysis with LLM-powered interpretations

**Key Functions:**

- `calculate_correlation()` - Pearson, Spearman, Kendall correlation analysis
- `calculate_trend()` - Time series trend analysis with forecasting
- `perform_comparative_analysis()` - t-tests, ANOVA, Mann-Whitney, Kruskal-Wallis
- `analyze_distribution()` - Distribution analysis with outlier detection
- `generate_interpretation()` - LLM-powered natural language interpretations
- `generate_insights()` - Contextual insights about data patterns
- `generate_recommendations()` - Actionable recommendations based on analysis
- `store_analysis_results()` - Save analysis to database
- `retrieve_analysis_results()` - Get analysis by ID
- `list_analyses_by_dataset()` - List all analyses for a dataset
- `create_correlation_heatmap()` - Correlation matrix visualization
- `create_trend_chart()` - Trend line with forecast visualization
- `create_comparison_boxplot()` - Group comparison visualization
- `create_distribution_histogram()` - Distribution with outliers visualization
- `validate_normality_assumption()` - Check parametric test assumptions
- `recommend_correlation_method()` - Suggest appropriate correlation method
- `recommend_comparison_test()` - Suggest appropriate statistical test
- `get_method_assumptions()` - Explain method assumptions and limitations

**Analysis Types:**

1. **Correlation Analysis:**
   - Pearson correlation for linear relationships
   - Spearman correlation for monotonic relationships
   - Kendall correlation for ordinal data
   - Statistical significance testing (p-values)
   - Correlation matrix and top correlations

2. **Trend Analysis:**
   - Linear regression for trend detection
   - Moving averages (7-day, 30-day)
   - Seasonal pattern detection via autocorrelation
   - Forecasting with 95% confidence intervals
   - R-squared and slope calculations

3. **Comparative Analysis:**
   - Independent t-tests for two-group comparisons
   - One-way ANOVA for multi-group comparisons
   - Mann-Whitney U test (non-parametric)
   - Kruskal-Wallis test (non-parametric)
   - Effect size calculations (Cohen's d)
   - Post-hoc pairwise comparisons

4. **Distribution Analysis:**
   - Skewness and kurtosis calculations
   - Shapiro-Wilk normality testing
   - IQR-based outlier detection
   - Z-score-based outlier detection
   - Quartile and percentile calculations

**LLM Integration:**

- Uses local Ollama (Llama 3.2 3B) for interpretations
- Generates natural language explanations of statistical results
- Provides contextual insights about library data patterns
- Creates actionable recommendations
- 60-second timeout for LLM generation
- Graceful fallback to statistical results only
- PII redaction applied to all outputs

**Database Tables:** quantitative_analyses

**Error Handling:**

- Insufficient data: Clear error with minimum requirements
- Non-numeric data: Identify problematic columns
- Missing date columns: Request date column for time series
- Ollama connection failures: Instructions for starting Ollama
- LLM timeouts: Return partial results with statistics only
- Statistical calculation failures: Explanatory error messages

#### 7. modules/report_generator.py (Report Creation)
**Purpose:** Generate statistical summaries and narrative reports

**Key Functions:**
- `generate_statistical_summary(dataset_id)` - Descriptive statistics
- `generate_narrative(summary, analysis)` - LLM-generated narrative
- `create_report(dataset_ids, include_viz, include_qualitative)` - Assemble report
- `export_report(report, format)` - Export to PDF/Markdown

**Report Structure:**
1. Title and metadata (generated date, author, datasets)
2. Executive summary (LLM-generated narrative)
3. Statistical summaries (mean, median, std dev, counts)
4. Visualizations (embedded charts if enabled)
5. Qualitative analysis (sentiment + themes if applicable)
6. Theme summaries with representative quotes
7. Data source citations
8. Timestamp

**Statistical Calculations:**
- Survey datasets: sentiment scores, response lengths, category counts
- Usage datasets: metric statistics by name, category distributions
- Descriptive stats: mean, median, std dev, min, max, count

**Narrative Generation:**
- Uses Ollama LLM to generate 2-3 paragraph summary
- Includes key findings, patterns, and insights
- Professional language for stakeholder reports
- PII redaction applied before returning

**Export Formats:**
- Markdown: Always available, includes all content
- PDF: Uses ReportLab, falls back to Markdown on failure
- Automatic fallback ensures users always get output


#### 7. modules/visualization.py (Chart Generation)
**Purpose:** Create accessible data visualizations

**Key Functions:**
- `create_bar_chart(data, x, y, title)` - Categorical comparisons
- `create_line_chart(data, x, y, title)` - Time series trends
- `create_pie_chart(data, values, names, title)` - Proportions
- `export_chart(fig, filename, format)` - Export to PNG/HTML

**Chart Features:**
- Accessible color palette (WCAG AA compliant)
- Clear axis labels and titles
- Responsive sizing for Streamlit
- Grid lines for readability
- White background for printing

**Color Palette:**
- 8 colors with sufficient contrast (4.5:1 minimum)
- Colorblind-friendly combinations
- Colors: Blue (#0077BB), Red (#CC3311), Teal (#009988), Orange (#EE7733), Cyan (#33BBEE), Magenta (#EE3377), Gray (#BBBBBB), Black (#000000)

**Export Options:**
- PNG: Requires kaleido, 1200x800px default
- HTML: Always available, interactive charts
- Automatic fallback to HTML if PNG fails

#### 8. modules/database.py (Data Layer)
**Purpose:** SQLite database management

**Key Functions:**
- `init_database(db_path)` - Create schema
- `get_db_connection(db_path)` - Context manager for connections
- `execute_query(query, params)` - SELECT queries
- `execute_update(query, params)` - INSERT/UPDATE/DELETE
- `migrate_database(db_path)` - Schema migrations

**Database Schema:**
- datasets: Core dataset metadata + FAIR/CARE fields
- survey_responses: Survey data with sentiment
- usage_statistics: Usage metrics and circulation
- themes: Identified themes from analysis
- users: User accounts with bcrypt hashes
- access_logs: Audit trail
- query_logs: RAG query history
- reports: Generated reports
- qualitative_analyses: Analysis results
- schema_version: Migration tracking

**Connection Management:**
- Context manager ensures proper cleanup
- Row factory for dict-like access
- Automatic commit/rollback
- Foreign key constraints enabled


#### 9. modules/pii_detector.py (Privacy Protection)
**Purpose:** Detect and redact PII for privacy-conscious governance

**Key Functions:**
- `detect_pii(text, patterns)` - Find PII instances
- `redact_pii(text, patterns)` - Replace with placeholders
- `flag_pii(text, patterns)` - Check without redacting
- `redact_pii_from_list(texts, patterns)` - Batch redaction
- `is_safe_output(text, patterns)` - Verify no PII
- `get_pii_summary(text, patterns)` - Human-readable summary

**PII Patterns (Regex):**
- Email: `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b`
- Phone: `\b\d{3}[-.]?\d{3}[-.]?\d{4}\b`
- SSN: `\b\d{3}-\d{2}-\d{4}\b`
- Student ID: Configurable pattern

**Redaction Placeholders:**
- [EMAIL], [PHONE], [SSN], [STUDENT_ID]

**Usage:**
- Applied to all LLM outputs before display
- Applied to report narratives
- Applied to analysis summaries
- Applied to representative quotes

#### 10. config/settings.py (Configuration)
**Purpose:** Centralized configuration management

**Key Settings:**
- Database paths (SQLite, ChromaDB)
- Ollama configuration (URL, model)
- RAG parameters (context window, top-k, chunk size)
- Analysis thresholds (sentiment, min responses)
- Timeouts (LLM generation, report creation)
- PII patterns
- FAIR/CARE options

**Environment Variable Support:**
- All settings can be overridden via env vars
- Defaults provided for MVP deployment
- Validation method to check configuration

## Data Flow

### 1. Data Upload Flow
```
User uploads CSV
    ↓
validate_csv() checks format
    ↓
parse_csv() creates DataFrame
    ↓
calculate_file_hash() for duplicate detection
    ↓
store_dataset() saves to SQLite
    ↓
User can index in ChromaDB for RAG
```

### 2. RAG Query Flow
```
User asks question
    ↓
Embed question (all-MiniLM-L6-v2)
    ↓
ChromaDB retrieves top-k docs
    ↓
Build context + conversation history
    ↓
Check context size (max 4000 tokens)
    ↓
Ollama generates answer
    ↓
redact_pii() removes sensitive info
    ↓
Extract citations from metadata
    ↓
Return answer + citations + suggestions
```


### 3. Qualitative Analysis Flow
```
User selects dataset
    ↓
analyze_dataset_sentiment() processes all responses
    ↓
TextBlob calculates polarity scores
    ↓
Categorize as positive/neutral/negative
    ↓
extract_themes() runs TF-IDF + K-means
    ↓
Identify top keywords per theme
    ↓
get_representative_quotes() finds examples
    ↓
Store results in themes table
    ↓
generate_summary() creates narrative
    ↓
redact_pii() from summary
    ↓
Display results + export option
```

### 4. Report Generation Flow
```
User selects datasets + options
    ↓
generate_statistical_summary() for each dataset
    ↓
create_visualizations() if enabled
    ↓
Retrieve qualitative analysis if applicable
    ↓
generate_narrative() using Ollama
    ↓
redact_pii() from narrative
    ↓
Assemble report structure
    ↓
export_report() to PDF or Markdown
    ↓
Fallback to Markdown if PDF fails
    ↓
Download file
```

## Security Architecture

### Authentication
- Password-based authentication with bcrypt
- Session state managed by Streamlit
- No JWT or token-based auth (single-user deployment)
- Audit logging for all access

### Data Protection
- All data stored locally (SQLite + ChromaDB)
- No external API calls
- PII detection and redaction on outputs
- privacy-conscious local processing through local processing

### Access Control
- Simple role model: authenticated users have full access
- Audit logs track all data access
- User can review access logs in UI

## Performance Considerations

### Bottlenecks
1. **LLM Generation:** 5-30 seconds per query (CPU-dependent)
2. **Theme Extraction:** 10-60 seconds for 1000 responses
3. **Report Generation:** 30-120 seconds with visualizations
4. **ChromaDB Indexing:** 1-5 seconds per 100 documents

### Optimization Strategies
- Conversation context limited to 5 turns
- Context size check before LLM generation (4000 token limit)
- Batch processing for sentiment analysis
- Caching of embeddings in ChromaDB
- Lazy loading of visualizations

### Resource Requirements
- **RAM:** 8GB for LLM + 4GB for application = 12GB minimum
- **Storage:** 20GB for models + 10GB for data = 30GB minimum
- **CPU:** 4 cores minimum, 8 cores recommended
- **GPU:** Optional but speeds up LLM inference 3-5x


## Error Handling Strategy

### Graceful Degradation
- Continue operation when possible
- Provide fallback options (e.g., Markdown if PDF fails)
- Skip problematic entries in batch operations
- Display warnings without blocking workflow

### User-Friendly Messages
- Avoid technical jargon
- Provide actionable guidance
- Suggest next steps
- Include examples when helpful

### Error Categories

**1. CSV Upload Errors**
- Invalid format → "Invalid CSV format. Please upload a valid CSV file."
- Missing columns → "Missing required columns: [list]. Expected: [list]"
- Empty file → "Uploaded file is empty. Please upload a file with data."
- Duplicate → "This dataset has already been uploaded. Upload date: [date]"

**2. Query Processing Errors**
- No relevant data → Suggest uploading data or rephrasing
- Context too large → Prompt to be more specific
- LLM timeout → Suggest simpler questions
- Ollama connection failed → Provide setup instructions

**3. Analysis Errors**
- Insufficient data → Show minimum requirements and current count
- TextBlob error → Skip problematic entries, continue with rest
- Theme extraction error → Explain issue with data characteristics

**4. Report Generation Errors**
- Missing visualizations → Generate report without them, include note
- PDF export failed → Automatically fall back to Markdown
- LLM narrative failed → Use basic summary instead

## Testing Strategy

### Test Organization
```
tests/
├── unit/              # Unit tests for individual functions
├── integration/       # Integration tests for workflows
├── property/          # Property-based tests (Hypothesis)
└── manual/            # Manual test scripts for UI
```

### Testing Approach

**Unit Tests:**
- Test individual functions in isolation
- Mock external dependencies (Ollama, ChromaDB)
- Focus on edge cases and error conditions
- Target: 80% code coverage

**Integration Tests:**
- Test complete workflows end-to-end
- Use test database and ChromaDB instance
- Verify data flows correctly between modules
- Test error propagation

**Property-Based Tests:**
- Use Hypothesis framework
- Test universal properties across all inputs
- Minimum 100 iterations per property
- Focus on data integrity and invariants

**Manual Tests:**
- UI interaction testing
- Visual verification of charts
- Report quality assessment
- Performance testing with large datasets

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=modules --cov-report=html

# Run specific test category
pytest tests/unit/
pytest tests/integration/
pytest tests/property/

# Run specific test file
pytest tests/unit/test_csv_handler.py

# Run with verbose output
pytest -v
```


### Test Data

**Synthetic CSV Files:**
- Generated with various structures
- Include edge cases (empty rows, special characters)
- Multiple dataset types (survey, usage, circulation)

**Sample Survey Responses:**
- Realistic text data for sentiment analysis
- Various lengths and sentiments
- Include edge cases (very short, very long, special characters)

**Performance Datasets:**
- Large files (1000+ rows) for performance testing
- Used to verify timeout handling
- Test memory usage and processing time

## Deployment

### Local Development Setup

1. **Install Ollama**
   ```bash
   # Follow instructions at https://ollama.ai
   ollama pull llama3.2:3b
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   python -m textblob.download_corpora
   ```

4. **Initialize Database**
   ```bash
   python scripts/init_app.py
   ```

5. **Run Application**
   ```bash
   streamlit run streamlit_app.py
   ```

### Production Deployment

**Single Machine Deployment:**
- Install on laptop or desktop
- No containerization required for MVP
- Ollama runs as background service
- Streamlit runs on localhost:8501

**Data Backup:**
- Backup `data/library.db` regularly
- Backup `data/chroma_db/` directory
- Export data manifest periodically

**Security Considerations:**
- Change default admin password immediately
- Store database file securely
- Review access logs regularly
- Keep Ollama and dependencies updated

## FAIR and CARE Implementation

### FAIR Principles

**Findable:**
- Rich metadata (title, description, source, keywords)
- Data manifest file for discoverability
- Unique identifiers for datasets
- Searchable metadata fields

**Accessible:**
- Simple authentication
- Export functionality (CSV, JSON)
- Clear access documentation
- Audit logging

**Interoperable:**
- Standard formats (CSV, JSON)
- Documented SQLite schema
- JSON metadata format
- Compatible with pandas, R, Excel

**Reusable:**
- Data provenance tracking
- Usage notes for context
- Source attribution
- Clear licensing


### CARE Principles

**Collective Benefit:**
- Usage notes explain community value
- Analysis results improve library services
- Reports support institutional goals
- Data governance documentation

**Authority to Control:**
- Users control data upload and retention
- Metadata editing capabilities
- Dataset deletion
- Local processing ensures institutional control

**Responsibility:**
- Ethical considerations field
- Data provenance for accountability
- Audit logging for transparency
- PII protection

**Ethics:**
- Data governance page explains ethical use
- Privacy protections built-in
- Clear documentation of purposes
- No external data transmission

## Future Enhancements

### Potential Improvements
1. **Multi-user Support:** Role-based access control
2. **Advanced Analytics:** More sophisticated NLP models
3. **Real-time Dashboards:** Live data visualization
4. **API Integration:** Connect to ILS, Qualtrics, etc.
5. **Collaborative Features:** Shared reports and annotations
6. **Advanced Visualizations:** More chart types, interactive dashboards
7. **Scheduled Reports:** Automated report generation
8. **Data Versioning:** Track dataset changes over time

### Scalability Considerations
- Current design supports up to 10,000 survey responses
- For larger datasets, consider:
  - Batch processing for analysis
  - Pagination for UI display
  - Database indexing optimization
  - Caching strategies

## Troubleshooting

### Common Issues

**Ollama Connection Error:**
- Ensure Ollama is running: `ollama serve`
- Check accessibility: `curl http://localhost:11434`
- Verify model is available: `ollama list`

**ChromaDB Error:**
- Delete `data/chroma_db/` and restart
- ChromaDB will reinitialize automatically

**Import Errors:**
- Activate virtual environment
- Reinstall dependencies: `pip install -r requirements.txt`

**Database Errors:**
- Delete `data/library.db` and reinitialize
- Run: `python -c "from modules.database import init_database; init_database()"`

**Slow Performance:**
- Check CPU/RAM usage
- Reduce context window size in settings
- Use smaller LLM model (phi3:mini)
- Clear conversation context frequently

## References

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Ollama Documentation](https://ollama.ai/docs)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [TextBlob Documentation](https://textblob.readthedocs.io/)
- [Plotly Documentation](https://plotly.com/python/)
- [FERPA Guidelines](https://www2.ed.gov/policy/gen/guid/fpco/ferpa/index.html)
- [FAIR Principles](https://www.go-fair.org/fair-principles/)
- [CARE Principles](https://www.gida-global.org/care)
