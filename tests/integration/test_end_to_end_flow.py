"""
Integration test for end-to-end upload and query flow.

This test validates the complete workflow from uploading a CSV file,
indexing it in ChromaDB, querying the RAG engine, and receiving an
answer with citations.

Tests Requirements: 1.1, 2.1, 2.2

NOTE: This test requires:
- ChromaDB and sentence-transformers to be installed
- Ollama to be running locally with llama3.2:3b model
- All dependencies from requirements.txt

To run this test:
1. Install dependencies: pip install -r requirements.txt
2. Start Ollama: ollama serve
3. Pull model: ollama pull llama3.2:3b
4. Run test: pytest tests/integration/test_end_to_end_flow.py -v

If dependencies are not available, this test will be skipped.
"""

import pytest
import pandas as pd
import os
import shutil
from io import StringIO
from pathlib import Path
from uuid import uuid4

# Try to import required modules
try:
    from modules.csv_handler import (
        validate_csv, parse_csv, store_dataset, 
        get_datasets, delete_dataset
    )
    from modules.rag_query import RAGQuery
    from modules.database import init_database
    from config import settings
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    SKIP_REASON = f"Required dependencies not available: {str(e)}"


# Skip all tests if dependencies are not available
pytestmark = pytest.mark.skipif(
    not DEPENDENCIES_AVAILABLE,
    reason="ChromaDB, sentence-transformers, or other dependencies not installed"
)


@pytest.fixture
def setup_test_environment():
    """Set up a temporary test database and ChromaDB."""
    if not DEPENDENCIES_AVAILABLE:
        pytest.skip("Dependencies not available")

    workspace_tmp_root = Path.cwd() / ".tmp_e2e"
    workspace_tmp_root.mkdir(exist_ok=True)
    temp_db_path = workspace_tmp_root / f"{uuid4().hex}.db"
    temp_chroma_dir = workspace_tmp_root / f"chroma_{uuid4().hex}"
    temp_chroma_dir.mkdir()
    
    # Override paths
    original_db_path = settings.Settings.DATABASE_PATH
    original_chroma_path = settings.Settings.CHROMA_DB_PATH
    
    settings.Settings.DATABASE_PATH = str(temp_db_path)
    settings.Settings.CHROMA_DB_PATH = str(temp_chroma_dir)
    
    # Initialize database
    init_database()
    
    yield {
        'db_path': str(temp_db_path),
        'chroma_path': str(temp_chroma_dir)
    }
    
    # Cleanup
    settings.Settings.DATABASE_PATH = original_db_path
    settings.Settings.CHROMA_DB_PATH = original_chroma_path
    
    try:
        os.unlink(temp_db_path)
    except OSError:
        pass
    
    try:
        shutil.rmtree(temp_chroma_dir, ignore_errors=True)
    except OSError:
        pass


@pytest.fixture
def sample_survey_csv():
    """Create a sample survey CSV file."""
    csv_content = """response_date,question,response_text
2024-01-15,What do you like most about the library?,"The quiet study spaces are excellent for focused work."
2024-01-16,What do you like most about the library?,"I love the extensive collection of research databases."
2024-01-17,What could we improve?,"The hours are too limited on weekends."
2024-01-18,What do you like most about the library?,"The staff are always helpful and knowledgeable."
2024-01-19,What could we improve?,"More power outlets near study areas would be great."
"""
    return StringIO(csv_content)


def test_end_to_end_upload_and_query_flow(setup_test_environment, sample_survey_csv):
    """
    Test complete end-to-end flow: CSV upload → indexing → query → answer with citations.
    
    This integration test validates:
    1. CSV file upload and validation (Requirement 1.1)
    2. Data storage in SQLite
    3. Document indexing in ChromaDB
    4. Natural language query processing (Requirement 2.1)
    5. Answer generation with citations (Requirement 2.2)
    
    Validates Requirements: 1.1, 2.1, 2.2
    """
    # Step 1: Validate CSV file
    is_valid, error = validate_csv(sample_survey_csv, "survey")
    assert is_valid is True, f"CSV validation failed: {error}"
    assert error is None
    
    # Step 2: Parse CSV file
    sample_survey_csv.seek(0)  # Reset file pointer
    df = parse_csv(sample_survey_csv)
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 5  # Should have 5 rows
    assert 'response_date' in df.columns
    assert 'question' in df.columns
    assert 'response_text' in df.columns
    
    # Step 3: Store dataset in SQLite
    metadata = {
        'title': 'Test Survey for E2E Flow',
        'description': 'Integration test dataset',
        'source': 'pytest',
        'keywords': ['test', 'integration', 'e2e']
    }
    
    dataset_id = store_dataset(
        df,
        'e2e_test_survey',
        'survey',
        'test_hash_e2e_12345',
        metadata
    )
    
    assert dataset_id is not None
    assert dataset_id > 0
    
    # Verify dataset was stored
    datasets = get_datasets()
    test_dataset = next((d for d in datasets if d['id'] == dataset_id), None)
    assert test_dataset is not None
    assert test_dataset['name'] == 'e2e_test_survey'
    assert test_dataset['dataset_type'] == 'survey'
    assert test_dataset['row_count'] == 5
    
    # Step 4: Initialize RAG engine and index the dataset
    rag_engine = RAGQuery()
    
    # Test Ollama connection first
    is_connected, error_msg = rag_engine.test_ollama_connection()
    if not is_connected:
        pytest.skip(f"Ollama not running: {error_msg}")
    
    # Index the dataset in ChromaDB
    indexed_count = rag_engine.index_dataset(dataset_id)
    assert indexed_count == 5, f"Expected 5 documents indexed, got {indexed_count}"
    
    # Step 5: Query the RAG engine
    question = "What do students like about the library?"
    
    result = rag_engine.query(
        question=question,
        session_id="test_e2e_session",
        username="test_user"
    )
    
    # Step 6: Validate query result structure
    assert 'answer' in result
    assert 'citations' in result
    assert 'confidence' in result
    assert 'suggested_questions' in result
    assert 'processing_time_ms' in result
    
    # Step 7: Validate answer content
    assert len(result['answer']) > 0, "Answer should not be empty"
    assert isinstance(result['answer'], str)
    
    # Answer should mention something from the data
    # (This is a weak assertion since LLM output varies)
    answer_lower = result['answer'].lower()
    assert any(keyword in answer_lower for keyword in [
        'study', 'database', 'staff', 'helpful', 'library'
    ]), "Answer should reference content from the survey data"
    
    # Step 8: Validate citations (Requirement 2.2)
    assert isinstance(result['citations'], list)
    assert len(result['citations']) > 0, "Citations should be provided"
    
    # Verify citation structure
    for citation in result['citations']:
        assert 'source_number' in citation
        assert 'dataset_id' in citation
        assert 'dataset_type' in citation
        assert citation['dataset_id'] == str(dataset_id)
        assert citation['dataset_type'] == 'survey'
    
    # Step 9: Validate confidence score
    assert isinstance(result['confidence'], float)
    assert 0.0 <= result['confidence'] <= 1.0
    
    # Step 10: Validate suggested questions
    assert isinstance(result['suggested_questions'], list)
    assert len(result['suggested_questions']) > 0
    
    # Step 11: Validate processing time
    assert isinstance(result['processing_time_ms'], int)
    assert result['processing_time_ms'] > 0
    
    # Step 12: Test follow-up query with conversation context
    follow_up_question = "What improvements were suggested?"
    
    follow_up_result = rag_engine.query(
        question=follow_up_question,
        session_id="test_e2e_session",  # Same session to maintain context
        username="test_user"
    )
    
    assert 'answer' in follow_up_result
    assert len(follow_up_result['answer']) > 0
    
    # Verify conversation history is maintained
    history = rag_engine.get_conversation_history("test_e2e_session")
    assert len(history) == 2, "Should have 2 conversation turns"
    assert history[0]['question'] == question
    assert history[1]['question'] == follow_up_question
    
    # Cleanup
    delete_dataset(dataset_id)


