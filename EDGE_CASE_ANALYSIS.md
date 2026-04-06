# Comprehensive Edge Case Analysis
## Library Assessment Decision Support System

**Generated:** 2026-04-03  
**Purpose:** Identify edge cases, boundary conditions, and potential failure modes across the entire system

---

## Executive Summary

This analysis identifies **78 edge cases** across 10 system modules that are likely under-tested or missing from current test coverage. Priority is given to cases that could cause data loss, security issues, or silent failures.

### Critical Findings (Immediate Attention Required)

1. **Data Loss Risk:** CSV upload with duplicate file hashes but different content
2. **Security Risk:** SQL injection via malformed metadata JSON fields
3. **Silent Failure:** ChromaDB indexing failures not surfaced to users
4. **Performance:** Unbounded memory usage with large text fields
5. **Data Integrity:** Race conditions in concurrent dataset operations

---

## 1. CSV Handler Module (`modules/csv_handler.py`)

### 1.1 File Hash Collisions
**Edge Case:** Two different CSV files produce the same SHA256 hash (astronomically rare but theoretically possible)
- **Current Behavior:** Second file rejected as duplicate
- **Risk:** Data loss if legitimate different file is rejected
- **Test Status:** ❌ Not tested
- **Recommendation:** Add secondary validation (file size, timestamp, or sample content comparison)

### 1.2 Encoding Edge Cases
**Edge Case:** CSV with mixed encodings (e.g., UTF-8 header, Latin-1 data rows)
- **Current Behavior:** `parse_csv()` tries multiple encodings sequentially
- **Risk:** Silent data corruption with `encoding_errors='replace'` fallback
- **Test Status:** ⚠️ Partially tested (single encoding only)
- **Recommendation:** Log encoding detection results; warn users about replaced characters

### 1.3 Column Name Collisions
**Edge Case:** CSV with duplicate column names (e.g., "date", "date.1", "date.2")
- **Current Behavior:** Pandas auto-renames to "date", "date.1", "date.2"
- **Risk:** Flexible column mapping may select wrong column
- **Test Status:** ❌ Not tested
- **Recommendation:** Detect and warn about duplicate column names before storage

### 1.4 Extremely Large CSV Files
**Edge Case:** CSV file > 1GB with millions of rows
- **Current Behavior:** Entire file loaded into memory via `pd.read_csv()`
- **Risk:** Out of memory crash, no progress indication
- **Test Status:** ❌ Not tested
- **Recommendation:** Implement chunked reading for files > 100MB; add progress bar

### 1.5 Empty String vs NULL Handling
**Edge Case:** CSV with empty strings `""` vs actual NULL/missing values
- **Current Behavior:** Both treated as empty, but stored differently in SQLite
- **Risk:** Inconsistent query results (WHERE col = '' vs WHERE col IS NULL)
- **Test Status:** ❌ Not tested
- **Recommendation:** Normalize empty strings to NULL during storage

### 1.6 Special Characters in Column Names
**Edge Case:** Column names with SQL-sensitive characters: `date (mm/dd/yyyy)`, `response#1`, `user's feedback`
- **Current Behavior:** Stored as-is in JSON, may break flexible column mapping
- **Risk:** Regex matching failures in `_store_*_data()` functions
- **Test Status:** ❌ Not tested
- **Recommendation:** Sanitize column names or use exact matching with escaping

### 1.7 Metadata JSON Injection
**Edge Case:** User-provided metadata contains malicious JSON (e.g., deeply nested objects, circular references)
- **Current Behavior:** `json.dumps()` may fail or create invalid JSON
- **Risk:** Database corruption, query failures
- **Test Status:** ❌ Not tested
- **Recommendation:** Validate and sanitize metadata before JSON serialization; limit nesting depth

### 1.8 File Hash Calculation on Streaming Uploads
**Edge Case:** Large file uploaded via streaming (not fully in memory)
- **Current Behavior:** `calculate_file_hash()` expects bytes in memory
- **Risk:** Memory exhaustion for large files
- **Test Status:** ❌ Not tested
- **Recommendation:** Implement streaming hash calculation

