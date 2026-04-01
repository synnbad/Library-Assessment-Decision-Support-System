"""
Integration tests for data upload functionality.
Tests the CSV handler functions used by the data upload page.
"""

import pytest
import pandas as pd
from io import StringIO
from modules import csv_handler
from modules.database import execute_query, execute_update


def test_csv_validation_survey():
    """Test CSV validation for survey data."""
    # Valid survey CSV
    csv_content = """response_date,question,response_text
2024-01-15,How satisfied?,Very satisfied
2024-01-16,What improvements?,More spaces"""
    
    file = StringIO(csv_content)
    is_valid, error = csv_handler.validate_csv(file, "survey")
    
    assert is_valid is True
    assert error is None


def test_csv_validation_missing_columns():
    """Test CSV validation with missing required columns."""
    # Missing response_text column
    csv_content = """response_date,question
2024-01-15,How satisfied?"""
    
    file = StringIO(csv_content)
    is_valid, error = csv_handler.validate_csv(file, "survey")
    
    assert is_valid is False
    assert "Missing required columns" in error
    assert "response_text" in error


def test_csv_validation_empty_file():
    """Test CSV validation with empty file."""
    csv_content = ""
    
    file = StringIO(csv_content)
    is_valid, error = csv_handler.validate_csv(file, "survey")
    
    assert is_valid is False
    assert "empty" in error.lower()


def test_store_and_retrieve_dataset():
    """Test storing and retrieving a dataset with metadata."""
    # Create test data
    df = pd.DataFrame({
        'response_date': ['2024-01-15', '2024-01-16'],
        'question': ['Q1', 'Q2'],
        'response_text': ['Answer 1', 'Answer 2']
    })
    
    metadata = {
        'title': 'Test Survey',
        'description': 'Test description',
        'source': 'Test source',
        'keywords': ['test', 'survey'],
        'usage_notes': 'Test usage notes',
        'ethical_considerations': 'Test ethical notes'
    }
    
    # Store dataset
    dataset_id = csv_handler.store_dataset(
        df,
        'test_dataset',
        'survey',
        'test_hash_123',
        metadata
    )
    
    assert dataset_id > 0
    
    # Retrieve datasets
    datasets = csv_handler.get_datasets()
    
    # Find our dataset
    test_dataset = next((d for d in datasets if d['id'] == dataset_id), None)
    
    assert test_dataset is not None
    assert test_dataset['name'] == 'test_dataset'
    assert test_dataset['dataset_type'] == 'survey'
    assert test_dataset['row_count'] == 2
    assert test_dataset['title'] == 'Test Survey'
    assert test_dataset['description'] == 'Test description'
    assert test_dataset['source'] == 'Test source'
    assert test_dataset['keywords'] == ['test', 'survey']
    
    # Clean up
    csv_handler.delete_dataset(dataset_id)


def test_update_dataset_metadata():
    """Test updating dataset metadata."""
    # Create test dataset
    df = pd.DataFrame({
        'response_date': ['2024-01-15'],
        'question': ['Q1'],
        'response_text': ['Answer 1']
    })
    
    dataset_id = csv_handler.store_dataset(
        df,
        'test_update',
        'survey',
        'test_hash_456',
        {'title': 'Original Title'}
    )
    
    # Update metadata
    new_metadata = {
        'title': 'Updated Title',
        'description': 'New description',
        'keywords': ['updated', 'metadata']
    }
    
    success = csv_handler.update_dataset_metadata(dataset_id, new_metadata)
    assert success is True
    
    # Verify update
    datasets = csv_handler.get_datasets()
    updated_dataset = next((d for d in datasets if d['id'] == dataset_id), None)
    
    assert updated_dataset['title'] == 'Updated Title'
    assert updated_dataset['description'] == 'New description'
    assert updated_dataset['keywords'] == ['updated', 'metadata']
    
    # Clean up
    csv_handler.delete_dataset(dataset_id)


