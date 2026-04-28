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

Author: Library Assessment DSS Team
"""

import pandas as pd
import hashlib
import json
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from modules.database import execute_query, execute_update, get_db_connection
from modules import data_importer, idempotency
from modules.logging_service import get_logger, log_operation

logger = get_logger(__name__)


# Maximum depth for nested JSON structures
MAX_JSON_DEPTH = 5
# Maximum string length for metadata fields
MAX_STRING_LENGTH = 10000
# Maximum array length for keywords
MAX_ARRAY_LENGTH = 100


def validate_and_sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize metadata to prevent SQL injection and malicious payloads.
    
    Args:
        metadata: Raw metadata dictionary
        
    Returns:
        Sanitized metadata dictionary
        
    Raises:
        ValueError: If metadata contains malicious content
    """
    if not isinstance(metadata, dict):
        raise ValueError("Metadata must be a dictionary")
    
    sanitized = {}
    
    # Validate and sanitize each field
    for key, value in metadata.items():
        # Check key is a valid string
        if not isinstance(key, str) or len(key) > 100:
            raise ValueError(f"Invalid metadata key: {key}")
        
        # Sanitize based on expected type
        if key == 'keywords':
            # Keywords should be a list of strings
            if not isinstance(value, list):
                raise ValueError("Keywords must be a list")
            if len(value) > MAX_ARRAY_LENGTH:
                raise ValueError(f"Keywords array too large (max {MAX_ARRAY_LENGTH})")
            
            sanitized_keywords = []
            for keyword in value:
                if not isinstance(keyword, str):
                    continue  # Skip non-string keywords
                if len(keyword) > 200:
                    keyword = keyword[:200]  # Truncate long keywords
                # Remove potentially dangerous characters
                keyword = keyword.replace('\x00', '').replace('\n', ' ').replace('\r', ' ')
                sanitized_keywords.append(keyword)
            sanitized[key] = sanitized_keywords
            
        elif isinstance(value, str):
            # String fields - check length and sanitize
            if len(value) > MAX_STRING_LENGTH:
                raise ValueError(f"Metadata field '{key}' too large (max {MAX_STRING_LENGTH} characters)")
            
            # Remove null bytes and control characters
            sanitized_value = value.replace('\x00', '').strip()
            
            # Check for suspicious SQL patterns (basic protection)
            suspicious_patterns = ['--', ';--', '/*', '*/', 'xp_', 'sp_', 'exec(', 'execute(']
            value_lower = sanitized_value.lower()
            for pattern in suspicious_patterns:
                if pattern in value_lower:
                    logger.warning(
                        f"Suspicious pattern '{pattern}' detected in metadata field '{key}'",
                        extra={"operation": "validate_metadata", "field": key, "pattern": pattern}
                    )
                    # Remove the suspicious pattern
                    sanitized_value = sanitized_value.replace(pattern, '')
            
            sanitized[key] = sanitized_value
            
        elif isinstance(value, (int, float, bool)):
            # Numeric and boolean values are safe
            sanitized[key] = value
            
        elif value is None:
            # None values are acceptable
            sanitized[key] = None
            
        else:
            # Reject complex nested structures
            raise ValueError(f"Unsupported metadata type for key '{key}': {type(value)}")
    
    return sanitized


def _check_json_depth(obj: Any, current_depth: int = 0) -> int:
    """
    Check the depth of a JSON structure.
    
    Args:
        obj: Object to check
        current_depth: Current recursion depth
        
    Returns:
        Maximum depth found
    """
    if current_depth > MAX_JSON_DEPTH:
        raise ValueError(f"JSON structure too deeply nested (max depth: {MAX_JSON_DEPTH})")
    
    if isinstance(obj, dict):
        if not obj:
            return current_depth
        return max(_check_json_depth(v, current_depth + 1) for v in obj.values())
    elif isinstance(obj, list):
        if not obj:
            return current_depth
        return max(_check_json_depth(item, current_depth + 1) for item in obj)
    else:
        return current_depth


# Suggested columns for each dataset type (flexible - not strictly required)
SUGGESTED_COLUMNS = {
    "survey": {
        "required": [],  # No strict requirements - accept any survey data
        "suggested": ["date", "response", "feedback", "comment", "question", "answer"],
        "description": "Survey data with responses, feedback, or comments"
    },
    "usage": {
        "required": [],  # No strict requirements
        "suggested": ["date", "visits", "sessions", "users", "metric", "value"],
        "description": "Usage statistics with dates and metrics"
    },
    "circulation": {
        "required": [],  # No strict requirements
        "suggested": ["date", "checkouts", "material", "patron", "item", "borrower"],
        "description": "Circulation data with checkout information"
    }
}

TEXT_DATASET_TYPES = data_importer.TEXT_DATASET_TYPES
METRIC_DATASET_TYPES = data_importer.METRIC_DATASET_TYPES
SUPPORTED_DATASET_TYPES = set(data_importer.DATASET_TYPES)

# Legacy support - keep for backward compatibility with tests
REQUIRED_COLUMNS = {
    "survey": ["response_date", "question", "response_text"],
    "usage": ["date", "metric_name", "metric_value"],
    "circulation": ["checkout_date", "material_type", "patron_type"]
}