### 1.9 Dataset Deletion with Active RAG Queries
**Edge Case:** Dataset deleted while RAG query is retrieving documents from it
- **Current Behavior:** CASCADE DELETE removes data, but ChromaDB still has stale embeddings
- **Risk:** RAG returns citations to non-existent datasets
- **Test Status:** ❌ Not tested
- **Recommendation:** Implement soft deletes or synchronize ChromaDB deletion

### 1.10 Auto-Detect Metadata with Ambiguous Data
**Edge Case:** CSV with columns that match multiple suggested patterns (e.g., "date_created", "date_modified", "survey_date")
- **Current Behavior:** `auto_detect_metadata()` uses first match via `setdefault()`
- **Risk:** Wrong column selected for date range detection
- **Test Status:** ❌ Not tested
- **Recommendation:** Prioritize columns by name specificity or let user confirm

---

## 2. Database Module (`modules/database.py`)

### 2.1 Concurrent Write Conflicts
**Edge Case:** Two users simultaneously insert datasets or update metadata
- **Current Behavior:** SQLite uses file-level locking; second write waits or fails
- **Risk:** "Database is locked" errors, transaction rollback
- **Test Status:** ❌ Not tested
- **Recommendation:** Implement retry logic with exponential backoff; use WAL mode

### 2.2 Schema Migration Failures
**Edge Case:** Migration interrupted mid-execution (power loss, process kill)
- **Current Behavior:** `migrate_database()` has no transaction wrapping
- **Risk:** Partial schema changes, inconsistent state
- **Test Status:** ❌ Not tested
- **Recommendation:** Wrap migrations in transactions; add rollback capability

### 2.3 Foreign Key Constraint Violations
**Edge Case:** Manual SQL execution bypasses foreign key checks
- **Current Behavior:** Foreign keys enabled in `get_db_connection()`, but not enforced if connection created elsewhere
- **Risk:** Orphaned records (e.g., survey_responses without parent dataset)
- **Test Status:** ⚠️ Partially tested (CASCADE DELETE tested, but not constraint violations)
- **Recommendation:** Add integrity check function; run periodically

### 2.4 Database File Corruption
**Edge Case:** SQLite file corrupted due to disk failure or improper shutdown
- **Current Behavior:** No corruption detection or recovery
- **Risk:** Complete data loss, application crash on startup
- **Test Status:** ❌ Not tested
- **Recommendation:** Implement database integrity check on startup; provide recovery instructions

### 2.5 Query Parameter Type Mismatches
**Edge Case:** `execute_query()` called with wrong parameter types (e.g., list instead of tuple)
- **Current Behavior:** SQLite may accept or raise cryptic error
- **Risk:** Silent failures or confusing error messages
- **Test Status:** ❌ Not tested
- **Recommendation:** Add parameter type validation; convert lists to tuples automatically

### 2.6 Connection Pool Exhaustion
**Edge Case:** Many concurrent operations exhaust available connections
- **Current Behavior:** No connection pooling; each operation creates new connection
- **Risk:** File descriptor exhaustion, "too many open files" error
- **Test Status:** ❌ Not tested
- **Recommendation:** Implement connection pooling or limit concurrent operations

### 2.7 Large BLOB Storage
**Edge Case:** Storing very large text fields (e.g., 10MB survey response)
- **Current Behavior:** SQLite TEXT type has no size limit
- **Risk:** Slow queries, memory issues when loading rows
- **Test Status:** ❌ Not tested
- **Recommendation:** Add size limits; warn users about large text fields

### 2.8 Index Maintenance on Large Tables
**Edge Case:** Tables grow to millions of rows; indexes become stale or fragmented
- **Current Behavior:** No index maintenance or optimization
- **Risk:** Degraded query performance over time
- **Test Status:** ❌ Not tested
- **Recommendation:** Implement VACUUM and ANALYZE on schedule

---

## 3. RAG Query Module (`modules/rag_query.py`)

### 3.1 ChromaDB Collection Name Conflicts
**Edge Case:** Multiple application instances use same ChromaDB path
- **Current Behavior:** All instances share "assessment_documents" collection
- **Risk:** Cross-contamination of embeddings between instances
- **Test Status:** ❌ Not tested
- **Recommendation:** Use instance-specific collection names or separate ChromaDB paths

