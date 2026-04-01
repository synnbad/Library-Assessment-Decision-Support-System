# FERPA-Compliant RAG Decision Support System (MVP)

An AI-powered library assessment assistant that demonstrates core AI/NLP capabilities while maintaining FERPA compliance through local-only processing. Built as a course final project (4-6 week timeline).

## Features

- **Manual CSV Data Upload**: Upload survey responses, usage statistics, and circulation data
- **RAG-Powered Queries**: Ask questions in natural language and get answers with citations
- **Qualitative Analysis**: Automated sentiment analysis and theme identification
- **Report Generation**: Generate reports with statistics, narrative text, and visualizations
- **Data Visualization**: Create bar, line, and pie charts with accessible color schemes
- **FERPA Compliance**: All processing happens locally via Ollama - no external API calls
- **FAIR & CARE Principles**: Implements responsible data governance practices

## System Requirements

- **Python**: 3.10 or higher
- **RAM**: 16GB minimum (8GB for LLM, 8GB for application)
- **Storage**: 50GB (20GB for models, 30GB for data)
- **CPU**: 4 cores minimum
- **GPU**: Optional but recommended for faster LLM inference
- **Ollama**: Must be installed and running locally

## Quick Start

### 1. Install Ollama

Follow instructions at [https://ollama.ai](https://ollama.ai) to install Ollama for your operating system.

### 2. Download LLM Model

```bash
# Download Llama 3.2 3B (recommended for MVP)
ollama pull llama3.2:3b

# Alternative: Phi-3 Mini
ollama pull phi3:mini
```

### 3. Clone Repository

```bash
git clone <repository-url>
cd <repository-name>
```

### 4. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt

# Download NLTK data for TextBlob
python -m textblob.download_corpora
```

### 6. Initialize Application

```bash
# Initialize database and create default admin user
python scripts/init_app.py
```

This will:
- Create the SQLite database with all required tables
- Create a default admin user (username: `admin`, password: `admin123`)
- ⚠️ **Important**: Change the default password after first login!

### 7. Run Application

```bash
streamlit run streamlit_app.py
```

The application will open in your browser at `http://localhost:8501`

## Project Structure

```
.
├── streamlit_app.py          # Main Streamlit application
├── modules/                   # Core Python modules
│   ├── auth.py               # Authentication
│   ├── csv_handler.py        # CSV upload and validation
│   ├── rag_query.py          # RAG query engine
│   ├── qualitative_analysis.py  # Sentiment and theme analysis
│   ├── report_generator.py  # Report generation
│   └── visualization.py      # Chart generation
├── config/                    # Configuration
│   └── settings.py           # System settings
├── data/                      # Data storage
│   ├── library.db            # SQLite database
│   └── chroma_db/            # ChromaDB vector store
├── tests/                     # Test suite
│   ├── unit/                 # Unit tests
│   ├── property/             # Property-based tests
│   └── integration/          # Integration tests
├── requirements.txt           # Python dependencies
└── README.md                 # This file
```

## Usage

### 1. Login

Use the credentials you created during setup.

### 2. Upload Data

- Navigate to "Data Upload" page
- Select dataset type (survey, usage, circulation)
- Upload CSV file
- Add FAIR/CARE metadata (title, description, source, etc.)
- Preview and confirm upload

### 3. Query Data

- Navigate to "Query Interface" page
- Type natural language questions
- View answers with citations
- Ask follow-up questions (context maintained)

### 4. Analyze Qualitative Data

- Navigate to "Qualitative Analysis" page
- Select dataset with text responses
- View sentiment distribution
- Explore identified themes
- Export analysis results

### 5. Generate Reports

- Navigate to "Report Generation" page
- Select datasets to include
- Choose whether to include visualizations
- Generate and preview report
- Export as PDF or Markdown

### 6. Create Visualizations

- Navigate to "Visualization" page
- Select dataset and chart type
- Choose columns for axes
- View and export charts

## CSV Format Requirements

### Survey Responses
Required columns: `response_date`, `question`, `response_text`

### Usage Statistics
Required columns: `date`, `metric_name`, `metric_value`

### Circulation Data
Required columns: `checkout_date`, `material_type`, `patron_type`

See USER_GUIDE.md for detailed format specifications.

## FAIR & CARE Principles

This system implements:

- **Findable**: Rich metadata, data manifest, searchable fields
- **Accessible**: Export functionality, clear access documentation
- **Interoperable**: Standard formats (CSV/JSON), documented schema
- **Reusable**: Provenance tracking, usage notes, source attribution
- **Collective Benefit**: Usage notes explain community value
- **Authority to Control**: User controls data lifecycle, local processing
- **Responsibility**: Provenance tracking, audit logging, ethical considerations
- **Ethics**: Privacy protections, ethical use documentation, FERPA compliance

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=modules --cov-report=html

# Run only unit tests
pytest tests/unit/

# Run only property tests
pytest tests/property/

# Run specific test file
pytest tests/unit/test_csv_handler.py
```

## Development

```bash
# Format code
black .

# Lint code
ruff check .

# Type checking (if using mypy)
mypy modules/
```

## Troubleshooting

### Ollama Connection Error
- Ensure Ollama is running: `ollama serve`
- Check Ollama is accessible: `curl http://localhost:11434`

### ChromaDB Error
- Delete `data/chroma_db/` directory and restart application
- ChromaDB will reinitialize automatically

### Import Errors
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

### Database Errors
- Delete `data/library.db` and reinitialize
- Run: `python -c "from modules.database import init_database; init_database()"`

## Security Notes

- Change default admin password immediately after setup
- Store database file (`data/library.db`) securely
- Regularly backup data directory
- Review access logs in `access_logs` table
- All data processing happens locally - no external API calls

## License

[Your License Here]

## Acknowledgments

Built as a course final project demonstrating:
- Local LLM deployment (Ollama)
- RAG implementation (ChromaDB + sentence-transformers)
- NLP analysis (TextBlob)
- Data visualization (Plotly)
- FERPA-compliant data handling
- FAIR & CARE data governance principles

## Support

For issues or questions, please [create an issue](link-to-issues) or contact [your-email].
