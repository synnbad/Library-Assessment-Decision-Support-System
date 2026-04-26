"""
Unit tests for query operation error handling.

Tests error handlers for:
- Ollama connection failures
- No relevant data found
- LLM timeouts
- Context too large

Validates Requirements: 2.5
"""

import pytest
from unittest.mock import Mock, patch
from modules import rag_query
from modules.rag_query import DependencyUnavailableError, ModelNotFoundError, RAGQuery, TimeoutError
from config.settings import Settings


@pytest.fixture
def mock_rag_engine():
    """Create a mock RAG engine for testing."""
    with patch('modules.rag_query.SentenceTransformer'), \
         patch('modules.rag_query.chromadb.PersistentClient'):
        engine = RAGQuery()
        return engine


def test_rag_query_initialization_requires_core_dependencies(monkeypatch):
    """RAGQuery should fail with a helpful error when core packages are unavailable."""
    monkeypatch.setattr(rag_query, "SentenceTransformer", None)
    monkeypatch.setattr(rag_query.chromadb, "PersistentClient", None)

    with pytest.raises(DependencyUnavailableError) as exc_info:
        rag_query.RAGQuery()

    error_message = str(exc_info.value)
    assert "chromadb" in error_message
    assert "pip install -r requirements.txt" in error_message


def test_rag_query_falls_back_to_chromadb_default_embeddings():
    """RAGQuery should keep working when sentence-transformers model init fails."""
    mock_collection = Mock()
    mock_client = Mock()
    mock_client.get_or_create_collection.return_value = mock_collection
    mock_default_embedding = Mock()

    with patch('modules.rag_query.SentenceTransformer', side_effect=ValueError("bad embedding model")), \
         patch('modules.rag_query.DefaultEmbeddingFunction', return_value=mock_default_embedding), \
         patch('modules.rag_query.chromadb.PersistentClient', return_value=mock_client):
        engine = RAGQuery()

    assert engine.embedding_backend == "chromadb-default"
    assert engine.collection_uses_internal_embeddings is True
    assert engine.embedding_model is mock_default_embedding
    assert mock_client.get_or_create_collection.call_count == 1
    assert (
        mock_client.get_or_create_collection.call_args.kwargs["embedding_function"]
        is mock_default_embedding
    )


def test_rag_query_loads_sentence_transformer_from_local_cache_first():
    """Embedding initialization should avoid runtime network lookups by default."""
    mock_collection = Mock()
    mock_client = Mock()
    mock_client.get_or_create_collection.return_value = mock_collection
    mock_embedding = Mock()

    with patch('modules.rag_query.SentenceTransformer', return_value=mock_embedding) as sentence_transformer, \
         patch('modules.rag_query.chromadb.PersistentClient', return_value=mock_client):
        engine = RAGQuery()

    sentence_transformer.assert_called_once_with(
        Settings.EMBEDDING_MODEL,
        local_files_only=True,
    )
    assert engine.embedding_backend == "sentence-transformers"
    assert engine.collection_uses_internal_embeddings is False
    assert engine.embedding_model is mock_embedding


def test_ollama_dependency_error_is_actionable():
    """Missing Ollama support should return a recovery-focused message."""
    with patch('modules.rag_query.SentenceTransformer'), \
         patch('modules.rag_query.chromadb.PersistentClient'), \
         patch.object(rag_query.ollama, 'list', None):
        engine = RAGQuery()
        is_connected, error_msg = engine.test_ollama_connection()

        assert is_connected is False
        assert error_msg is not None
        assert "ollama" in error_msg.lower()
        assert "pip install -r requirements.txt" in error_msg


def test_ollama_connection_failure():
    """
    Test that Ollama connection failures are properly detected.
    
    Validates Requirements: 2.5
    """
    with patch('modules.rag_query.SentenceTransformer'), \
         patch('modules.rag_query.chromadb.PersistentClient'):
        engine = RAGQuery()
    
    # Mock ollama.list to raise an exception
    with patch('modules.rag_query.ollama.list', side_effect=Exception("Connection refused")):
        is_connected, error_msg = engine.test_ollama_connection()
        
        assert is_connected is False
        assert error_msg is not None
        assert "Cannot connect to Ollama" in error_msg


def test_ollama_connection_success():
    """
    Test that successful Ollama connection is properly detected.
    
    Validates Requirements: 2.5
    """
    with patch('modules.rag_query.SentenceTransformer'), \
         patch('modules.rag_query.chromadb.PersistentClient'):
        engine = RAGQuery()
    
    # Mock ollama.list to succeed
    with patch('modules.rag_query.ollama.list', return_value=[]):
        is_connected, error_msg = engine.test_ollama_connection()
        
        assert is_connected is True
        assert error_msg is None


