# Critical Edge Case Test Plan
## Immediate Action Items for System Robustness

**Generated:** 2026-04-03  
**Purpose:** Actionable test cases for the 15 highest-priority edge cases identified in the comprehensive analysis

---

## Test Execution Priority

### P0 - Critical (Execute This Week)
- [ ] Test 1: SQL Injection via Metadata JSON
- [ ] Test 2: PII Leakage in RAG Context
- [ ] Test 3: ChromaDB Indexing Silent Failures
- [ ] Test 4: Concurrent Dataset Operations

### P1 - High (Execute Next Week)
- [ ] Test 5: Large File Memory Exhaustion
- [ ] Test 6: Session ID Collisions
- [ ] Test 7: Brute Force Authentication
- [ ] Test 8: Database Corruption Detection

---

## P0 Tests (Critical)

### Test 1: SQL Injection via Metadata JSON

**Module:** `modules/csv_handler.py`  
**Function:** `store_dataset()`  
**Risk:** Database corruption, unauthorized data access

**Test Case 1.1: Malicious JSON in Keywords**
```python
def test_sql_injection_in_keywords():
    """Test that malicious JSON in keywords doesn't cause SQL injection."""
    df = pd.DataFrame({
        'response_date': ['2024-01-01'],
        'question': ['Test'],
        'response_text': ['Test response']
    })
    
    # Attempt SQL injection via keywords
    malicious_metadata = {
        'title': 'Test Dataset',
        'keywords': ["'; DROP TABLE datasets; --", "normal_keyword"]
    }
    
    # Should not raise exception or corrupt database
    dataset_id = csv_handler.store_dataset(
        df, 'test', 'survey', 'hash123', malicious_metadata
    )
    
    # Verify database integrity
    datasets = csv_handler.get_datasets()
    assert len(datasets) > 0, "Datasets table should not be dropped"
    
    # Verify keywords stored safely
    dataset = next(d for d in datasets if d['id'] == dataset_id)
    assert "DROP TABLE" in str(dataset['keywords']), "Malicious content should be escaped"
```

**Test Case 1.2: Deeply Nested JSON**
```python
def test_deeply_nested_json_in_metadata():
    """Test that deeply nested JSON doesn't cause stack overflow."""
    df = pd.DataFrame({'response_date': ['2024-01-01'], 'question': ['Test'], 'response_text': ['Test']})
    
    # Create deeply nested structure
    nested = {'level': 1}
    current = nested
    for i in range(1000):
        current['child'] = {'level': i + 2}
        current = current['child']
    
    malicious_metadata = {
        'title': 'Test',
        'description': json.dumps(nested)  # Deeply nested JSON as string
    }
    
    # Should handle gracefully (truncate or reject)
    try:
        dataset_id = csv_handler.store_dataset(df, 'test', 'survey', 'hash123', malicious_metadata)
        # If successful, verify it's stored safely
        datasets = csv_handler.get_datasets()
        dataset = next(d for d in datasets if d['id'] == dataset_id)
        assert len(dataset['description']) < 100000, "Should truncate excessive nesting"
    except ValueError as e:
        assert "nesting" in str(e).lower() or "depth" in str(e).lower()
```

**Fix Required:**
```python
# In csv_handler.py, add validation before json.dumps()
def _validate_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize metadata before storage."""
    MAX_NESTING_DEPTH = 5
    MAX_STRING_LENGTH = 10000
    
    def check_depth(obj, depth=0):
        if depth > MAX_NESTING_DEPTH:
            raise ValueError(f"Metadata nesting depth exceeds {MAX_NESTING_DEPTH}")
        if isinstance(obj, dict):
            for v in obj.values():
                check_depth(v, depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                check_depth(item, depth + 1)
    
    # Validate each field
    for key, value in metadata.items():
        if isinstance(value, str) and len(value) > MAX_STRING_LENGTH:
            metadata[key] = value[:MAX_STRING_LENGTH] + "... [truncated]"
        check_depth(value)
    
    return metadata
```

---

### Test 2: PII Leakage in RAG Context

**Module:** `modules/rag_query.py`  
**Function:** `query()`  
**Risk:** FERPA violation, privacy breach

