"""
Configuration settings for Library Assessment Decision Support System.

This module provides centralized configuration management with support for
environment variable overrides.
"""

import os
from pathlib import Path
from typing import Optional


class Settings:
    """Application configuration settings."""
    
    # Base paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    EXPORTS_DIR = BASE_DIR / "exports"
    
    # Database configuration
    DATABASE_PATH = os.getenv(
        "DATABASE_PATH",
        str(DATA_DIR / "library.db")
    )
    
    # ChromaDB configuration
    CHROMA_DB_PATH = os.getenv(
        "CHROMA_DB_PATH",
        str(DATA_DIR / "chroma_db")
    )
    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL",
        "all-MiniLM-L6-v2"
    )
    EMBEDDING_LOCAL_FILES_ONLY = os.getenv(
        "EMBEDDING_LOCAL_FILES_ONLY",
        "true"
    ).lower() == "true"
    
    # Ollama configuration
    OLLAMA_URL = os.getenv(
        "OLLAMA_URL",
        "http://localhost:11434"
    )
    OLLAMA_MODEL = os.getenv(
        "OLLAMA_MODEL",
        "llama3.2:3b"  # Default to Llama 3.2 3B
    )
    # Alternative model: "phi3:mini"
    
    # RAG configuration
    CONTEXT_WINDOW_SIZE = int(os.getenv("CONTEXT_WINDOW_SIZE", "5"))
    TOP_K_RETRIEVAL = int(os.getenv("TOP_K_RETRIEVAL", "5"))
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
    
    # Qualitative analysis configuration
    DEFAULT_N_THEMES = int(os.getenv("DEFAULT_N_THEMES", "5"))
    SENTIMENT_POSITIVE_THRESHOLD = float(os.getenv("SENTIMENT_POSITIVE_THRESHOLD", "0.1"))
    SENTIMENT_NEGATIVE_THRESHOLD = float(os.getenv("SENTIMENT_NEGATIVE_THRESHOLD", "-0.1"))
    MIN_RESPONSES_FOR_ANALYSIS = int(os.getenv("MIN_RESPONSES_FOR_ANALYSIS", "10"))
    ENABLE_ENHANCED_SENTIMENT = os.getenv("ENABLE_ENHANCED_SENTIMENT", "false").lower() == "true"
    
    # Report generation configuration
    REPORT_TIMEOUT_SECONDS = int(os.getenv("REPORT_TIMEOUT_SECONDS", "120"))
    MAX_REPORT_DATASETS = int(os.getenv("MAX_REPORT_DATASETS", "10"))
    
    # Query operation configuration
    LLM_GENERATION_TIMEOUT_SECONDS = int(os.getenv("LLM_GENERATION_TIMEOUT_SECONDS", "90"))
    MAX_CONTEXT_TOKENS = int(os.getenv("MAX_CONTEXT_TOKENS", "4000"))  # Conservative limit for 8K context models
    
    # Visualization configuration
    CHART_WIDTH = int(os.getenv("CHART_WIDTH", "800"))
    CHART_HEIGHT = int(os.getenv("CHART_HEIGHT", "600"))
    CHART_DPI = int(os.getenv("CHART_DPI", "300"))
    
    # Authentication configuration
    SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "60"))
    MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    ENABLE_DEMO_LOGIN = os.getenv("ENABLE_DEMO_LOGIN", "false").lower() == "true"
    DEMO_USERNAME = os.getenv("DEMO_USERNAME", "demo_user")
    
    # PII detection patterns
    PII_PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "address": r'\b\d+\s+[A-Za-z0-9\s,]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Circle|Cir|Way)\b'
    }
    
    # Logging configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    ENABLE_AUDIT_LOGGING = os.getenv("ENABLE_AUDIT_LOGGING", "true").lower() == "true"
    
    # FAIR/CARE configuration
    ENABLE_DATA_PROVENANCE = os.getenv("ENABLE_DATA_PROVENANCE", "true").lower() == "true"
    MANIFEST_FILENAME = os.getenv("MANIFEST_FILENAME", "data_manifest.json")
    
    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist."""
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.EXPORTS_DIR.mkdir(exist_ok=True)
        (cls.DATA_DIR / "chroma_db").mkdir(exist_ok=True)
    
    @classmethod
    def get_ollama_model(cls) -> str:
        """Get configured Ollama model name."""
        return cls.OLLAMA_MODEL
    
    @classmethod
    def get_embedding_model(cls) -> str:
        """Get configured embedding model name."""
        return cls.EMBEDDING_MODEL
    
    @classmethod
    def validate_configuration(cls) -> tuple[bool, Optional[str]]:
        """
        Validate configuration settings.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check Ollama model is valid
        valid_models = ["llama3.2:3b", "phi3:mini"]
        if cls.OLLAMA_MODEL not in valid_models:
            return False, f"Invalid Ollama model: {cls.OLLAMA_MODEL}. Must be one of {valid_models}"
        
        # Check embedding model is valid
        valid_embeddings = ["all-MiniLM-L6-v2"]
        if cls.EMBEDDING_MODEL not in valid_embeddings:
            return False, f"Invalid embedding model: {cls.EMBEDDING_MODEL}. Must be one of {valid_embeddings}"
        
        # Check numeric values are positive
        if cls.CONTEXT_WINDOW_SIZE <= 0:
            return False, "CONTEXT_WINDOW_SIZE must be positive"
        
        if cls.TOP_K_RETRIEVAL <= 0:
            return False, "TOP_K_RETRIEVAL must be positive"
        
        return True, None


# Initialize directories on import
Settings.ensure_directories()
