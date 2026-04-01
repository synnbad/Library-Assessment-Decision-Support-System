# Testing Guide

## Overview

The FERPA-Compliant RAG Decision Support System uses a comprehensive testing strategy combining unit tests, integration tests, property-based tests, and manual tests to ensure correctness and reliability.

## Testing Philosophy

**Dual Testing Approach:**
- **Unit Tests:** Verify specific examples, edge cases, and error conditions
- **Property-Based Tests:** Verify universal properties across all inputs
- **Integration Tests:** Verify complete workflows end-to-end
- **Manual Tests:** Verify UI interactions and visual quality

**Coverage Goals:**
- Minimum 80% code coverage
- 100% coverage of error handling paths
- All correctness properties tested
- Integration tests for main workflows

## Test Organization

```
tests/
├── unit/                    # Unit tests for individual functions
│   ├── test_auth.py
│   ├── test_csv_handler.py
│   ├── test_csv_error_handling.py
│   ├── test_pii_detector.py
│   ├── test_report_generator.py
│   ├── test_visualization.py
│   └── ...
├── integration/             # Integration tests for workflows
│   ├── test_data_upload.py
│   ├── test_query_interface.py
│   ├── test_report_assembly.py
│   └── ...
├── property/                # Property-based tests (Hypothesis)
│   └── (property tests TBD)
└── manual/                  # Manual test scripts for UI
    ├── test_upload_page.py
    ├── test_query_interface.py
    ├── test_visualization_page.py
    └── ...
```

## Running Tests

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=modules --cov-report=html
```

### Run Specific Test Category
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Property-based tests only
pytest tests/property/
```

### Run Specific Test File
```bash
pytest tests/unit/test_csv_handler.py
```

### Run with Verbose Output
```bash
pytest -v
```

### Run Specific Test Function
```bash
pytest tests/unit/test_csv_handler.py::test_validate_csv_valid_survey
```


## Unit Tests

### Purpose
Test individual functions in isolation with specific examples and edge cases.

### Approach
- Mock external dependencies (Ollama, ChromaDB)
- Test happy path and error conditions
- Verify error messages are user-friendly
- Test edge cases (empty inputs, special characters, etc.)

### Example: CSV Handler Tests

**Test Categories:**
1. **Valid CSV Files:** Verify successful parsing
2. **Invalid Format:** Test malformed CSV, non-CSV content
3. **Missing Columns:** Test error messages for missing required columns
4. **Empty Files:** Test empty file detection
5. **Duplicate Detection:** Test file hash-based duplicate detection
6. **Error Message Quality:** Verify messages are actionable

**Example Test:**
```python
def test_missing_columns_error_message():
    """Test that missing columns error provides expected columns."""
    csv_content = """wrong_col1,wrong_col2
val1,val2"""
    
    file = StringIO(csv_content)
    is_valid, error = csv_handler.validate_csv(file, "survey")
    
    assert is_valid is False
    assert "Missing required columns" in error
    assert "Expected columns" in error
    assert "response_date" in error
    assert "question" in error
    assert "response_text" in error
```

### Running Unit Tests
```bash
# All unit tests
pytest tests/unit/

# Specific module
pytest tests/unit/test_csv_handler.py

# With coverage
pytest tests/unit/ --cov=modules.csv_handler
```

## Integration Tests

### Purpose
Test complete workflows end-to-end with real components.

### Approach
- Use test database and ChromaDB instance
- Verify data flows correctly between modules
- Test error propagation
- Verify state changes

### Example: Data Upload Workflow

**Test Flow:**
1. Upload CSV file
2. Verify validation passes
3. Verify data stored in database
4. Verify preview matches uploaded data
5. Verify dataset appears in list
6. Verify dataset can be deleted

**Example Test:**
```python
def test_complete_upload_workflow():
    """Test complete data upload workflow."""
    # Create test CSV
    df = pd.DataFrame({
        'response_date': ['2024-01-15'],
        'question': ['How satisfied?'],
        'response_text': ['Very satisfied']
    })
    
    # Store dataset
    dataset_id = csv_handler.store_dataset(
        df, 'test_dataset', 'survey', 'test_hash', {}
    )
    
    # Verify in database
    datasets = csv_handler.get_datasets()
    assert any(d['id'] == dataset_id for d in datasets)
    
    # Verify preview
    preview = csv_handler.get_preview(dataset_id, n_rows=10)
    assert len(preview) == 1
    
    # Clean up
    csv_handler.delete_dataset(dataset_id)
```

### Running Integration Tests
```bash
# All integration tests
pytest tests/integration/

# Specific workflow
pytest tests/integration/test_data_upload.py
```


## Property-Based Tests

### Purpose
Verify universal properties that should hold across all inputs using Hypothesis.

### Approach
- Generate random test data
- Verify properties hold for all generated inputs
- Minimum 100 iterations per property
- Focus on data integrity and invariants

