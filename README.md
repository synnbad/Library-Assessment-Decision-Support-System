# Library Assessment Decision Support System

Local-first Streamlit application for library assessment workflows. The app helps library teams upload assessment data, validate CSV files, run qualitative and quantitative analysis, ask cited natural-language questions, and generate reports without sending core data to a hosted AI service.

## Key Capabilities

- Import CSV, TSV, TXT, Excel, and JSON assessment datasets.
- Normalize survey, usage, circulation, e-resource, spaces, instruction, reference, events, collection, and benchmark data into analysis-ready tables.
- Validate, profile, and generate data dictionaries before analysis.
- Store local data in SQLite with provenance metadata.
- Index uploaded records with ChromaDB for retrieval-augmented querying.
- Use Ollama for local answer generation.
- Suggest proactive questions based on dataset shape and quality.
- Run sentiment, theme, trend, comparison, and distribution analysis.
- Plan assessment projects, peer benchmarks, dashboard user stories, KPI blueprints, modeling-readiness checks, and staff training outlines.
- Pin query insights into report generation.
- Export reports as Markdown or PDF.
- Detect and redact PII in retrieved context and generated outputs.
- Review logs, errors, performance signals, and audit activity.

## Repository Structure

```text
.
|-- config/              Environment-backed application settings
|-- data/                Local runtime storage and committed sample JSON fixtures
|-- docs/                Architecture, user, testing, data, and project documentation
|   `-- presentations/   Generated course and demo presentation decks
|-- examples/            Small demonstration scripts
|-- models/              Placeholder for local model artifacts
|-- modules/             Core business logic, data, RAG, analysis, reports, logging
|-- scripts/             Setup, audit, and utility scripts
|-- test_data/           Sample CSV files for manual testing and demos
|-- tests/               Unit, integration, property, and manual smoke tests
|-- ui/                  Streamlit page modules and shared UI helpers
|-- streamlit_app.py     Main Streamlit entry point
|-- pyproject.toml       Project metadata and tool configuration
`-- requirements.txt     Runtime dependency list
```

## Requirements

- Python 3.10 or newer
- Ollama
- Local Ollama model: `llama3.2:3b`
- Recommended RAM: 16 GB or more

## Quick Start

```powershell
git clone https://github.com/synnbad/Library-Assessment-Decision-Support-System.git
cd Library-Assessment-Decision-Support-System

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
python -m textblob.download_corpora
ollama pull llama3.2:3b
python scripts/init_app.py
streamlit run streamlit_app.py
```

Default local login:

```text
username: admin
password: admin123
```

Change the default password before using real or sensitive data.

## Configuration

Copy `.env.example` to `.env` when you need local overrides.

Important defaults:

```env
DATABASE_PATH=data/library.db
CHROMA_DB_PATH=data/chroma_db
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_LOCAL_FILES_ONLY=true
LLM_GENERATION_TIMEOUT_SECONDS=90
ENABLE_DEMO_LOGIN=false
```

`EMBEDDING_LOCAL_FILES_ONLY=true` keeps embedding model loading local-first and avoids runtime Hugging Face network calls after the model is available locally.

## Supported Data Imports

The import UI accepts CSV, TSV, TXT, Excel `.xlsx`, and JSON files. It normalizes common library assessment exports into CSV-compatible tables that continue through the existing metadata, validation, indexing, analysis, visualization, governance, and reporting workflow.

Supported assessment domains:

- Survey and feedback data
- General usage statistics
- Circulation and borrowing data
- E-resource and COUNTER-style usage reports
- Spaces, room bookings, and gate counts
- Instruction and learning assessment data
- Reference, chat, and service interaction logs
- Events and program attendance
- Collection assessment data
- Peer, ACRL, ARL, IPEDS, or benchmark comparison data

Canonical table shapes are still supported and remain the safest path for direct CSV uploads:

- Survey: `response_date`, `question`, `response_text`
- Usage: `date`, `metric_name`, `metric_value`
- Circulation: `checkout_date`, `material_type`, `patron_type`

Sample CSV files are available in `test_data/`.

## Assessment Workspace

The Assessment Workspace adds workflow support around the analysis engine:

- Projects: goals, research questions, stakeholders, methods, attached datasets, findings, and recommendations.
- Benchmarking: peer comparison summaries, rank, percentile, and top-performer views.
- Dashboard Studio: user stories, KPI recommendations, audience notes, and visualization plans for Power BI or Tableau handoff.
- Modeling Checks: missingness, numeric readiness, trend readiness, and outlier signals.
- Methods & Training: generated workshop outlines and staff-facing documentation starters.

## Testing

Run the full suite:

```powershell
pytest
```

Run lint and compile checks:

```powershell
ruff check .
python -m compileall modules ui tests
```

Current verified baseline:

```text
246 passed
```

## Presentation

The course presentation deck for `NLP for Information Professionals` is available at:

```text
docs/presentations/nlp_final_project_library_assessment_assistant.pptx
```

## Documentation

- [Documentation index](docs/README.md)
- [Architecture](docs/ARCHITECTURE.md)
- [User guide](docs/USER_GUIDE.md)
- [Testing guide](docs/TESTING.md)
- [Data format guide](docs/DATA_FORMAT_GUIDE.md)
- [Dependency strategy](docs/DEPENDENCY_STRATEGY.md)
- [Module interfaces](docs/MODULE_INTERFACES.md)
- [Changelog](docs/CHANGELOG.md)

## Runtime Notes

- Ollama must be running for generated query answers.
- RAG uses `sentence-transformers/all-MiniLM-L6-v2` for embeddings when available.
- If that embedding model cannot load, the app can fall back to ChromaDB default embeddings.
- PDF export falls back to Markdown if `reportlab` is unavailable.
- Runtime databases, vector stores, logs, and exports are intentionally ignored by Git.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