def _read_file_sample(file, sample_size: int = 2048) -> bytes:
    """Read a small sample from a file-like object without consuming it."""
    current_pos = None
    if hasattr(file, "tell"):
        try:
            current_pos = file.tell()
        except Exception:
            current_pos = None

    try:
        if hasattr(file, "seek"):
            file.seek(0)
        sample = file.read(sample_size)
    finally:
        if current_pos is not None and hasattr(file, "seek"):
            try:
                file.seek(current_pos)
            except Exception:
                pass

    if isinstance(sample, str):
        return sample.encode("utf-8", errors="ignore")
    return sample or b""


def _looks_like_binary(sample: bytes) -> bool:
    """Heuristic check for non-text file uploads such as images."""
    if not sample:
        return False

    if sample.startswith((b"\x89PNG", b"\xff\xd8\xff", b"GIF87a", b"GIF89a", b"%PDF")):
        return True

    if b"\x00" in sample:
        return True

    text_chars = bytes(range(32, 127)) + b"\n\r\t\b\f"
    non_text = sum(byte not in text_chars for byte in sample)
    return (non_text / max(len(sample), 1)) > 0.3


def calculate_file_hash(file_content: bytes) -> str:
    """
    Calculate SHA256 hash of file content for duplicate detection.
    
    Args:
        file_content: File content as bytes
        
    Returns:
        SHA256 hash as hex string
    """
    return hashlib.sha256(file_content).hexdigest()