### Configuration
```python
from hypothesis import given, settings
import hypothesis.strategies as st

@settings(max_examples=100)  # Minimum 100 iterations
@given(...)
def test_property_name(...):
    """Feature: ferpa-compliant-rag-dss, Property N: [property text]"""
    # Test implementation
```

### Example Properties

**Property 1: CSV Upload Acceptance**
```python
@settings(max_examples=100)
@given(
    dataset_type=st.sampled_from(['survey', 'usage', 'circulation']),
    data=st.data()
)
def test_csv_upload_acceptance(dataset_type, data):
    """Property 1: For any valid CSV and dataset type, upload succeeds."""
    # Generate valid CSV for dataset type
    df = generate_valid_csv(dataset_type, data)
    
    # Upload should succeed
    dataset_id = csv_handler.store_dataset(df, 'test', dataset_type, 'hash', {})
    assert dataset_id > 0
    
    # Clean up
    csv_handler.delete_dataset(dataset_id)
```

**Property 3: Data Storage Round-Trip**
```python
@settings(max_examples=100)
@given(
    data=st.data()
)
def test_data_storage_round_trip(data):
    """Property 3: For any valid CSV, querying DB returns equivalent data."""
    # Generate and store data
    df = generate_valid_survey_csv(data)
    dataset_id = csv_handler.store_dataset(df, 'test', 'survey', 'hash', {})
    
    # Retrieve data
    retrieved = csv_handler.get_preview(dataset_id, n_rows=len(df))
    
    # Verify equivalence
    assert len(retrieved) == len(df)
    assert set(retrieved.columns) >= set(df.columns)
    
    # Clean up
    csv_handler.delete_dataset(dataset_id)
```

### Running Property-Based Tests
```bash
# All property tests
pytest tests/property/

# With verbose output to see generated examples
pytest tests/property/ -v

# Run more examples for thorough testing
pytest tests/property/ --hypothesis-show-statistics
```

## Manual Tests

### Purpose
Verify UI interactions, visual quality, and user experience.

### Approach
- Manual execution of test scripts
- Visual verification of outputs
- User experience assessment
- Performance testing with large datasets

### Test Scripts

**1. Upload Page Test (tests/manual/test_upload_page.py)**
- Verify file uploader works
- Test validation error messages
- Verify preview display
- Test metadata form
- Verify success messages

**2. Query Interface Test (tests/manual/test_query_interface.py)**
- Verify chat interface
- Test question submission
- Verify answer display
- Test citations display
- Verify conversation context
- Test suggested questions

**3. Visualization Page Test (tests/manual/test_visualization_page.py)**
- Verify chart generation
- Test different chart types
- Verify color accessibility
- Test export functionality
- Verify responsive sizing

### Running Manual Tests
```bash
# Start application
streamlit run streamlit_app.py

# Follow test script instructions
# Manually verify each step
# Document any issues found
```


## Test Data

### Synthetic CSV Files

**Survey Data:**
```csv
response_date,question,response_text
2024-01-15,How satisfied?,Very satisfied with services
2024-01-16,What improvements?,More study spaces needed
2024-01-17,Overall experience?,Great experience overall
```

**Usage Data:**
```csv
date,metric_name,metric_value,category
2024-01-15,visits,150,daily
2024-01-16,checkouts,45,daily
2024-01-17,database_searches,230,daily
```

**Circulation Data:**
```csv
checkout_date,material_type,patron_type
2024-01-15,book,undergraduate
2024-01-16,dvd,graduate
2024-01-17,journal,faculty
```

### Edge Cases

**Empty File:**
```csv
```

**Headers Only:**
```csv
response_date,question,response_text
```

**Missing Columns:**
```csv
response_date,question
2024-01-15,How satisfied?
```

**Special Characters:**
```csv
response_date,question,response_text
2024-01-15,"How satisfied?","Very satisfied! 😊"
2024-01-16,"What's needed?","More spaces & resources"
```

**Commas in Fields:**
```csv
response_date,question,response_text
2024-01-15,"How satisfied?","Very satisfied, extremely happy"
```

### Performance Datasets

**Large Survey Dataset (1000 rows):**
- Generated programmatically
- Various response lengths
- Mixed sentiments
- Multiple themes

**Large Usage Dataset (5000 rows):**
- Time series data
- Multiple metrics
- Various categories

## Mocking External Dependencies

### Ollama LLM
```python
from unittest.mock import Mock, patch

@patch('ollama.generate')
def test_rag_query_with_mock_llm(mock_generate):
    """Test RAG query with mocked Ollama."""
    # Mock LLM response
    mock_generate.return_value = {
        'response': 'This is a test answer with citations.'
    }
    
    # Test query
    rag = RAGQuery()
    result = rag.query("Test question")
    
    assert 'answer' in result
    assert mock_generate.called
```

