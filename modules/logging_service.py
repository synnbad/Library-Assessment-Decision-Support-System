"""
Centralized Logging Service

Provides structured logging with:
- Python logging module (console + rotating file)
- Database handler for persistent log storage
- Context tracking (user, session, module, duration)
- Helper decorators for automatic operation logging

Usage:
    from modules.logging_service import get_logger, log_operation

    logger = get_logger(__name__)
    logger.info("Something happened")

    @log_operation("qualitative_analysis")
    def run_analysis(dataset_id):
        ...
"""

import logging
import logging.handlers
import time
import traceback
import json
import functools
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

from config.settings import Settings


# File paths
LOG_DIR = Path(Settings.BASE_DIR) / "logs"
LOG_DIR.mkdir(exist_ok=True)

APP_LOG_FILE = LOG_DIR / "app.log"
ERROR_LOG_FILE = LOG_DIR / "errors.log"


# Formatter
class StructuredFormatter(logging.Formatter):
    """JSON-structured log formatter for machine-readable output."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "module": record.name,
            "func": record.funcName,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        # Attach any extra context fields
        for key in ("user", "session_id", "operation", "duration_ms", "dataset_id"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload)


# Database handler
class DatabaseLogHandler(logging.Handler):
    """Writes log records to the application_logs SQLite table."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            from modules.database import execute_update  # lazy import to avoid circular deps
            msg = self.format(record)
            exc_text = None
            if record.exc_info:
                exc_text = logging.Formatter().formatException(record.exc_info)

            context = {}
            for key in ("user", "session_id", "operation", "duration_ms", "dataset_id"):
                if hasattr(record, key):
                    context[key] = getattr(record, key)

            execute_update(
                """
                INSERT INTO application_logs
                    (timestamp, level, module, function, message, context, exception)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.utcfromtimestamp(record.created).isoformat(),
                    record.levelname,
                    record.name,
                    record.funcName,
                    record.getMessage(),
                    json.dumps(context) if context else None,
                    exc_text,
                ),
            )
        except Exception:
            # Never let logging crash the app
            self.handleError(record)


# Root logger setup (called once at import)
def _setup_root_logger() -> None:
    root = logging.getLogger("library_app")
    if root.handlers:
        return  # already configured

    level = getattr(logging, Settings.LOG_LEVEL.upper(), logging.INFO)
    root.setLevel(level)

    # Console handler - human-readable
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S")
    )
    root.addHandler(console)

    # Rotating file handler - structured JSON, keeps last 5 x 5 MB
    file_handler = logging.handlers.RotatingFileHandler(
        APP_LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(StructuredFormatter())
    root.addHandler(file_handler)

    # Separate error-only file
    error_handler = logging.handlers.RotatingFileHandler(
        ERROR_LOG_FILE, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(StructuredFormatter())
    root.addHandler(error_handler)

    # Database handler (WARNING+ to avoid flooding the DB with DEBUG noise)
    db_handler = DatabaseLogHandler()
    db_handler.setLevel(logging.WARNING)
    root.addHandler(db_handler)


_setup_root_logger()


# Public API
def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the library_app namespace."""
    # Strip leading 'modules.' for cleaner names
    short = name.replace("modules.", "").replace("src.", "")
    return logging.getLogger(f"library_app.{short}")


def log_operation(operation_name: str, level: int = logging.INFO):
    """
    Decorator that logs entry, exit, duration, and any exception for a function.

    Usage:
        @log_operation("csv_upload")
        def store_dataset(...):
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start = time.perf_counter()
            logger.log(level, "START %s", operation_name,
                       extra={"operation": operation_name})
            try:
                result = func(*args, **kwargs)
                duration_ms = int((time.perf_counter() - start) * 1000)
                logger.log(level, "OK %s (%dms)", operation_name, duration_ms,
                           extra={"operation": operation_name, "duration_ms": duration_ms})
                return result
            except Exception as exc:
                duration_ms = int((time.perf_counter() - start) * 1000)
                logger.error(
                    "FAIL %s (%dms): %s", operation_name, duration_ms, exc,
                    exc_info=True,
                    extra={"operation": operation_name, "duration_ms": duration_ms},
                )
                raise
        return wrapper
    return decorator


# Query helpers for the monitoring dashboard
def get_recent_logs(limit: int = 200, level: Optional[str] = None,
                    module: Optional[str] = None) -> list[dict]:
    """Fetch recent application_logs rows from the database."""
    from modules.database import execute_query
    conditions, params = [], []
    if level:
        conditions.append("level = ?")
        params.append(level)
    if module:
        conditions.append("module LIKE ?")
        params.append(f"%{module}%")
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    rows = execute_query(
        f"SELECT * FROM application_logs {where} ORDER BY timestamp DESC LIMIT ?",
        (*params, limit),
    )
    return [dict(r) for r in rows]


def get_error_summary(hours: int = 24) -> list[dict]:
    """Return error counts grouped by module for the last N hours."""
    from modules.database import execute_query
    rows = execute_query(
        """
        SELECT module, level, COUNT(*) as count
        FROM application_logs
        WHERE level IN ('ERROR','CRITICAL')
          AND timestamp >= datetime('now', ?)
        GROUP BY module, level
        ORDER BY count DESC
        """,
        (f"-{hours} hours",),
    )
    return [dict(r) for r in rows]


def get_operation_stats(hours: int = 24) -> list[dict]:
    """Return avg/max duration per operation from context JSON."""
    from modules.database import execute_query
    rows = execute_query(
        """
        SELECT
            json_extract(context, '$.operation') AS operation,
            COUNT(*) AS calls,
            ROUND(AVG(CAST(json_extract(context, '$.duration_ms') AS REAL)), 1) AS avg_ms,
            MAX(CAST(json_extract(context, '$.duration_ms') AS INTEGER)) AS max_ms
        FROM application_logs
        WHERE context IS NOT NULL
          AND json_extract(context, '$.operation') IS NOT NULL
          AND timestamp >= datetime('now', ?)
        GROUP BY operation
        ORDER BY calls DESC
        """,
        (f"-{hours} hours",),
    )
    return [dict(r) for r in rows]


def get_access_log_summary(hours: int = 24) -> list[dict]:
    """Return recent access_log entries."""
    from modules.database import execute_query
    rows = execute_query(
        """
        SELECT username, action, timestamp, resource_type, details
        FROM access_logs
        WHERE timestamp >= datetime('now', ?)
        ORDER BY timestamp DESC
        LIMIT 200
        """,
        (f"-{hours} hours",),
    )
    return [dict(r) for r in rows]