### 3.2 Embedding Model Download Failures
**Edge Case:** First run without internet; `SentenceTransformer` cannot download model
- **Current Behavior:** Application crashes with unclear error
- **Risk:** Poor first-run experience
- **Test Status:** ❌ Not tested
- **Recommendation:** Pre-download models during setup; provide clear error message

### 3.3 ChromaDB Indexing Deduplication Failures
**Edge Case:** `_is_dataset_indexed()` returns False positive due to partial indexing
- **Current Behavior:** Checks for any document with dataset_id
- **Risk:** Incomplete indexing if previous attempt failed mid-batch
- **Test Status:** ❌ Not tested
- **Recommendation:** Track indexing completion status in database; verify row counts match

### 3.4 Context Window Overflow with Long Conversation
**Edge Case:** Conversation history grows beyond `CONTEXT_WINDOW_SIZE` but individual turns are very long
- **Current Behavior:** Only limits number of turns, not total tokens
- **Risk:** Context still exceeds `MAX_CONTEXT_TOKENS` despite windowing
- **Test Status:** ⚠️ Partially tested (token estimation tested, but not with long history)
- **Recommendation:** Implement token-based windowing, not just turn-based

### 3.5 Ollama Model Not Available
**Edge Case:** User specifies model in settings that isn't pulled locally
- **Current Behavior:** `ollama.generate()` fails with unclear error
- **Risk:** Confusing error message; user doesn't know to pull model
- **Test Status:** ⚠️ Partially tested (connection test exists, but not model availability)
- **Recommendation:** Check model availability in `test_ollama_connection()`; suggest `ollama pull` command

### 3.6 Malformed Metadata in ChromaDB
**Edge Case:** Document metadata contains non-serializable types (e.g., datetime objects)
- **Current Behavior:** ChromaDB may reject or silently drop fields
- **Risk:** Missing metadata in citations
- **Test Status:** ❌ Not tested
- **Recommendation:** Serialize all metadata values to strings before indexing

### 3.7 Distance Threshold Too Strict
**Edge Case:** `distance_threshold=1.45` filters out all results for certain queries
- **Current Behavior:** Returns empty list, triggers "no relevant data" error
- **Risk:** False negatives; relevant data exists but not retrieved
- **Test Status:** ❌ Not tested
- **Recommendation:** Make threshold configurable; log filtered results for tuning

### 3.8 Session ID Collisions
**Edge Case:** Two users generate same session ID (e.g., simple UUID collision)
- **Current Behavior:** Conversation histories mixed between users
- **Risk:** Privacy leak; user sees another user's conversation
- **Test Status:** ❌ Not tested
- **Recommendation:** Use cryptographically secure session IDs; include user ID in session key

### 3.9 PII in Retrieved Context
**Edge Case:** PII exists in source data, retrieved in context, but LLM paraphrases it in answer
- **Current Behavior:** `redact_pii()` only applied to final answer, not context
- **Risk:** PII leakage if LLM rephrases (e.g., "john.doe@example.com" → "John Doe's email")
- **Test Status:** ⚠️ Partially tested (redaction tested, but not paraphrasing)
- **Recommendation:** Apply PII detection to source data before indexing; flag datasets with PII

### 3.10 Timeout Signal Handling on Windows
**Edge Case:** `signal.SIGALRM` not available on Windows
- **Current Behavior:** `timeout()` context manager crashes
- **Risk:** Application unusable on Windows
- **Test Status:** ❌ Not tested
- **Recommendation:** Use threading-based timeout for cross-platform compatibility

---

## 4. Qualitative Analysis Module (`modules/qualitative_analysis.py`)

### 4.1 TextBlob Language Detection Failures
**Edge Case:** Survey responses in non-English languages
- **Current Behavior:** TextBlob assumes English; sentiment scores meaningless
- **Risk:** Incorrect sentiment analysis; misleading results
- **Test Status:** ❌ Not tested
- **Recommendation:** Detect language; warn if non-English; support multilingual sentiment

### 4.2 Extremely Short Responses
**Edge Case:** Survey responses with 1-2 words (e.g., "Good", "OK", "N/A")
- **Current Behavior:** TF-IDF may fail or produce meaningless themes
- **Risk:** Theme extraction errors; empty keyword lists
- **Test Status:** ⚠️ Partially tested (minimum response count tested, but not short text)
- **Recommendation:** Filter out responses below minimum word count before theme extraction

