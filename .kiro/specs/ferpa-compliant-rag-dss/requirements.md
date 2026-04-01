# Requirements Document - MVP

## Introduction

This document specifies requirements for an MVP (Minimum Viable Product) AI-powered NLP system for library assessment. The system is designed as a course final project that demonstrates core AI/NLP capabilities while remaining achievable in a 4-6 week timeframe.

The MVP focuses on essential features: manual data upload, RAG-powered question answering, basic qualitative analysis, simple report generation, and basic visualizations. All processing happens locally to maintain FERPA compliance.

## Glossary

- **Assessment_Assistant**: The AI-powered NLP system that assists Library Assessment Specialists
- **Local_LLM**: Small language model running locally via Ollama (Llama 3.2 3B or Phi-3 Mini)
- **RAG_Engine**: Retrieval-Augmented Generation component for question answering using ChromaDB
- **Query_Interface**: Natural language chat interface built with Streamlit
- **Qualitative_Analyzer**: NLP component for sentiment analysis and theme identification
- **Report_Generator**: Component that generates statistical summaries and narrative text
- **Visualization_Engine**: Component that generates basic charts for data presentation
- **FERPA**: Family Educational Rights and Privacy Act (student data privacy law)
- **Assessment_Specialist**: Library staff member responsible for assessment initiatives
- **PII**: Personally Identifiable Information that must be protected

## Requirements

### Requirement 1: Manual Data Upload and Storage

**User Story:** As an Assessment Specialist, I want to upload CSV files containing survey responses and usage statistics, so that I can analyze library data without complex integrations.

#### Acceptance Criteria

1. THE Assessment_Assistant SHALL accept CSV file uploads through the web interface
2. WHEN a CSV file is uploaded, THE Assessment_Assistant SHALL validate the file format and structure
3. THE Assessment_Assistant SHALL store uploaded data in a local SQLite database
4. THE Assessment_Assistant SHALL display a preview of uploaded data for verification
5. IF a CSV file has formatting errors, THEN THE Assessment_Assistant SHALL display specific error messages
6. THE Assessment_Assistant SHALL support multiple CSV uploads for different data types (surveys, usage statistics, circulation data)
7. THE Assessment_Assistant SHALL allow the Assessment_Specialist to delete previously uploaded datasets

### Requirement 2: Natural Language Query Interface with RAG

**User Story:** As an Assessment Specialist, I want to ask questions in plain English about my library data and get accurate answers with citations, so that I can quickly find insights without writing queries or searching through spreadsheets.

#### Acceptance Criteria

1. WHEN the Assessment_Specialist asks a question in natural language, THE Query_Interface SHALL interpret the intent and retrieve relevant data
2. THE RAG_Engine SHALL generate answers using the Local_LLM with citations to specific data sources
3. THE Query_Interface SHALL maintain conversation context for follow-up questions
4. THE RAG_Engine SHALL retrieve relevant information from ChromaDB vector store
5. IF the query cannot be answered with available data, THEN THE Query_Interface SHALL explain what data is missing
6. THE Query_Interface SHALL display the chat conversation in a user-friendly interface
7. THE Local_LLM SHALL run via Ollama using Llama 3.2 3B or Phi-3 Mini models

### Requirement 3: Basic Qualitative Analysis

**User Story:** As an Assessment Specialist, I want the AI to analyze open-ended survey responses and identify themes and sentiment, so that I can process hundreds of comments efficiently.

#### Acceptance Criteria

1. WHEN open-ended survey responses are provided, THE Qualitative_Analyzer SHALL perform sentiment analysis
2. THE Qualitative_Analyzer SHALL categorize responses as positive, negative, or neutral
3. THE Qualitative_Analyzer SHALL identify recurring themes using keyword extraction or basic clustering
4. THE Qualitative_Analyzer SHALL generate a summary of identified themes with frequency counts
5. THE Qualitative_Analyzer SHALL display sentiment distribution statistics
6. THE Qualitative_Analyzer SHALL show representative quotes for each identified theme
7. THE Qualitative_Analyzer SHALL export analysis results to CSV format

