# Implementation Plan: Library Assessment Decision Support System

## Overview

This implementation plan breaks down the MVP into discrete coding tasks suitable for a 4-6 week course project. The system is a single Streamlit application with 6 Python modules, SQLite database, ChromaDB embedded mode, and Ollama for local LLM inference.

The implementation follows an incremental approach: set up infrastructure first, implement core modules, build the UI, add testing, and finalize documentation.

The system incorporates FAIR (Findable, Accessible, Interoperable, Reusable) and CARE (Collective Benefit, Authority to Control, Responsibility, Ethics) principles for responsible data governance.

## Tasks

- [x] 1. Project setup and infrastructure
  - [x] 1.1 Initialize project structure and dependencies
    - Create directory structure (modules/, data/, config/)
    - Create requirements.txt with all dependencies (streamlit, chromadb, ollama, textblob, plotly, hypothesis, pytest, bcrypt, pandas, reportlab)
    - Create README.md with setup instructions
    - Initialize git repository with .gitignore
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 1.2 Create configuration module
    - Implement config/settings.py with configuration parameters (database path, ChromaDB path, Ollama model name, embedding model, context window size)
    - Add environment variable support for configuration overrides
    - _Requirements: 2.7, 6.4_

  - [x] 1.3 Set up SQLite database schema
    - Create database initialization script with all tables (datasets with FAIR/CARE metadata fields, survey_responses, usage_statistics, themes, users, access_logs)
    - Implement database connection management with context managers
    - Add database migration support for schema updates
    - _Requirements: 1.3, 6.3, 7.1, 7.3_

  - [ ]* 1.4 Write property test for database schema
    - **Property 3: Data Storage Round-Trip**
    - **Validates: Requirements 1.3**

- [x] 2. Implement authentication module (modules/auth.py)
  - [x] 2.1 Create authentication functions
    - Implement password hashing with bcrypt
    - Implement user creation and credential verification
    - Implement session state management using Streamlit session state
    - Add access logging with timestamps and action details
    - _Requirements: 6.6, 6.7_

  - [ ]* 2.2 Write unit tests for authentication
    - Test password hashing and verification
    - Test invalid credentials handling
    - Test session state management
    - _Requirements: 6.6_

  - [ ]* 2.3 Write property test for authentication enforcement
    - **Property 30: Authentication Enforcement**
    - **Validates: Requirements 6.6**

  - [ ]* 2.4 Write property test for audit logging
    - **Property 31: Audit Log Completeness**
    - **Validates: Requirements 6.7**

- [x] 3. Checkpoint - Verify infrastructure setup
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement CSV handler module (modules/csv_handler.py)
  - [x] 4.1 Create CSV validation functions
    - Implement validate_csv() to check format and structure
    - Add validation rules for required columns by dataset type
    - Implement specific error messages with line numbers
    - Add file hash calculation for duplicate detection
    - _Requirements: 1.2, 1.5_

  - [x] 4.2 Create CSV parsing and storage functions
    - Implement parse_csv() to convert CSV to DataFrame
    - Implement store_dataset() to save data to SQLite with FAIR/CARE metadata support
    - Add preview generation for uploaded data
    - Implement get_datasets() to list uploaded datasets with metadata
    - Implement update_dataset_metadata() to add/edit FAIR/CARE metadata
    - Implement export_dataset() to export in CSV or JSON format
    - Implement generate_data_manifest() to create discoverability manifest
    - Implement delete_dataset() with cascade deletion
    - _Requirements: 1.1, 1.3, 1.4, 1.6, 1.7, 7.1, 7.2, 7.7_

  - [ ]* 4.3 Write property test for CSV upload acceptance
    - **Property 1: CSV Upload Acceptance for Multiple Types**
    - **Validates: Requirements 1.1, 1.6**

  - [ ]* 4.4 Write property test for CSV validation
    - **Property 2: CSV Validation Correctness**
    - **Validates: Requirements 1.2, 1.5**

  - [ ]* 4.5 Write property test for upload preview accuracy
    - **Property 4: Upload Preview Accuracy**
    - **Validates: Requirements 1.4**

  - [ ]* 4.6 Write property test for dataset deletion
    - **Property 5: Dataset Deletion Completeness**
    - **Validates: Requirements 1.7**

  - [ ]* 4.7 Write property test for FAIR metadata completeness
    - **Property 32: FAIR Metadata Completeness**
    - **Validates: Requirements 7.1**

  - [ ]* 4.8 Write property test for dataset export interoperability
    - **Property 33: Dataset Export Interoperability**
    - **Validates: Requirements 7.2**

  - [ ]* 4.9 Write property test for data provenance tracking
    - **Property 34: Data Provenance Tracking**
    - **Validates: Requirements 7.3**

  - [ ]* 4.10 Write property test for data manifest generation
    - **Property 35: Data Manifest Generation**
    - **Validates: Requirements 7.7**