**Test Case 2.1: PII in Source Data Paraphrased by LLM**
```python
def test_pii_paraphrasing_by_llm():
    """Test that LLM doesn't paraphrase PII from context."""
    # Create dataset with PII
    df = pd.DataFrame({
        'response_date': ['2024-01-01'],
        'question': ['Contact info'],
        'response_text': ['My email is john.doe@example.com and phone is 555-123-4567']
    })
    
    dataset_id = csv_handler.store_dataset(df, 'test_pii', 'survey', 'hash_pii', {})
    
    # Index in RAG
    rag = RAGQuery()
    rag.index_dataset(dataset_id)
    
    # Query that might trigger paraphrasing
    result = rag.query("What contact information did patrons provide?")
    
    # Answer should not contain PII in any form
    answer = result['answer'].lower()
    assert 'john' not in answer, "Name should be redacted"
    assert 'doe' not in answer, "Name should be redacted"
    assert '555-123-4567' not in answer, "Phone should be redacted"
    assert 'example.com' not in answer, "Email domain should be redacted"
    
    # Should contain redaction placeholders
    assert '[email]' in answer.lower() or 'redacted' in answer.lower()
```

**Test Case 2.2: PII in Retrieved Context**
```python
def test_pii_in_retrieved_context():
    """Test that retrieved context is scanned for PII before LLM generation."""
    df = pd.DataFrame({
        'response_date': ['2024-01-01'],
        'question': ['Feedback'],
        'response_text': ['Student ID 123-45-6789 had issues with SSN 987-65-4321']
    })
    
    dataset_id = csv_handler.store_dataset(df, 'test_pii2', 'survey', 'hash_pii2', {})
    
    rag = RAGQuery()
    rag.index_dataset(dataset_id)
    
    # Retrieve documents directly
    docs = rag.retrieve_relevant_docs("What issues did students have?")
    
    # Context should be redacted before LLM sees it
    for doc in docs:
        text = doc['text']
        assert '123-45-6789' not in text, "Student ID should be redacted from context"
        assert '987-65-4321' not in text, "SSN should be redacted from context"
```

**Fix Required:**
```python
# In rag_query.py, add PII redaction to retrieved context
def retrieve_relevant_docs(self, question: str, k: Optional[int] = None) -> List[Dict[str, Any]]:
    # ... existing retrieval code ...
    
    # Redact PII from retrieved documents before returning
    from modules.pii_detector import redact_pii
    for doc in documents:
        doc['text'], _ = redact_pii(doc['text'])
    
    return documents[:k]
```

---

### Test 3: ChromaDB Indexing Silent Failures

**Module:** `modules/rag_query.py`  
**Function:** `index_dataset()`  
**Risk:** Incomplete indexing, missing data in queries

**Test Case 3.1: Partial Indexing Failure**
```python
def test_partial_indexing_failure():
    """Test that partial indexing failures are detected and reported."""
    # Create large dataset
    df = pd.DataFrame({
        'response_date': [f'2024-01-{i:02d}' for i in range(1, 101)],
        'question': ['Test'] * 100,
        'response_text': [f'Response {i}' for i in range(100)]
    })
    
    dataset_id = csv_handler.store_dataset(df, 'test_large', 'survey', 'hash_large', {})
    
    # Mock ChromaDB to fail mid-batch
    rag = RAGQuery()
    original_add = rag.collection.add
    call_count = [0]
    
    def failing_add(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 2:  # Fail on second batch
            raise Exception("ChromaDB connection lost")
        return original_add(*args, **kwargs)
    
    rag.collection.add = failing_add
    
    # Indexing should raise exception, not silently fail
    with pytest.raises(Exception) as exc_info:
        rag.index_dataset(dataset_id)
    
    assert "ChromaDB" in str(exc_info.value)
    
    # Verify dataset is marked as not fully indexed
    assert not rag._is_dataset_indexed(dataset_id), "Should detect incomplete indexing"
```

