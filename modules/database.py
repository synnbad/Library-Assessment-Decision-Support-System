"""
Database Module

This module provides SQLite database management for the FERPA-Compliant RAG
Decision Support System, including schema initialization, connection management,
and query execution.

Key Features:
- SQLite database initialization with complete schema
- Context manager for safe connection handling
- Query execution helpers (SELECT, INSERT, UPDATE, DELETE)
- Schema migration support
- Foreign key constraints enabled
- Indexes for performance optimization
- Row factory for dict-like access

Database Schema:
- datasets: Core dataset metadata + FAIR/CARE fields
- survey_responses: Survey data with sentiment analysis
- usage_statistics: Usage metrics and circulation data
- themes: Identified themes from qualitative analysis
- users: User accounts with bcrypt password hashes
- access_logs: Audit trail of all access events
- query_logs: RAG query history with performance metrics
- reports: Generated report metadata
- qualitative_analyses: Qualitative analysis results
- quantitative_analyses: Quantitative analysis results with LLM interpretations
- schema_version: Migration tracking

Module Functions:
- init_database(): Create database schema
- get_db_connection(): Context manager for connections
- execute_query(): Execute SELECT queries
- execute_update(): Execute INSERT/UPDATE/DELETE queries
- migrate_database(): Apply schema migrations

Connection Management:
- Context manager ensures proper cleanup
- Automatic commit on success
- Automatic rollback on error
- Row factory for dict-like column access
- Foreign key constraints enabled

Performance Optimizations:
- Indexes on frequently queried columns
- Efficient foreign key relationships
- Cascade deletes for data integrity
- Connection pooling via context manager

Requirements Implemented:
- 1.3: Store data in local SQLite database
- 6.3: Store all data locally
- 6.7: Log all data access
- 7.1: Store FAIR metadata
- 7.3: Document data provenance

Configuration (config/settings.py):
- DATABASE_PATH: Path to SQLite database file (default: data/library.db)

Usage Example:
    from modules.database import init_database, get_db_connection, execute_query
    
    # Initialize database
    init_database()
    
    # Query using helper
    datasets = execute_query("SELECT * FROM datasets WHERE dataset_type = ?", ("survey",))
    for dataset in datasets:
        print(f"Dataset: {dataset['name']}")
    
    # Query using context manager
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        for user in users:
            print(f"User: {user['username']}")

Schema Version:
- Current version: 1
- Migration support for future schema changes
- Version tracking in schema_version table

Author: FERPA-Compliant RAG DSS Team
"""

import sqlite3
import time
import random
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Callable, TypeVar
from functools import wraps
from config.settings import Settings


# Database schema version for migrations
SCHEMA_VERSION = 4

# Retry configuration for database locks
MAX_RETRIES = 5
INITIAL_BACKOFF_MS = 100
MAX_BACKOFF_MS = 5000

T = TypeVar('T')
CORE_TABLES = {"datasets", "survey_responses", "usage_statistics", "schema_version"}


