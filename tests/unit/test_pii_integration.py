"""
Unit tests for PII redaction integration in output paths.

Tests that PII redaction is properly integrated into:
- RAG query answers
- Report generation narratives
- Qualitative analysis summaries
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Mock dependencies before importing modules
_MOCKED_MODULES = {
    'textblob': MagicMock(),
    'sklearn': MagicMock(),
    'sklearn.feature_extraction': MagicMock(),
    'sklearn.feature_extraction.text': MagicMock(),
    'sklearn.cluster': MagicMock(),
    'chromadb': MagicMock(),
    'chromadb.config': MagicMock(),
    'ollama': MagicMock(),
    'sentence_transformers': MagicMock(),
}
_ORIGINAL_MODULES = {name: sys.modules.get(name) for name in _MOCKED_MODULES}
sys.modules.update(_MOCKED_MODULES)

from modules.rag_query import RAGQuery  # noqa: E402
from modules.report_generator import generate_narrative  # noqa: E402
from modules.qualitative_analysis import generate_summary  # noqa: E402

for name, original_module in _ORIGINAL_MODULES.items():
    if original_module is None:
        sys.modules.pop(name, None)
    else:
        sys.modules[name] = original_module


@pytest.fixture
def mock_rag_dependencies():
    """Patch heavy RAG dependencies so tests are order-independent."""
    with patch('modules.rag_query.SentenceTransformer'), \
         patch('modules.rag_query.chromadb.PersistentClient'):
        yield


class TestRAGQueryPIIRedaction:
    """Test PII redaction in RAG query answers."""
    
    @patch('modules.rag_query.ollama.Client')
    @patch('modules.rag_query.execute_update')
    @patch('modules.rag_query.execute_query')
    def test_query_redacts_pii_from_answer(self, mock_query, mock_update, mock_client_cls, mock_rag_dependencies):
        """Test that query() redacts PII from LLM-generated answers."""
        # Setup mocks
        mock_client = Mock()
        mock_client.generate.return_value = {
            'response': 'Contact John at john.doe@example.com or call 555-123-4567 for more info.'
        }
        mock_client_cls.return_value = mock_client
        mock_update.return_value = 1
        
        # Create RAG instance
        rag = RAGQuery()
        
        # Mock collection query to return documents
        rag.collection.count = Mock(return_value=1)
        rag.collection.query = Mock(return_value={
            'documents': [['Sample document text']],
            'metadatas': [[{'dataset_id': '1', 'dataset_type': 'survey'}]],
            'distances': [[0.5]]
        })
        
        # Execute query
        result = rag.query("What is the contact info?", session_id="test_session")
        
        # Verify PII was redacted
        assert '[EMAIL]' in result['answer']
        assert '[PHONE]' in result['answer']
        assert 'john.doe@example.com' not in result['answer']
        assert '555-123-4567' not in result['answer']
    
    @patch('modules.rag_query.ollama.Client')
    @patch('modules.rag_query.execute_update')
    @patch('modules.rag_query.execute_query')
    def test_query_preserves_non_pii_content(self, mock_query, mock_update, mock_client_cls, mock_rag_dependencies):
        """Test that query() preserves non-PII content."""
        # Setup mocks
        mock_client = Mock()
        mock_client.generate.return_value = {
            'response': 'The library has 5000 books and serves 1000 students.'
        }
        mock_client_cls.return_value = mock_client
        mock_update.return_value = 1
        
        # Create RAG instance
        rag = RAGQuery()
        
        # Mock collection query
        rag.collection.count = Mock(return_value=1)
        rag.collection.query = Mock(return_value={
            'documents': [['Sample document text']],
            'metadatas': [[{'dataset_id': '1', 'dataset_type': 'usage'}]],
            'distances': [[0.3]]
        })
        
        # Execute query
        result = rag.query("How many books?", session_id="test_session")
        
        # Verify content is preserved
        assert '5000 books' in result['answer']
        assert '1000 students' in result['answer']


class TestReportGeneratorPIIRedaction:
    """Test PII redaction in report generation."""
    
    @patch('ollama.generate')
    def test_generate_narrative_redacts_pii(self, mock_generate):
        """Test that generate_narrative() redacts PII from LLM output."""
        # Setup mock
        mock_generate.return_value = {
            'response': 'Survey responses show positive feedback. Contact admin@library.edu for details.'
        }
        
        # Create summary
        summary = {
            'dataset_name': 'Test Survey',
            'dataset_type': 'survey',
            'row_count': 100,
            'statistics': {
                'sentiment_score': {
                    'mean': 0.75,
                    'median': 0.8,
                    'count': 100
                }
            }
        }
        
        # Generate narrative
        narrative = generate_narrative(summary)
        
        # Verify PII was redacted
        assert '[EMAIL]' in narrative
        assert 'admin@library.edu' not in narrative
        assert 'positive feedback' in narrative  # Non-PII preserved
    
    @patch('ollama.generate')
    def test_generate_narrative_handles_multiple_pii_types(self, mock_generate):
        """Test that generate_narrative() handles multiple PII types."""
        # Setup mock with multiple PII types (using default patterns: email, phone, ssn)
        mock_generate.return_value = {
            'response': 'Contact us at info@example.com or 555-987-6543. SSN: 123-45-6789.'
        }
        
        summary = {
            'dataset_name': 'Test',
            'dataset_type': 'survey',
            'row_count': 50,
            'statistics': {}
        }
        
        # Generate narrative
        narrative = generate_narrative(summary)
        
        # Verify all PII types were redacted
        assert '[EMAIL]' in narrative
        assert '[PHONE]' in narrative
        assert '[SSN]' in narrative
        assert 'info@example.com' not in narrative
        assert '555-987-6543' not in narrative
        assert '123-45-6789' not in narrative


class TestQualitativeAnalysisPIIRedaction:
    """Test PII redaction in qualitative analysis summaries."""
    
    @patch('modules.qualitative_analysis.execute_query')
    def test_generate_summary_redacts_pii_from_quotes(self, mock_query):
        """Test that generate_summary() redacts PII from representative quotes."""
        # Setup mock data with PII in quotes
        mock_query.return_value = [{
            'id': 1,
            'response_count': 50,
            'themes': '[{"theme_name": "Theme 1", "keywords": ["library", "resources"], "frequency": 25, "percentage": 50.0, "sentiment_distribution": {"positive": 0.8, "neutral": 0.1, "negative": 0.1}, "representative_quotes": ["Contact librarian at help@library.edu for assistance", "Great service!", "Very helpful staff"]}]',
            'overall_sentiment': '{"positive": 0.6, "neutral": 0.3, "negative": 0.1}'
        }]
        
        # Generate summary
        summary = generate_summary(1)
        
        # Verify PII was redacted from quotes
        assert '[EMAIL]' in summary
        assert 'help@library.edu' not in summary
        assert 'Theme 1' in summary  # Non-PII preserved
    
    @patch('modules.qualitative_analysis.execute_query')
    def test_generate_summary_redacts_pii_from_entire_summary(self, mock_query):
        """Test that generate_summary() applies final redaction pass."""
        # Setup mock data
        mock_query.return_value = [{
            'id': 1,
            'response_count': 30,
            'themes': '[{"theme_name": "Contact Info", "keywords": ["email", "phone"], "frequency": 15, "percentage": 50.0, "sentiment_distribution": {"positive": 0.5, "neutral": 0.3, "negative": 0.2}, "representative_quotes": ["My email is student@university.edu"]}]',
            'overall_sentiment': '{"positive": 0.5, "neutral": 0.3, "negative": 0.2}'
        }]
        
        # Generate summary
        summary = generate_summary(1)
        
        # Verify comprehensive PII redaction
        assert '[EMAIL]' in summary
        assert 'student@university.edu' not in summary
        assert 'Contact Info' in summary  # Theme name preserved
    
    @patch('modules.qualitative_analysis.execute_query')
    def test_generate_summary_preserves_statistics(self, mock_query):
        """Test that generate_summary() preserves statistical information."""
        # Setup mock data without PII
        mock_query.return_value = [{
            'id': 1,
            'response_count': 100,
            'themes': '[{"theme_name": "Library Hours", "keywords": ["hours", "open", "close"], "frequency": 40, "percentage": 40.0, "sentiment_distribution": {"positive": 0.7, "neutral": 0.2, "negative": 0.1}, "representative_quotes": ["Library hours are convenient"]}]',
            'overall_sentiment': '{"positive": 0.7, "neutral": 0.2, "negative": 0.1}'
        }]
        
        # Generate summary
        summary = generate_summary(1)
        
        # Verify statistics are preserved
        assert '100' in summary  # Response count
        assert '70.0%' in summary or '70%' in summary  # Positive sentiment
        assert 'Library Hours' in summary


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