**Test Case 3.2: Indexing Status Tracking**
```python
def test_indexing_status_tracking():
    """Test that indexing status is tracked in database."""
    df = pd.DataFrame({
        'response_date': ['2024-01-01'],
        'question': ['Test'],
        'response_text': ['Test response']
    })
    
    dataset_id = csv_handler.store_dataset(df, 'test_status', 'survey', 'hash_status', {})
    
    # Check initial status
    datasets = csv_handler.get_datasets()
    dataset = next(d for d in datasets if d['id'] == dataset_id)
    assert dataset.get('indexing_status') == 'not_indexed'
    
    # Index dataset
    rag = RAGQuery()
    num_docs = rag.index_dataset(dataset_id)
    
    # Verify status updated
    datasets = csv_handler.get_datasets()
    dataset = next(d for d in datasets if d['id'] == dataset_id)
    assert dataset.get('indexing_status') == 'indexed'
    assert dataset.get('indexed_doc_count') == num_docs
```

**Fix Required:**
```python
# Add indexing_status column to datasets table
# In database.py, add to schema:
cursor.execute("""
    ALTER TABLE datasets ADD COLUMN indexing_status TEXT DEFAULT 'not_indexed'
""")
cursor.execute("""
    ALTER TABLE datasets ADD COLUMN indexed_doc_count INTEGER DEFAULT 0
""")

# In rag_query.py, update status after indexing:
def index_dataset(self, dataset_id: int) -> int:
    try:
        # ... existing indexing code ...
        num_docs = len(texts)
        
        # Update status in database
        execute_update(
            "UPDATE datasets SET indexing_status = ?, indexed_doc_count = ? WHERE id = ?",
            ('indexed', num_docs, dataset_id)
        )
        
        return num_docs
    except Exception as e:
        # Mark as failed
        execute_update(
            "UPDATE datasets SET indexing_status = ? WHERE id = ?",
            ('failed', dataset_id)
        )
        raise
```

---

### Test 4: Concurrent Dataset Operations

**Module:** `modules/database.py`  
**Function:** `execute_update()`  
**Risk:** Data corruption, race conditions

**Test Case 4.1: Concurrent Dataset Creation**
```python
import threading
import time

def test_concurrent_dataset_creation():
    """Test that concurrent dataset creation doesn't cause corruption."""
    df = pd.DataFrame({
        'response_date': ['2024-01-01'],
        'question': ['Test'],
        'response_text': ['Test response']
    })
    
    results = []
    errors = []
    
    def create_dataset(i):
        try:
            dataset_id = csv_handler.store_dataset(
                df.copy(), f'concurrent_test_{i}', 'survey', f'hash_{i}', {}
            )
            results.append(dataset_id)
        except Exception as e:
            errors.append(str(e))
    
    # Create 10 datasets concurrently
    threads = [threading.Thread(target=create_dataset, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # All should succeed (or fail gracefully with retry)
    assert len(results) == 10, f"Expected 10 datasets, got {len(results)}. Errors: {errors}"
    assert len(set(results)) == 10, "Dataset IDs should be unique"
    
    # Verify database integrity
    datasets = csv_handler.get_datasets()
    concurrent_datasets = [d for d in datasets if d['name'].startswith('concurrent_test_')]
    assert len(concurrent_datasets) == 10
```

**Test Case 4.2: Concurrent Read-Write**
```python
def test_concurrent_read_write():
    """Test that concurrent reads during writes don't cause errors."""
    df = pd.DataFrame({
        'response_date': ['2024-01-01'],
        'question': ['Test'],
        'response_text': ['Test response']
    })
    
    dataset_id = csv_handler.store_dataset(df, 'rw_test', 'survey', 'hash_rw', {})
    
    read_results = []
    write_errors = []
    
    def read_datasets():
        for _ in range(100):
            try:
                datasets = csv_handler.get_datasets()
                read_results.append(len(datasets))
            except Exception as e:
                read_results.append(f"ERROR: {e}")
            time.sleep(0.01)
    
    def update_metadata():
        for i in range(50):
            try:
                csv_handler.update_dataset_metadata(
                    dataset_id,
                    {'title': f'Updated {i}', 'description': f'Description {i}'}
                )
            except Exception as e:
                write_errors.append(str(e))
            time.sleep(0.02)
    
    # Run concurrent reads and writes
    reader = threading.Thread(target=read_datasets)
    writer = threading.Thread(target=update_metadata)
    
    reader.start()
    writer.start()
    reader.join()
    writer.join()
    
    # No errors should occur
    error_count = sum(1 for r in read_results if isinstance(r, str) and 'ERROR' in r)
    assert error_count == 0, f"Read errors: {[r for r in read_results if isinstance(r, str)]}"
    assert len(write_errors) == 0, f"Write errors: {write_errors}"
```