def test_no_relevant_data_error(mock_rag_engine):
    """
    Test that queries with no relevant data return appropriate error message.
    
    Validates Requirements: 2.5
    """
    # Mock retrieve_relevant_docs to return empty list
    mock_rag_engine.retrieve_relevant_docs = Mock(return_value=[])
    
    result = mock_rag_engine.query("What is the meaning of life?")
    
    assert result["error_type"] == "no_relevant_data"
    assert "couldn't find relevant data" in result["answer"]
    assert result["confidence"] == 0.0
    assert len(result["citations"]) == 0
    assert len(result["suggested_questions"]) > 0


def test_context_too_large_error(mock_rag_engine):
    """
    Test that queries with too much context return appropriate error message.
    
    Validates Requirements: 2.5
    """
    # Mock retrieve_relevant_docs to return large documents
    large_text = "A" * 20000  # Very large text
    mock_docs = [
        {
            "text": large_text,
            "metadata": {"dataset_id": "1", "dataset_type": "survey"},
            "distance": 0.5
        }
    ]
    mock_rag_engine.retrieve_relevant_docs = Mock(return_value=mock_docs)
    
    # Set a low max_context_tokens for testing
    mock_rag_engine.max_context_tokens = 100
    
    result = mock_rag_engine.query("Tell me everything about the data")
    
    assert result["error_type"] == "context_too_large"
    assert "too much context" in result["answer"]
    assert result["confidence"] == 0.0
    assert len(result["suggested_questions"]) > 0


def test_llm_timeout_error(mock_rag_engine):
    """
    Test that LLM generation timeouts return appropriate error message.
    
    Validates Requirements: 2.5
    """
    # Mock retrieve_relevant_docs to return documents
    mock_docs = [
        {
            "text": "Sample data",
            "metadata": {"dataset_id": "1", "dataset_type": "survey"},
            "distance": 0.5
        }
    ]
    mock_rag_engine.retrieve_relevant_docs = Mock(return_value=mock_docs)
    
    # Mock generate_answer to raise TimeoutError
    mock_rag_engine.generate_answer = Mock(side_effect=TimeoutError("Timeout"))
    
    result = mock_rag_engine.query("What is the data about?")
    
    assert result["error_type"] == "llm_timeout"
    assert "timed out" in result["answer"].lower()
    assert result["confidence"] == 0.0
    assert len(result["suggested_questions"]) > 0


def test_ollama_model_missing_error(mock_rag_engine):
    """
    Test that missing local Ollama models return an actionable error message.

    Validates Requirements: 2.5
    """
    mock_docs = [
        {
            "text": "Sample data",
            "metadata": {"dataset_id": "1", "dataset_type": "survey"},
            "distance": 0.5
        }
    ]
    mock_rag_engine.retrieve_relevant_docs = Mock(return_value=mock_docs)
    mock_rag_engine.generate_answer = Mock(
        side_effect=ModelNotFoundError("Configured model 'llama3.2:3b' is not available locally.")
    )

    result = mock_rag_engine.query("What is the data about?")

    assert result["error_type"] == "ollama_model_missing"
    assert "ollama pull" in result["answer"]
    assert "model" in result["answer"].lower()
    assert result["confidence"] == 0.0
    assert len(result["suggested_questions"]) > 0


def test_ollama_connection_failed_during_generation(mock_rag_engine):
    """
    Test that Ollama connection failures during generation return appropriate error message.
    
    Validates Requirements: 2.5
    """
    # Mock retrieve_relevant_docs to return documents
    mock_docs = [
        {
            "text": "Sample data",
            "metadata": {"dataset_id": "1", "dataset_type": "survey"},
            "distance": 0.5
        }
    ]
    mock_rag_engine.retrieve_relevant_docs = Mock(return_value=mock_docs)
    
    # Mock generate_answer to raise RuntimeError (Ollama connection failure)
    mock_rag_engine.generate_answer = Mock(side_effect=RuntimeError("Connection to Ollama failed"))
    
    result = mock_rag_engine.query("What is the data about?")
    
    assert result["error_type"] == "ollama_connection_failed"
    assert "Cannot connect to Ollama" in result["answer"]
    assert "ollama serve" in result["answer"]
    assert result["confidence"] == 0.0
    assert len(result["suggested_questions"]) > 0


