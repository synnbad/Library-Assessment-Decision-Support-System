"""
Configuration settings for the library feedback sentiment analysis service.

This module handles all configuration for the application, loading values from
environment variables with sensible defaults.
"""
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class Config:
    """
    Application configuration class.
    
    Centralizes all configuration settings and loads them from environment variables.
    This approach allows for easy configuration changes without code modifications.
    """
    
    # Server settings
    # Host address for the FastAPI server (0.0.0.0 allows external connections)
    HOST = os.getenv("HOST", "0.0.0.0")
    # Port number for the FastAPI server
    PORT = int(os.getenv("PORT", 8000))
    
    # Model settings
    # Whether to use AI model for classification (true) or fall back to rules (false)
    USE_AI_MODEL = os.getenv("USE_AI_MODEL", "true").lower() == "true"
    # Minimum confidence percentage before flagging for human review
    CONFIDENCE_THRESHOLD = int(os.getenv("CONFIDENCE_THRESHOLD", 70))
    
    # Sentiment labels
    # The three sentiment categories for student library feedback
    SENTIMENT_LABELS = ["positive", "neutral", "negative"]
    
    def __init__(self):
        """Initialize configuration and validate settings."""
        self._validate()
    
    def _validate(self):
        """Validate configuration settings."""
        if not (1 <= self.PORT <= 65535):
            logger.warning("Invalid PORT value: %d. Using default: 8000", self.PORT)
            self.PORT = 8000
        
        if not (0 <= self.CONFIDENCE_THRESHOLD <= 100):
            logger.warning("Invalid CONFIDENCE_THRESHOLD: %d. Using default: 70", 
                          self.CONFIDENCE_THRESHOLD)
            self.CONFIDENCE_THRESHOLD = 70
        
        logger.info("Configuration loaded successfully")
        logger.info("Server: %s:%d", self.HOST, self.PORT)
        logger.info("AI Model Enabled: %s", self.USE_AI_MODEL)
        logger.info("Confidence Threshold: %d%%", self.CONFIDENCE_THRESHOLD)


# Global configuration instance - import this in other modules
config = Config()