def retry_on_db_lock(max_retries: int = MAX_RETRIES) -> Callable:
    """
    Decorator to retry database operations on lock errors with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        
    Returns:
        Decorated function that retries on sqlite3.OperationalError
        
    Example:
        @retry_on_db_lock(max_retries=5)
        def my_db_operation():
            # Database operation that might encounter locks
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            backoff_ms = INITIAL_BACKOFF_MS
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    last_exception = e
                    error_msg = str(e).lower()
                    
                    # Only retry on database lock errors
                    if 'locked' not in error_msg and 'busy' not in error_msg:
                        raise
                    
                    # Don't sleep on the last attempt
                    if attempt < max_retries - 1:
                        # Add jitter to prevent thundering herd
                        jitter = random.uniform(0, backoff_ms * 0.1)
                        sleep_time = (backoff_ms + jitter) / 1000.0
                        time.sleep(sleep_time)
                        
                        # Exponential backoff with cap
                        backoff_ms = min(backoff_ms * 2, MAX_BACKOFF_MS)
            
            # All retries exhausted
            raise last_exception
        
        return wrapper
    return decorator


def init_database(db_path: Optional[str] = None) -> None:
    """
    Initialize SQLite database with schema.
    
    Args:
        db_path: Optional path to database file. Uses Settings.DATABASE_PATH if not provided.
    """
    if db_path is None:
        db_path = Settings.DATABASE_PATH
    
    # Ensure data directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable WAL mode for better concurrent write performance
    # WAL mode allows multiple readers and one writer to operate concurrently
    cursor.execute("PRAGMA journal_mode=WAL")
    
    # Set busy timeout to 5 seconds (5000ms) as additional protection
    cursor.execute("PRAGMA busy_timeout=5000")
    
    # Create datasets table with FAIR/CARE metadata
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dataset_type TEXT NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            row_count INTEGER,
            column_names TEXT,
            file_hash TEXT,
            -- FAIR metadata
            title TEXT,
            description TEXT,
            source TEXT,
            keywords TEXT,
            -- CARE metadata
            usage_notes TEXT,
            ethical_considerations TEXT,
            data_provenance TEXT,
            -- Analysis capabilities (JSON)
            analysis_capabilities TEXT,
            -- Indexing status tracking
            indexing_status TEXT DEFAULT 'pending',
            indexing_error TEXT,
            indexed_at TIMESTAMP
        )
    """)
    
    # Create survey_responses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS survey_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_id INTEGER,
            response_date DATE,
            question TEXT,
            response_text TEXT,
            sentiment TEXT,
            sentiment_score REAL,
            themes TEXT,
            FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
        )
    """)
    
    # Create usage_statistics table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usage_statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_id INTEGER,
            date DATE,
            metric_name TEXT,
            metric_value REAL,
            category TEXT,
            FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
        )
    """)
    
    # Create themes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS themes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_id INTEGER,
            theme_name TEXT,
            keywords TEXT,
            frequency INTEGER,
            representative_quotes TEXT,
            FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
        )
    """)
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create access_logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            action TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resource_type TEXT,
            resource_id TEXT,
            details TEXT
        )
    """)
    
    # Create query_logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS query_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            confidence REAL,
            citations TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            session_id TEXT,
            processing_time_ms INTEGER
        )
    """)
    
    # Create reports table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            dataset_ids TEXT,
            analysis_ids TEXT,
            content_markdown TEXT,
            visualization_paths TEXT,
            file_path TEXT
        )
    """)

    # Create pinned report insights table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pinned_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            source TEXT DEFAULT 'Query',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create qualitative_analyses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS qualitative_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            response_count INTEGER,
            themes TEXT,
            overall_sentiment TEXT,
            FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
        )
    """)
    
    # Create quantitative_analyses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quantitative_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_id INTEGER NOT NULL,
            analysis_type TEXT NOT NULL,
            parameters TEXT,
            statistical_results TEXT,
            interpretation TEXT,
            insights TEXT,
            recommendations TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
        )
    """)
    
    # Create indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_datasets_type ON datasets(dataset_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_query_logs_timestamp ON query_logs(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_access_logs_username ON access_logs(username)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_access_logs_timestamp ON access_logs(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_survey_responses_dataset ON survey_responses(dataset_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_statistics_dataset ON usage_statistics(dataset_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quantitative_analyses_dataset ON quantitative_analyses(dataset_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quantitative_analyses_type ON quantitative_analyses(analysis_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pinned_insights_username ON pinned_insights(username)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pinned_insights_created ON pinned_insights(created_at)")
    
    # Create application_logs table (centralized structured logging)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS application_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            level TEXT NOT NULL,
            module TEXT,
            function TEXT,
            message TEXT,
            context TEXT,
            exception TEXT
        )
    """)
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_app_logs_timestamp ON application_logs(timestamp)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_app_logs_level ON application_logs(level)"
    )

    # Create schema_version table for migrations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insert current schema version
    cursor.execute("INSERT OR IGNORE INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
    
    conn.commit()
    conn.close()
    
    print(f"Database initialized successfully at {db_path}")


def _default_database_needs_initialization(db_path: str) -> bool:
    """Return True when the default on-disk database is missing its schema."""
    path = Path(db_path)
    if not path.exists() or path.stat().st_size == 0:
        return True

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name IN (?, ?, ?, ?)",
            tuple(CORE_TABLES),
        )
        existing = {row[0] for row in cursor.fetchall()}
        conn.close()
        return not CORE_TABLES.issubset(existing)
    except sqlite3.DatabaseError:
        return True


@contextmanager
def get_db_connection(db_path: Optional[str] = None):
    """
    Context manager for database connections.
    
    Args:
        db_path: Optional path to database file. Uses Settings.DATABASE_PATH if not provided.
        
    Yields:
        sqlite3.Connection: Database connection
        
    Example:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM datasets")
            results = cursor.fetchall()
    """
    if db_path is None:
        db_path = Settings.DATABASE_PATH
        if _default_database_needs_initialization(db_path):
            init_database(db_path)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    
    # Enable WAL mode for concurrent writes
    conn.execute("PRAGMA journal_mode=WAL")
    
    # Set busy timeout to 5 seconds
    conn.execute("PRAGMA busy_timeout=5000")
    
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


@retry_on_db_lock()
def execute_query(query: str, params: tuple = (), db_path: Optional[str] = None) -> list:
    """
    Execute a SELECT query and return results.
    
    Args:
        query: SQL SELECT query
        params: Query parameters
        db_path: Optional database path
        
    Returns:
        List of rows as dictionaries
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


