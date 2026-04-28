# Design Document - MVP

## Overview

This design document specifies a simplified, single-application architecture for an AI-powered library assessment system suitable for a 4-6 week course project. The system provides natural language query capabilities, qualitative analysis, and basic reporting while supporting privacy-conscious local processing.

### Core Design Principles

1. **Single Application Architecture**: All functionality runs in one Streamlit application
2. **Local Processing Only**: No external API calls; all AI processing via Ollama
3. **Simple Data Storage**: SQLite database for all persistent data
4. **Manual Data Upload**: CSV file uploads instead of automated integrations
5. **Embedded Vector Store**: ChromaDB in embedded mode without external services
6. **Minimal Dependencies**: Use lightweight libraries appropriate for MVP scope

### Technology Stack

- **Web Framework**: Streamlit (single-page application)
- **Language Model**: Llama 3.2 3B or Phi-3 Mini via Ollama
- **Vector Store**: ChromaDB (embedded mode)
- **Embeddings**: all-MiniLM-L6-v2 (sentence-transformers)
- **Database**: SQLite
- **NLP**: TextBlob for sentiment analysis
- **Visualization**: Plotly (bar, line, pie charts)
- **PDF Generation**: ReportLab or similar
- **Authentication**: Simple password-based auth

## Architecture

### Single Application Structure

```
streamlit_app.py (main application)
├── modules/
│   ├── csv_handler.py       # CSV upload and validation
│   ├── rag_query.py          # RAG engine with ChromaDB
│   ├── qualitative_analysis.py  # Sentiment and theme analysis
│   ├── report_generator.py  # Report creation
│   ├── visualization.py      # Chart generation
│   └── auth.py               # Simple authentication
├── data/
│   ├── library.db            # SQLite database
│   └── chroma_db/            # ChromaDB embedded storage
└── config/
    └── settings.py           # Configuration parameters
```

### Application Flow

1. **Authentication**: User logs in with password
2. **Data Upload**: User uploads CSV files via Streamlit file uploader
3. **Data Storage**: CSV data parsed and stored in SQLite
4. **Vector Indexing**: Text data embedded and stored in ChromaDB
5. **Ask**: Chat interface for natural language questions
6. **Analysis**: Qualitative analysis on demand
7. **Reporting**: Generate reports with visualizations
8. **Export**: Download reports as PDF/Markdown or charts as PNG

### Deployment Model

- Single machine deployment (laptop or desktop)
- Python virtual environment
- Ollama installed locally
- No containerization required for MVP
- Run via `streamlit run streamlit_app.py`

## Components and Interfaces

### 1. CSV Handler Module

**Purpose**: Handle CSV file uploads, validation, and storage

**Key Functions**:
```python
def validate_csv(file) -> tuple[bool, str]:
    """Validate CSV format and structure"""
    
def parse_csv(file) -> pd.DataFrame:
    """Parse CSV into DataFrame"""
    
def store_dataset(df: pd.DataFrame, dataset_type: str, metadata: dict = None) -> int:
    """
    Store DataFrame in SQLite with FAIR/CARE metadata, return dataset_id.
    
    Args:
        df: DataFrame to store
        dataset_type: Type of dataset (survey, usage, circulation)
        metadata: Optional dict with FAIR/CARE fields:
            - title: Human-readable title
            - description: Dataset description
            - source: Data source/origin
            - keywords: List of keywords for findability
            - usage_notes: Context and responsible use guidance
            - ethical_considerations: Ethical use notes
    """
    
def get_datasets() -> list[dict]:
    """Retrieve list of uploaded datasets with metadata"""
    
def update_dataset_metadata(dataset_id: int, metadata: dict) -> bool:
    """Update FAIR/CARE metadata for existing dataset"""
    
def delete_dataset(dataset_id: int) -> bool:
    """Delete dataset from database"""
    
def export_dataset(dataset_id: int, format: str = 'csv') -> bytes:
    """Export dataset in standard format (CSV or JSON) for interoperability"""
    
def generate_data_manifest() -> dict:
    """Generate manifest file listing all datasets with metadata for discoverability"""
```

