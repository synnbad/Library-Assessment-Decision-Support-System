"""
CSV Handler Module

This module provides comprehensive CSV file handling for library assessment data,
including validation, parsing, storage, and FAIR/CARE metadata management.

Key Features:
- CSV format validation with detailed error messages
- Support for multiple dataset types (survey, usage, circulation)
- Duplicate detection using SHA256 file hashing
- FAIR/CARE metadata storage and management
- Data provenance tracking
- Export functionality (CSV, JSON)
- Data manifest generation for discoverability

Module Functions:
- validate_csv(): Validate CSV format and required columns
- parse_csv(): Parse CSV file into pandas DataFrame
- store_dataset(): Store dataset in SQLite with metadata
- get_datasets(): Retrieve list of all datasets
- update_dataset_metadata(): Update FAIR/CARE metadata
- delete_dataset(): Remove dataset and related data
- export_dataset(): Export dataset in standard formats
- generate_data_manifest(): Create FAIR-compliant manifest
- check_duplicate(): Detect duplicate uploads by file hash
- calculate_file_hash(): Generate SHA256 hash for files

Database Tables Used:
- datasets: Core dataset metadata and FAIR/CARE fields
- survey_responses: Survey data with sentiment analysis
- usage_statistics: Usage metrics and circulation data

Requirements Implemented:
- 1.1: Accept CSV file uploads
- 1.2: Validate file format and structure
- 1.3: Store data in SQLite
- 1.4: Display preview of uploaded data
- 1.5: Display specific error messages
- 1.6: Support multiple dataset types
- 1.7: Allow dataset deletion
- 7.1: Store FAIR metadata
- 7.2: Provide export functionality
- 7.3: Document data provenance
- 7.7: Generate data manifest

Author: FERPA-Compliant RAG DSS Team
"""

import pandas as pd
import hashlib
import json
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
from modules.database import execute_query, execute_update, get_db_connection
from config.settings import Settings


# Required columns for each dataset type
REQUIRED_COLUMNS = {
    "survey": ["response_date", "question", "response_text"],
    "usage": ["date", "metric_name", "metric_value"],
    "circulation": ["checkout_date", "material_type", "patron_type"]
}


def calculate_file_hash(file_content: bytes) -> str:
    """
    Calculate SHA256 hash of file content for duplicate detection.
    
    Args:
        file_content: File content as bytes
        
    Returns:
        SHA256 hash as hex string
    """
    return hashlib.sha256(file_content).hexdigest()


def validate_csv(file, dataset_type: str) -> Tuple[bool, Optional[str]]:
    """
    Validate CSV file format and structure.
    
    Args:
        file: Uploaded file object
        dataset_type: Type of dataset (survey, usage, circulation)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Try to read CSV
        df = pd.read_csv(file)
        
        # Reset file pointer for subsequent reads
        file.seek(0)
        
        # Check if file is empty
        if df.empty:
            return False, "Uploaded file is empty. Please upload a file with data."
        
        # Check required columns
        if dataset_type in REQUIRED_COLUMNS:
            required = REQUIRED_COLUMNS[dataset_type]
            missing = [col for col in required if col not in df.columns]
            
            if missing:
                return False, f"Missing required columns: {', '.join(missing)}. Expected columns: {', '.join(required)}"
        
        # Check for completely empty columns
        empty_cols = [col for col in df.columns if df[col].isna().all()]
        if empty_cols:
            return False, f"The following columns are completely empty: {', '.join(empty_cols)}. Please ensure all columns contain data."
        
        return True, None
        
    except pd.errors.EmptyDataError:
        return False, "Uploaded file is empty. Please upload a file with data."
    except pd.errors.ParserError as e:
        return False, f"Invalid CSV format. Please upload a valid CSV file. Details: {str(e)}"
    except Exception as e:
        return False, f"Invalid CSV format. Please upload a valid CSV file."


def parse_csv(file) -> pd.DataFrame:
    """
    Parse CSV file into DataFrame.
    
    Args:
        file: Uploaded file object
        
    Returns:
        pandas DataFrame
    """
    return pd.read_csv(file)


def store_dataset(
    df: pd.DataFrame,
    dataset_name: str,
    dataset_type: str,
    file_hash: str,
    metadata: Optional[Dict[str, Any]] = None
) -> int:
    """
    Store DataFrame in SQLite with FAIR/CARE metadata.
    
    Args:
        df: DataFrame to store
        dataset_name: Name for the dataset
        dataset_type: Type (survey, usage, circulation)
        file_hash: SHA256 hash of original file
        metadata: Optional FAIR/CARE metadata dict with keys:
            - title, description, source, keywords
            - usage_notes, ethical_considerations
            
    Returns:
        dataset_id of stored dataset
    """
    # Prepare metadata
    meta = metadata or {}
    column_names = json.dumps(df.columns.tolist())
    keywords_json = json.dumps(meta.get('keywords', []))
    
    # Initialize data provenance
    provenance = {
        "upload": {
            "timestamp": datetime.now().isoformat(),
            "source": meta.get('source', 'manual_upload'),
            "row_count": len(df)
        },
        "transformations": [],
        "queries": []
    }
    provenance_json = json.dumps(provenance)
    
    # Insert dataset record
    dataset_id = execute_update(
        """
        INSERT INTO datasets (
            name, dataset_type, row_count, column_names, file_hash,
            title, description, source, keywords,
            usage_notes, ethical_considerations, data_provenance
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            dataset_name,
            dataset_type,
            len(df),
            column_names,
            file_hash,
            meta.get('title'),
            meta.get('description'),
            meta.get('source'),
            keywords_json,
            meta.get('usage_notes'),
            meta.get('ethical_considerations'),
            provenance_json
        )
    )
    
    # Store data based on dataset type
    if dataset_type == "survey":
        _store_survey_data(df, dataset_id)
    elif dataset_type == "usage":
        _store_usage_data(df, dataset_id)
    elif dataset_type == "circulation":
        _store_circulation_data(df, dataset_id)
    
    return dataset_id


