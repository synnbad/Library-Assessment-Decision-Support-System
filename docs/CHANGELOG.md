# Changelog - Library Assessment Decision Support System

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-04-06

### Added
- **Ollama Crash Handling**: Graceful error handling when Ollama crashes or is unavailable
  - 30-second timeout prevents application hangs
  - Clear error messages with recovery instructions
  - ConnectionError detection for all connection types (ConnectionError, ConnectionRefusedError, httpx.ConnectError)
  - Timeout handling (httpx.ReadTimeout, httpx.TimeoutException)
  - Comprehensive unit tests (13 tests, all passing)
  - Integration with RAG query system for graceful degradation

- **Real-Time Error Monitoring**: Development tools for catching and fixing errors
  - Background error monitor script (`.kiro/monitor_streamlit_errors.py`)
  - Quick error check utility (`.kiro/check_errors.sh`)
  - Error context capture tool (`.kiro/capture_error_context.sh`)
  - Comprehensive monitoring documentation

### Fixed
- **Plotly Visualization Bug**: Fixed invalid `titleside` property in correlation heatmap colorbar
  - Location: `modules/quantitative_analysis.py` line 3062
  - Changed to proper nested structure: `title=dict(text="Correlation", side="right")`
  - Correlation analysis visualizations now work correctly
  - Module imports successfully with no syntax errors

- **Report Generation Bug**: Fixed UnboundLocalError when accessing report variable
  - Location: `streamlit_app.py` line 1688
  - Moved visualization warnings section inside `if 'current_report' in st.session_state:` block
  - Report generation page no longer crashes
  - All report variable accesses now within proper scope

- **Error Handling**: Improved error messages throughout the application
  - User-friendly messages for Ollama connection issues
  - Clear recovery instructions for common errors (restart Ollama, check model availability)
  - Better error context in logs with operation tracking
  - Graceful degradation when services are unavailable

### Security
- ✅ All Phase 1 (P0) critical security tasks complete (9/10)
- ✅ PII redaction in RAG context (defense-in-depth approach)
- ✅ Authentication rate limiting (5 attempts per 60 seconds)
- ✅ Cryptographically secure session IDs
- ✅ SQL injection prevention through parameterized queries
- ✅ Database-ChromaDB synchronization prevents data inconsistencies

### Testing
- Added comprehensive Ollama crash handling tests (13 tests)
  - Connection error detection tests
  - Timeout handling tests
  - Error message validation tests
  - Integration with query() method tests
- All integration tests passing (7/7 for RAG-PII end-to-end)
- Historical task-level coverage estimate; rerun coverage before reporting current numbers
- No regressions in existing functionality

### Documentation
- Updated README with system status and reliability information
- Added troubleshooting section with common issues and solutions
- Documented security hardening measures
- Added backup strategy recommendations
- Created comprehensive CHANGELOG

---

## [Previous Releases]

### Phase 1: Critical Security & Data Integrity (Completed 90%)

#### Task 1: Data Integrity Issues ✅
- **1.1**: Database-ChromaDB synchronization
  - Modified csv_handler.delete_dataset() to remove embeddings
  - Added error handling for ChromaDB deletion failures
  - Logging for synchronization operations

- **1.2**: SQLite WAL mode for concurrent writes
  - Added PRAGMA journal_mode=WAL to database initialization
  - Implemented retry logic with exponential backoff
  - Prevents "database is locked" errors

- **1.3**: Metadata validation and sanitization
  - JSON validation with depth and size limits
  - Sanitization of user-provided metadata
  - Parameterized queries prevent SQL injection

- **1.4**: Duplicate column detection
  - CSV validation detects duplicate columns
  - Clear warning messages to users
  - Suggestions for column renaming

- **1.5**: ChromaDB indexing status tracking
  - Added indexing_status column to datasets table
  - Status updates during indexing (pending, in_progress, completed, failed)
  - Indexing errors surfaced to users in UI

#### Task 2: Security Vulnerabilities ✅
- **2.1**: PII redaction in RAG context
  - PII detection applied to retrieved documents before LLM generation
  - Comprehensive PII patterns (emails, phones, SSNs, addresses)
  - Multi-layer protection prevents leakage

- **2.2**: Authentication rate limiting
  - Max 5 attempts per 60 seconds
  - Exponential backoff delays
  - Tracking per username and IP
  - Clear lockout messages

- **2.3**: Cryptographically secure session IDs
  - Replaced simple UUIDs with secure tokens
  - User ID and timestamp in session key
  - Session validation on each request

#### Task 3: Cascading Failures (90% Complete)
- **3.1**: Ollama crash handling ✅
  - ConnectionError detection in generate_answer()
  - 30-second timeout for Ollama requests
  - Clear error messages with recovery instructions
  - Application doesn't hang when Ollama crashes

- **3.2**: NULL sentiment handling ⚠️
  - Pending: Filter NULL sentiment before theme extraction
  - Minor edge case, low priority

### Core Features (Stable)

#### Data Management
- Multi-source data integration
- Flexible CSV upload (any format)
- Auto-fill metadata (FAIR/CARE)
- PII detection and warnings
- Dataset management interface

#### Analysis Capabilities
- **RAG-Powered Queries**: Natural language queries with citations
- **Quantitative Analysis**: Correlation, trend, comparative, distribution analysis with LLM interpretations
- **Qualitative Analysis**: Sentiment analysis and theme identification
- **Cross-Dataset Insights**: Query across multiple data sources simultaneously

#### Visualization
- Interactive charts (bar, line, pie, heatmap, trend)
- WCAG AA compliant colors
- Accessible design
- Export capabilities

#### Reporting
- Multi-source report generation
- Statistical summaries
- Narrative insights
- Visualization integration
- PDF and Markdown export

#### Privacy And Governance
- Privacy-conscious local processing
- PII detection and redaction
- FAIR data principles
- CARE data principles
- Audit logging

---

## Version History

**Current Status**: Prototype/workbench suitable for local demonstration, coursework, and portfolio review
- Phase 1 (P0): 9/10 tasks complete
- Phase 2 (P1): 0/9 tasks complete (planned)
- Phase 3 (P2): 0/13 tasks complete (planned)
- Phase 4 (P3): 0/4 tasks complete (planned)

**Next Milestone**: Complete Phase 2 high-priority reliability tasks
- Chunked CSV reading for large files
- Conversation history cleanup
- Disk space monitoring
- Progress indicators for long operations
- Concurrency improvements
- UI synchronization fixes

---

## Deployment Readiness

### Suitable for local demonstration and pilot review
- Core workflows are present
- Local-first privacy design is documented
- Error handling and test coverage continue to improve
- Documentation is being aligned around the Library Assessment Decision Support System identity

### Recommended before institution-managed deployment
- Complete Task 3.2 (NULL sentiment handling)
- Complete Task 4.1 (Database integrity checks)
- Complete Phase 2 (P1) reliability tasks
- Set up production monitoring
- Configure automated backups
- Implement SSL/TLS
- Complete institutional privacy, security, accessibility, and FERPA/legal review

### Suitable For
- ✅ Internal deployment
- ✅ Pilot programs
- ✅ Development/staging environments
- ⚠️ Public or institution-wide deployment only after additional governance hardening

---

## Contributors

Built with a focus on:
- Human-centered AI design
- Privacy-preserving technology
- Responsible data governance
- Accessibility and inclusion
- Open source principles