def validate_csv(file, dataset_type: str, strict_mode: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Validate CSV file format and structure.
    
    Args:
        file: Uploaded file object
        dataset_type: Type of dataset (survey, usage, circulation)
        strict_mode: If True, enforce strict column requirements (for testing)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        sample = _read_file_sample(file)
        if _looks_like_binary(sample):
            return False, "Uploaded file does not appear to be a valid text CSV. Please upload a CSV file exported from your data source."

        # Try to read CSV with encoding detection
        df = parse_csv(file)
        
        # Reset file pointer for subsequent reads
        file.seek(0)
        
        # Check if file is empty
        if df.empty:
            return False, "Uploaded file is empty. Please upload a file with data."
        
        # Check for duplicate column names
        duplicate_cols = df.columns[df.columns.duplicated()].tolist()
        if duplicate_cols:
            unique_duplicates = list(set(duplicate_cols))
            return False, (
                f"Duplicate column names detected: {', '.join(unique_duplicates)}. "
                f"Each column must have a unique name. Please rename duplicate columns in your CSV file before uploading."
            )
        
        # Check for completely empty columns
        empty_cols = [col for col in df.columns if df[col].isna().all()]
        if empty_cols:
            return False, f"The following columns are completely empty: {', '.join(empty_cols)}. Please ensure all columns contain data."
        
        # Strict mode: Check required columns
        if strict_mode and dataset_type in REQUIRED_COLUMNS:
            required = REQUIRED_COLUMNS[dataset_type]
            missing = [col for col in required if col not in df.columns]
            
            if missing:
                return False, f"Missing required columns: {', '.join(missing)}. Expected columns: {', '.join(required)}"
        
        # Flexible mode: Just provide helpful suggestions
        if not strict_mode and dataset_type in SUGGESTED_COLUMNS:
            suggestions = SUGGESTED_COLUMNS[dataset_type]
            suggested_cols = suggestions["suggested"]
            
            # Check if any suggested columns are present
            found_suggested = [col for col in df.columns if any(sugg in col.lower() for sugg in suggested_cols)]
            
            # If no suggested columns found, provide a helpful message (but still allow upload)
            if not found_suggested:
                # This is just informational - not an error
                pass
        
        return True, None
        
    except pd.errors.EmptyDataError:
        return False, "Uploaded file is empty. Please upload a file with data."
    except pd.errors.ParserError as e:
        return False, f"Invalid CSV format. Please upload a valid CSV file. Details: {str(e)}"
    except UnicodeDecodeError:
        return False, "Unable to read file due to encoding issues. Please save your CSV with UTF-8 encoding and try again."
    except Exception:
        return False, "Invalid CSV format. Please upload a valid CSV file."


def parse_csv(file, encoding=None) -> pd.DataFrame:
    """
    Parse CSV file into DataFrame with automatic encoding detection.
    
    Args:
        file: Uploaded file object
        encoding: Optional encoding (if None, will try common encodings)
        
    Returns:
        pandas DataFrame
    """
    if encoding:
        return pd.read_csv(file, encoding=encoding)
    
    # Try common encodings
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
    
    for enc in encodings:
        try:
            file.seek(0)
            df = pd.read_csv(file, encoding=enc)
            return df
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            # If it's not an encoding error, raise it
            if 'codec' not in str(e).lower() and 'decode' not in str(e).lower():
                raise
    
    # If all encodings fail, try with error handling
    file.seek(0)
    return pd.read_csv(file, encoding='utf-8', encoding_errors='replace')


def auto_detect_metadata(df: pd.DataFrame, dataset_type: str, filename: str) -> Dict[str, Any]:
    """
    Auto-detect metadata from uploaded dataset.
    
    Args:
        df: Parsed DataFrame
        dataset_type: Type of dataset (survey, usage, circulation)
        filename: Original filename
        
    Returns:
        Dict with auto-detected metadata fields
    """
    enhanced = data_importer.build_metadata_suggestions(df, dataset_type, filename)
    metadata = {
        "title": enhanced.get("title", ""),
        "description": enhanced.get("description", ""),
        "source": enhanced.get("source", ""),
        "keywords": enhanced.get("keywords", []),
    }
    
    # Auto-generate title from filename
    title = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title()
    metadata['title'] = metadata.get("title") or title
    
    # Generate description based on dataset characteristics
    num_rows = len(df)
    num_cols = len(df.columns)
    
    description_parts = [
        f"{dataset_type.title()} dataset with {num_rows:,} records and {num_cols} fields."
    ]
    
    # Add column information
    if dataset_type == "survey":
        if 'feedback' in df.columns or 'response' in df.columns:
            description_parts.append("Contains textual feedback responses.")
        if 'rating' in df.columns or 'score' in df.columns:
            description_parts.append("Includes rating/score data.")
    elif dataset_type == "usage":
        if 'visits' in df.columns or 'sessions' in df.columns:
            description_parts.append("Tracks usage patterns and visit statistics.")
    elif dataset_type == "circulation":
        if 'checkouts' in df.columns or 'borrowing' in df.columns:
            description_parts.append("Contains circulation and borrowing data.")
    
    # Check for date columns
    date_cols = [col for col in df.columns if any(date_term in col.lower() 
                 for date_term in ['date', 'time', 'timestamp', 'year', 'month'])]
    if date_cols:
        # Try to detect date range
        for col in date_cols:
            try:
                dates = pd.to_datetime(df[col], errors='coerce')
                dates = dates.dropna()
                if len(dates) > 0:
                    min_date = dates.min().strftime('%Y-%m-%d')
                    max_date = dates.max().strftime('%Y-%m-%d')
                    description_parts.append(f"Date range: {min_date} to {max_date}.")
                    break
            except (TypeError, ValueError, OverflowError):
                continue
    
    legacy_description = " ".join(description_parts)
    if legacy_description not in metadata.get("description", ""):
        metadata['description'] = f"{metadata.get('description', '').strip()} {legacy_description}".strip()
    
    # Auto-detect keywords from columns and dataset type
    keywords = [dataset_type]
    
    # Add keywords based on column names
    column_keywords = set()
    for col in df.columns:
        col_lower = col.lower()
        if 'feedback' in col_lower or 'comment' in col_lower or 'response' in col_lower:
            column_keywords.add('feedback')
        if 'rating' in col_lower or 'score' in col_lower or 'satisfaction' in col_lower:
            column_keywords.add('ratings')
        if 'student' in col_lower or 'undergraduate' in col_lower or 'graduate' in col_lower:
            column_keywords.add('students')
        if 'faculty' in col_lower or 'staff' in col_lower:
            column_keywords.add('faculty-staff')
        if 'visit' in col_lower or 'session' in col_lower:
            column_keywords.add('visits')
        if 'checkout' in col_lower or 'borrow' in col_lower or 'circulation' in col_lower:
            column_keywords.add('circulation')
        if 'book' in col_lower or 'material' in col_lower or 'item' in col_lower:
            column_keywords.add('materials')
    
    keywords.extend(sorted(column_keywords))
    
    # Add year if detected
    current_year = pd.Timestamp.now().year
    if any(str(current_year) in str(val) for col in df.columns for val in df[col].head()):
        keywords.append(str(current_year))
    
    metadata['keywords'] = _dedupe_metadata_values([*metadata.get("keywords", []), *keywords])
    
    # Suggest source based on dataset characteristics
    if metadata.get("source") and metadata["source"] != "Data Import Hub":
        return metadata
    if 'qualtrics' in filename.lower():
        metadata['source'] = 'Qualtrics Survey'
    elif 'google' in filename.lower():
        metadata['source'] = 'Google Forms'
    elif 'ils' in filename.lower() or 'alma' in filename.lower() or 'sierra' in filename.lower():
        metadata['source'] = 'Integrated Library System (ILS)'
    else:
        metadata['source'] = 'CSV Upload'
    
    return metadata


def _dedupe_metadata_values(values: List[Any]) -> List[str]:
    """Return normalized unique metadata values while preserving order."""
    seen = set()
    result = []
    for value in values:
        text = str(value).strip()
        if text and text not in seen:
            result.append(text)
            seen.add(text)
    return result


@log_operation("store_dataset")
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
        
    Raises:
        ValueError: If metadata contains malicious content
    """
    # Validate and sanitize metadata
    upload_key = idempotency.make_key("store_dataset", file_hash, dataset_name, dataset_type)
    cached = idempotency.get_completed_result("store_dataset", upload_key)
    if cached is not None and cached.get("dataset_id"):
        cached_dataset_id = int(cached["dataset_id"])
        cached_rows = execute_query("SELECT id FROM datasets WHERE id = ?", (cached_dataset_id,))
        if cached_rows:
            return cached_dataset_id

    existing_rows = execute_query(
        """
        SELECT id FROM datasets
        WHERE file_hash = ? AND name = ? AND dataset_type = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (file_hash, dataset_name, dataset_type),
    )
    if existing_rows:
        dataset_id = int(existing_rows[0]["id"])
        idempotency.start_operation("store_dataset", upload_key)
        idempotency.complete_operation("store_dataset", upload_key, {"dataset_id": dataset_id})
        return dataset_id

    idempotency.start_operation("store_dataset", upload_key)

    # Validate and sanitize metadata
    if metadata:
        try:
            metadata = validate_and_sanitize_metadata(metadata)
        except ValueError as e:
            logger.error(
                f"Metadata validation failed: {str(e)}",
                extra={"operation": "store_dataset", "error": str(e)}
            )
            idempotency.fail_operation("store_dataset", upload_key, str(e))
            raise ValueError(f"Invalid metadata: {str(e)}")
    
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
    
    # Insert dataset record using parameterized query (SQL injection safe)
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
    
    # Store data based on dataset type. New assessment domains reuse the existing
    # canonical tables so querying, visualizations, and reports keep working.
    if dataset_type in TEXT_DATASET_TYPES:
        _store_survey_data(df, dataset_id)
    elif dataset_type == "usage":
        _store_usage_data(df, dataset_id)
    elif dataset_type == "circulation":
        _store_circulation_data(df, dataset_id)
    elif dataset_type in METRIC_DATASET_TYPES:
        _store_usage_data(df, dataset_id)
    else:
        _store_usage_data(df, dataset_id)

    # Evaluate and persist analysis capabilities
    capabilities = evaluate_dataset_capabilities(df, dataset_type, dataset_id)
    capabilities["data_dictionary"] = data_importer.build_data_dictionary(df)
    capabilities["metadata_suggestions"] = data_importer.build_metadata_suggestions(
        df, dataset_type, dataset_name
    )
    execute_update(
        "UPDATE datasets SET analysis_capabilities = ? WHERE id = ?",
        (json.dumps(capabilities), dataset_id)
    )

    idempotency.complete_operation("store_dataset", upload_key, {"dataset_id": dataset_id})
    return dataset_id


