"""
Integration tests for query interface functionality.

Tests the integration between the RAG query module and the Streamlit interface,
verifying that queries can be processed and results displayed correctly.

NOTE: These tests require:
- ChromaDB and sentence-transformers to be installed
- Ollama to be running locally with llama3.2:3b model
- All dependencies from requirements.txt

To run these tests:
1. Install dependencies: pip install -r requirements.txt
2. Start Ollama: ollama serve
3. Pull model: ollama pull llama3.2:3b
4. Run tests: pytest tests/integration/test_query_interface.py -v

If dependencies are not available, these tests will be skipped.
"""

import pytest

# Try to import required modules
try:
    from modules.rag_query import RAGQuery, get_missing_rag_dependencies
    from modules.database import init_database
    from modules.csv_handler import store_dataset
    import pandas as pd
    import os
    from pathlib import Path
    from uuid import uuid4
    DEPENDENCIES_AVAILABLE = len(get_missing_rag_dependencies()) == 0
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    SKIP_REASON = f"Required dependencies not available: {str(e)}"


@pytest.fixture
def setup_test_db():
    """Set up a temporary test database."""
    if not DEPENDENCIES_AVAILABLE:
        pytest.skip("Dependencies not available")

    workspace_tmp_root = Path.cwd() / ".tmp_pytest_query"
    workspace_tmp_root.mkdir(exist_ok=True)
    
    # Create temporary database
    temp_db_path = workspace_tmp_root / f"{uuid4().hex}.db"
    
    # Override database path
    from config import settings
    original_db_path = settings.Settings.DATABASE_PATH
    original_chroma_path = settings.Settings.CHROMA_DB_PATH
    temp_chroma_dir = workspace_tmp_root / f"chroma_{uuid4().hex}"
    temp_chroma_dir.mkdir()
    settings.Settings.DATABASE_PATH = str(temp_db_path)
    settings.Settings.CHROMA_DB_PATH = str(temp_chroma_dir)
    
    # Initialize database
    init_database()
    
    yield str(temp_db_path)
    
    # Cleanup
    settings.Settings.DATABASE_PATH = original_db_path
    settings.Settings.CHROMA_DB_PATH = original_chroma_path
    try:
        os.unlink(temp_db_path)
    except OSError:
        pass
    try:
        import shutil
        shutil.rmtree(temp_chroma_dir, ignore_errors=True)
    except OSError:
        pass


@pytest.fixture
def sample_survey_data():
    """Create sample survey data for testing."""
    if not DEPENDENCIES_AVAILABLE:
        pytest.skip("Dependencies not available")
    
    return pd.DataFrame({
        'response_date': ['2024-01-15', '2024-01-16', '2024-01-17'],
        'question': ['How satisfied are you with library services?'] * 3,
        'response_text': [
            'Very satisfied with the study spaces and helpful staff.',
            'The library hours are great but need more computers.',
            'Excellent resources and quiet environment for studying.'
        ]
    })


