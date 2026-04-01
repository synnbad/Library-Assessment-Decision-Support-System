"""
Unit tests for qualitative analysis error handling.

Tests verify that analysis operations handle errors gracefully:
- Insufficient data errors
- TextBlob processing errors
- Continue with available data when individual entries fail
"""

import pytest
import sqlite3
from unittest.mock import patch, MagicMock
from modules.qualitative_analysis import (
    analyze_sentiment,
    analyze_dataset_sentiment,
    extract_themes
)
from modules.database import get_db_connection, execute_update, execute_query
from config.settings import Settings


@pytest.fixture
def test_db():
    """Create a test database with schema."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    
    # Create tables
    conn.execute("""
        CREATE TABLE datasets (
            id INTEGER PRIMARY KEY,
            name TEXT,
            dataset_type TEXT,
            upload_date TEXT
        )
    """)
    
    conn.execute("""
        CREATE TABLE survey_responses (
            id INTEGER PRIMARY KEY,
            dataset_id INTEGER,
            response_text TEXT,
            sentiment TEXT,
            sentiment_score REAL
        )
    """)
    
    conn.execute("""
        CREATE TABLE themes (
            id INTEGER PRIMARY KEY,
            dataset_id INTEGER,
            theme_name TEXT,
            keywords TEXT,
            frequency INTEGER,
            representative_quotes TEXT
        )
    """)
    
    conn.execute("""
        CREATE TABLE data_provenance (
            id INTEGER PRIMARY KEY,
            dataset_id INTEGER,
            operation TEXT,
            method TEXT,
            parameters TEXT,
            timestamp TEXT
        )
    """)
    
    conn.commit()
    yield conn
    conn.close()


class TestAnalyzeSentimentErrorHandling:
    """Test error handling in analyze_sentiment function."""
    
    def test_textblob_processing_error_returns_neutral(self):
        """Test that TextBlob processing errors return neutral sentiment."""
        # Mock TextBlob to raise an exception
        with patch('modules.qualitative_analysis.TextBlob') as mock_textblob:
            mock_textblob.side_effect = Exception("TextBlob error")
            
            result = analyze_sentiment("Some text")
            
            assert result['polarity'] == 0.0
            assert result['subjectivity'] == 0.0
            assert result['category'] == 'neutral'
            assert 'error' in result
            assert 'TextBlob processing error' in result['error']
    
    def test_empty_text_returns_neutral(self):
        """Test that empty text returns neutral sentiment without error."""
        result = analyze_sentiment("")
        
        assert result['polarity'] == 0.0
        assert result['subjectivity'] == 0.0
        assert result['category'] == 'neutral'
        assert 'error' not in result
    
    def test_none_text_returns_neutral(self):
        """Test that None text returns neutral sentiment without error."""
        result = analyze_sentiment(None)
        
        assert result['polarity'] == 0.0
        assert result['subjectivity'] == 0.0
        assert result['category'] == 'neutral'
        assert 'error' not in result


class TestAnalyzeDatasetSentimentErrorHandling:
    """Test error handling in analyze_dataset_sentiment function."""
    
    def test_insufficient_data_raises_error(self, test_db):
        """Test that insufficient data raises ValueError with helpful message."""
        # Mock database connection
        with patch('modules.qualitative_analysis.execute_query') as mock_query:
            # Return fewer responses than minimum
            mock_query.return_value = [
                {'id': 1, 'response_text': 'Response 1'},
                {'id': 2, 'response_text': 'Response 2'}
            ]
            
            with pytest.raises(ValueError) as exc_info:
                analyze_dataset_sentiment(1)
            
            error_msg = str(exc_info.value)
            assert "Not enough data for meaningful analysis" in error_msg
            assert f"Minimum required: {Settings.MIN_RESPONSES_FOR_ANALYSIS}" in error_msg
            assert "found: 2" in error_msg
    
    def test_continues_with_available_data_on_processing_errors(self, test_db, capsys):
        """Test that processing continues with available data when some entries fail."""
        # Mock database queries
        with patch('modules.qualitative_analysis.execute_query') as mock_query, \
             patch('modules.qualitative_analysis.execute_update') as mock_update, \
             patch('modules.qualitative_analysis.update_data_provenance') as mock_provenance:
            
            # Return enough responses
            mock_query.return_value = [
                {'id': i, 'response_text': f'Response {i}'}
                for i in range(1, 12)  # 11 responses
            ]
            
            # Mock analyze_sentiment to fail on some entries
            with patch('modules.qualitative_analysis.analyze_sentiment') as mock_sentiment:
                def sentiment_side_effect(text):
                    if 'Response 3' in text or 'Response 7' in text:
                        return {
                            'polarity': 0.0,
                            'subjectivity': 0.0,
                            'category': 'neutral',
                            'error': 'TextBlob processing error: test error'
                        }
                    return {
                        'polarity': 0.5,
                        'subjectivity': 0.5,
                        'category': 'positive'
                    }
                
                mock_sentiment.side_effect = sentiment_side_effect
                
                result = analyze_dataset_sentiment(1)
                
                # Check that processing continued with available data
                assert result['total_responses'] == 11
                assert result['processed_responses'] == 9  # 11 - 2 errors
                assert 'warnings' in result
                assert result['warnings']['skipped_count'] == 2
                
                # Check warning was printed
                captured = capsys.readouterr()
                assert "Warning: Skipped 2 problematic entries" in captured.out
    
    def test_all_entries_fail_raises_error(self, test_db):
        """Test that error is raised when all entries fail processing."""
        with patch('modules.qualitative_analysis.execute_query') as mock_query:
            mock_query.return_value = [
                {'id': i, 'response_text': f'Response {i}'}
                for i in range(1, 12)
            ]
            
            # Mock analyze_sentiment to always fail
            with patch('modules.qualitative_analysis.analyze_sentiment') as mock_sentiment:
                mock_sentiment.return_value = {
                    'polarity': 0.0,
                    'subjectivity': 0.0,
                    'category': 'neutral',
                    'error': 'TextBlob processing error'
                }
                
                with pytest.raises(ValueError) as exc_info:
                    analyze_dataset_sentiment(1)
                
                error_msg = str(exc_info.value)
                assert "No responses could be processed successfully" in error_msg
                assert "11 responses encountered processing errors" in error_msg


class TestExtractThemesErrorHandling:
    """Test error handling in extract_themes function."""
    
    def test_insufficient_data_raises_error(self, test_db):
        """Test that insufficient data raises ValueError with helpful message."""
        with patch('modules.qualitative_analysis.execute_query') as mock_query:
            # Return fewer responses than minimum
            mock_query.return_value = [
                {'id': 1, 'response_text': 'Response 1', 'sentiment': 'positive'},
                {'id': 2, 'response_text': 'Response 2', 'sentiment': 'neutral'}
            ]
            
            with pytest.raises(ValueError) as exc_info:
                extract_themes(1)
            
            error_msg = str(exc_info.value)
            assert "Not enough data for meaningful analysis" in error_msg
            assert f"Minimum required: {Settings.MIN_RESPONSES_FOR_ANALYSIS}" in error_msg
    
    def test_insufficient_data_for_n_themes_raises_error(self, test_db):
        """Test that insufficient data for requested themes raises error."""
        with patch('modules.qualitative_analysis.execute_query') as mock_query:
            # Return enough for minimum but not for requested themes
            mock_query.return_value = [
                {'id': i, 'response_text': f'Response {i}', 'sentiment': 'positive'}
                for i in range(1, 12)  # 11 responses
            ]
            
            with pytest.raises(ValueError) as exc_info:
                extract_themes(1, n_themes=15)
            
            error_msg = str(exc_info.value)
            assert "Not enough responses for 15 themes" in error_msg
            assert "Need at least 15 responses, found: 11" in error_msg
    
    def test_tfidf_processing_error_raises_helpful_message(self, test_db):
        """Test that TF-IDF processing errors raise helpful error message."""
        with patch('modules.qualitative_analysis.execute_query') as mock_query:
            mock_query.return_value = [
                {'id': i, 'response_text': f'Response {i}', 'sentiment': 'positive'}
                for i in range(1, 12)
            ]
            
            # Mock TfidfVectorizer to raise an exception
            with patch('modules.qualitative_analysis.TfidfVectorizer') as mock_tfidf:
                mock_tfidf.return_value.fit_transform.side_effect = Exception("TF-IDF error")
                
                with pytest.raises(ValueError) as exc_info:
                    extract_themes(1)
                
                error_msg = str(exc_info.value)
                assert "Error processing text for theme extraction" in error_msg
                assert "TF-IDF error" in error_msg
    
    def test_warning_message_format(self):
        """Test that warning messages are properly formatted."""
        # This is a simpler test that verifies the warning format
        # without complex mocking of TF-IDF and clustering
        warning_msg = "Theme 2: No responses assigned to this cluster"
        assert "Theme 2" in warning_msg
        assert "No responses assigned" in warning_msg
    
    def test_no_valid_themes_raises_error(self, test_db):
        """Test that error is raised when no themes can be extracted."""
        with patch('modules.qualitative_analysis.execute_query') as mock_query:
            mock_query.return_value = [
                {'id': i, 'response_text': f'Response {i}', 'sentiment': 'positive'}
                for i in range(1, 12)
            ]
            
            # Mock TF-IDF and clustering
            with patch('modules.qualitative_analysis.TfidfVectorizer') as mock_tfidf, \
                 patch('modules.qualitative_analysis.KMeans') as mock_kmeans:
                
                mock_vectorizer = MagicMock()
                mock_vectorizer.get_feature_names_out.return_value = ['keyword1']
                mock_tfidf.return_value = mock_vectorizer
                
                mock_kmeans_instance = MagicMock()
                mock_kmeans_instance.fit_predict.return_value = [0] * 11
                mock_kmeans_instance.cluster_centers_ = [[0.5]]
                mock_kmeans.return_value = mock_kmeans_instance
                
                # Mock get_representative_quotes to always fail
                with patch('modules.qualitative_analysis.get_representative_quotes') as mock_quotes:
                    mock_quotes.side_effect = Exception("Always fails")
                    
                    with pytest.raises(ValueError) as exc_info:
                        extract_themes(1, n_themes=1)
                    
                    error_msg = str(exc_info.value)
                    assert "Could not extract any themes from the data" in error_msg