def test_successful_query_no_error(mock_rag_engine):
    """
    Test that successful queries have no error_type.
    
    Validates Requirements: 2.5
    """
    # Mock retrieve_relevant_docs to return documents
    mock_docs = [
        {
            "text": "Sample survey response",
            "metadata": {"dataset_id": "1", "dataset_type": "survey", "date": "2024-01-01"},
            "distance": 0.3
        }
    ]
    mock_rag_engine.retrieve_relevant_docs = Mock(return_value=mock_docs)
    
    # Mock generate_answer to return a response
    mock_rag_engine.generate_answer = Mock(return_value="Based on the data, the answer is...")
    
    # Mock PII redaction
    with patch('modules.rag_query.redact_pii', return_value=("Based on the data, the answer is...", {})):
        # Mock database operations
        with patch('modules.rag_query.execute_update'):
            result = mock_rag_engine.query("What does the data say?")
    
    assert result["error_type"] is None
    assert "answer" in result
    assert result["confidence"] > 0.0
    assert len(result["citations"]) > 0


def test_confidence_uses_retrieval_threshold_not_absolute_one(mock_rag_engine):
    """Distances above 1.0 can still be relevant under Chroma's configured threshold."""
    docs = [
        {"distance": 1.2},
        {"distance": 1.0},
    ]

    confidence = mock_rag_engine._calculate_confidence(docs)

    assert confidence > 0.0
    assert confidence < 1.0


def test_context_size_estimation(mock_rag_engine):
    """
    Test that context size estimation works correctly.
    
    Validates Requirements: 2.5
    """
    # Test token estimation
    short_text = "Hello world"
    estimated_tokens = mock_rag_engine._estimate_token_count(short_text)
    assert estimated_tokens > 0
    assert estimated_tokens < 10  # Should be around 2-3 tokens
    
    long_text = "A" * 1000
    estimated_tokens = mock_rag_engine._estimate_token_count(long_text)
    assert estimated_tokens > 200  # Should be around 250 tokens


def test_context_size_check_within_limit(mock_rag_engine):
    """
    Test that context size check correctly identifies contexts within limit.
    
    Validates Requirements: 2.5
    """
    context = "This is a short context"
    question = "What is this about?"
    history = []
    
    is_within_limit, estimated_tokens = mock_rag_engine._check_context_size(context, question, history)
    
    assert is_within_limit is True
    assert estimated_tokens > 0


def test_context_size_check_exceeds_limit(mock_rag_engine):
    """
    Test that context size check correctly identifies contexts exceeding limit.
    
    Validates Requirements: 2.5
    """
    # Create a very large context
    context = "A" * 20000
    question = "What is this about?"
    history = []
    
    # Set a low limit for testing
    mock_rag_engine.max_context_tokens = 100
    
    is_within_limit, estimated_tokens = mock_rag_engine._check_context_size(context, question, history)
    
    assert is_within_limit is False
    assert estimated_tokens > mock_rag_engine.max_context_tokens


def test_error_messages_include_recovery_options():
    """
    Test that all error messages include actionable recovery options.
    
    Validates Requirements: 2.5
    """
    with patch('modules.rag_query.SentenceTransformer'), \
         patch('modules.rag_query.chromadb.PersistentClient'):
        engine = RAGQuery()
    
    # Test no relevant data error
    engine.retrieve_relevant_docs = Mock(return_value=[])
    result = engine.query("test question")
    assert "upload data" in result["answer"].lower() or "rephrase" in result["answer"].lower()
    
    # Test context too large error
    mock_docs = [{"text": "A" * 20000, "metadata": {"dataset_id": "1"}, "distance": 0.5}]
    engine.retrieve_relevant_docs = Mock(return_value=mock_docs)
    engine.max_context_tokens = 100
    result = engine.query("test question")
    assert "more specific" in result["answer"].lower() or "smaller questions" in result["answer"].lower()
    
    # Test Ollama connection failure error
    mock_docs = [{"text": "Sample data", "metadata": {"dataset_id": "1"}, "distance": 0.5}]
    engine.retrieve_relevant_docs = Mock(return_value=mock_docs)
    engine.generate_answer = Mock(side_effect=RuntimeError("Connection failed"))
    result = engine.query("test question")
    assert "ollama serve" in result["answer"].lower() or "start ollama" in result["answer"].lower()


def test_error_types_are_logged():
    """
    Test that error types are properly tracked in query results.
    
    Validates Requirements: 2.5
    """
    with patch('modules.rag_query.SentenceTransformer'), \
         patch('modules.rag_query.chromadb.PersistentClient'):
        engine = RAGQuery()
    
    # Test that error_type field exists in all error scenarios
    engine.retrieve_relevant_docs = Mock(return_value=[])
    result = engine.query("test")
    assert "error_type" in result
    assert result["error_type"] == "no_relevant_data"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