def test_query_interface_basic_structure():
    """
    Test that query interface components are properly structured.
    
    This is a lightweight test that verifies the interface structure without
    requiring full dependencies.
    
    Validates Requirements: 2.6
    """
    from ui.query_ui import show_query_interface_page

    # Verify the workflow registry points at the modularized Ask interface
    import streamlit_app
    assert "Ask" in streamlit_app.PAGE_REGISTRY
    assert streamlit_app.PAGE_REGISTRY["Ask"] == ("ui.query_ui", "show_query_interface_page")
    assert callable(show_query_interface_page)


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Full dependencies required")
def test_query_interface_basic_flow(setup_test_db, sample_survey_data):
    """
    Test basic query interface flow: upload data, index, query, get answer.
    
    Validates Requirements: 2.1, 2.2
    """
    # Store sample dataset
    dataset_id = store_dataset(
        sample_survey_data,
        'test_survey',
        'survey',
        'test_hash_123',
        {'title': 'Test Survey', 'description': 'Test data'}
    )
    
    assert dataset_id is not None
    
    # Initialize RAG engine
    rag_engine = RAGQuery()
    
    # Index the dataset
    indexed_count = rag_engine.index_dataset(dataset_id)
    assert indexed_count == 3  # Should index 3 survey responses
    
    # Query the data (may fail if Ollama not running, that's ok for this test)
    try:
        result = rag_engine.query(
            question="What do students say about the library?",
            session_id="test_session_1",
            username="test_user"
        )
        
        # Verify result structure
        assert 'answer' in result
        assert 'citations' in result
        assert 'confidence' in result
        assert 'suggested_questions' in result
        assert 'processing_time_ms' in result
        
        # Verify answer is not empty
        assert len(result['answer']) > 0
        
        # Verify confidence is a valid value
        assert 0.0 <= result['confidence'] <= 1.0
        
        # Verify processing time is recorded
        assert result['processing_time_ms'] > 0
    except RuntimeError as e:
        # If Ollama is not running, that's expected in CI/CD
        if "Ollama" in str(e):
            pytest.skip("Ollama not running - expected in test environment")
        else:
            raise


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Full dependencies required")
def test_query_interface_conversation_context(setup_test_db, sample_survey_data):
    """
    Test that conversation context is maintained across multiple queries.
    
    Validates Requirements: 2.3
    """
    # Store sample dataset
    dataset_id = store_dataset(
        sample_survey_data,
        'test_survey',
        'survey',
        'test_hash_456',
        {'title': 'Test Survey', 'description': 'Test data'}
    )
    
    # Initialize RAG engine
    rag_engine = RAGQuery()
    rag_engine.index_dataset(dataset_id)
    
    session_id = "test_session_2"
    
    # Test conversation history management without requiring Ollama
    # Verify initial state
    history = rag_engine.get_conversation_history(session_id)
    assert len(history) == 0
    
    # Manually add to conversation history (simulating queries)
    rag_engine.conversation_histories[session_id] = [
        {"question": "First question", "answer": "First answer"},
        {"question": "Second question", "answer": "Second answer"}
    ]
    
    # Verify history is maintained
    history = rag_engine.get_conversation_history(session_id)
    assert len(history) == 2
    
    # Clear conversation
    rag_engine.clear_conversation(session_id)
    
    # Verify history is cleared
    history = rag_engine.get_conversation_history(session_id)
    assert len(history) == 0


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Full dependencies required")
def test_query_interface_no_relevant_data(setup_test_db):
    """
    Test that the system handles queries when no relevant data is found.
    
    Validates Requirements: 2.5
    """
    # Initialize RAG engine with empty database
    rag_engine = RAGQuery()
    
    # Query without any indexed data (should not require Ollama)
    result = rag_engine.query(
        question="What is the library usage?",
        session_id="test_session_3",
        username="test_user"
    )
    
    # Verify result structure
    assert 'answer' in result
    assert 'citations' in result
    
    # Verify answer explains no data was found
    assert "couldn't find relevant data" in result['answer'].lower() or \
           "no data" in result['answer'].lower() or \
           "upload data" in result['answer'].lower()
    
    # Verify no citations (no data found)
    assert len(result['citations']) == 0
    
    # Verify suggested questions are provided
    assert len(result['suggested_questions']) > 0


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Full dependencies required")
def test_query_interface_ollama_connection():
    """
    Test that Ollama connection is properly tested.
    
    Validates Requirements: 2.1
    """
    # Initialize RAG engine
    rag_engine = RAGQuery()
    
    # Test connection
    is_connected, error_msg = rag_engine.test_ollama_connection()
    
    # Verify return type
    assert isinstance(is_connected, bool)
    
    if not is_connected:
        # If not connected, error message should be provided
        assert error_msg is not None
        assert len(error_msg) > 0
    else:
        # If connected, no error message
        assert error_msg is None


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Full dependencies required")
def test_query_interface_citations_format(setup_test_db, sample_survey_data):
    """
    Test that citations are properly formatted with required fields.
    
    Validates Requirements: 2.2
    """
    # Store sample dataset
    dataset_id = store_dataset(
        sample_survey_data,
        'test_survey',
        'survey',
        'test_hash_789',
        {'title': 'Test Survey', 'description': 'Test data'}
    )
    
    # Initialize RAG engine
    rag_engine = RAGQuery()
    rag_engine.index_dataset(dataset_id)
    
    # Retrieve documents to verify citation structure
    docs = rag_engine.retrieve_relevant_docs("What feedback did we receive?")
    
    # Verify documents have proper metadata for citations
    if docs:
        for doc in docs:
            assert 'metadata' in doc
            meta = doc['metadata']
            
            # Verify required metadata fields for citations
            assert 'dataset_id' in meta
            assert 'dataset_type' in meta
            assert meta['dataset_type'] in ['survey', 'usage', 'circulation']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