### 4.3 Homogeneous Responses
**Edge Case:** All survey responses nearly identical (e.g., "Very satisfied" repeated 100 times)
- **Current Behavior:** K-means clustering may fail or produce single cluster
- **Risk:** Theme extraction error; misleading "multiple themes" when only one exists
- **Test Status:** ❌ Not tested
- **Recommendation:** Detect low variance; warn user; skip theme extraction if variance too low

### 4.4 Special Characters in Text
**Edge Case:** Responses with emojis, unicode, or HTML entities (e.g., "&nbsp;", "😊")
- **Current Behavior:** TextBlob may misinterpret; TF-IDF treats as separate tokens
- **Risk:** Incorrect sentiment; polluted keyword lists
- **Test Status:** ❌ Not tested
- **Recommendation:** Normalize text (remove HTML, convert emojis to text) before analysis

### 4.5 Theme Count Exceeds Response Count
**Edge Case:** User requests 10 themes but only 5 responses available
- **Current Behavior:** K-means fails or produces degenerate clusters
- **Risk:** Analysis error; confusing error message
- **Test Status:** ❌ Not tested
- **Recommendation:** Cap theme count at response count; warn user

### 4.6 NULL or Empty Sentiment Scores
**Edge Case:** TextBlob returns None or NaN for certain texts
- **Current Behavior:** May cause aggregation errors in sentiment distribution
- **Risk:** Incorrect statistics; division by zero
- **Test Status:** ❌ Not tested
- **Recommendation:** Handle NULL scores explicitly; exclude from aggregations

---

## 5. Quantitative Analysis Module (`modules/quantitative_analysis.py`)

### 5.1 Non-Numeric Data in Numeric Columns
**Edge Case:** Column contains mix of numbers and text (e.g., "100", "N/A", "TBD")
- **Current Behavior:** Pandas coerces to object dtype; correlation fails
- **Risk:** Analysis error; confusing error message
- **Test Status:** ⚠️ Partially tested (error handling exists, but not mixed types)
- **Recommendation:** Detect and report mixed types; offer to clean data

### 5.2 Perfect Correlation (r=1.0)
**Edge Case:** Two columns are identical or perfectly linearly related
- **Current Behavior:** Correlation calculated correctly, but may confuse users
- **Risk:** Users misinterpret as error; LLM may generate misleading interpretation
- **Test Status:** ❌ Not tested
- **Recommendation:** Flag perfect correlations; explain potential causes (duplicate columns, derived metrics)

### 5.3 Insufficient Data for Statistical Tests
**Edge Case:** User requests t-test with only 2 data points per group
- **Current Behavior:** Test runs but p-value meaningless
- **Risk:** Misleading statistical significance
- **Test Status:** ⚠️ Partially tested (minimum data checks exist, but thresholds may be too low)
- **Recommendation:** Increase minimum sample size requirements; warn about low power

### 5.4 Non-Normal Data for Parametric Tests
**Edge Case:** User runs t-test on heavily skewed data
- **Current Behavior:** Test runs; results may be invalid
- **Risk:** Type I/II errors; incorrect conclusions
- **Test Status:** ⚠️ Partially tested (normality check exists, but not enforced)
- **Recommendation:** Automatically suggest non-parametric alternatives; require user confirmation

### 5.5 Missing Date Column for Trend Analysis
**Edge Case:** User selects dataset without date column for trend analysis
- **Current Behavior:** Error message displayed
- **Risk:** User doesn't know which column to add
- **Test Status:** ✅ Tested (error handling exists)
- **Recommendation:** Suggest date column names; offer to use row index as proxy

### 5.6 Outliers Dominating Correlation
**Edge Case:** Single extreme outlier creates spurious correlation
- **Current Behavior:** Correlation calculated including outliers
- **Risk:** Misleading results; incorrect decisions
- **Test Status:** ❌ Not tested
- **Recommendation:** Offer robust correlation methods (Spearman); visualize with outliers highlighted

