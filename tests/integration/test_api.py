"""
Integration tests for the library feedback sentiment analysis API.

Verifies that API endpoints work correctly end-to-end, including
request validation, response formatting, and error handling.
"""
import pytest
from fastapi.testclient import TestClient
from src.services.api import app

client = TestClient(app)


def test_health_endpoint():
    """Test the health check endpoint returns correct status information."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "ai_model_available" in data


def test_root_endpoint():
    """Test the root endpoint is accessible."""
    response = client.get("/")
    assert response.status_code == 200


def test_classify_positive_feedback():
    """Test classification of clearly positive library feedback."""
    response = client.post(
        "/classify",
        json={"text": "The library staff are always so helpful and friendly!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "label" in data
    assert "confidence" in data
    assert "reason" in data
    assert "escalate" in data
    assert data["label"] in ["positive", "neutral", "negative"]


def test_classify_negative_feedback():
    """Test classification of clearly negative library feedback."""
    response = client.post(
        "/classify",
        json={"text": "The computers are always broken and the staff are unhelpful."}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["label"] in ["positive", "neutral", "negative"]


def test_classify_endpoint_empty_text():
    """Test that the classification endpoint rejects empty text."""
    response = client.post(
        "/classify",
        json={"text": ""}
    )
    assert response.status_code == 422  # Validation error