**Fix Required:**
```python
# In database.py, enable WAL mode and add retry logic
def get_db_connection(db_path: Optional[str] = None):
    if db_path is None:
        db_path = Settings.DATABASE_PATH
    
    conn = sqlite3.connect(db_path, timeout=30.0)  # Increase timeout
    conn.row_factory = sqlite3.Row
    
    # Enable WAL mode for better concurrency
    conn.execute("PRAGMA journal_mode=WAL")
    
    try:
        yield conn
        conn.commit()
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            # Retry with exponential backoff
            for attempt in range(3):
                time.sleep(0.1 * (2 ** attempt))
                try:
                    conn.commit()
                    break
                except sqlite3.OperationalError:
                    if attempt == 2:
                        raise
        else:
            raise
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
```

---

## P1 Tests (High Priority)

### Test 5: Large File Memory Exhaustion

**Test Case 5.1: 500MB CSV File**
```python
def test_large_csv_file_handling():
    """Test that large CSV files don't exhaust memory."""
    import tempfile
    import psutil
    import os
    
    # Create 500MB CSV file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write('response_date,question,response_text\n')
        # Write 5 million rows (~500MB)
        for i in range(5_000_000):
            f.write(f'2024-01-01,Question {i},Response text for row {i}\n')
        temp_path = f.name
    
    try:
        # Monitor memory usage
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Parse CSV (should use chunking)
        with open(temp_path, 'rb') as f:
            is_valid, error = csv_handler.validate_csv(f, 'survey')
        
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        mem_increase = mem_after - mem_before
        
        # Memory increase should be < 1GB (file is 500MB)
        assert mem_increase < 1024, f"Memory increased by {mem_increase}MB (should use chunking)"
        
    finally:
        os.unlink(temp_path)
```

**Fix Required:**
```python
# In csv_handler.py, add chunked reading for large files
def validate_csv(file, dataset_type: str, strict_mode: bool = False) -> Tuple[bool, Optional[str]]:
    # Check file size first
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset
    
    CHUNK_SIZE_MB = 100
    if file_size > CHUNK_SIZE_MB * 1024 * 1024:
        # Use chunked reading for large files
        try:
            chunk_iter = pd.read_csv(file, chunksize=10000)
            first_chunk = next(chunk_iter)
            # Validate first chunk only
            # ... validation logic ...
        except Exception as e:
            return False, f"Error reading large file: {str(e)}"
    else:
        # Existing logic for small files
        df = parse_csv(file)
        # ... existing validation ...
```

---

### Test 6: Session ID Collisions

**Test Case 6.1: UUID Collision Detection**
```python
def test_session_id_uniqueness():
    """Test that session IDs are cryptographically unique."""
    rag = RAGQuery()
    
    # Generate 10,000 session IDs
    session_ids = set()
    for _ in range(10000):
        import uuid
        session_id = str(uuid.uuid4())
        assert session_id not in session_ids, "Session ID collision detected"
        session_ids.add(session_id)
        
        # Store conversation
        rag.query("Test question", session_id=session_id, username=f"user_{len(session_ids)}")
    
    # Verify all conversations are isolated
    assert len(rag.conversation_histories) == 10000
```

**Test Case 6.2: Session Isolation**
```python
def test_session_isolation():
    """Test that conversations don't leak between sessions."""
    rag = RAGQuery()
    
    # User 1 conversation
    result1 = rag.query("What is the average satisfaction?", session_id="session_1", username="user1")
    
    # User 2 conversation (different session)
    result2 = rag.query("What are the main themes?", session_id="session_2", username="user2")
    
    # User 1 follow-up
    result3 = rag.query("Can you elaborate?", session_id="session_1", username="user1")
    
    # User 1's history should not contain User 2's question
    history1 = rag.get_conversation_history("session_1")
    assert len(history1) == 2
    assert "themes" not in str(history1).lower()
    
    # User 2's history should not contain User 1's question
    history2 = rag.get_conversation_history("session_2")
    assert len(history2) == 1
    assert "satisfaction" not in str(history2).lower()
```