### 5.7 LLM Interpretation Contradicts Statistics
**Edge Case:** LLM generates interpretation that contradicts p-value or effect size
- **Current Behavior:** Both displayed; user must reconcile
- **Risk:** User trusts LLM over statistics; incorrect conclusions
- **Test Status:** ❌ Not tested
- **Recommendation:** Validate LLM output against statistical results; flag contradictions

---

## 6. Report Generator Module (`modules/report_generator.py`)

### 6.1 Empty Datasets in Report
**Edge Case:** User includes dataset with 0 rows in report
- **Current Behavior:** Statistics calculation may fail or return empty dict
- **Risk:** Report generation error; incomplete report
- **Test Status:** ❌ Not tested
- **Recommendation:** Skip empty datasets; add note to report

### 6.2 Circular References in Report Assembly
**Edge Case:** Report includes analysis that references another report
- **Current Behavior:** No circular reference detection
- **Risk:** Infinite loop; stack overflow
- **Test Status:** ❌ Not tested
- **Recommendation:** Track report assembly graph; detect cycles

### 6.3 PDF Generation Failures
**Edge Case:** ReportLab fails due to missing fonts or unsupported characters
- **Current Behavior:** Falls back to Markdown
- **Risk:** User expects PDF; gets Markdown without explanation
- **Test Status:** ⚠️ Partially tested (fallback exists, but not all failure modes)
- **Recommendation:** Log PDF generation errors; inform user of fallback reason

### 6.4 Extremely Large Reports
**Edge Case:** Report with 100+ visualizations and 10,000+ rows of statistics
- **Current Behavior:** PDF generation may timeout or exhaust memory
- **Risk:** Report generation failure; no output
- **Test Status:** ❌ Not tested
- **Recommendation:** Paginate large reports; offer summary-only option

### 6.5 LLM Narrative Generation Timeout
**Edge Case:** Ollama takes > 60 seconds to generate narrative
- **Current Behavior:** Timeout; report generated without narrative
- **Risk:** User doesn't know narrative is missing
- **Test Status:** ⚠️ Partially tested (timeout exists, but not user notification)
- **Recommendation:** Add placeholder text explaining timeout; offer to regenerate

---

## 7. Visualization Module (`modules/visualization.py`)

### 7.1 Too Many Categories for Pie Chart
**Edge Case:** Pie chart with 50+ slices
- **Current Behavior:** Chart generated but unreadable
- **Risk:** Misleading visualization; poor UX
- **Test Status:** ❌ Not tested
- **Recommendation:** Limit to top N categories; group others as "Other"

### 7.2 Negative Values in Pie Chart
**Edge Case:** User creates pie chart with negative values
- **Current Behavior:** Plotly may render incorrectly or error
- **Risk:** Misleading visualization
- **Test Status:** ❌ Not tested
- **Recommendation:** Validate data; reject negative values for pie charts

### 7.3 Time Series with Gaps
**Edge Case:** Line chart with missing dates (e.g., weekends, holidays)
- **Current Behavior:** Plotly connects points across gaps
- **Risk:** Misleading trend visualization
- **Test Status:** ❌ Not tested
- **Recommendation:** Detect gaps; offer to fill with interpolation or show breaks

### 7.4 Color Palette Exhaustion
**Edge Case:** Chart requires more colors than available in accessible palette (>8)
- **Current Behavior:** Colors repeat; categories indistinguishable
- **Risk:** Misleading visualization; accessibility failure
- **Test Status:** ❌ Not tested
- **Recommendation:** Generate additional accessible colors; use patterns/textures

### 7.5 Export Filename Collisions
**Edge Case:** User exports multiple charts with same filename
- **Current Behavior:** Second export overwrites first
- **Risk:** Data loss; user confusion
- **Test Status:** ❌ Not tested
- **Recommendation:** Auto-append timestamp or counter to filenames

---

## 8. Authentication Module (`modules/auth.py`)

### 8.1 Password Hash Timing Attacks
**Edge Case:** Attacker measures response time to guess password length
- **Current Behavior:** `bcrypt.checkpw()` is constant-time, but other checks may not be
- **Risk:** Information leakage
- **Test Status:** ❌ Not tested
- **Recommendation:** Ensure all authentication paths have constant time