- [x] 5. Implement RAG query module (modules/rag_query.py)
  - [x] 5.1 Initialize RAG engine components
    - Implement initialize_rag_engine() to set up Ollama client and ChromaDB
    - Configure ChromaDB in embedded mode with all-MiniLM-L6-v2 embeddings
    - Add connection error handling for Ollama
    - _Requirements: 2.4, 2.7, 6.1, 6.2, 6.4_

  - [x] 5.2 Implement document indexing
    - Implement index_documents() to embed and store documents in ChromaDB
    - Add metadata extraction (dataset_id, dataset_type, source_row_id, date)
    - Implement batch processing for large datasets
    - _Requirements: 2.4_

  - [x] 5.3 Implement retrieval and generation pipeline
    - Implement retrieve_relevant_docs() for vector similarity search
    - Implement generate_answer() to call Ollama LLM with context
    - Implement query() to orchestrate retrieval and generation
    - Add citation extraction from metadata
    - Implement conversation context management (last 5 turns)
    - Track data provenance for queries (which datasets were accessed)
    - _Requirements: 2.1, 2.2, 2.3, 2.5, 7.3_

  - [ ]* 5.4 Write property test for query response completeness
    - **Property 6: Query Response Completeness**
    - **Validates: Requirements 2.1, 2.5**

  - [ ]* 5.5 Write property test for citation inclusion
    - **Property 7: Citation Inclusion in Answers**
    - **Validates: Requirements 2.2**

  - [ ]* 5.6 Write property test for conversation context
    - **Property 8: Conversation Context Preservation**
    - **Validates: Requirements 2.3**

  - [ ]* 5.7 Write property test for vector store retrieval
    - **Property 9: Vector Store Retrieval**
    - **Validates: Requirements 2.4**

  - [ ]* 5.8 Write property test for local processing guarantee
    - **Property 28: Local Processing Guarantee**
    - **Validates: Requirements 6.1, 6.2, 6.3**

- [x] 6. Checkpoint - Verify core RAG functionality
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement qualitative analysis module (modules/qualitative_analysis.py)
  - [x] 7.1 Create sentiment analysis functions
    - Implement analyze_sentiment() using TextBlob polarity scores
    - Implement sentiment categorization (positive >0.1, negative <-0.1, neutral between)
    - Calculate sentiment distribution statistics
    - Store sentiment results in SQLite
    - _Requirements: 3.1, 3.2, 3.5_

  - [x] 7.2 Create theme identification functions
    - Implement extract_themes() using TF-IDF keyword extraction
    - Implement simple K-means clustering on embeddings
    - Calculate theme frequency counts
    - Implement get_representative_quotes() to find quotes containing theme keywords
    - _Requirements: 3.3, 3.4, 3.6_

  - [x] 7.3 Create analysis summary and export functions
    - Implement generate_summary() to create text summary of analysis
    - Implement export_analysis() to export results to CSV
    - Track data provenance for analysis operations
    - _Requirements: 3.7, 7.3_

  - [ ]* 7.4 Write property test for sentiment analysis completeness
    - **Property 10: Sentiment Analysis Completeness**
    - **Validates: Requirements 3.1**

  - [ ]* 7.5 Write property test for sentiment categorization
    - **Property 11: Sentiment Categorization Validity**
    - **Validates: Requirements 3.2**

  - [ ]* 7.6 Write property test for theme identification
    - **Property 12: Theme Identification**
    - **Validates: Requirements 3.3**

  - [ ]* 7.7 Write property test for theme summary completeness
    - **Property 13: Theme Summary Completeness**
    - **Validates: Requirements 3.4, 3.5**

  - [ ]* 7.8 Write property test for representative quotes
    - **Property 14: Representative Quotes Association**
    - **Validates: Requirements 3.6**

  - [ ]* 7.9 Write property test for analysis export round-trip
    - **Property 15: Analysis Export Round-Trip**
    - **Validates: Requirements 3.7**