def _store_survey_data(df: pd.DataFrame, dataset_id: int) -> None:
    """Store survey response data, handling flexible column names."""
    # Map flexible column names to canonical names
    col_map = {}
    for col in df.columns:
        cl = col.lower()
        if 'date' in cl or 'time' in cl:
            col_map.setdefault('response_date', col)
        elif any(k in cl for k in ['question', 'prompt', 'item']):
            col_map.setdefault('question', col)
        elif any(k in cl for k in ['response', 'answer', 'feedback', 'comment', 'text']):
            col_map.setdefault('response_text', col)

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
                    row.get(col_map.get('response_date', 'response_date')),
                    row.get(col_map.get('question', 'question')),
                    row.get(col_map.get('response_text', 'response_text'))
                )
            )


def _store_usage_data(df: pd.DataFrame, dataset_id: int) -> None:
    """Store usage statistics data, handling flexible column names."""
    col_map = {}
    for col in df.columns:
        cl = col.lower()
        if 'date' in cl or 'time' in cl or 'period' in cl:
            col_map.setdefault('date', col)
        elif any(k in cl for k in ['metric', 'name', 'measure', 'indicator']):
            col_map.setdefault('metric_name', col)
        elif any(k in cl for k in ['value', 'count', 'total', 'number', 'visits', 'sessions']):
            col_map.setdefault('metric_value', col)
        elif any(k in cl for k in ['category', 'type', 'group']):
            col_map.setdefault('category', col)

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
                    row.get(col_map.get('date', 'date')),
                    row.get(col_map.get('metric_name', 'metric_name')),
                    row.get(col_map.get('metric_value', 'metric_value')),
                    row.get(col_map.get('category', 'category'), '')
                )
            )


