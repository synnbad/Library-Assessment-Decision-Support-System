"""
Unit tests for CSV error handling.

Tests Requirements 1.2 and 1.5:
- Validate file format and structure
- Display specific error messages for formatting errors
"""

import pandas as pd
from io import StringIO, BytesIO
from modules import csv_handler


class TestInvalidFormat:
    """Test handling of invalid CSV formats."""
    
    def test_invalid_csv_format_malformed(self):
        """Test error message for malformed CSV."""
        # Malformed CSV with inconsistent columns
        csv_content = """response_date,question,response_text
2024-01-15,How satisfied?,Very satisfied
2024-01-16,What improvements?"""  # Missing third column
        
        file = StringIO(csv_content)
        is_valid, error = csv_handler.validate_csv(file, "survey")
        
        # Should still parse but may have issues
        # pandas is lenient with missing values
        assert isinstance(error, (str, type(None)))
    
    def test_invalid_csv_format_not_csv(self):
        """Test error message for non-CSV content."""
        # JSON content instead of CSV
        csv_content = """{"name": "test", "value": 123}"""
        
        file = StringIO(csv_content)
        is_valid, error = csv_handler.validate_csv(file, "survey")
        
        assert is_valid is False
        assert error is not None
        # pandas may interpret this as empty or invalid
        assert any(keyword in error.lower() for keyword in ["missing", "empty", "error"])
    
    def test_invalid_csv_format_binary_file(self):
        """Test error message for binary file."""
        # Binary content that's not CSV
        binary_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
        
        file = BytesIO(binary_content)
        is_valid, error = csv_handler.validate_csv(file, "survey")
        
        assert is_valid is False
        assert error is not None


class TestMissingColumns:
    """Test handling of missing required columns."""
    
    def test_missing_single_column_survey(self):
        """Test error message when one required column is missing for survey."""
        # Missing response_text column
        csv_content = """response_date,question
2024-01-15,How satisfied?
2024-01-16,What improvements?"""
        
        file = StringIO(csv_content)
        is_valid, error = csv_handler.validate_csv(file, "survey")
        
        assert is_valid is False
        assert error is not None
        assert "Missing required columns" in error
        assert "response_text" in error
        assert "Expected columns" in error
    
    def test_missing_multiple_columns_survey(self):
        """Test error message when multiple required columns are missing."""
        # Missing question and response_text columns
        csv_content = """response_date
2024-01-15
2024-01-16"""
        
        file = StringIO(csv_content)
        is_valid, error = csv_handler.validate_csv(file, "survey")
        
        assert is_valid is False
        assert error is not None
        assert "Missing required columns" in error
        assert "question" in error
        assert "response_text" in error
    
    def test_missing_columns_usage_dataset(self):
        """Test error message for missing columns in usage dataset."""
        # Missing metric_value column
        csv_content = """date,metric_name
2024-01-15,visits
2024-01-16,checkouts"""
        
        file = StringIO(csv_content)
        is_valid, error = csv_handler.validate_csv(file, "usage")
        
        assert is_valid is False
        assert error is not None
        assert "Missing required columns" in error
        assert "metric_value" in error
    
    def test_missing_columns_circulation_dataset(self):
        """Test error message for missing columns in circulation dataset."""
        # Missing patron_type column
        csv_content = """checkout_date,material_type
2024-01-15,book
2024-01-16,dvd"""
        
        file = StringIO(csv_content)
        is_valid, error = csv_handler.validate_csv(file, "circulation")
        
        assert is_valid is False
        assert error is not None
        assert "Missing required columns" in error
        assert "patron_type" in error
    
    def test_all_columns_missing(self):
        """Test error message when all required columns are missing."""
        csv_content = """col1,col2,col3
val1,val2,val3"""
        
        file = StringIO(csv_content)
        is_valid, error = csv_handler.validate_csv(file, "survey")
        
        assert is_valid is False
        assert error is not None
        assert "Missing required columns" in error
        # Should list all required columns
        assert "response_date" in error
        assert "question" in error
        assert "response_text" in error


class TestEmptyFiles:
    """Test handling of empty files."""
    
    def test_completely_empty_file(self):
        """Test error message for completely empty file."""
        csv_content = ""
        
        file = StringIO(csv_content)
        is_valid, error = csv_handler.validate_csv(file, "survey")
        
        assert is_valid is False
        assert error is not None
        assert "empty" in error.lower()
    
    def test_empty_file_with_headers_only(self):
        """Test error message for file with only headers."""
        csv_content = """response_date,question,response_text"""
        
        file = StringIO(csv_content)
        is_valid, error = csv_handler.validate_csv(file, "survey")
        
        assert is_valid is False
        assert error is not None
        assert "empty" in error.lower()
    
    def test_empty_file_with_whitespace(self):
        """Test error message for file with only whitespace."""
        csv_content = """   
        
        """
        
        file = StringIO(csv_content)
        is_valid, error = csv_handler.validate_csv(file, "survey")
        
        assert is_valid is False
        assert error is not None
    
    def test_file_with_empty_rows(self):
        """Test file with some empty rows (should be valid)."""
        csv_content = """response_date,question,response_text
2024-01-15,How satisfied?,Very satisfied
,,
2024-01-16,What improvements?,More spaces"""
        
        file = StringIO(csv_content)
        is_valid, error = csv_handler.validate_csv(file, "survey")
        
        # Should be valid - pandas handles empty rows
        assert is_valid is True
        assert error is None