- [x] 8. Implement visualization module (modules/visualization.py)
  - [x] 8.1 Create chart generation functions
    - Implement create_bar_chart() using Plotly
    - Implement create_line_chart() for time series
    - Implement create_pie_chart() for proportions
    - Apply accessible color schemes with WCAG AA contrast ratios
    - Add clear labels, titles, and legends to all charts
    - _Requirements: 5.1, 5.2, 5.3, 5.6, 5.7_

  - [x] 8.2 Create chart export function
    - Implement export_chart() to save charts as PNG
    - _Requirements: 5.5_

  - [ ]* 8.3 Write property test for bar chart generation
    - **Property 22: Bar Chart Generation**
    - **Validates: Requirements 5.1**

  - [ ]* 8.4 Write property test for line chart generation
    - **Property 23: Line Chart Generation**
    - **Validates: Requirements 5.2**

  - [ ]* 8.5 Write property test for pie chart generation
    - **Property 24: Pie Chart Generation**
    - **Validates: Requirements 5.3**

  - [ ]* 8.6 Write property test for chart PNG export
    - **Property 25: Chart PNG Export**
    - **Validates: Requirements 5.5**

  - [ ]* 8.7 Write property test for chart metadata completeness
    - **Property 26: Chart Metadata Completeness**
    - **Validates: Requirements 5.6**

  - [ ]* 8.8 Write property test for chart color accessibility
    - **Property 27: Chart Color Accessibility**
    - **Validates: Requirements 5.7**

- [x] 9. Implement report generator module (modules/report_generator.py)
  - [x] 9.1 Create statistical summary functions
    - Implement generate_statistical_summary() to calculate descriptive statistics
    - Calculate mean, median, standard deviation, counts for datasets
    - _Requirements: 4.1_

  - [x] 9.2 Create narrative generation function
    - Implement generate_narrative() to create explanatory text using Ollama
    - Include key findings and insights in narrative
    - _Requirements: 4.2_

  - [x] 9.3 Create report assembly and export functions
    - Implement create_report() to assemble complete report structure
    - Include title, metadata, executive summary, statistics, visualizations, qualitative analysis, theme summaries, citations, timestamp
    - Implement export_report() to export to PDF and Markdown formats
    - Add data source citations to all reports
    - Include theme summaries when qualitative analysis performed
    - _Requirements: 4.3, 4.4, 4.5, 4.7_

  - [ ]* 9.4 Write property test for report statistical content
    - **Property 16: Report Statistical Content**
    - **Validates: Requirements 4.1**

  - [ ]* 9.5 Write property test for report narrative inclusion
    - **Property 17: Report Narrative Inclusion**
    - **Validates: Requirements 4.2**

  - [ ]* 9.6 Write property test for report visualization inclusion
    - **Property 18: Report Visualization Inclusion**
    - **Validates: Requirements 4.3**

  - [ ]* 9.7 Write property test for report export format validity
    - **Property 19: Report Export Format Validity**
    - **Validates: Requirements 4.4**

  - [ ]* 9.8 Write property test for report citation completeness
    - **Property 20: Report Citation Completeness**
    - **Validates: Requirements 4.5**

  - [ ]* 9.9 Write property test for conditional theme summary inclusion
    - **Property 21: Conditional Theme Summary Inclusion**
    - **Validates: Requirements 4.7**

- [x] 10. Checkpoint - Verify all modules implemented
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Implement Streamlit application (streamlit_app.py)
  - [x] 11.1 Create main application structure and authentication
    - Set up Streamlit page configuration
    - Implement login page with authentication
    - Implement session state management
    - Add logout functionality
    - _Requirements: 6.6_

  - [x] 11.2 Create data upload page
    - Implement CSV file uploader widget
    - Add dataset type selection (survey, usage, circulation)
    - Add FAIR/CARE metadata input fields (title, description, source, keywords, usage notes, ethical considerations)
    - Display upload preview and validation results
    - Show list of uploaded datasets with metadata and delete buttons
    - Add "Edit Metadata" button for existing datasets
    - Add "Export Dataset" button with format selection (CSV/JSON)
    - Add "Download Data Manifest" button
    - Add error message display for validation failures
    - _Requirements: 1.1, 1.2, 1.4, 1.5, 1.6, 1.7, 7.1, 7.2, 7.7_

  - [x] 11.3 Create query interface page
    - Implement chat interface with message history
    - Add text input for natural language questions
    - Display answers with citations
    - Show conversation context indicator
    - Add "Clear context" button
    - Handle Ollama connection errors gracefully
    - _Requirements: 2.1, 2.2, 2.3, 2.5, 2.6_

  - [x] 11.4 Create qualitative analysis page
    - Add dataset selector for analysis
    - Display sentiment distribution statistics and charts
    - Show identified themes with frequency counts
    - Display representative quotes for each theme
    - Add export button for analysis results
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

  - [x] 11.5 Create visualization page
    - Add dataset selector and chart type selector
    - Implement column selection for x and y axes
    - Display generated charts in Streamlit
    - Add chart export button for PNG download
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 11.6 Create report generation page
    - Add multi-select for datasets to include
    - Add checkbox for including visualizations
    - Display report preview
    - Add export buttons for PDF and Markdown formats
    - Show report generation progress indicator
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

  - [x] 11.7 Create data governance documentation page
    - Display FAIR principles explanation and how system implements them
    - Display CARE principles explanation and how system implements them
    - Document what data is collected and how it's used
    - Document privacy protections (local processing, PII redaction, access logging)
    - Document ethical use guidelines for library assessment data
    - Document user access and control mechanisms
    - _Requirements: 7.4, 7.5, 7.6_