def test_export_dataset_csv():
    """Test exporting dataset as CSV."""
    # Create test dataset
    df = pd.DataFrame({
        'response_date': ['2024-01-15', '2024-01-16'],
        'question': ['Q1', 'Q2'],
        'response_text': ['Answer 1', 'Answer 2']
    })
    
    dataset_id = csv_handler.store_dataset(
        df,
        'test_export',
        'survey',
        'test_hash_789',
        {}
    )
    
    # Export as CSV
    csv_data = csv_handler.export_dataset(dataset_id, 'csv')
    
    assert csv_data is not None
    assert b'response_date' in csv_data
    assert b'question' in csv_data
    assert b'response_text' in csv_data
    assert b'Answer 1' in csv_data
    
    # Clean up
    csv_handler.delete_dataset(dataset_id)


def test_export_dataset_json():
    """Test exporting dataset as JSON."""
    # Create test dataset
    df = pd.DataFrame({
        'response_date': ['2024-01-15'],
        'question': ['Q1'],
        'response_text': ['Answer 1']
    })
    
    dataset_id = csv_handler.store_dataset(
        df,
        'test_export_json',
        'survey',
        'test_hash_abc',
        {}
    )
    
    # Export as JSON
    json_data = csv_handler.export_dataset(dataset_id, 'json')
    
    assert json_data is not None
    assert b'response_date' in json_data
    assert b'question' in json_data
    assert b'Answer 1' in json_data
    
    # Clean up
    csv_handler.delete_dataset(dataset_id)


def test_delete_dataset():
    """Test deleting a dataset."""
    # Create test dataset
    df = pd.DataFrame({
        'response_date': ['2024-01-15'],
        'question': ['Q1'],
        'response_text': ['Answer 1']
    })
    
    dataset_id = csv_handler.store_dataset(
        df,
        'test_delete',
        'survey',
        'test_hash_def',
        {}
    )
    
    # Verify it exists
    datasets = csv_handler.get_datasets()
    assert any(d['id'] == dataset_id for d in datasets)
    
    # Delete it
    success = csv_handler.delete_dataset(dataset_id)
    assert success is True
    
    # Verify it's gone
    datasets = csv_handler.get_datasets()
    assert not any(d['id'] == dataset_id for d in datasets)


def test_generate_data_manifest():
    """Test generating data manifest."""
    # Create test dataset
    df = pd.DataFrame({
        'response_date': ['2024-01-15'],
        'question': ['Q1'],
        'response_text': ['Answer 1']
    })
    
    metadata = {
        'title': 'Manifest Test',
        'description': 'Test for manifest',
        'keywords': ['manifest', 'test']
    }
    
    dataset_id = csv_handler.store_dataset(
        df,
        'test_manifest',
        'survey',
        'test_hash_ghi',
        metadata
    )
    
    # Generate manifest
    manifest = csv_handler.generate_data_manifest()
    
    assert 'generated' in manifest
    assert 'system' in manifest
    assert 'datasets' in manifest
    assert len(manifest['datasets']) > 0
    
    # Find our dataset in manifest
    test_dataset = next((d for d in manifest['datasets'] if d['id'] == dataset_id), None)
    assert test_dataset is not None
    assert test_dataset['name'] == 'test_manifest'
    assert test_dataset['title'] == 'Manifest Test'
    
    # Clean up
    csv_handler.delete_dataset(dataset_id)


def test_check_duplicate():
    """Test duplicate file detection."""
    # Create test dataset
    df = pd.DataFrame({
        'response_date': ['2024-01-15'],
        'question': ['Q1'],
        'response_text': ['Answer 1']
    })
    
    file_hash = 'unique_hash_123'
    
    dataset_id = csv_handler.store_dataset(
        df,
        'test_duplicate',
        'survey',
        file_hash,
        {}
    )
    
    # Check for duplicate
    duplicate = csv_handler.check_duplicate(file_hash)
    
    assert duplicate is not None
    assert duplicate['name'] == 'test_duplicate'
    
    # Check non-existent hash
    no_duplicate = csv_handler.check_duplicate('non_existent_hash')
    assert no_duplicate is None
    
    # Clean up
    csv_handler.delete_dataset(dataset_id)
