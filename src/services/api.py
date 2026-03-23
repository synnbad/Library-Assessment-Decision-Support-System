"""
FastAPI service for library student feedback sentiment analysis.

This module provides the REST API service for sentiment classification operations.
It defines all API endpoints and configures the FastAPI application with
middleware and static file serving.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.models import ClassificationRequest, ClassificationResponse, HealthResponse
from src.config import config
from src.modeling.predict import get_classifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Application version
__version__ = "1.0.0"

# Initialize FastAPI application with metadata
app = FastAPI(
    title="Library Feedback Sentiment Analysis",
    description="Classifies student library feedback as positive, neutral, or negative",
    version=__version__
)

# Enable CORS (Cross-Origin Resource Sharing) for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (adjust for production)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Mount static files directory to serve the frontend demo page
app.mount("/static", StaticFiles(directory="reports/web-demo"), name="static")


@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    logger.info("Starting Sentiment Analysis API v%s", __version__)
    logger.info("Server configured for %s:%s", config.HOST, config.PORT)


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler."""
    logger.info("Shutting down Sentiment Analysis API")


@app.get("/", tags=["Health"])
async def root():
    """
    Root endpoint providing basic API information.
    
    Returns a welcome message directing users to the demo page.
    """
    return {
        "name": "Library Feedback Sentiment Analysis API",
        "version": __version__,
        "status": "running",
        "demo": "/static/index.html",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring service status.
    
    Returns:
        HealthResponse: Contains service status, version, and AI availability
    """
    classifier = get_classifier()
    ai_available = classifier.ai_classifier.is_available()
    
    return HealthResponse(
        status="healthy",
        version=__version__,
        ai_model_available=ai_available
    )


@app.post("/classify", response_model=ClassificationResponse, tags=["Classification"])
async def classify_text(request: ClassificationRequest):
    """
    Classify student library feedback sentiment.

    This is the main classification endpoint. It accepts feedback text and returns
    the predicted sentiment along with confidence metrics and reasoning.

    Args:
        request: ClassificationRequest containing the feedback text to classify

    Returns:
        ClassificationResponse: Contains:
            - label: The sentiment (positive/neutral/negative)
            - confidence: How sure the model is (0-100%)
            - reason: Brief explanation for the classification
            - escalate: Whether human review is needed (true if confidence < threshold)
    """
    logger.debug("Processing classification request for text: %s", request.text[:50])
    
    # Get the classifier instance
    classifier = get_classifier()
    
    # Perform classification with escalation check
    result = classifier.classify_with_escalation(request.text)
    
    logger.info("Classification result: label=%s, confidence=%.2f, escalate=%s",
                result['label'], result['confidence'], result['escalate'])
    
    # Return the classification result
    return ClassificationResponse(
        label=result['label'],
        confidence=result['confidence'],
        reason=result['reason'],
        escalate=result['escalate']
    )


if __name__ == "__main__":
    # Allow running the app directly with: python -m src.services.api
    # This starts the uvicorn server with settings from config
    import uvicorn
    logger.info("Starting server on %s:%s", config.HOST, config.PORT)
    uvicorn.run(app, host=config.HOST, port=config.PORT)