**Validation Rules**:
- Check for valid CSV format
- Verify required columns based on dataset type
- Check for empty files
- Validate data types in columns
- Report specific errors with line numbers

### 2. RAG Query Module

**Purpose**: Implement retrieval-augmented generation for question answering

**Key Functions**:
```python
def initialize_rag_engine(ollama_model: str):
    """Initialize Ollama client and ChromaDB"""
    
def index_documents(texts: list[str], metadata: list[dict]):
    """Embed and store documents in ChromaDB"""
    
def query(question: str, conversation_history: list) -> dict:
    """Process natural language query and return answer with citations"""
    
def retrieve_relevant_docs(question: str, k: int = 5) -> list[dict]:
    """Retrieve top-k relevant documents from ChromaDB"""
    
def generate_answer(question: str, context: str, history: list) -> str:
    """Generate answer using Ollama LLM"""
```

**RAG Pipeline**:
1. User submits question
2. Question embedded using all-MiniLM-L6-v2
3. ChromaDB retrieves top-k similar documents
4. Context + question sent to Ollama
5. LLM generates answer
6. Citations extracted from metadata
7. Answer + citations returned to user

**Conversation Context**:
- Maintain last 5 conversation turns in memory
- Include in prompt for follow-up questions
- Clear context on user request

### 3. Qualitative Analysis Module

**Purpose**: Analyze open-ended text responses for sentiment and themes

**Key Functions**:
```python
def analyze_sentiment(texts: list[str]) -> list[dict]:
    """Analyze sentiment using TextBlob"""
    
def extract_themes(texts: list[str], n_themes: int = 5) -> dict:
    """Identify recurring themes using keyword extraction"""
    
def get_representative_quotes(texts: list[str], theme: str, n: int = 3) -> list[str]:
    """Find representative quotes for a theme"""
    
def generate_summary(analysis_results: dict) -> str:
    """Generate text summary of analysis"""
    
def export_analysis(analysis_results: dict, format: str) -> bytes:
    """Export analysis to CSV"""
```

**Sentiment Analysis**:
- Use TextBlob polarity scores
- Categorize: positive (>0.1), negative (<-0.1), neutral (between)
- Calculate distribution statistics
- Store results in SQLite

**Theme Identification**:
- Extract keywords using TF-IDF
- Simple clustering (K-means on embeddings)
- Count theme frequency
- Link themes to original responses

### 4. Report Generator Module

**Purpose**: Generate reports with statistics, narrative text, and visualizations

**Key Functions**:
```python
def generate_statistical_summary(dataset_id: int) -> dict:
    """Calculate descriptive statistics"""
    
def generate_narrative(summary: dict, analysis: dict) -> str:
    """Generate narrative text using Ollama"""
    
def create_report(dataset_ids: list[int], include_viz: bool = True) -> dict:
    """Create complete report structure"""
    
def export_report(report: dict, format: str) -> bytes:
    """Export report to PDF or Markdown"""
```

**Report Structure**:
1. Title and metadata
2. Executive summary (LLM-generated)
3. Statistical summaries (descriptive stats)
4. Visualizations (embedded charts)
5. Qualitative analysis results (if applicable)
6. Theme summaries with quotes
7. Data source citations
8. Timestamp and author

**Performance Target**: Generate report within 2 minutes for typical datasets (up to 1000 rows)

### 5. Visualization Module

**Purpose**: Generate basic charts for data presentation

**Key Functions**:
```python
def create_bar_chart(data: pd.DataFrame, x: str, y: str, title: str) -> go.Figure:
    """Create bar chart using Plotly"""
    
def create_line_chart(data: pd.DataFrame, x: str, y: str, title: str) -> go.Figure:
    """Create line chart for time series"""
    
def create_pie_chart(data: pd.DataFrame, values: str, names: str, title: str) -> go.Figure:
    """Create pie chart for proportions"""
    
def export_chart(fig: go.Figure, filename: str) -> bytes:
    """Export chart as PNG"""
```