### ChromaDB
```python
@patch('chromadb.PersistentClient')
def test_rag_indexing_with_mock_chroma(mock_client):
    """Test document indexing with mocked ChromaDB."""
    # Mock ChromaDB collection
    mock_collection = Mock()
    mock_client.return_value.get_or_create_collection.return_value = mock_collection
    
    # Test indexing
    rag = RAGQuery()
    rag.index_documents(['test doc'], [{'id': 1}])
    
    assert mock_collection.add.called
```

## Continuous Integration

### GitHub Actions Workflow (Example)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        python -m textblob.download_corpora
    
    - name: Run tests
      run: |
        pytest --cov=modules --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```


## Test Coverage

### Viewing Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=modules --cov-report=html

# Open report in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Coverage Goals by Module

| Module | Target Coverage | Focus Areas |
|--------|----------------|-------------|
| csv_handler.py | 90% | Validation, error handling |
| auth.py | 85% | Authentication, logging |
| rag_query.py | 75% | Query processing, error handling |
| qualitative_analysis.py | 80% | Sentiment, theme extraction |
| report_generator.py | 80% | Statistics, narrative generation |
| visualization.py | 85% | Chart generation, export |
| database.py | 90% | Schema, queries |
| pii_detector.py | 95% | Detection, redaction |

### Uncovered Code

**Acceptable Uncovered Code:**
- Streamlit UI code (tested manually)
- Error handling for rare edge cases
- Defensive programming checks
- Logging statements

**Must Be Covered:**
- Core business logic
- Data validation
- Error handling for common cases
- Security-critical code (auth, PII)

## Debugging Tests

### Run Single Test with Print Statements
```bash
pytest tests/unit/test_csv_handler.py::test_validate_csv -s
```

### Run with Debugger
```bash
pytest tests/unit/test_csv_handler.py::test_validate_csv --pdb
```

### Show Test Output
```bash
pytest -v -s
```

### Run Failed Tests Only
```bash
pytest --lf  # last failed
pytest --ff  # failed first
```

## Performance Testing

### Timing Tests
```python
import time

def test_query_performance():
    """Test that queries complete within acceptable time."""
    rag = RAGQuery()
    
    start = time.time()
    result = rag.query("Test question")
    duration = time.time() - start
    
    # Should complete within 30 seconds
    assert duration < 30
```

### Memory Testing
```python
import tracemalloc

def test_memory_usage():
    """Test that analysis doesn't exceed memory limits."""
    tracemalloc.start()
    
    # Run analysis
    analyze_dataset_sentiment(dataset_id=1)
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    # Should use less than 500MB
    assert peak < 500 * 1024 * 1024
```

## Test Maintenance

### Adding New Tests

1. **Identify Test Category:** Unit, integration, property, or manual
2. **Create Test File:** Follow naming convention `test_*.py`
3. **Write Test Function:** Use descriptive name `test_*`
4. **Add Docstring:** Explain what is being tested
5. **Run Test:** Verify it passes
6. **Update Coverage:** Check coverage report

### Updating Existing Tests

1. **Understand Test Purpose:** Read docstring and code
2. **Make Changes:** Update test logic
3. **Verify Still Passes:** Run test
4. **Check Coverage:** Ensure coverage maintained
5. **Update Documentation:** If test behavior changed

### Removing Obsolete Tests

1. **Verify Obsolete:** Confirm feature removed or changed
2. **Check Dependencies:** Ensure no other tests depend on it
3. **Remove Test:** Delete test function
4. **Update Coverage:** Verify coverage still acceptable
5. **Document Removal:** Note in commit message

## Best Practices

### Test Naming
- Use descriptive names: `test_validate_csv_with_missing_columns`
- Include what is being tested and expected outcome
- Group related tests in classes

### Test Structure
- **Arrange:** Set up test data
- **Act:** Execute function being tested
- **Assert:** Verify expected outcome
- **Cleanup:** Remove test data

### Test Independence
- Each test should be independent
- Don't rely on test execution order
- Clean up test data after each test
- Use fixtures for shared setup

### Test Documentation
- Add docstrings to all test functions
- Explain what is being tested
- Note any special setup or requirements
- Reference requirements if applicable

### Error Messages
- Use descriptive assertion messages
- Help future developers understand failures
- Include actual vs expected values

```python
def test_example():
    """Test example with good error message."""
    result = some_function()
    expected = "expected value"
    assert result == expected, f"Expected '{expected}', got '{result}'"
```

## Troubleshooting

### Tests Fail Locally But Pass in CI
- Check Python version matches CI
- Verify all dependencies installed
- Check for environment-specific code
- Review test isolation

### Tests Pass Locally But Fail in CI
- Check for timing issues (use timeouts)
- Verify test data is committed
- Check for hardcoded paths
- Review CI environment differences

### Flaky Tests
- Add retries for network-dependent tests
- Increase timeouts for slow operations
- Mock external dependencies
- Check for race conditions

### Slow Tests
- Mock expensive operations
- Use smaller test datasets
- Parallelize test execution
- Profile tests to find bottlenecks

```bash
# Run tests in parallel
pytest -n auto
```

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