def test_end_to_end_flow_with_no_relevant_data(setup_test_environment):
    """
    Test end-to-end flow when query has no relevant data.
    
    This validates that the system handles queries gracefully when
    no relevant documents are found in the vector store.
    
    Validates Requirements: 2.1, 2.5
    """
    # Initialize RAG engine with empty database
    rag_engine = RAGQuery()
    
    # Query without any indexed data
    result = rag_engine.query(
        question="What are the library usage statistics?",
        session_id="test_empty_session",
        username="test_user"
    )
    
    # Validate result structure
    assert 'answer' in result
    assert 'citations' in result
    assert 'error_type' in result
    
    # Verify error type is set
    assert result['error_type'] == 'no_relevant_data'
    
    # Verify answer explains the issue
    answer_lower = result['answer'].lower()
    assert any(phrase in answer_lower for phrase in [
        "couldn't find", "no data", "upload data", "no relevant"
    ]), "Answer should explain that no relevant data was found"
    
    # Verify no citations (no data found)
    assert len(result['citations']) == 0
    
    # Verify confidence is low
    assert result['confidence'] == 0.0
    
    # Verify suggested questions are provided
    assert len(result['suggested_questions']) > 0


def test_end_to_end_flow_multiple_datasets(setup_test_environment):
    """
    Test end-to-end flow with multiple datasets indexed.
    
    This validates that the RAG engine can retrieve and cite
    information from multiple datasets correctly.
    
    Validates Requirements: 1.1, 1.6, 2.1, 2.2
    """
    # Create first dataset (survey)
    survey_csv = StringIO("""response_date,question,response_text
2024-01-15,What do you like?,The study spaces are great
2024-01-16,What do you like?,The databases are helpful
""")
    
    df1 = parse_csv(survey_csv)
    dataset_id_1 = store_dataset(
        df1, 'survey_dataset', 'survey', 'hash_1', 
        {'title': 'Survey Data'}
    )
    
    # Create second dataset (usage)
    usage_csv = StringIO("""date,metric_name,metric_value
2024-01-15,Daily Visitors,450
2024-01-16,Daily Visitors,520
""")
    
    df2 = parse_csv(usage_csv)
    dataset_id_2 = store_dataset(
        df2, 'usage_dataset', 'usage', 'hash_2',
        {'title': 'Usage Statistics'}
    )
    
    # Initialize RAG engine
    rag_engine = RAGQuery()
    
    # Test Ollama connection
    is_connected, error_msg = rag_engine.test_ollama_connection()
    if not is_connected:
        pytest.skip(f"Ollama not running: {error_msg}")
    
    # Index both datasets
    count1 = rag_engine.index_dataset(dataset_id_1)
    count2 = rag_engine.index_dataset(dataset_id_2)
    
    assert count1 == 2
    assert count2 == 2
    
    # Query that should retrieve from survey dataset
    result = rag_engine.query(
        question="What feedback did we receive about the library?",
        session_id="test_multi_session",
        username="test_user"
    )
    
    assert len(result['answer']) > 0
    assert len(result['citations']) > 0
    
    # Verify citations reference the correct dataset
    citation_dataset_ids = [int(c['dataset_id']) for c in result['citations']]
    assert dataset_id_1 in citation_dataset_ids or dataset_id_2 in citation_dataset_ids
    
    # Cleanup
    delete_dataset(dataset_id_1)
    delete_dataset(dataset_id_2)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