@retry_on_db_lock()
def execute_update(query: str, params: tuple = (), db_path: Optional[str] = None) -> int:
    """
    Execute an INSERT, UPDATE, or DELETE query.
    
    Args:
        query: SQL query
        params: Query parameters
        db_path: Optional database path
        
    Returns:
        Number of affected rows or last inserted row ID
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.lastrowid if cursor.lastrowid else cursor.rowcount


def migrate_database(db_path: Optional[str] = None) -> None:
    """
    Apply database migrations to update schema.
    
    Args:
        db_path: Optional path to database file
    """
    if db_path is None:
        db_path = Settings.DATABASE_PATH
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Get current schema version
        cursor.execute("SELECT MAX(version) as version FROM schema_version")
        result = cursor.fetchone()
        current_version = result['version'] if result['version'] else 0
        
        # Apply migrations
        if current_version < SCHEMA_VERSION:
            print(f"Migrating database from version {current_version} to {SCHEMA_VERSION}")

            if current_version < 2:
                # Add analysis_capabilities column to datasets
                try:
                    cursor.execute(
                        "ALTER TABLE datasets ADD COLUMN analysis_capabilities TEXT"
                    )
                except Exception:
                    pass  # Column may already exist
                cursor.execute("INSERT OR IGNORE INTO schema_version (version) VALUES (2)")

            if current_version < 3:
                # Add indexing status tracking columns
                try:
                    cursor.execute(
                        "ALTER TABLE datasets ADD COLUMN indexing_status TEXT DEFAULT 'pending'"
                    )
                except Exception:
                    pass  # Column may already exist
                try:
                    cursor.execute(
                        "ALTER TABLE datasets ADD COLUMN indexing_error TEXT"
                    )
                except Exception:
                    pass
                try:
                    cursor.execute(
                        "ALTER TABLE datasets ADD COLUMN indexed_at TIMESTAMP"
                    )
                except Exception:
                    pass
                cursor.execute("INSERT OR IGNORE INTO schema_version (version) VALUES (3)")

            if current_version < 4:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS pinned_insights (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT,
                        question TEXT NOT NULL,
                        answer TEXT NOT NULL,
                        source TEXT DEFAULT 'Query',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_pinned_insights_username ON pinned_insights(username)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_pinned_insights_created ON pinned_insights(created_at)"
                )
                cursor.execute("INSERT OR IGNORE INTO schema_version (version) VALUES (4)")

            print("Database migration completed")
        else:
            print(f"Database is up to date (version {current_version})")


if __name__ == "__main__":
    # Initialize database when run directly
    init_database()
    print("Database initialization complete!")
