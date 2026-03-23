# Library Feedback Sentiment Analysis

A machine learning system that automatically classifies student library feedback as **Positive**, **Neutral**, or **Negative** to help academic libraries identify trends and improve services.

## Problem & Objective

Academic libraries collect large amounts of student feedback through surveys, comments, and reviews. Manually analysing this feedback is time-consuming and difficult to scale.

This project develops a model that automatically classifies the sentiment of student feedback so libraries can quickly identify trends and act on them.

**Key Question:** Can machine learning accurately predict student sentiment toward library services?

## What It Does

- Accepts student feedback text (survey responses, comments, reviews)
- Returns a sentiment label: **positive**, **neutral**, or **negative**
- Provides a confidence score (0–100%)
- Gives a brief explanation for the classification
- Flags low-confidence results for human review

## Project Structure

```
sentiment-analysis/
├── src/
│   ├── config.py            # Configuration settings
│   ├── dataset.py           # Dataset loading and validation utilities
│   ├── models.py            # Pydantic request/response models
│   ├── modeling/
│   │   ├── predict.py       # Sentiment classification engine
│   │   └── train.py         # Training pipeline (placeholder)
│   └── services/
│       └── api.py           # FastAPI application and endpoints
├── scripts/
│   ├── run_demo.py          # Interactive demo
│   └── evaluate_model.py    # Evaluation script with accuracy metrics
├── data/
│   └── raw/
│       └── library_feedback.json   # Labelled library feedback dataset
├── reports/web-demo/        # Web interface for live demo
├── tests/                   # Unit and integration tests
├── requirements.txt
└── .env.example
```

## Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Mac/Linux
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy the environment file:
   ```bash
   copy .env.example .env
   ```

### Running the API

```bash
uvicorn src.services.api:app --reload
```

Then open:
- Web demo: `http://localhost:8000/static/index.html`
- API docs: `http://localhost:8000/docs`

## API Usage

### Classify Feedback

**Endpoint:** `POST /classify`

**Request:**
```json
{
  "text": "The library staff were incredibly helpful with my research."
}
```

**Response:**
```json
{
  "label": "positive",
  "confidence": 91.5,
  "reason": "Expresses satisfaction with library services ('helpful')",
  "escalate": false
}
```

### Health Check

**Endpoint:** `GET /health`

## Running Tests

```bash
pytest tests/
```

## Running the Demo

```bash
python scripts/run_demo.py
```

## Evaluation

```bash
python scripts/evaluate_model.py
```

## Configuration

Edit `.env` to customise:

- `USE_AI_MODEL`: `true` to use Hugging Face DistilBERT, `false` for rule-based only
- `CONFIDENCE_THRESHOLD`: Minimum confidence % before escalation (default: 70)
- `HOST` / `PORT`: Server settings

## Tech Stack

- **Backend:** FastAPI, Python 3.8+
- **AI/ML:** Hugging Face Transformers (DistilBERT), PyTorch
- **Frontend:** HTML, CSS, Vanilla JavaScript
- **Testing:** pytest

## AI Model

Uses **DistilBERT** (`distilbert-base-uncased-finetuned-sst-2-english`) from Hugging Face:
- Runs locally — no API key needed
- Works offline
- Free to use
- Binary POSITIVE/NEGATIVE output mapped to positive/neutral/negative using confidence thresholds

## Author

Sinbad Adjuik

---

*Library Assessment Project — v1.0*