**Chart Requirements**:
- Clear axis labels and titles
- Accessible color schemes (colorblind-friendly)
- Sufficient contrast for readability
- Legend when multiple series
- Responsive sizing for Streamlit display

### 6. Authentication Module

**Purpose**: Provide basic password authentication for web interface

**Key Functions**:
```python
def authenticate(username: str, password: str) -> bool:
    """Verify credentials"""
    
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    
def create_user(username: str, password: str) -> bool:
    """Create new user account"""
    
def log_access(username: str, action: str):
    """Log access for audit trail"""
```

**Security Measures**:
- Passwords hashed with bcrypt
- Session state management via Streamlit
- Access logging with timestamps
- Simple role: all authenticated users have same permissions

## Data Models

### SQLite Database Schema

#### datasets table
```sql
CREATE TABLE datasets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    dataset_type TEXT NOT NULL,  -- 'survey', 'usage', 'circulation'
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    row_count INTEGER,
    column_names TEXT,  -- JSON array of column names
    file_hash TEXT,  -- SHA256 hash to detect duplicates
    -- FAIR metadata
    title TEXT,  -- Human-readable title
    description TEXT,  -- Dataset description
    source TEXT,  -- Data source/origin
    keywords TEXT,  -- JSON array of keywords for findability
    -- CARE metadata
    usage_notes TEXT,  -- Context and responsible use guidance
    ethical_considerations TEXT,  -- Ethical use notes
    data_provenance TEXT  -- JSON object tracking transformations
);
```

#### survey_responses table
```sql
CREATE TABLE survey_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id INTEGER,
    response_date DATE,
    question TEXT,
    response_text TEXT,
    sentiment TEXT,  -- 'positive', 'negative', 'neutral'
    sentiment_score REAL,
    themes TEXT,  -- JSON array of theme IDs
    FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
);
```

#### usage_statistics table
```sql
CREATE TABLE usage_statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id INTEGER,
    date DATE,
    metric_name TEXT,
    metric_value REAL,
    category TEXT,
    FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
);
```