- [x] 12. Implement PII detection and redaction
  - [x] 12.1 Create PII detection function
    - Implement regex patterns for email, phone, SSN detection
    - Implement redaction function to replace PII with placeholders
    - Add PII flagging in outputs
    - _Requirements: 6.5_

  - [x] 12.2 Integrate PII redaction into all output paths
    - Add PII redaction to query answers
    - Add PII redaction to report generation
    - Add PII redaction to analysis summaries
    - _Requirements: 6.5_

  - [ ]* 12.3 Write property test for PII redaction
    - **Property 29: PII Redaction**
    - **Validates: Requirements 6.5**

- [x] 13. Add error handling and user feedback
  - [x] 13.1 Implement error handlers for CSV operations
    - Add handlers for invalid format, missing columns, empty files, duplicate datasets
    - Display user-friendly error messages with actionable guidance
    - _Requirements: 1.2, 1.5_

  - [x] 13.2 Implement error handlers for query operations
    - Add handlers for Ollama connection failures, no relevant data, LLM timeouts, context too large
    - Display helpful error messages with recovery options
    - _Requirements: 2.5_

  - [x] 13.3 Implement error handlers for analysis operations
    - Add handlers for insufficient data, TextBlob processing errors
    - Display warnings and continue with available data
    - _Requirements: 3.1_

  - [x] 13.4 Implement error handlers for report generation
    - Add handlers for missing visualizations, PDF export failures
    - Provide fallback options (Markdown export)
    - _Requirements: 4.4_

- [x] 14. Create example test data and documentation
  - [x] 14.1 Create sample CSV files
    - Create sample survey responses CSV with realistic data
    - Create sample usage statistics CSV
    - Create sample circulation data CSV
    - Include edge cases (empty responses, special characters, long text)
    - _Requirements: 1.1, 1.6_

  - [x] 14.2 Write user documentation
    - Create USER_GUIDE.md with setup instructions
    - Document CSV format requirements for each dataset type
    - Add usage examples for each feature
    - Include troubleshooting section
    - _Requirements: 1.2, 2.6_

  - [x] 14.3 Write developer documentation
    - Document module interfaces and functions
    - Add code comments to all modules
    - Create ARCHITECTURE.md explaining system design
    - Document testing approach and how to run tests
    - _Requirements: All_

- [x] 15. Integration testing and final validation
  - [x]* 15.1 Write integration test for end-to-end upload and query flow
    - Test CSV upload → indexing → query → answer with citations
    - _Requirements: 1.1, 2.1, 2.2_

  - [x]* 15.2 Write integration test for analysis and report generation
    - Test CSV upload → qualitative analysis → report generation → export
    - _Requirements: 3.1, 3.3, 4.1, 4.2, 4.4_

  - [ ]* 15.3 Write example test for Ollama model configuration
    - Verify system uses Llama 3.2 3B or Phi-3 Mini
    - _Requirements: 2.7_

  - [ ]* 15.4 Write example test for ChromaDB embedded mode
    - Verify ChromaDB initialized in embedded mode without external connections
    - _Requirements: 6.4_

  - [ ]* 15.5 Write example test for report generation performance
    - Verify report generation completes within 2 minutes for 1000-row dataset
    - _Requirements: 4.6_

- [x] 16. Final checkpoint - Complete system validation
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP delivery
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation throughout development
- Property tests validate universal correctness properties with minimum 100 iterations using Hypothesis
- Unit tests validate specific examples and edge cases
- The implementation assumes Ollama is already installed and running locally
- All data processing happens locally without external API calls to support privacy-conscious local processing
- The system implements FAIR and CARE principles through metadata tracking, data provenance, export capabilities, and ethical use documentation
- The system is designed for single-user deployment on a laptop or desktop