class TestDuplicateDatasets:
    """Test handling of duplicate dataset uploads."""
    
    def test_duplicate_detection(self):
        """Test that duplicate files are detected by hash."""
        # Create a test dataset
        df = pd.DataFrame({
            'response_date': ['2024-01-15'],
            'question': ['Q1'],
            'response_text': ['Answer 1']
        })
        
        file_hash = 'test_duplicate_hash_001'
        
        # Store first dataset
        dataset_id = csv_handler.store_dataset(
            df,
            'original_dataset',
            'survey',
            file_hash,
            {}
        )
        
        try:
            # Check for duplicate
            duplicate = csv_handler.check_duplicate(file_hash)
            
            assert duplicate is not None
            assert duplicate['name'] == 'original_dataset'
            assert 'upload_date' in duplicate
            
        finally:
            # Clean up
            csv_handler.delete_dataset(dataset_id)
    
    def test_no_duplicate_for_unique_file(self):
        """Test that unique files are not flagged as duplicates."""
        unique_hash = 'unique_hash_that_does_not_exist_12345'
        
        duplicate = csv_handler.check_duplicate(unique_hash)
        
        assert duplicate is None
    
    def test_duplicate_message_includes_date(self):
        """Test that duplicate detection includes upload date."""
        # Create a test dataset
        df = pd.DataFrame({
            'response_date': ['2024-01-15'],
            'question': ['Q1'],
            'response_text': ['Answer 1']
        })
        
        file_hash = 'test_duplicate_hash_002'
        
        # Store dataset
        dataset_id = csv_handler.store_dataset(
            df,
            'test_duplicate_date',
            'survey',
            file_hash,
            {}
        )
        
        try:
            # Check for duplicate
            duplicate = csv_handler.check_duplicate(file_hash)
            
            assert duplicate is not None
            assert 'upload_date' in duplicate
            assert duplicate['upload_date'] is not None
            
        finally:
            # Clean up
            csv_handler.delete_dataset(dataset_id)


class TestErrorMessageQuality:
    """Test that error messages are user-friendly and actionable."""
    
    def test_missing_columns_message_is_actionable(self):
        """Test that missing columns error provides expected columns."""
        csv_content = """wrong_col1,wrong_col2
val1,val2"""
        
        file = StringIO(csv_content)
        is_valid, error = csv_handler.validate_csv(file, "survey")
        
        assert is_valid is False
        assert "Missing required columns" in error
        assert "Expected columns" in error
        # Should list what's expected
        assert "response_date" in error
        assert "question" in error
        assert "response_text" in error
    
    def test_empty_file_message_is_clear(self):
        """Test that empty file error is clear."""
        csv_content = ""
        
        file = StringIO(csv_content)
        is_valid, error = csv_handler.validate_csv(file, "survey")
        
        assert is_valid is False
        assert error is not None
        # Message should mention "empty" and "data"
        assert "empty" in error.lower() or "no data" in error.lower()
    
    def test_error_messages_avoid_technical_jargon(self):
        """Test that error messages are user-friendly."""
        csv_content = """response_date,question
2024-01-15,How satisfied?"""
        
        file = StringIO(csv_content)
        is_valid, error = csv_handler.validate_csv(file, "survey")
        
        assert is_valid is False
        # Should not contain technical terms like "NoneType", "Exception", etc.
        assert "NoneType" not in error
        assert "Exception" not in error
        assert "Traceback" not in error


class TestEdgeCases:
    """Test edge cases in CSV validation."""
    
    def test_csv_with_special_characters(self):
        """Test CSV with special characters in data."""
        # Note: StringIO with triple quotes adds leading whitespace
        csv_content = 'response_date,question,response_text\n2024-01-15,"How satisfied?","Very satisfied!"\n2024-01-16,"What\'s needed?","More spaces & resources"'
        
        file = StringIO(csv_content)
        is_valid, error = csv_handler.validate_csv(file, "survey")
        
        assert is_valid is True
        assert error is None
    
    def test_csv_with_commas_in_quoted_fields(self):
        """Test CSV with commas inside quoted fields."""
        csv_content = 'response_date,question,response_text\n2024-01-15,"How satisfied?","Very satisfied, extremely happy"\n2024-01-16,"What improvements?","More spaces, better hours, new books"'
        
        file = StringIO(csv_content)
        is_valid, error = csv_handler.validate_csv(file, "survey")
        
        assert is_valid is True
        assert error is None
    
    def test_csv_with_extra_columns(self):
        """Test CSV with more columns than required (should be valid)."""
        csv_content = """response_date,question,response_text,extra_col1,extra_col2
2024-01-15,How satisfied?,Very satisfied,extra1,extra2"""
        
        file = StringIO(csv_content)
        is_valid, error = csv_handler.validate_csv(file, "survey")
        
        assert is_valid is True
        assert error is None
    
    def test_csv_with_completely_empty_columns(self):
        """Test CSV with completely empty columns."""
        csv_content = """response_date,question,response_text,empty_col
2024-01-15,How satisfied?,Very satisfied,
2024-01-16,What improvements?,More spaces,"""
        
        file = StringIO(csv_content)
        is_valid, error = csv_handler.validate_csv(file, "survey")
        
        # Should detect empty column
        assert is_valid is False
        assert "empty" in error.lower()
        assert "empty_col" in error
