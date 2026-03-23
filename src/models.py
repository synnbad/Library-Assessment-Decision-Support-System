"""
Data models for the library feedback sentiment analysis service.

This module defines all Pydantic models used for request/response validation
and serialization in the API. Pydantic ensures type safety and automatic
validation of incoming and outgoing data.
"""
from pydantic import BaseModel, Field
from typing import Literal


class ClassificationRequest(BaseModel):
    """
    Request model for sentiment classification endpoint.
    
    Attributes:
        text: The student feedback text to classify. Must be non-empty.
    """
    text: str = Field(
        min_length=1, 
        description="Student feedback text to classify",
        examples=["The library staff were incredibly helpful today!"]
    )


class ClassificationResponse(BaseModel):
    """
    Response model for sentiment classification endpoint.
    
    Returns the sentiment result with confidence metrics and reasoning.
    
    Attributes:
        label: The sentiment label (positive, neutral, or negative)
        confidence: How confident the model is in its prediction (0-100%)
        reason: A brief human-readable explanation for the classification
        escalate: True if confidence is below threshold and needs human review
    """
    label: Literal["positive", "neutral", "negative"] = Field(
        description="Sentiment label",
        examples=["positive"]
    )
    confidence: float = Field(
        ge=0, 
        le=100, 
        description="Confidence score (0-100%)",
        examples=[85.5]
    )
    reason: str = Field(
        description="Short explanation for the sentiment classification",
        examples=["Expresses satisfaction with library services"]
    )
    escalate: bool = Field(
        description="Flag indicating if human review is needed",
        examples=[False]
    )


class HealthResponse(BaseModel):
    """
    Response model for health check endpoint.
    
    Provides system status and availability information.
    
    Attributes:
        status: Overall health status of the service
        version: Current version of the application
        ai_model_available: Whether AI model is configured and available
    """
    status: str
    version: str
    ai_model_available: bool