#### themes table
```sql
CREATE TABLE themes (
### ChromaDB Collections

#### documents collection
- **id**: Unique document identifier
- **embedding**: Vector embedding (384 dimensions for all-MiniLM-L6-v2)
- **metadata**:
  - dataset_id: Reference to source dataset
  - dataset_type: Type of data
  - source_row_id: Reference to original row in SQLite
  - text_snippet: Preview of text
  - date: Associated date if applicable
- **document**: Full text content

## FAIR and CARE Principles Implementation

### FAIR Principles (Findable, Accessible, Interoperable, Reusable)

The system implements FAIR principles for research data management:

**Findable**:
- Each dataset has rich metadata (title, description, source, keywords)
- Data manifest file lists all datasets with metadata for discoverability
- Unique identifiers (auto-incrementing IDs) for each dataset
- Searchable metadata fields in SQLite database

**Accessible**:
- Simple authentication ensures authorized access
- Export functionality provides data in standard formats (CSV, JSON)
- Clear documentation of access procedures
- Audit logging tracks all data access

**Interoperable**:
- Standard data formats (CSV, JSON) for import/export
- SQLite database with documented schema
- JSON metadata format for machine readability
- Compatible with common data analysis tools (pandas, R, Excel)

**Reusable**:
- Data provenance tracking documents transformations and analysis methods
- Usage notes field provides context for responsible reuse
- Clear licensing and ethical use documentation
- Metadata includes source information for proper attribution

### CARE Principles (Collective Benefit, Authority to Control, Responsibility, Ethics)

The system implements CARE principles for indigenous data governance and ethical data use:

**Collective Benefit**:
- Usage notes field allows documenting how data benefits the library community
- Analysis results can be shared to improve library services
- Reports include context about how findings support institutional goals
- Data governance documentation explains intended purposes

**Authority to Control**:
- Users control what data is uploaded and retained
- Metadata editing allows updating context and usage restrictions
- Dataset deletion provides control over data lifecycle
- Clear documentation of who has access and what they can do
- Local processing ensures data doesn't leave institutional control

**Responsibility**:
- Ethical considerations field documents responsible use guidelines
- Data provenance tracks all transformations for accountability
- Audit logging provides transparency of data access
- PII detection and redaction protects individual privacy
- privacy-conscious governance ensures student data protection

**Ethics**:
- Data governance page explains ethical use principles
- Privacy protections (local processing, PII redaction) built into system
- Clear documentation of data collection and use purposes
- Ethical considerations field prompts reflection on data use
- No external data transmission maintains ethical boundaries

### Implementation Details

**Metadata Fields**:
- `title`: Human-readable dataset title
- `description`: Detailed description of dataset contents
- `source`: Origin of the data (survey platform, ILS, manual entry)
- `keywords`: List of keywords for findability
- `usage_notes`: Context and guidance for responsible reuse
- `ethical_considerations`: Ethical use notes and restrictions
- `data_provenance`: JSON object tracking transformations and analysis methods

**Data Provenance Structure**:
```json
{
  "upload": {
    "timestamp": "2024-01-15T10:30:00Z",
    "user": "username",
    "source": "Qualtrics survey export"
  },
  "transformations": [
    {
      "operation": "sentiment_analysis",
      "timestamp": "2024-01-15T11:00:00Z",
      "method": "TextBlob",
      "parameters": {}
    },
    {
      "operation": "theme_extraction",
      "timestamp": "2024-01-15T11:15:00Z",
      "method": "TF-IDF + K-means",
      "parameters": {"n_themes": 5}
    }
  ],
  "queries": [
    {
      "timestamp": "2024-01-15T14:00:00Z",
      "user": "username",
      "question": "What are the main themes in student feedback?"
    }
  ]
}
```

**Data Manifest Format**:
```json
{
  "generated": "2024-01-15T15:00:00Z",
  "system": "Library Assessment Decision Support System",
  "version": "1.0.0",
  "datasets": [
    {
      "id": 1,
      "name": "spring_2024_survey",
      "title": "Spring 2024 Library User Survey",
      "type": "survey",
      "upload_date": "2024-01-15T10:30:00Z",
      "row_count": 342,
      "description": "Survey responses from undergraduate students about library services",
      "source": "Qualtrics",
      "keywords": ["survey", "undergraduate", "spring 2024", "user satisfaction"],
      "usage_notes": "Data collected with IRB approval. Use for library assessment only.",
      "ethical_considerations": "Contains student feedback. Maintain confidentiality."
    }
  ]
}
```

## Error Handling

### CSV Upload Errors

);
```

#### access_logs table
```sql
CREATE TABLE access_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    action TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details TEXT
);
```

### ChromaDB Collections

#### documents collection
- **id**: Unique document identifier
- **embedding**: Vector embedding (384 dimensions for all-MiniLM-L6-v2)
- **metadata**:
  - dataset_id: Reference to source dataset
  - dataset_type: Type of data
  - source_row_id: Reference to original row in SQLite
  - text_snippet: Preview of text
  - date: Associated date if applicable
- **document**: Full text content

## Error Handling

### CSV Upload Errors

**Invalid Format**:
- Display: "Invalid CSV format. Please upload a valid CSV file."
- Log error details
- Allow user to retry

**Missing Required Columns**:
- Display: "Missing required columns: [column_names]. Expected columns: [expected_columns]"
- Show example of correct format
- Allow user to retry

**Empty File**:
- Display: "Uploaded file is empty. Please upload a file with data."
- Allow user to retry