def _store_survey_data(df: pd.DataFrame, dataset_id: int) -> None:
    """Store survey response data."""
    with get_db_connection() as conn:
        for _, row in df.iterrows():
            conn.execute(
                """
                INSERT INTO survey_responses (
                    dataset_id, response_date, question, response_text
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    dataset_id,
                    row.get('response_date'),
                    row.get('question'),
                    row.get('response_text')
                )
            )


def _store_usage_data(df: pd.DataFrame, dataset_id: int) -> None:
    """Store usage statistics data."""
    with get_db_connection() as conn:
        for _, row in df.iterrows():
            conn.execute(
                """
                INSERT INTO usage_statistics (
                    dataset_id, date, metric_name, metric_value, category
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    dataset_id,
                    row.get('date'),
                    row.get('metric_name'),
                    row.get('metric_value'),
                    row.get('category', '')
                )
            )


def _store_circulation_data(df: pd.DataFrame, dataset_id: int) -> None:
    """Store circulation data (stored as usage statistics for MVP)."""
    with get_db_connection() as conn:
        for _, row in df.iterrows():
            conn.execute(
                """
                INSERT INTO usage_statistics (
                    dataset_id, date, metric_name, metric_value, category
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    dataset_id,
                    row.get('checkout_date'),
                    row.get('material_type'),
                    1,  # Count of 1 per checkout
                    row.get('patron_type', '')
                )
            )



def get_preview(dataset_id: int, n_rows: int = 10) -> pd.DataFrame:
    """
    Get preview of uploaded dataset.
    
    Args:
        dataset_id: Dataset identifier
        n_rows: Number of rows to return
        
    Returns:
        DataFrame with preview data
    """
    # Get dataset info
    datasets = execute_query(
        "SELECT dataset_type FROM datasets WHERE id = ?",
        (dataset_id,)
    )
    
    if not datasets:
        return pd.DataFrame()
    
    dataset_type = datasets[0]['dataset_type']
    
    # Query appropriate table
    if dataset_type == "survey":
        rows = execute_query(
            "SELECT * FROM survey_responses WHERE dataset_id = ? LIMIT ?",
            (dataset_id, n_rows)
        )
    else:  # usage or circulation
        rows = execute_query(
            "SELECT * FROM usage_statistics WHERE dataset_id = ? LIMIT ?",
            (dataset_id, n_rows)
        )
    
    return pd.DataFrame(rows)


def get_datasets() -> List[Dict[str, Any]]:
    """
    Retrieve list of all uploaded datasets with metadata.
    
    Returns:
        List of dataset dictionaries
    """
    datasets = execute_query(
        """
        SELECT id, name, dataset_type, upload_date, row_count,
               title, description, source, keywords,
               usage_notes, ethical_considerations
        FROM datasets
        ORDER BY upload_date DESC
        """
    )
    
    # Parse JSON fields
    for dataset in datasets:
        if dataset.get('keywords'):
            dataset['keywords'] = json.loads(dataset['keywords'])
    
    return datasets


def update_dataset_metadata(dataset_id: int, metadata: Dict[str, Any]) -> bool:
    """
    Update FAIR/CARE metadata for existing dataset.
    
    Args:
        dataset_id: Dataset identifier
        metadata: Dictionary with metadata fields to update
        
    Returns:
        True if successful, False if dataset not found
    """
    # Check if dataset exists
    datasets = execute_query(
        "SELECT id FROM datasets WHERE id = ?",
        (dataset_id,)
    )
    
    if not datasets:
        return False
    
    # Prepare keywords as JSON
    keywords_json = json.dumps(metadata.get('keywords', []))
    
    # Update metadata
    execute_update(
        """
        UPDATE datasets SET
            title = ?,
            description = ?,
            source = ?,
            keywords = ?,
            usage_notes = ?,
            ethical_considerations = ?
        WHERE id = ?
        """,
        (
            metadata.get('title'),
            metadata.get('description'),
            metadata.get('source'),
            keywords_json,
            metadata.get('usage_notes'),
            metadata.get('ethical_considerations'),
            dataset_id
        )
    )
    
    return True



def delete_dataset(dataset_id: int) -> bool:
    """
    Delete dataset from database (cascade deletes related data).
    
    Args:
        dataset_id: Dataset identifier
        
    Returns:
        True if deleted, False if not found
    """
    # Check if dataset exists
    datasets = execute_query(
        "SELECT id FROM datasets WHERE id = ?",
        (dataset_id,)
    )
    
    if not datasets:
        return False
    
    # Delete dataset (cascade will handle related tables)
    execute_update(
        "DELETE FROM datasets WHERE id = ?",
        (dataset_id,)
    )
    
    return True


def export_dataset(dataset_id: int, format: str = 'csv') -> Optional[bytes]:
    """
    Export dataset in standard format (CSV or JSON) for interoperability.
    
    Args:
        dataset_id: Dataset identifier
        format: Export format ('csv' or 'json')
        
    Returns:
        Exported data as bytes, or None if dataset not found
    """
    # Get dataset info
    datasets = execute_query(
        "SELECT dataset_type FROM datasets WHERE id = ?",
        (dataset_id,)
    )
    
    if not datasets:
        return None
    
    dataset_type = datasets[0]['dataset_type']
    
    # Query data
    if dataset_type == "survey":
        rows = execute_query(
            "SELECT * FROM survey_responses WHERE dataset_id = ?",
            (dataset_id,)
        )
    else:
        rows = execute_query(
            "SELECT * FROM usage_statistics WHERE dataset_id = ?",
            (dataset_id,)
        )
    
    df = pd.DataFrame(rows)
    
    # Export in requested format
    if format == 'csv':
        return df.to_csv(index=False).encode('utf-8')
    elif format == 'json':
        return df.to_json(orient='records', indent=2).encode('utf-8')
    else:
        raise ValueError(f"Unsupported format: {format}")


def generate_data_manifest() -> Dict[str, Any]:
    """
    Generate data manifest file listing all datasets with metadata.
    
    Returns:
        Dictionary containing manifest data
    """
    datasets = get_datasets()
    
    manifest = {
        "generated": datetime.now().isoformat(),
        "system": "FERPA-Compliant RAG Decision Support System",
        "version": "1.0.0",
        "datasets": []
    }
    
    for dataset in datasets:
        manifest["datasets"].append({
            "id": dataset['id'],
            "name": dataset['name'],
            "title": dataset.get('title'),
            "type": dataset['dataset_type'],
            "upload_date": dataset['upload_date'],
            "row_count": dataset['row_count'],
            "description": dataset.get('description'),
            "source": dataset.get('source'),
            "keywords": dataset.get('keywords', []),
            "usage_notes": dataset.get('usage_notes'),
            "ethical_considerations": dataset.get('ethical_considerations')
        })
    
    return manifest


def check_duplicate(file_hash: str) -> Optional[Dict[str, Any]]:
    """
    Check if a file with the same hash has already been uploaded.
    
    Args:
        file_hash: SHA256 hash of file
        
    Returns:
        Dataset info if duplicate found, None otherwise
    """
    datasets = execute_query(
        "SELECT id, name, upload_date FROM datasets WHERE file_hash = ?",
        (file_hash,)
    )
    
    return datasets[0] if datasets else None


def update_data_provenance(
    dataset_id: int,
    operation: str,
    method: str,
    parameters: Optional[Dict[str, Any]] = None
) -> None:
    """
    Update data provenance tracking for a dataset.
    
    Args:
        dataset_id: Dataset identifier
        operation: Operation performed (e.g., 'sentiment_analysis', 'theme_extraction')
        method: Method used (e.g., 'TextBlob', 'TF-IDF + K-means')
        parameters: Optional parameters used in operation
    """
    # Get current provenance
    datasets = execute_query(
        "SELECT data_provenance FROM datasets WHERE id = ?",
        (dataset_id,)
    )
    
    if not datasets:
        return
    
    provenance = json.loads(datasets[0]['data_provenance'] or '{"transformations": []}')
    
    # Add new transformation
    provenance.setdefault('transformations', []).append({
        "operation": operation,
        "timestamp": datetime.now().isoformat(),
        "method": method,
        "parameters": parameters or {}
    })
    
    # Update database
    execute_update(
        "UPDATE datasets SET data_provenance = ? WHERE id = ?",
        (json.dumps(provenance), dataset_id)
    )


def add_query_to_provenance(dataset_id: int, question: str, username: str) -> None:
    """
    Add query to dataset provenance for tracking data access.
    
    Args:
        dataset_id: Dataset identifier
        question: Question asked
        username: User who asked the question
    """
    # Get current provenance
    datasets = execute_query(
        "SELECT data_provenance FROM datasets WHERE id = ?",
        (dataset_id,)
    )
    
    if not datasets:
        return
    
    provenance = json.loads(datasets[0]['data_provenance'] or '{"queries": []}')
    
    # Add query
    provenance.setdefault('queries', []).append({
        "timestamp": datetime.now().isoformat(),
        "user": username,
        "question": question
    })
    
    # Update database
    execute_update(
        "UPDATE datasets SET data_provenance = ? WHERE id = ?",
        (json.dumps(provenance), dataset_id)
    )