---

### Test 7: Brute Force Authentication

**Test Case 7.1: Rate Limiting**
```python
def test_authentication_rate_limiting():
    """Test that repeated failed logins are rate-limited."""
    import time
    
    # Attempt 100 failed logins rapidly
    start_time = time.time()
    failed_attempts = 0
    
    for i in range(100):
        result = auth.authenticate("admin", f"wrong_password_{i}")
        if not result:
            failed_attempts += 1
    
    elapsed = time.time() - start_time
    
    # Should take at least 10 seconds due to rate limiting (100ms per attempt minimum)
    assert elapsed > 10, f"100 attempts took only {elapsed}s (should be rate-limited)"
    assert failed_attempts == 100
```

**Fix Required:**
```python
# In auth.py, add rate limiting
import time
from collections import defaultdict

_login_attempts = defaultdict(list)  # username -> [timestamp, ...]
_RATE_LIMIT_WINDOW = 60  # seconds
_MAX_ATTEMPTS = 5

def authenticate(username: str, password: str) -> bool:
    # Check rate limit
    now = time.time()
    attempts = _login_attempts[username]
    
    # Remove old attempts outside window
    attempts = [t for t in attempts if now - t < _RATE_LIMIT_WINDOW]
    _login_attempts[username] = attempts
    
    if len(attempts) >= _MAX_ATTEMPTS:
        time.sleep(1)  # Slow down attacker
        return False
    
    # Record attempt
    _login_attempts[username].append(now)
    
    # ... existing authentication logic ...
```

---

### Test 8: Database Corruption Detection

**Test Case 8.1: Integrity Check on Startup**
```python
def test_database_integrity_check():
    """Test that database corruption is detected on startup."""
    import shutil
    
    # Create valid database
    init_database()
    
    # Corrupt database file
    db_path = Settings.DATABASE_PATH
    backup_path = db_path + '.backup'
    shutil.copy(db_path, backup_path)
    
    try:
        # Truncate database file (simulate corruption)
        with open(db_path, 'r+b') as f:
            f.truncate(100)  # Corrupt by truncating
        
        # Attempt to use database
        with pytest.raises(Exception) as exc_info:
            datasets = csv_handler.get_datasets()
        
        assert "corrupt" in str(exc_info.value).lower() or "malformed" in str(exc_info.value).lower()
        
    finally:
        # Restore backup
        shutil.copy(backup_path, db_path)
        os.unlink(backup_path)
```

**Fix Required:**
```python
# In database.py, add integrity check
def check_database_integrity(db_path: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """Check database integrity and return status."""
    if db_path is None:
        db_path = Settings.DATABASE_PATH
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Run integrity check
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        
        conn.close()
        
        if result == "ok":
            return True, None
        else:
            return False, f"Database integrity check failed: {result}"
    except Exception as e:
        return False, f"Cannot access database: {str(e)}"

# Call on application startup
def init_database(db_path: Optional[str] = None) -> None:
    # Check integrity first
    is_valid, error = check_database_integrity(db_path)
    if not is_valid:
        raise RuntimeError(f"Database corruption detected: {error}. Please restore from backup.")
    
    # ... existing initialization ...
```

---

## Test Execution Checklist

- [ ] Set up test environment with test database
- [ ] Install pytest and required testing libraries
- [ ] Create test fixtures for common data
- [ ] Run P0 tests and verify all pass
- [ ] Implement fixes for failing P0 tests
- [ ] Run P1 tests and verify all pass
- [ ] Implement fixes for failing P1 tests
- [ ] Add tests to CI/CD pipeline
- [ ] Document test results and coverage improvements

---

## Success Criteria

- All P0 tests pass with fixes implemented
- All P1 tests pass with fixes implemented
- Test coverage increases by at least 15%
- No critical security vulnerabilities remain
- System handles edge cases gracefully with clear error messages