**Duplicate Dataset**:
- Display: "This dataset has already been uploaded (detected by file hash). Upload date: [date]"
- Offer option to upload anyway or cancel

### Query Processing Errors

**Ollama Connection Failed**:
- Display: "Cannot connect to Ollama. Please ensure Ollama is running locally."
- Provide instructions to start Ollama
- Retry button

**No Relevant Data Found**:
- Display: "I couldn't find relevant data to answer your question. Available datasets: [list]. Please upload data or rephrase your question."
- Suggest related queries

**LLM Generation Timeout**:
- Display: "Response generation timed out. Please try a simpler question or check system resources."
- Offer to retry

**Context Too Large**:
- Display: "Your question requires too much context. Please be more specific or break it into smaller questions."
- Suggest narrower scope

### Analysis Errors

**Insufficient Data**:
- Display: "Not enough data for meaningful analysis. Minimum required: [n] responses."
- Show current count
- Suggest uploading more data

**TextBlob Processing Error**:
- Log error details
- Display: "Error processing text. Skipping problematic entries."
- Continue with remaining data

### Report Generation Errors

**Missing Visualizations**:
- Display warning: "Some visualizations could not be generated due to insufficient data."
- Generate report without missing charts
- Include note in report

**PDF Export Failed**:
- Display: "PDF export failed. Downloading as Markdown instead."
- Provide Markdown download
- Log error for debugging

### Authentication Errors

**Invalid Credentials**:
- Display: "Invalid username or password."
- Increment failed attempt counter
- Rate limit after 5 failed attempts

**Session Expired**:
- Display: "Your session has expired. Please log in again."
- Redirect to login page
- Preserve unsaved work if possible

### General Error Handling Strategy

1. **User-Friendly Messages**: Avoid technical jargon in error messages
2. **Actionable Guidance**: Tell users what to do next
3. **Graceful Degradation**: Continue operation when possible
4. **Detailed Logging**: Log full error details for debugging
5. **Recovery Options**: Provide retry or alternative actions

## Testing Strategy

### Dual Testing Approach

This system requires both unit testing and property-based testing for comprehensive coverage:

**Unit Tests**: Focus on specific examples, edge cases, and integration points
- CSV parsing with various formats
- Authentication flows
- Database operations
- Specific error conditions
- UI component rendering

**Property-Based Tests**: Verify universal properties across all inputs
- Data integrity properties
- Round-trip properties (serialization, parsing)
- Invariant preservation
- Input validation rules
- Each property test runs minimum 100 iterations

### Property-Based Testing Configuration

**Framework**: Hypothesis (Python property-based testing library)

**Configuration**:
```python
from hypothesis import given, settings
import hypothesis.strategies as st

@settings(max_examples=100)  # Minimum 100 iterations
@given(...)
def test_property_name(...):
    """Feature: library-assessment-decision-support, Property N: [property text]"""
    # Test implementation
```

**Test Organization**:
- Each correctness property implemented as single property-based test
- Tests tagged with feature name and property number
- Tests reference design document property
- Generators create realistic test data

### Testing Tools

- **pytest**: Test runner
- **Hypothesis**: Property-based testing
- **pytest-cov**: Coverage reporting
- **unittest.mock**: Mocking external dependencies
- **Streamlit testing**: Component testing utilities

### Test Data

- **Synthetic CSV files**: Generated with various structures
- **Sample survey responses**: Realistic text data
- **Edge cases**: Empty files, malformed data, special characters
- **Performance datasets**: Large files for performance testing

### Coverage Goals

- Minimum 80% code coverage
- 100% coverage of error handling paths
- All correctness properties tested
- Integration tests for main workflows


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, I identified several opportunities to consolidate redundant properties:

- Properties 1.1 and 1.6 both test CSV upload acceptance; combined into single property covering multiple dataset types
- Properties 1.3 and 1.7 both test database operations; these are distinct (insert vs delete) and kept separate
- Properties 3.4 and 3.5 both test summary statistics; combined into comprehensive summary property
- Properties 5.1, 5.2, and 5.3 all test chart generation; kept separate as they test different chart types
- Properties 6.1, 6.2, and 6.3 all test local processing; combined into single comprehensive property
- Properties 4.1 and 4.2 both test report content; kept separate as they test different content types

### Property 1: CSV Upload Acceptance for Multiple Types

*For any* valid CSV file and any dataset type (survey, usage, circulation), the system should successfully accept the upload and return a success indicator.

**Validates: Requirements 1.1, 1.6**

### Property 2: CSV Validation Correctness

*For any* CSV file, the validation function should correctly identify whether it has valid format and structure, returning appropriate error messages for invalid files.

**Validates: Requirements 1.2, 1.5**

### Property 3: Data Storage Round-Trip

*For any* valid CSV data uploaded to the system, querying the SQLite database should return data equivalent to the original upload.

**Validates: Requirements 1.3**

### Property 4: Upload Preview Accuracy

*For any* uploaded CSV file, the preview data returned should match a subset of the actual uploaded data.

**Validates: Requirements 1.4**

### Property 5: Dataset Deletion Completeness

*For any* dataset stored in the system, after deletion, queries for that dataset should return no results and the dataset should not appear in the dataset list.

**Validates: Requirements 1.7**

### Property 6: Query Response Completeness

*For any* natural language question submitted to the Query_Interface, the system should return a response (either an answer or an explanation of why it cannot answer).

**Validates: Requirements 2.1, 2.5**

### Property 7: Citation Inclusion in Answers

*For any* answer generated by the RAG_Engine, the response should include citations referencing specific data sources.

**Validates: Requirements 2.2**

### Property 8: Conversation Context Preservation

*For any* sequence of questions in a conversation, the system should maintain context including the previous N turns (where N is the configured context window).

**Validates: Requirements 2.3**

### Property 9: Vector Store Retrieval

*For any* query to the RAG_Engine, ChromaDB should return a non-empty list of documents when relevant data exists in the vector store.

**Validates: Requirements 2.4**

### Property 10: Sentiment Analysis Completeness

*For any* set of text responses provided to the Qualitative_Analyzer, sentiment scores should be returned for all responses.

**Validates: Requirements 3.1**

### Property 11: Sentiment Categorization Validity

*For any* sentiment score calculated by the system, it should map to exactly one category: positive, negative, or neutral.

**Validates: Requirements 3.2**

### Property 12: Theme Identification

*For any* set of text responses with sufficient data (minimum N responses), the Qualitative_Analyzer should identify at least one theme.

**Validates: Requirements 3.3**

### Property 13: Theme Summary Completeness

*For any* set of identified themes, the summary should include frequency counts for all themes, and the sum of frequencies should equal the total number of analyzed responses.

**Validates: Requirements 3.4, 3.5**

### Property 14: Representative Quotes Association

*For any* identified theme, the system should provide representative quotes that actually contain keywords associated with that theme.

**Validates: Requirements 3.6**

### Property 15: Analysis Export Round-Trip

*For any* analysis results exported to CSV format, re-importing and parsing the CSV should produce data equivalent to the original analysis results.

**Validates: Requirements 3.7**

### Property 16: Report Statistical Content

*For any* report generated by the Report_Generator, it should contain descriptive statistics (mean, median, standard deviation, or count) for the included datasets.

**Validates: Requirements 4.1**

### Property 17: Report Narrative Inclusion

*For any* report generated by the Report_Generator, it should include narrative text sections explaining findings.

**Validates: Requirements 4.2**

### Property 18: Report Visualization Inclusion

*For any* report generated with visualizations enabled, the report should contain at least one visualization element.

**Validates: Requirements 4.3**

### Property 19: Report Export Format Validity

*For any* report exported to PDF or Markdown format, the exported file should be a valid file of the specified format.

