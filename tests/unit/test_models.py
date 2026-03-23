"""
Unit tests for Pydantic data models.

Tests validation and structure of API data models for the library
feedback sentiment analysis service.
"""
import pytest
from src.models import ClassificationRequest, ClassificationResponse


def test_classification_request_valid():
    """Test that a valid classification request is accepted."""
    request = ClassificationRequest(text="The library staff were very helpful today.")
    assert request.text == "The library staff were very helpful today."


def test_classification_request_empty_fails():
    """Test that empty text is rejected by Pydantic validation."""
    with pytest.raises(ValueError):
        ClassificationRequest(text="")


def test_classification_response_positive():
    """Test that a positive sentiment response is valid."""
    response = ClassificationResponse(
        label="positive",
        confidence=88.0,
        reason="Expresses satisfaction with library services",
        escalate=False
    )
    assert response.label == "positive"
    assert response.confidence == 88.0
    assert response.escalate is False


def test_classification_response_negative():
    """Test that a negative sentiment response is valid."""
    response = ClassificationResponse(
        label="negative",
        confidence=75.5,
        reason="Expresses dissatisfaction with library services",
        escalate=False
    )
    assert response.label == "negative"


def test_classification_response_neutral():
    """Test that a neutral sentiment response is valid."""
    response = ClassificationResponse(
        label="neutral",
        confidence=55.0,
        reason="Neutral observation about library services",
        escalate=True
    )
    assert response.label == "neutral"
    assert response.escalate is True


def test_classification_response_invalid_label():
    """Test that an invalid label is rejected."""
    with pytest.raises(ValueError):
        ClassificationResponse(
            label="complaint",  # old label — should be rejected
            confidence=80.0,
            reason="Some reason",
            escalate=False
        )