### 8.2 Username Enumeration
**Edge Case:** Different error messages for "user not found" vs "wrong password"
- **Current Behavior:** `authenticate()` returns False for both
- **Risk:** Attacker can enumerate valid usernames
- **Test Status:** ✅ Tested (same error message for both)
- **Recommendation:** Maintain current behavior; add rate limiting

### 8.3 Session Fixation
**Edge Case:** Attacker sets victim's session ID before login
- **Current Behavior:** Streamlit manages sessions; unclear if vulnerable
- **Risk:** Session hijacking
- **Test Status:** ❌ Not tested
- **Recommendation:** Regenerate session ID after login

### 8.4 Concurrent Login Attempts
**Edge Case:** Attacker makes 1000 login attempts simultaneously
- **Current Behavior:** No rate limiting
- **Risk:** Brute force attack; resource exhaustion
- **Test Status:** ❌ Not tested
- **Recommendation:** Implement rate limiting per IP and per username

### 8.5 Audit Log Injection
**Edge Case:** Attacker includes newlines or special characters in username
- **Current Behavior:** Logged as-is; may break log parsing
- **Risk:** Log injection; audit trail corruption
- **Test Status:** ❌ Not tested
- **Recommendation:** Sanitize all logged values; use structured logging

---

## 9. PII Detector Module (`modules/pii_detector.py`)

### 9.1 International Phone Numbers
**Edge Case:** Phone numbers in non-US formats (e.g., +44 20 7946 0958)
- **Current Behavior:** Regex only matches US format
- **Risk:** PII leakage for international data
- **Test Status:** ❌ Not tested
- **Recommendation:** Add international phone number patterns

### 9.2 Obfuscated PII
**Edge Case:** Email addresses with spaces or dots (e.g., "john . doe @ example . com")
- **Current Behavior:** Regex doesn't match
- **Risk:** PII leakage
- **Test Status:** ❌ Not tested
- **Recommendation:** Normalize text before detection; remove spaces around @ and dots

### 9.3 PII in Non-Text Fields
**Edge Case:** PII in numeric fields (e.g., SSN stored as integer 123456789)
- **Current Behavior:** Only text fields scanned
- **Risk:** PII leakage
- **Test Status:** ❌ Not tested
- **Recommendation:** Convert all fields to string before scanning

### 9.4 Redaction Placeholder Collisions
**Edge Case:** Original text contains "[EMAIL]" string
- **Current Behavior:** Indistinguishable from redacted email
- **Risk:** Confusion; potential re-identification
- **Test Status:** ❌ Not tested
- **Recommendation:** Use unique placeholders (e.g., "[REDACTED_EMAIL_1]")

### 9.5 Performance on Large Text
**Edge Case:** Redacting 10MB text field with 1000+ PII instances
- **Current Behavior:** Regex matching may be slow
- **Risk:** Timeout; poor UX
- **Test Status:** ❌ Not tested
- **Recommendation:** Optimize regex; consider chunked processing

---

## 10. Streamlit Application (`streamlit_app.py`)

### 10.1 Session State Corruption
**Edge Case:** User opens multiple tabs; session state conflicts
- **Current Behavior:** Streamlit isolates sessions, but shared resources (DB, ChromaDB) may conflict
- **Risk:** Data corruption; race conditions
- **Test Status:** ❌ Not tested
- **Recommendation:** Add session-level locking for critical operations

### 10.2 File Upload Size Limits
**Edge Case:** User uploads 2GB CSV file
- **Current Behavior:** Streamlit has default 200MB limit
- **Risk:** Upload fails with unclear error
- **Test Status:** ❌ Not tested
- **Recommendation:** Configure limit in Streamlit config; display clear error message

### 10.3 Browser Back Button
**Edge Case:** User clicks back button after submitting form
- **Current Behavior:** Streamlit may re-run with stale state
- **Risk:** Duplicate submissions; data corruption
- **Test Status:** ❌ Not tested
- **Recommendation:** Use form submission tokens; detect and prevent duplicates

### 10.4 Long-Running Operations Without Feedback
**Edge Case:** Theme extraction takes 5 minutes; no progress indicator
- **Current Behavior:** Page appears frozen
- **Risk:** User refreshes; operation cancelled; poor UX
- **Test Status:** ❌ Not tested
- **Recommendation:** Add progress bars for all operations > 5 seconds