def _store_circulation_data(df: pd.DataFrame, dataset_id: int) -> None:
    """Store circulation data, handling flexible column names."""
    col_map = {}
    for col in df.columns:
        cl = col.lower()
        if 'date' in cl or 'time' in cl:
            col_map.setdefault('checkout_date', col)
        elif any(k in cl for k in ['material', 'type', 'format', 'item', 'resource']):
            col_map.setdefault('material_type', col)
        elif any(k in cl for k in ['patron', 'user', 'borrower', 'member', 'category']):
            col_map.setdefault('patron_type', col)

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
                    row.get(col_map.get('checkout_date', 'checkout_date')),
                    row.get(col_map.get('material_type', 'material_type')),
                    1,  # Count of 1 per checkout
                    row.get(col_map.get('patron_type', 'patron_type'), '')
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
    if dataset_type in TEXT_DATASET_TYPES:
        rows = execute_query(
            "SELECT * FROM survey_responses WHERE dataset_id = ? LIMIT ?",
            (dataset_id, n_rows)
        )
    else:
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
               usage_notes, ethical_considerations, analysis_capabilities,
               indexing_status, indexing_error, indexed_at
        FROM datasets
        ORDER BY upload_date DESC
        """
    )
    
    # Parse JSON fields
    for dataset in datasets:
        if dataset.get('keywords'):
            dataset['keywords'] = json.loads(dataset['keywords'])
        if dataset.get('analysis_capabilities'):
            dataset['analysis_capabilities'] = json.loads(dataset['analysis_capabilities'])
    
    return datasets


def update_dataset_metadata(dataset_id: int, metadata: Dict[str, Any]) -> bool:
    """
    Update FAIR/CARE metadata for existing dataset.
    
    Args:
        dataset_id: Dataset identifier
        metadata: Dictionary with metadata fields to update
        
    Returns:
        True if successful, False if dataset not found
        
    Raises:
        ValueError: If metadata contains malicious content
    """
    # Check if dataset exists
    datasets = execute_query(
        "SELECT id FROM datasets WHERE id = ?",
        (dataset_id,)
    )
    
    if not datasets:
        return False
    
    # Validate and sanitize metadata
    try:
        metadata = validate_and_sanitize_metadata(metadata)
    except ValueError as e:
        logger.error(
            f"Metadata validation failed: {str(e)}",
            extra={"operation": "update_dataset_metadata", "dataset_id": dataset_id, "error": str(e)}
        )
        raise ValueError(f"Invalid metadata: {str(e)}")
    
    # Prepare keywords as JSON
    keywords_json = json.dumps(metadata.get('keywords', []))
    
    # Update metadata using parameterized query (SQL injection safe)
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
    Delete dataset from database and ChromaDB (synchronized deletion).
    
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
    
    # Delete from ChromaDB first to maintain synchronization
    try:
        from modules.rag_query import RAGQuery
        rag = RAGQuery()
        
        # Get all document IDs for this dataset
        results = rag.collection.get(
            where={"dataset_id": str(dataset_id)}
        )
        
        if results['ids']:
            # Delete embeddings from ChromaDB
            rag.collection.delete(ids=results['ids'])
            logger.info(
                f"Deleted {len(results['ids'])} embeddings from ChromaDB for dataset {dataset_id}",
                extra={"operation": "delete_dataset", "dataset_id": dataset_id, "embeddings_deleted": len(results['ids'])}
            )
        else:
            logger.info(
                f"No embeddings found in ChromaDB for dataset {dataset_id}",
                extra={"operation": "delete_dataset", "dataset_id": dataset_id}
            )
    except Exception as e:
        # Log error but continue with database deletion to avoid orphaned database records
        logger.error(
            f"Failed to delete embeddings from ChromaDB for dataset {dataset_id}: {str(e)}",
            extra={"operation": "delete_dataset", "dataset_id": dataset_id, "error": str(e)}
        )
        # Note: We continue with database deletion even if ChromaDB deletion fails
        # This prevents orphaned database records, though it may leave orphaned embeddings
    
    # Delete dataset from database (cascade will handle related tables)
    execute_update(
        "DELETE FROM datasets WHERE id = ?",
        (dataset_id,)
    )
    
    logger.info(
        f"Successfully deleted dataset {dataset_id} from database",
        extra={"operation": "delete_dataset", "dataset_id": dataset_id}
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
    if dataset_type in TEXT_DATASET_TYPES:
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
        "system": "Library Assessment Decision Support System",
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


def evaluate_dataset_capabilities(df: pd.DataFrame, dataset_type: str, dataset_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Inspect a DataFrame and return a detailed capability report covering
    which analyses can be run, why, and what the data looks like.

    Args:
        df: The dataset as a DataFrame
        dataset_type: 'survey', 'usage', or 'circulation'
        dataset_id: Optional — if provided, also checks actual stored rows

    Returns:
        Dict with keys:
            - analyses: dict of analysis_name -> {available, reason, details}
            - summary: short human-readable paragraph
            - warnings: list of data quality issues
            - stats: basic numeric/text stats
    """
    row_count = len(df)
    col_count = len(df.columns)
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    text_cols = [c for c in df.columns if df[c].dtype == object]
    date_cols = [c for c in df.columns if any(t in c.lower() for t in ['date', 'time', 'period', 'month', 'year'])]
    warnings = []

    # Check for sparse data
    null_pct = df.isnull().mean()
    sparse_cols = null_pct[null_pct > 0.5].index.tolist()
    if sparse_cols:
        warnings.append(f"Columns with >50% missing values: {', '.join(sparse_cols)}")

    # --- Qualitative ---
    has_text = len(text_cols) > 0
    enough_for_qual = row_count >= 10
    is_text_type = dataset_type in TEXT_DATASET_TYPES
    is_metric_type = dataset_type in METRIC_DATASET_TYPES
    qual_available = is_text_type and has_text and enough_for_qual

    qual_reason = ""
    if not is_text_type:
        qual_reason = f"Dataset type is '{dataset_type}' — qualitative analysis requires survey/text data."
    elif not has_text:
        qual_reason = "No text columns detected."
    elif not enough_for_qual:
        qual_reason = f"Only {row_count} rows — need at least 10 for meaningful analysis."
    else:
        qual_reason = f"Ready: {row_count} text responses across {len(text_cols)} text column(s)."

    # --- Correlation ---
    # Need ≥2 numeric cols and ≥10 complete rows
    usable_numeric = [c for c in numeric_cols if df[c].notna().sum() >= 10]
    corr_available = len(usable_numeric) >= 2 and is_metric_type
    corr_reason = (
        f"Ready: {len(usable_numeric)} numeric columns with sufficient data."
        if corr_available else
        f"Need ≥2 numeric columns with ≥10 values. Found {len(usable_numeric)} usable."
        if is_metric_type else
        "Correlation requires numeric usage/circulation data."
    )

    # --- Trend ---
    has_date = len(date_cols) > 0
    trend_available = has_date and len(usable_numeric) >= 1 and is_metric_type
    trend_reason = (
        f"Ready: date column '{date_cols[0]}' + {len(usable_numeric)} numeric metric(s)."
        if trend_available else
        "No date column detected — trend analysis requires time series data."
        if not has_date else
        "Trend requires numeric usage/circulation data."
    )

    # --- Comparative ---
    # Need a categorical grouping column and a numeric value column
    cat_cols = [c for c in df.columns if df[c].dtype == object and df[c].nunique() <= 20 and df[c].nunique() >= 2]
    comp_available = len(cat_cols) >= 1 and len(usable_numeric) >= 1 and is_metric_type
    comp_reason = (
        f"Ready: can compare across '{cat_cols[0]}' ({df[cat_cols[0]].nunique()} groups)."
        if comp_available else
        f"Need a categorical grouping column (≤20 unique values). Found {len(cat_cols)}."
        if is_metric_type else
        "Comparative analysis requires usage/circulation data."
    )

    # --- Distribution ---
    dist_available = len(usable_numeric) >= 1 and is_metric_type
    dist_reason = (
        f"Ready: {len(usable_numeric)} numeric column(s) available."
        if dist_available else
        "Distribution analysis requires at least one numeric column."
        if is_metric_type else
        "Distribution analysis requires usage/circulation data."
    )

    # --- RAG / Query ---
    rag_available = row_count >= 1
    rag_reason = f"Ready: {row_count} rows will be indexed for natural language queries."

    analyses = {
        "qualitative_sentiment": {"available": qual_available, "reason": qual_reason},
        "qualitative_themes":    {"available": qual_available, "reason": qual_reason},
        "correlation":           {"available": corr_available, "reason": corr_reason},
        "trend":                 {"available": trend_available, "reason": trend_reason},
        "comparative":           {"available": comp_available, "reason": comp_reason},
        "distribution":          {"available": dist_available, "reason": dist_reason},
        "rag_query":             {"available": rag_available,  "reason": rag_reason},
    }

    available_names = [k for k, v in analyses.items() if v['available']]
    unavailable_names = [k for k, v in analyses.items() if not v['available']]

    summary = (
        f"This {dataset_type} dataset has {row_count:,} rows and {col_count} columns. "
        f"Available analyses: {', '.join(available_names) if available_names else 'none'}. "
        + (f"Not available: {', '.join(unavailable_names)}." if unavailable_names else "")
    )

    return {
        "analyses": analyses,
        "summary": summary,
        "warnings": warnings,
        "stats": {
            "row_count": row_count,
            "col_count": col_count,
            "numeric_cols": numeric_cols,
            "text_cols": text_cols,
            "date_cols": date_cols,
            "usable_numeric_cols": usable_numeric,
        }
    }


