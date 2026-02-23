# Sentiment Analysis - Intent Triage

A lightweight web interface that classifies text messages as **Question**, **Comment**, or **Complaint** using AI and a rule-based classification system.

##  What It Does

- Accepts any text input
- Returns a classification label (question/comment/complaint)
- Provides a confidence score (0-100%)
- Gives a brief explanation for the classification
- Flags low-confidence results for human review

##  Project Structure

```
sentiment-analysis/
├── backend/              # FastAPI backend service
│   ├── __init__.py
│   ├── main.py          # Main API application
│   ├── config.py        # Configuration settings
│   └── models.py        # Pydantic data models
├── frontend/            # Demo web interface
│   ├── index.html       # Main page
│   ├── styles.css       # Styling
│   └── app.js           # JavaScript logic
├── tests/               # Unit and integration tests
├── data/                # Test datasets
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
└── README.md           # This file
```

##  Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sentiment-analysis
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - Windows (PowerShell):
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - Windows (Command Prompt):
     ```cmd
     venv\Scripts\activate.bat
     ```
   - Mac/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables (optional)**
   ```bash
   copy .env.example .env
   ```
   Edit `.env` to customize settings like confidence threshold.

### Running the Application

1. **Start the server**
   ```bash
   python -m backend.main
   ```
   Or use uvicorn directly:
   ```bash
   uvicorn backend.main:app --reload
   ```

2. **Open the demo page**
   - Navigate to: `http://localhost:8000/static/index.html`
   - Or use the API directly: `http://localhost:8000/docs` (Swagger UI)

##  API Usage

### Classify Text

**Endpoint:** `POST /classify`

**Request:**
```json
{
  "text": "How do I reset my password?"
}
```

**Response:**
```json
{
  "label": "question",
  "confidence": 95.0,
  "reason": "Text contains interrogative words and seeks information",
  "escalate": false
}
```

### Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "ai_model_available": true
}
```

##  Running Tests

```bash
pytest tests/
```

For coverage:
```bash
pytest tests/ --cov=backend
```

##  Development Status

**Current Version:** v1.0  
**Week 1:**  Project structure and basic setup  
**Week 2:**  Classification logic and testing (in progress)  
**Week 3:**  Demo and refinement (upcoming)

##  Configuration

Edit `.env` file to customize:

- `USE_AI_MODEL`: Set to `true` to use AI (Hugging Face), `false` for rule-based only
- `CONFIDENCE_THRESHOLD`: Minimum confidence % before escalation (default: 70)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)

##  Tech Stack

- **Backend:** FastAPI, Python 3.8+
- **AI/ML:** Hugging Face Transformers (DistilBERT), PyTorch
- **Frontend:** HTML, CSS, Vanilla JavaScript
- **Testing:** pytest

##  AI Model

Uses **DistilBERT** from Hugging Face - a lightweight, open-source sentiment analysis model that:
- Runs locally (no API key needed)
- Works offline
- Free to use
- ~87% accuracy on test datasets

##  Niche Use Cases & Datasets

This sentiment analysis application can be adapted for various specialized domains beyond general customer support. Explore:

- **[Niche Use Cases Guide](NICHE_USE_CASES.md)**: Detailed documentation of 10+ specialized domains including healthcare, finance, education, legal, and more
- **[Datasets Reference](DATASETS_REFERENCE.md)**: Comprehensive list of publicly available datasets for training domain-specific models

Learn how to adapt this application for:
- 🏥 Healthcare patient feedback triage
- 💰 Financial services and fraud detection
- 🎓 Educational support systems
- ⚖️ Legal inquiry classification
- 👥 HR and employee feedback analysis
- 🛍️ E-commerce review analysis
- And many more specialized applications

##  License

This is a practice project for educational purposes.

##  Author

Sinbad Adjuik

---

**Note:** This is v1.0 - a minimal viable product for learning and demonstration purposes.