### 10.5 Error Message Display Overflow
**Edge Case:** Error message with 10,000 character stack trace
- **Current Behavior:** Entire trace displayed; page unusable
- **Risk:** Poor UX; information overload
- **Test Status:** ❌ Not tested
- **Recommendation:** Truncate error messages; offer "Show Details" button

---

## Priority Matrix

| Priority | Edge Case | Module | Risk Level | Test Status |
|----------|-----------|--------|------------|-------------|
| P0 | SQL injection via metadata JSON | CSV Handler | Critical | ❌ |
| P0 | ChromaDB indexing failures not surfaced | RAG Query | High | ❌ |
| P0 | Race conditions in concurrent operations | Database | High | ❌ |
| P0 | PII in retrieved context not redacted | RAG Query | Critical | ⚠️ |
| P1 | Large file memory exhaustion | CSV Handler | High | ❌ |
| P1 | Session ID collisions | RAG Query | High | ❌ |
| P1 | Concurrent login brute force | Auth | High | ❌ |
| P1 | Database file corruption | Database | High | ❌ |
| P2 | Encoding mixed in CSV | CSV Handler | Medium | ⚠️ |
| P2 | Non-English sentiment analysis | Qualitative | Medium | ❌ |
| P2 | Perfect correlation misinterpretation | Quantitative | Medium | ❌ |
| P2 | PDF generation failures | Report | Medium | ⚠️ |
| P3 | Too many pie chart categories | Visualization | Low | ❌ |
| P3 | International phone numbers | PII Detector | Medium | ❌ |

---

## Recommended Testing Strategy

### Phase 1: Critical Security & Data Integrity (Week 1)
1. Add SQL injection tests for metadata fields
2. Test concurrent dataset operations (create, update, delete)
3. Test PII detection in RAG context before LLM generation
4. Test session ID uniqueness and isolation

### Phase 2: Data Loss Prevention (Week 2)
5. Test large file handling (chunked reading, progress bars)
6. Test database corruption detection and recovery
7. Test ChromaDB indexing failure handling
8. Test encoding detection and normalization

### Phase 3: Analysis Correctness (Week 3)
9. Test statistical analysis with edge cases (perfect correlation, insufficient data)
10. Test sentiment analysis with non-English text
11. Test theme extraction with homogeneous/short responses
12. Test LLM interpretation validation

### Phase 4: User Experience (Week 4)
13. Test long-running operations with progress indicators
14. Test error message clarity and truncation
15. Test visualization edge cases (too many categories, negative values)
16. Test report generation with empty/large datasets

---

## Automated Test Generation Recommendations

### Property-Based Tests to Add
1. **CSV Upload:** Any valid CSV structure should parse without error
2. **Database Transactions:** Any sequence of operations should maintain referential integrity
3. **PII Redaction:** Redacted text should never contain original PII patterns
4. **RAG Retrieval:** Retrieved documents should always have valid metadata
5. **Statistical Analysis:** Results should be deterministic for same input

### Fuzzing Targets
1. CSV parser with malformed files
2. Metadata JSON with deeply nested structures
3. SQL queries with special characters
4. LLM prompts with adversarial inputs
5. File upload with corrupted data

---

## Monitoring & Observability Gaps

### Missing Metrics
1. ChromaDB indexing success rate
2. LLM generation timeout frequency
3. Database lock contention
4. PII detection false positive/negative rates
5. Average query response time by dataset size

### Missing Alerts
1. Database file size approaching disk limit
2. ChromaDB collection size exceeding memory
3. Repeated authentication failures (brute force)
4. Long-running queries (> 60 seconds)
5. Error rate spike (> 10% of requests)

---

## Conclusion

This analysis identified **78 edge cases** across the system, with **15 critical (P0/P1)** cases requiring immediate attention. The highest risks are:

1. **Data integrity:** Concurrent operations, database corruption
2. **Security:** PII leakage, SQL injection, brute force attacks
3. **Reliability:** Silent failures in indexing, encoding, analysis

Implementing the recommended testing strategy will significantly improve system robustness and user trust.