**Validates: Requirements 4.4**

### Property 20: Report Citation Completeness

*For any* report generated from datasets, the report should include citations referencing all source datasets used.

**Validates: Requirements 4.5**

### Property 21: Conditional Theme Summary Inclusion

*For any* report where qualitative analysis has been performed, the report should include theme summaries in its content.

**Validates: Requirements 4.7**

### Property 22: Bar Chart Generation

*For any* categorical dataset with valid structure, the Visualization_Engine should generate a valid Plotly bar chart object.

**Validates: Requirements 5.1**

### Property 23: Line Chart Generation

*For any* time series dataset with valid structure, the Visualization_Engine should generate a valid Plotly line chart object.

**Validates: Requirements 5.2**

### Property 24: Pie Chart Generation

*For any* proportion dataset with valid structure, the Visualization_Engine should generate a valid Plotly pie chart object.

**Validates: Requirements 5.3**

### Property 25: Chart PNG Export

*For any* generated chart, exporting to PNG should produce a valid PNG image file.

**Validates: Requirements 5.5**
### Property 31: Audit Log Completeness

*For any* data access operation, a corresponding log entry should be created with timestamp, username, and action details.

**Validates: Requirements 6.7**

### Property 32: FAIR Metadata Completeness

*For any* dataset stored in the system, it should have associated metadata including at minimum: name, type, upload date, and row count. Optionally: title, description, source, and keywords.

**Validates: Requirements 7.1**

### Property 33: Dataset Export Interoperability

*For any* dataset exported from the system, the exported file should be in a standard format (CSV or JSON) that can be read by common data analysis tools.

**Validates: Requirements 7.2**

### Property 34: Data Provenance Tracking

*For any* dataset that has undergone analysis or transformation, the data provenance field should contain a record of operations performed.

**Validates: Requirements 7.3**

### Property 35: Data Manifest Generation

*For any* state of the system with one or more datasets, generating a data manifest should produce a valid JSON file listing all datasets with their metadata.

**Validates: Requirements 7.7**
**Validates: Requirements 5.6**

### Property 27: Chart Color Accessibility

*For any* color scheme used in generated charts, the contrast ratios should meet WCAG AA standards (minimum 4.5:1 for normal text, 3:1 for large text).

**Validates: Requirements 5.7**

### Property 28: Local Processing Guarantee

*For any* data processing operation (LLM inference, data storage, vector operations), the system should not make external network calls, verified by monitoring network activity.

**Validates: Requirements 6.1, 6.2, 6.3**

### Property 29: PII Redaction

*For any* output text containing PII patterns (email addresses, phone numbers, SSNs), the system should redact or flag the PII before display.

**Validates: Requirements 6.5**

### Property 30: Authentication Enforcement

*For any* request to access protected resources, unauthenticated requests should be rejected with an authentication error.

**Validates: Requirements 6.6**

### Property 31: Audit Log Completeness

*For any* data access operation, a corresponding log entry should be created with timestamp, username, and action details.

**Validates: Requirements 6.7**

### Edge Cases and Examples

The following criteria are best tested as specific examples rather than universal properties:

**Example Test 1: Ollama Model Configuration**
- Verify system is configured to use Llama 3.2 3B or Phi-3 Mini
- **Validates: Requirements 2.7**

**Example Test 2: ChromaDB Embedded Mode**
- Verify ChromaDB is initialized in embedded mode without external connections
- **Validates: Requirements 6.4**

**Example Test 3: Report Generation Performance**
- Verify report generation completes within 2 minutes for dataset with 1000 rows
- **Validates: Requirements 4.6**

### Non-Testable Criteria

The following criteria involve subjective qualities that cannot be automatically tested:

- **Requirement 2.6**: "User-friendly interface" is subjective and requires human evaluation
- **Requirement 5.4**: "Display visualizations in web interface" requires browser-based testing beyond unit/property test scope
