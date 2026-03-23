"""
Library Feedback Sentiment Analysis

Classifies student library feedback as positive, neutral, or negative.
"""

__version__ = "1.0.0"
__author__ = "Sinbad Adjuik"

from src.modeling.predict import get_classifier, IntentClassifier
from src.models import ClassificationRequest, ClassificationResponse, HealthResponse
from src.config import config

__all__ = [
    'get_classifier',
    'IntentClassifier',
    'ClassificationRequest',
    'ClassificationResponse',
    'HealthResponse',
    'config',
]