### Requirement 4: Simple Report Generation

**User Story:** As an Assessment Specialist, I want the AI to generate reports with statistical summaries and narrative text, so that I can produce stakeholder reports quickly.

#### Acceptance Criteria

1. WHEN the Assessment_Specialist requests a report, THE Report_Generator SHALL produce statistical summaries with descriptive statistics
2. THE Report_Generator SHALL generate narrative text explaining key findings using the Local_LLM
3. THE Report_Generator SHALL include data visualizations in the report
4. THE Report_Generator SHALL export reports to PDF or Markdown format
5. THE Report_Generator SHALL include citations for all data sources used
6. THE Report_Generator SHALL generate reports within 2 minutes for typical datasets
7. WHERE qualitative analysis has been performed, THE Report_Generator SHALL include theme summaries in the report

### Requirement 5: Basic Data Visualization

**User Story:** As an Assessment Specialist, I want to generate simple charts from my data, so that I can visualize trends and patterns for presentations.

#### Acceptance Criteria

1. THE Visualization_Engine SHALL generate bar charts for categorical data comparisons
2. THE Visualization_Engine SHALL generate line charts for time series data
3. THE Visualization_Engine SHALL generate pie charts for proportion visualization
4. THE Visualization_Engine SHALL display visualizations in the web interface
5. THE Visualization_Engine SHALL allow export of charts as PNG images
6. THE Visualization_Engine SHALL apply clear labels and titles to all charts
7. THE Visualization_Engine SHALL use accessible color schemes with sufficient contrast

### Requirement 6: FERPA Compliance and Local Processing

**User Story:** As an Assessment Specialist, I want all AI processing to happen locally without sending data to external APIs, so that I maintain FERPA compliance and protect student privacy.

#### Acceptance Criteria

1. THE Local_LLM SHALL run entirely on local infrastructure via Ollama without external API calls
2. THE Assessment_Assistant SHALL process all data locally without transmission to external services
3. THE Assessment_Assistant SHALL store all data in local SQLite database
4. THE Assessment_Assistant SHALL use ChromaDB in embedded mode without external connections
5. IF PII is detected in outputs, THEN THE Assessment_Assistant SHALL redact or flag it before display
6. THE Assessment_Assistant SHALL implement basic password authentication for web interface access
7. THE Assessment_Assistant SHALL log all data access with timestamps for audit purposes

### Requirement 7: FAIR and CARE Data Principles

**User Story:** As an Assessment Specialist, I want the system to follow FAIR (Findable, Accessible, Interoperable, Reusable) and CARE (Collective Benefit, Authority to Control, Responsibility, Ethics) principles, so that library assessment data is managed responsibly and can be shared appropriately.

#### Acceptance Criteria

1. THE Assessment_Assistant SHALL store metadata for each dataset including title, description, upload date, data type, and source information (FAIR: Findable)
2. THE Assessment_Assistant SHALL provide export functionality for datasets and analysis results in standard formats (CSV, JSON) (FAIR: Accessible, Interoperable)
3. THE Assessment_Assistant SHALL document data provenance including upload source, transformations applied, and analysis methods used (FAIR: Reusable)
4. THE Assessment_Assistant SHALL include a data governance documentation page explaining ethical use, privacy protections, and intended purposes (CARE: Ethics, Responsibility)
5. THE Assessment_Assistant SHALL allow users to add usage notes and context to datasets to support responsible reuse (CARE: Collective Benefit)
6. THE Assessment_Assistant SHALL provide clear documentation of what data is collected, how it's used, and who has access (CARE: Authority to Control)
7. THE Assessment_Assistant SHALL generate a data manifest file listing all datasets with their metadata for discoverability (FAIR: Findable)
