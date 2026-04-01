# Module Interfaces Reference

## Overview

This document provides a comprehensive reference for all module interfaces in the FERPA-Compliant RAG Decision Support System. Each module is documented with its purpose, key functions, parameters, return values, and usage examples.

## Table of Contents

1. [auth.py - Authentication](#authpy---authentication)
2. [csv_handler.py - Data Upload](#csv_handlerpy---data-upload)
3. [rag_query.py - RAG Engine](#rag_querypy---rag-engine)
4. [qualitative_analysis.py - NLP Analysis](#qualitative_analysispy---nlp-analysis)
5. [report_generator.py - Report Creation](#report_generatorpy---report-creation)
6. [visualization.py - Chart Generation](#visualizationpy---chart-generation)
7. [database.py - Data Layer](#databasepy---data-layer)
8. [pii_detector.py - Privacy Protection](#pii_detectorpy---privacy-protection)
9. [settings.py - Configuration](#settingspy---configuration)

---

## auth.py - Authentication

### Purpose
Provides secure user authentication and session management with bcrypt password hashing and audit logging.

### Key Functions

#### `create_user(username: str, password: str) -> bool`
Create a new user account with hashed password.

**Parameters:**
- `username` (str): Unique username for the account
- `password` (str): Plain text password (will be hashed)

**Returns:**
- `bool`: True if user created successfully, False if username already exists

**Example:**
```python
from modules import auth

if auth.create_user("admin", "secure_password"):
    print("User created successfully")
else:
    print("Username already exists")
```

#### `authenticate(username: str, password: str) -> bool`
Verify user credentials.

**Parameters:**
- `username` (str): Username to authenticate
- `password` (str): Plain text password to verify

**Returns:**
- `bool`: True if credentials are valid, False otherwise

**Side Effects:**
- Logs authentication attempt to access_logs table

**Example:**
```python
if auth.authenticate("admin", "secure_password"):
    print("Login successful")
else:
    print("Invalid credentials")
```

#### `log_access(username: str, action: str, resource_type: Optional[str] = None, resource_id: Optional[str] = None, details: Optional[str] = None) -> None`
Log user access for audit trail.

**Parameters:**
- `username` (str): Username performing the action
- `action` (str): Action being performed (e.g., 'login', 'upload', 'query', 'delete')
- `resource_type` (Optional[str]): Type of resource accessed (e.g., 'dataset', 'report')
- `resource_id` (Optional[str]): ID of resource accessed
- `details` (Optional[str]): Additional details about the action

**Returns:**
- None

**Example:**
```python
auth.log_access(
    username="admin",
    action="upload",
    resource_type="dataset",
    resource_id="123",
    details="Uploaded survey data"
)
```


#### `change_password(username: str, old_password: str, new_password: str) -> tuple[bool, str]`
Change user password.

**Parameters:**
- `username` (str): Username
- `old_password` (str): Current password
- `new_password` (str): New password

**Returns:**
- `tuple[bool, str]`: (success, message)

**Example:**
```python
success, message = auth.change_password("admin", "old_pass", "new_pass")
if success:
    print(message)  # "Password changed successfully"
```

#### Session Management Functions

**`login_user(session_state: Any, username: str) -> None`**
Mark user as logged in (Streamlit session management).

**`logout_user(session_state: Any) -> None`**
Log out user and clear session.

**`is_authenticated(session_state: Any) -> bool`**
Check if user is authenticated.

**`get_current_user(session_state: Any) -> Optional[str]`**
Get current authenticated username.

---

## csv_handler.py - Data Upload

### Purpose
Handles CSV file validation, parsing, storage, and FAIR/CARE metadata management.

### Key Functions

#### `validate_csv(file, dataset_type: str) -> Tuple[bool, Optional[str]]`
Validate CSV file format and structure.

**Parameters:**
- `file`: Uploaded file object (file-like object)
- `dataset_type` (str): Type of dataset ('survey', 'usage', 'circulation')

**Returns:**
- `Tuple[bool, Optional[str]]`: (is_valid, error_message)
  - `is_valid`: True if valid, False otherwise
  - `error_message`: None if valid, error description if invalid

**Validation Rules:**
- Survey: requires response_date, question, response_text
- Usage: requires date, metric_name, metric_value
- Circulation: requires checkout_date, material_type, patron_type
- Checks for empty files, missing columns, completely empty columns

**Example:**
```python
from modules import csv_handler

with open('survey.csv', 'rb') as file:
    is_valid, error = csv_handler.validate_csv(file, 'survey')
    if is_valid:
        print("CSV is valid")
    else:
        print(f"Validation error: {error}")
```

#### `parse_csv(file) -> pd.DataFrame`
Parse CSV file into pandas DataFrame.

**Parameters:**
- `file`: Uploaded file object

**Returns:**
- `pd.DataFrame`: Parsed data

**Example:**
```python
with open('survey.csv', 'rb') as file:
    df = csv_handler.parse_csv(file)
    print(f"Loaded {len(df)} rows")
```

#### `store_dataset(df: pd.DataFrame, dataset_name: str, dataset_type: str, file_hash: str, metadata: Optional[Dict[str, Any]] = None) -> int`
Store DataFrame in SQLite with FAIR/CARE metadata.

**Parameters:**
- `df` (pd.DataFrame): DataFrame to store
- `dataset_name` (str): Name for the dataset
- `dataset_type` (str): Type ('survey', 'usage', 'circulation')
- `file_hash` (str): SHA256 hash of original file
- `metadata` (Optional[Dict]): FAIR/CARE metadata with keys:
  - `title`: Human-readable title
  - `description`: Dataset description
  - `source`: Data source/origin
  - `keywords`: List of keywords
  - `usage_notes`: Context and responsible use guidance
  - `ethical_considerations`: Ethical use notes

**Returns:**
- `int`: dataset_id of stored dataset

**Example:**
```python
metadata = {
    'title': 'Spring 2024 Library Survey',
    'description': 'Student satisfaction survey',
    'source': 'Qualtrics',
    'keywords': ['survey', 'satisfaction', 'spring 2024'],
    'usage_notes': 'Use for assessment only',
    'ethical_considerations': 'Contains student feedback'
}

dataset_id = csv_handler.store_dataset(
    df=df,
    dataset_name='spring_2024_survey',
    dataset_type='survey',
    file_hash='abc123...',
    metadata=metadata
)
print(f"Stored dataset with ID: {dataset_id}")
```


#### `get_datasets() -> List[Dict[str, Any]]`
Retrieve list of all uploaded datasets with metadata.

**Returns:**
- `List[Dict]`: List of dataset dictionaries with keys:
  - `id`, `name`, `dataset_type`, `upload_date`, `row_count`
  - `title`, `description`, `source`, `keywords`
  - `usage_notes`, `ethical_considerations`

**Example:**
```python
datasets = csv_handler.get_datasets()
for dataset in datasets:
    print(f"{dataset['name']}: {dataset['row_count']} rows")
```

#### `export_dataset(dataset_id: int, format: str = 'csv') -> Optional[bytes]`
Export dataset in standard format (CSV or JSON).

**Parameters:**
- `dataset_id` (int): Dataset identifier
- `format` (str): Export format ('csv' or 'json')

**Returns:**
- `Optional[bytes]`: Exported data as bytes, or None if dataset not found

**Example:**
```python
csv_data = csv_handler.export_dataset(1, 'csv')
with open('export.csv', 'wb') as f:
    f.write(csv_data)
```

#### `generate_data_manifest() -> Dict[str, Any]`
Generate FAIR-compliant data manifest listing all datasets.

**Returns:**
- `Dict`: Manifest with keys:
  - `generated`: ISO timestamp
  - `system`: System name
  - `version`: System version
  - `datasets`: List of dataset metadata

**Example:**
```python
manifest = csv_handler.generate_data_manifest()
import json
with open('manifest.json', 'w') as f:
    json.dump(manifest, f, indent=2)
```

---

## rag_query.py - RAG Engine

### Purpose
Implements retrieval-augmented generation for natural language question answering using ChromaDB and Ollama.

### Key Classes

#### `RAGQuery`
Main RAG engine class.

**Initialization:**
```python
from modules.rag_query import RAGQuery

rag = RAGQuery()
```

### Key Methods

#### `test_ollama_connection() -> Tuple[bool, Optional[str]]`
Test connection to Ollama server.

**Returns:**
- `Tuple[bool, Optional[str]]`: (is_connected, error_message)

**Example:**
```python
is_connected, error = rag.test_ollama_connection()
if not is_connected:
    print(f"Ollama error: {error}")
```

#### `index_dataset(dataset_id: int) -> int`
Index a dataset in ChromaDB for RAG retrieval.

**Parameters:**
- `dataset_id` (int): Dataset identifier

**Returns:**
- `int`: Number of documents indexed

**Example:**
```python
num_docs = rag.index_dataset(dataset_id=1)
print(f"Indexed {num_docs} documents")
```

#### `query(question: str, session_id: Optional[str] = None, username: Optional[str] = None) -> Dict[str, Any]`
Answer natural language question about library data.

**Parameters:**
- `question` (str): Natural language question
- `session_id` (Optional[str]): Session ID for conversation context
- `username` (Optional[str]): Username for provenance tracking

**Returns:**
- `Dict[str, Any]`: Result dictionary with keys:
  - `answer` (str): Generated answer with PII redacted
  - `confidence` (float): Confidence score (0.0 to 1.0)
  - `citations` (List[Dict]): List of source citations
  - `suggested_questions` (List[str]): Follow-up question suggestions
  - `processing_time_ms` (int): Processing time in milliseconds
  - `error_type` (Optional[str]): Error type if applicable

**Error Types:**
- `no_relevant_data`: No documents found for question
- `context_too_large`: Context exceeds token limit
- `llm_timeout`: LLM generation timed out
- `ollama_connection_failed`: Cannot connect to Ollama

**Example:**
```python
result = rag.query(
    question="What are the main themes in student feedback?",
    session_id="user_123",
    username="admin"
)

print(f"Answer: {result['answer']}")
print(f"Confidence: {result['confidence']:.2f}")
print(f"Citations: {len(result['citations'])}")
print(f"Processing time: {result['processing_time_ms']}ms")

for citation in result['citations']:
    print(f"  Source {citation['source_number']}: Dataset {citation['dataset_id']}")
```


#### `clear_conversation(session_id: str) -> None`
Clear conversation history for a session.

**Parameters:**
- `session_id` (str): Session identifier

**Example:**
```python
rag.clear_conversation("user_123")
```

---

## qualitative_analysis.py - NLP Analysis

### Purpose
Provides sentiment analysis and theme identification for open-ended text responses.

### Key Functions

#### `analyze_dataset_sentiment(dataset_id: int) -> Dict[str, Any]`
Analyze sentiment for all responses in a dataset.

**Parameters:**
- `dataset_id` (int): Dataset identifier

**Returns:**
- `Dict[str, Any]`: Sentiment analysis results with keys:
  - `total_responses` (int): Total number of responses
  - `processed_responses` (int): Successfully processed responses
  - `distribution` (Dict): Sentiment distribution (positive, neutral, negative)
  - `sentiments` (List[Dict]): Individual sentiment scores
  - `warnings` (Optional[Dict]): Warnings if errors occurred

**Raises:**
- `ValueError`: If insufficient data (< 10 responses)

**Example:**
```python
from modules import qualitative_analysis

results = qualitative_analysis.analyze_dataset_sentiment(dataset_id=1)
print(f"Processed {results['processed_responses']} responses")
print(f"Distribution: {results['distribution']}")
```

#### `extract_themes(dataset_id: int, n_themes: Optional[int] = None) -> Dict[str, Any]`
Identify recurring themes using TF-IDF and K-means clustering.

**Parameters:**
- `dataset_id` (int): Dataset identifier
- `n_themes` (Optional[int]): Number of themes to identify (default: 5)

**Returns:**
- `Dict[str, Any]`: Theme extraction results with keys:
  - `n_themes` (int): Number of themes identified
  - `themes` (List[Dict]): List of themes with:
    - `theme_id` (int): Theme identifier
    - `theme_name` (str): Theme name with top keyword
    - `keywords` (List[str]): Top 5 keywords
    - `frequency` (int): Number of responses in theme
    - `percentage` (float): Percentage of total responses
    - `representative_quotes` (List[str]): Example quotes
    - `sentiment_distribution` (Dict): Sentiment breakdown
  - `total_responses` (int): Total responses analyzed
  - `warnings` (Optional[List[str]]): Warnings if issues occurred

**Raises:**
- `ValueError`: If insufficient data or theme extraction fails

**Example:**
```python
results = qualitative_analysis.extract_themes(dataset_id=1, n_themes=5)
for theme in results['themes']:
    print(f"{theme['theme_name']}: {theme['frequency']} responses")
    print(f"  Keywords: {', '.join(theme['keywords'])}")
    print(f"  Quotes: {theme['representative_quotes'][0]}")
```

#### `generate_summary(analysis_id: int) -> str`
Generate text summary of analysis results with PII redaction.

**Parameters:**
- `analysis_id` (int): Analysis identifier

**Returns:**
- `str`: Text summary with PII redacted

**Example:**
```python
summary = qualitative_analysis.generate_summary(analysis_id=1)
print(summary)
```

---

## report_generator.py - Report Creation

### Purpose
Generates comprehensive assessment reports with statistics, narratives, and visualizations.

### Key Functions

#### `generate_statistical_summary(dataset_id: int, db_path: Optional[str] = None) -> Dict[str, Any]`
Calculate descriptive statistics for a dataset.

**Parameters:**
- `dataset_id` (int): Dataset identifier
- `db_path` (Optional[str]): Optional database path

**Returns:**
- `Dict[str, Any]`: Statistical summary with keys:
  - `dataset_id` (int)
  - `dataset_name` (str)
  - `dataset_type` (str)
  - `row_count` (int)
  - `statistics` (Dict): Descriptive stats (mean, median, std_dev, count, min, max)
  - `categorical_counts` (Dict): Category distributions

**Raises:**
- `ValueError`: If dataset not found

**Example:**
```python
from modules import report_generator

summary = report_generator.generate_statistical_summary(dataset_id=1)
print(f"Dataset: {summary['dataset_name']}")
print(f"Rows: {summary['row_count']}")
for metric, stats in summary['statistics'].items():
    print(f"{metric}: mean={stats['mean']:.2f}, median={stats['median']:.2f}")
```


#### `create_report(dataset_ids: List[int], include_viz: bool = True, include_qualitative: bool = False, db_path: Optional[str] = None) -> Dict[str, Any]`
Create complete report structure with all components.

**Parameters:**
- `dataset_ids` (List[int]): List of dataset IDs to include
- `include_viz` (bool): Whether to include visualizations (default: True)
- `include_qualitative` (bool): Whether to include qualitative analysis (default: False)
- `db_path` (Optional[str]): Optional database path

**Returns:**
- `Dict[str, Any]`: Complete report structure with keys:
  - `title` (str): Report title
  - `metadata` (Dict): Generation metadata
  - `executive_summary` (str): LLM-generated summary
  - `statistical_summaries` (List[Dict]): Statistics per dataset
  - `visualizations` (List[Dict]): Chart objects
  - `qualitative_analysis` (Optional[Dict]): Analysis results
  - `theme_summaries` (List[Dict]): Theme information
  - `citations` (List[str]): Data source citations
  - `timestamp` (str): Generation timestamp

**Raises:**
- `ValueError`: If dataset_ids is empty or contains invalid IDs

**Example:**
```python
report = report_generator.create_report(
    dataset_ids=[1, 2],
    include_viz=True,
    include_qualitative=True
)

print(f"Title: {report['title']}")
print(f"Executive Summary: {report['executive_summary']}")
print(f"Visualizations: {len(report['visualizations'])}")
```

#### `export_report(report: Dict[str, Any], format: str = 'markdown') -> tuple[bytes, str]`
Export report to PDF or Markdown format with automatic fallback.

**Parameters:**
- `report` (Dict): Report dictionary from create_report()
- `format` (str): Export format - 'pdf' or 'markdown' (default: 'markdown')

**Returns:**
- `tuple[bytes, str]`: (report_content_bytes, actual_format_used)
  - Falls back to Markdown if PDF export fails

**Raises:**
- `ValueError`: If format is not 'pdf' or 'markdown'

**Example:**
```python
content, format_used = report_generator.export_report(report, format='pdf')
with open(f'report.{format_used}', 'wb') as f:
    f.write(content)
print(f"Exported as {format_used}")
```

---

## visualization.py - Chart Generation

### Purpose
Creates accessible data visualizations using Plotly with WCAG AA compliant colors.

### Key Functions

#### `create_bar_chart(data: pd.DataFrame, x: str, y: str, title: str, x_label: Optional[str] = None, y_label: Optional[str] = None) -> go.Figure`
Create a bar chart for categorical data.

**Parameters:**
- `data` (pd.DataFrame): Data to visualize
- `x` (str): Column name for x-axis (categorical)
- `y` (str): Column name for y-axis (values)
- `title` (str): Chart title
- `x_label` (Optional[str]): Custom x-axis label
- `y_label` (Optional[str]): Custom y-axis label

**Returns:**
- `go.Figure`: Plotly Figure object

**Example:**
```python
from modules import visualization
import pandas as pd

data = pd.DataFrame({
    'category': ['Books', 'DVDs', 'Journals'],
    'count': [150, 75, 50]
})

fig = visualization.create_bar_chart(
    data=data,
    x='category',
    y='count',
    title='Library Materials by Type',
    x_label='Material Type',
    y_label='Count'
)

# Display in Streamlit
import streamlit as st
st.plotly_chart(fig)
```

#### `create_line_chart(data: pd.DataFrame, x: str, y: str, title: str, x_label: Optional[str] = None, y_label: Optional[str] = None) -> go.Figure`
Create a line chart for time series data.

**Parameters:**
- Same as create_bar_chart

**Returns:**
- `go.Figure`: Plotly Figure object

**Example:**
```python
data = pd.DataFrame({
    'date': ['2024-01', '2024-02', '2024-03'],
    'visits': [1200, 1350, 1500]
})

fig = visualization.create_line_chart(
    data=data,
    x='date',
    y='visits',
    title='Monthly Library Visits'
)
```

#### `create_pie_chart(data: pd.DataFrame, values: str, names: str, title: str) -> go.Figure`
Create a pie chart for proportions.

**Parameters:**
- `data` (pd.DataFrame): Data to visualize
- `values` (str): Column name for values (slice sizes)
- `names` (str): Column name for labels (slice names)
- `title` (str): Chart title

**Returns:**
- `go.Figure`: Plotly Figure object

**Example:**
```python
data = pd.DataFrame({
    'sentiment': ['Positive', 'Neutral', 'Negative'],
    'count': [120, 50, 30]
})

fig = visualization.create_pie_chart(
    data=data,
    values='count',
    names='sentiment',
    title='Sentiment Distribution'
)
```

#### `export_chart(fig: go.Figure, filename: str, format: str = 'png') -> bytes`
Export chart as PNG or HTML with automatic fallback.

**Parameters:**
- `fig` (go.Figure): Plotly Figure to export
- `filename` (str): Desired filename (without extension)
- `format` (str): Export format - 'png' or 'html' (default: 'png')

**Returns:**
- `bytes`: Image or HTML data as bytes
  - Falls back to HTML if PNG export fails (kaleido not available)

**Example:**
```python
img_bytes = visualization.export_chart(fig, 'chart', format='png')
with open('chart.png', 'wb') as f:
    f.write(img_bytes)
```

---

## database.py - Data Layer

### Purpose
Provides SQLite database management with schema initialization and query helpers.

### Key Functions

#### `init_database(db_path: Optional[str] = None) -> None`
Initialize SQLite database with complete schema.

**Parameters:**
- `db_path` (Optional[str]): Path to database file (uses Settings.DATABASE_PATH if not provided)

**Side Effects:**
- Creates database file and all tables
- Creates indexes for performance
- Initializes schema_version table

**Example:**
```python
from modules import database

database.init_database()
print("Database initialized")
```

#### `get_db_connection(db_path: Optional[str] = None)`
Context manager for database connections.

**Parameters:**
- `db_path` (Optional[str]): Path to database file

**Yields:**
- `sqlite3.Connection`: Database connection with row factory

**Example:**
```python
with database.get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM datasets")
    results = cursor.fetchall()
    for row in results:
        print(row['name'])
```

#### `execute_query(query: str, params: tuple = (), db_path: Optional[str] = None) -> list`
Execute SELECT query and return results.

**Parameters:**
- `query` (str): SQL SELECT query
- `params` (tuple): Query parameters
- `db_path` (Optional[str]): Database path

**Returns:**
- `list`: List of rows as dictionaries

**Example:**
```python
datasets = database.execute_query(
    "SELECT * FROM datasets WHERE dataset_type = ?",
    ("survey",)
)
for dataset in datasets:
    print(f"{dataset['name']}: {dataset['row_count']} rows")
```

#### `execute_update(query: str, params: tuple = (), db_path: Optional[str] = None) -> int`
Execute INSERT, UPDATE, or DELETE query.

**Parameters:**
- `query` (str): SQL query
- `params` (tuple): Query parameters
- `db_path` (Optional[str]): Database path

**Returns:**
- `int`: Last inserted row ID or number of affected rows

**Example:**
```python
dataset_id = database.execute_update(
    "INSERT INTO datasets (name, dataset_type) VALUES (?, ?)",
    ("test_dataset", "survey")
)
print(f"Created dataset with ID: {dataset_id}")
```

---

## pii_detector.py - Privacy Protection

### Purpose
Detects and redacts PII to maintain FERPA compliance.

### Key Functions

#### `detect_pii(text: str, patterns: Dict[str, str] = None) -> Dict[str, List[str]]`
Detect PII in text using regex patterns.

**Parameters:**
- `text` (str): Text to scan for PII
- `patterns` (Optional[Dict]): Custom patterns (uses Settings.PII_PATTERNS if not provided)

**Returns:**
- `Dict[str, List[str]]`: Mapping of PII type to detected instances

**Example:**
```python
from modules import pii_detector

text = "Contact me at john@example.com or 555-123-4567"
detected = pii_detector.detect_pii(text)
print(detected)
# {'email': ['john@example.com'], 'phone': ['555-123-4567']}
```

#### `redact_pii(text: str, patterns: Dict[str, str] = None) -> Tuple[str, Dict[str, int]]`
Redact PII from text by replacing with placeholders.

**Parameters:**
- `text` (str): Text to redact PII from
- `patterns` (Optional[Dict]): Custom patterns

**Returns:**
- `Tuple[str, Dict[str, int]]`: (redacted_text, pii_counts)

**Example:**
```python
text = "Contact me at john@example.com or 555-123-4567"
redacted, counts = pii_detector.redact_pii(text)
print(redacted)  # "Contact me at [EMAIL] or [PHONE]"
print(counts)    # {'email': 1, 'phone': 1}
```

#### `is_safe_output(text: str, patterns: Dict[str, str] = None) -> bool`
Check if text is safe to display (contains no PII).

**Parameters:**
- `text` (str): Text to check
- `patterns` (Optional[Dict]): Custom patterns

**Returns:**
- `bool`: True if text contains no PII, False otherwise

**Example:**
```python
if pii_detector.is_safe_output(text):
    print("Safe to display")
else:
    print("Contains PII - redact before displaying")
```

---

## settings.py - Configuration

### Purpose
Centralized configuration management with environment variable support.

### Key Settings

#### Database Configuration
- `DATABASE_PATH`: Path to SQLite database (default: data/library.db)
- `CHROMA_DB_PATH`: Path to ChromaDB storage (default: data/chroma_db)

#### Ollama Configuration
- `OLLAMA_URL`: Ollama server URL (default: http://localhost:11434)
- `OLLAMA_MODEL`: LLM model name (default: llama3.2:3b)
- `EMBEDDING_MODEL`: Embedding model (default: all-MiniLM-L6-v2)

#### RAG Configuration
- `CONTEXT_WINDOW_SIZE`: Conversation turns to keep (default: 5)
- `TOP_K_RETRIEVAL`: Documents to retrieve (default: 5)
- `MAX_CONTEXT_TOKENS`: Token limit for context (default: 4000)
- `LLM_GENERATION_TIMEOUT_SECONDS`: Timeout for generation (default: 60)

#### Analysis Configuration
- `DEFAULT_N_THEMES`: Number of themes (default: 5)
- `SENTIMENT_POSITIVE_THRESHOLD`: Positive cutoff (default: 0.1)
- `SENTIMENT_NEGATIVE_THRESHOLD`: Negative cutoff (default: -0.1)
- `MIN_RESPONSES_FOR_ANALYSIS`: Minimum responses (default: 10)

### Usage

```python
from config.settings import Settings

# Access settings
print(f"Database: {Settings.DATABASE_PATH}")
print(f"Model: {Settings.OLLAMA_MODEL}")

# Ensure directories exist
Settings.ensure_directories()

# Validate configuration
is_valid, error = Settings.validate_configuration()
if not is_valid:
    print(f"Configuration error: {error}")
```

### Environment Variables

Override settings using environment variables:

```bash
export DATABASE_PATH="/custom/path/library.db"
export OLLAMA_MODEL="phi3:mini"
export CONTEXT_WINDOW_SIZE="10"
```

---

## Error Handling

All modules follow consistent error handling patterns:

### Exceptions
- `ValueError`: Invalid input parameters
- `RuntimeError`: Operation failures (e.g., Ollama connection)
- `TimeoutError`: Operation timeouts

### Return Values
- Functions return `None` or empty collections when data not found
- Boolean functions return `False` on failure
- Tuple returns include error messages: `(success, error_message)`

### Example Error Handling

```python
try:
    result = rag.query("What are the themes?")
    if result.get('error_type'):
        print(f"Error: {result['error_type']}")
        print(f"Message: {result['answer']}")
    else:
        print(f"Answer: {result['answer']}")
except ValueError as e:
    print(f"Invalid input: {e}")
except RuntimeError as e:
    print(f"Operation failed: {e}")
```

---

## Best Practices

### Import Conventions
```python
# Import modules
from modules import auth, csv_handler, rag_query
from modules import qualitative_analysis, report_generator
from modules import visualization, database, pii_detector
from config.settings import Settings

# Import specific functions
from modules.csv_handler import validate_csv, store_dataset
from modules.pii_detector import redact_pii
```

### Error Handling
- Always check return values for errors
- Use try-except for operations that may fail
- Log errors for debugging
- Provide user-friendly error messages

### Resource Management
- Use context managers for database connections
- Close file handles properly
- Clean up test data in tests
- Clear conversation context when done

### Security
- Never log passwords or sensitive data
- Always redact PII before displaying
- Use audit logging for access tracking
- Validate all user inputs

---

## Quick Reference

### Common Workflows

**Upload and Index Dataset:**
```python
# Validate
is_valid, error = csv_handler.validate_csv(file, 'survey')
if not is_valid:
    print(f"Error: {error}")
    return

# Parse and store
df = csv_handler.parse_csv(file)
file_hash = csv_handler.calculate_file_hash(file_content)
dataset_id = csv_handler.store_dataset(df, 'name', 'survey', file_hash, metadata)

# Index for RAG
rag = RAGQuery()
num_docs = rag.index_dataset(dataset_id)
```

**Query and Display Answer:**
```python
rag = RAGQuery()
result = rag.query("What are the main themes?", session_id="user_123")
print(f"Answer: {result['answer']}")
for citation in result['citations']:
    print(f"Source: Dataset {citation['dataset_id']}")
```

**Analyze and Generate Report:**
```python
# Analyze
sentiment = qualitative_analysis.analyze_dataset_sentiment(dataset_id)
themes = qualitative_analysis.extract_themes(dataset_id, n_themes=5)

# Generate report
report = report_generator.create_report(
    dataset_ids=[dataset_id],
    include_viz=True,
    include_qualitative=True
)

# Export
content, format_used = report_generator.export_report(report, 'pdf')
with open(f'report.{format_used}', 'wb') as f:
    f.write(content)
```