def classify_dataset_for_analysis(dataset: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify a dataset as suitable for qualitative and/or quantitative analysis.

    Returns a dict with:
        - qualitative: bool
        - quantitative: bool
        - reason: str  (human-readable explanation)
        - recommended: 'qualitative' | 'quantitative' | 'both' | 'neither'
    """
    dtype = dataset.get('dataset_type', '')
    if dtype in TEXT_DATASET_TYPES:
        return {
            'qualitative': True,
            'quantitative': False,
            'reason': 'Survey datasets contain text responses — best suited for sentiment and theme analysis.',
            'recommended': 'qualitative',
        }
    elif dtype in METRIC_DATASET_TYPES:
        return {
            'qualitative': False,
            'quantitative': True,
            'reason': f'{dtype.title()} datasets contain numeric metrics — best suited for correlation, trend, and distribution analysis.',
            'recommended': 'quantitative',
        }
    else:
        return {
            'qualitative': False,
            'quantitative': False,
            'reason': 'Unknown dataset type.',
            'recommended': 'neither',
        }


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


# ============================================================================
# CSV Round-Trip Validation Functions
# ============================================================================

def _legacy_serialize_to_csv(df: pd.DataFrame) -> str:
    """
    Serialize DataFrame to CSV string.
    
    Args:
        df: DataFrame to serialize
        
    Returns:
        CSV string representation
    """
    return df.to_csv(index=False)


def _legacy_parse_from_csv(csv_string: str) -> pd.DataFrame:
    """
    Parse CSV string to DataFrame.
    
    Args:
        csv_string: CSV content as string
        
    Returns:
        Parsed DataFrame
    """
    from io import StringIO
    return pd.read_csv(
        StringIO(csv_string),
        dtype=str,
        keep_default_na=False,
        engine="python",
    )


def _legacy_dataframes_equivalent(df1: pd.DataFrame, df2: pd.DataFrame, 
                          float_tolerance: float = 1e-9) -> bool:
    """
    Check if two DataFrames are equivalent for round-trip purposes.
    
    Handles:
    - Column order differences
    - Floating point precision
    - Index differences
    - Data type compatibility (int vs float)
    
    Args:
        df1: First DataFrame
        df2: Second DataFrame
        float_tolerance: Tolerance for floating point comparison
        
    Returns:
        True if DataFrames are equivalent, False otherwise
    """
    # Check shape
    if df1.shape != df2.shape:
        return False
    
    # Sort columns to handle order differences
    df1_sorted = df1.sort_index(axis=1)
    df2_sorted = df2.sort_index(axis=1)
    
    # Check column names
    if not df1_sorted.columns.equals(df2_sorted.columns):
        return False
    
    # Check each column
    for col in df1_sorted.columns:
        col1 = df1_sorted[col]
        col2 = df2_sorted[col]
        
        # Handle numeric columns with tolerance
        if pd.api.types.is_numeric_dtype(col1) and pd.api.types.is_numeric_dtype(col2):
            # Convert to float for comparison
            col1_float = col1.astype(float)
            col2_float = col2.astype(float)
            
            # Check for NaN equality
            nan_mask1 = pd.isna(col1_float)
            nan_mask2 = pd.isna(col2_float)
            
            if not nan_mask1.equals(nan_mask2):
                return False
            
            # Compare non-NaN values with tolerance
            non_nan_mask = ~nan_mask1
            if not pd.Series(
                abs(col1_float[non_nan_mask] - col2_float[non_nan_mask]) <= float_tolerance
            ).all():
                return False
        else:
            # For non-numeric columns, use direct comparison
            if not col1.equals(col2):
                return False
    
    return True


def _legacy_validate_round_trip(df: pd.DataFrame, dataset_type: str) -> tuple:
    """
    Validate that DataFrame can round-trip through CSV serialization.
    
    Tests: df → serialize → parse → df' where df ≈ df'
    
    Args:
        df: DataFrame to validate
        dataset_type: Type of dataset (survey, usage, circulation)
        
    Returns:
        (success: bool, error_message: str)
    """
    try:
        # Serialize to CSV
        csv_string = serialize_to_csv(df)
        
        # Parse back to DataFrame
        df_restored = parse_from_csv(csv_string)
        
        # Check equivalence
        if not dataframes_equivalent(df, df_restored):
            return False, "Round-trip validation failed: DataFrames are not equivalent after serialization"
        
        # Validate restored DataFrame still meets dataset requirements
        is_valid, error_msg = validate_csv_dataframe(df_restored, dataset_type)
        if not is_valid:
            return False, f"Round-trip validation failed: Restored DataFrame invalid: {error_msg}"
        
        return True, "Round-trip validation passed"
        
    except Exception as e:
        return False, f"Round-trip validation error: {str(e)}"


def _legacy_validate_csv_dataframe(df: pd.DataFrame, dataset_type: str) -> tuple:
    """
    Validate DataFrame structure for a given dataset type.
    
    This is a helper function for round-trip validation that checks
    if a DataFrame meets the structural requirements.
    
    Args:
        df: DataFrame to validate
        dataset_type: Type of dataset (survey, usage, circulation)
        
    Returns:
        (is_valid: bool, error_message: str)
    """
    # Check if DataFrame is empty
    if df.empty:
        return False, "DataFrame is empty"
    
    # Dataset type specific validation
    if dataset_type == "survey":
        # Survey datasets are flexible - any columns accepted
        # Just check it has some data
        if len(df.columns) == 0:
            return False, "Survey dataset has no columns"
    
    elif dataset_type == "usage":
        # Usage datasets are flexible - any columns accepted
        # Just check it has some data
        if len(df.columns) == 0:
            return False, "Usage dataset has no columns"
    
    elif dataset_type == "circulation":
        # Circulation datasets are flexible - any columns accepted
        # Just check it has some data
        if len(df.columns) == 0:
            return False, "Circulation dataset has no columns"
    
    else:
        return False, f"Unknown dataset type: {dataset_type}"
    
    return True, "Validation passed"


# ============================================================================
# CSV Round-Trip Validation Functions
# ============================================================================

def serialize_to_csv(df: pd.DataFrame) -> str:
    """
    Serialize DataFrame to CSV string.
    
    Args:
        df: DataFrame to serialize
        
    Returns:
        CSV string representation
    """
    return df.to_csv(index=False)


def parse_from_csv(csv_string: str) -> pd.DataFrame:
    """
    Parse CSV string to DataFrame.
    
    Args:
        csv_string: CSV string to parse
        
    Returns:
        Parsed DataFrame
    """
    from io import StringIO
    return pd.read_csv(
        StringIO(csv_string),
        dtype=str,
        keep_default_na=False,
        engine="python",
    )


def dataframes_equivalent(df1: pd.DataFrame, df2: pd.DataFrame, tolerance: float = 1e-9) -> bool:
    """
    Check if two DataFrames are equivalent for round-trip purposes.
    
    Handles:
    - Floating point comparison with tolerance
    - Column order differences
    - Index differences
    - Type coercion (int -> float)
    
    Args:
        df1: First DataFrame
        df2: Second DataFrame
        tolerance: Floating point comparison tolerance
        
    Returns:
        True if DataFrames are equivalent
    """
    # Check shape
    if df1.shape != df2.shape:
        return False
    
    # Sort columns to handle order differences
    df1_sorted = df1.sort_index(axis=1)
    df2_sorted = df2.sort_index(axis=1)
    
    # Check column names
    if not df1_sorted.columns.equals(df2_sorted.columns):
        return False
    
    # Check each column
    for col in df1_sorted.columns:
        col1 = df1_sorted[col]
        col2 = df2_sorted[col]
        
        # Handle numeric columns with tolerance
        if pd.api.types.is_numeric_dtype(col1) and pd.api.types.is_numeric_dtype(col2):
            # Convert to float for comparison
            col1_float = col1.astype(float)
            col2_float = col2.astype(float)
            
            # Check for NaN equality
            nan_mask1 = pd.isna(col1_float)
            nan_mask2 = pd.isna(col2_float)
            
            if not nan_mask1.equals(nan_mask2):
                return False
            
            # Compare non-NaN values with tolerance
            non_nan_mask = ~nan_mask1
            if not pd.Series(col1_float[non_nan_mask]).sub(col2_float[non_nan_mask]).abs().le(tolerance).all():
                return False
        
        # Handle string-to-numeric coercion (e.g., "00000" -> 0)
        elif pd.api.types.is_string_dtype(col1) and pd.api.types.is_numeric_dtype(col2):
            # Try converting string column to numeric
            try:
                col1_numeric = pd.to_numeric(col1, errors='coerce')
                col2_float = col2.astype(float)
                
                # Check for NaN equality (including empty strings that become NaN)
                nan_mask1 = pd.isna(col1_numeric) | (col1 == '')
                nan_mask2 = pd.isna(col2_float)
                
                if not nan_mask1.equals(nan_mask2):
                    return False
                
                # Compare non-NaN values with tolerance
                non_nan_mask = ~nan_mask1
                if len(col1_numeric[non_nan_mask]) > 0:
                    if not pd.Series(col1_numeric[non_nan_mask]).sub(col2_float[non_nan_mask]).abs().le(tolerance).all():
                        return False
            except (TypeError, ValueError):
                # If conversion fails, columns are not equivalent
                return False
        
        # Handle numeric-to-string coercion (reverse case)
        elif pd.api.types.is_numeric_dtype(col1) and pd.api.types.is_string_dtype(col2):
            # Try converting string column to numeric
            try:
                col1_float = col1.astype(float)
                col2_numeric = pd.to_numeric(col2, errors='coerce')
                
                # Check for NaN equality (including empty strings that become NaN)
                nan_mask1 = pd.isna(col1_float)
                nan_mask2 = pd.isna(col2_numeric) | (col2 == '')
                
                if not nan_mask1.equals(nan_mask2):
                    return False
                
                # Compare non-NaN values with tolerance
                non_nan_mask = ~nan_mask1
                if len(col1_float[non_nan_mask]) > 0:
                    if not pd.Series(col1_float[non_nan_mask]).sub(col2_numeric[non_nan_mask]).abs().le(tolerance).all():
                        return False
            except (TypeError, ValueError):
                # If conversion fails, columns are not equivalent
                return False
        
        else:
            # For non-numeric columns, handle empty string vs NaN
            col1_filled = col1.fillna('')
            col2_filled = col2.fillna('')
            
            if not col1_filled.equals(col2_filled):
                return False
    
    return True


def validate_round_trip(df: pd.DataFrame, dataset_type: str) -> tuple[bool, str]:
    """
    Validate that DataFrame can round-trip through CSV serialization.
    
    Tests: df → serialize → parse → df' where df ≈ df'
    
    Args:
        df: DataFrame to validate
        dataset_type: Type of dataset (survey, usage, circulation)
        
    Returns:
        (success, error_message)
    """
    try:
        # Serialize to CSV
        csv_string = serialize_to_csv(df)
        
        # Parse back to DataFrame
        df_restored = parse_from_csv(csv_string)
        
        # Check equivalence
        if not dataframes_equivalent(df, df_restored):
            return False, "Round-trip validation failed: DataFrames are not equivalent after serialization"
        
        # Validate restored DataFrame has correct schema for dataset type
        is_valid, error_msg = validate_csv_dataframe(df_restored, dataset_type)
        if not is_valid:
            return False, f"Round-trip validation failed: Restored DataFrame invalid: {error_msg}"
        
        return True, ""
        
    except Exception as e:
        return False, f"Round-trip validation error: {str(e)}"


def validate_csv_dataframe(df: pd.DataFrame, dataset_type: str) -> tuple[bool, str]:
    """
    Validate DataFrame structure for a given dataset type.
    
    This is a helper function for round-trip validation.
    
    Args:
        df: DataFrame to validate
        dataset_type: Type of dataset (survey, usage, circulation)
        
    Returns:
        (is_valid, error_message)
    """
    if df.empty:
        return False, "DataFrame is empty"
    
    # For round-trip validation, we accept any column structure
    # as long as the data is preserved
    return True, ""
