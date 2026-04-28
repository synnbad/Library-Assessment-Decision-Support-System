# Library Assessment Decision Support System

A local-first Streamlit application for small-team library assessment workflows that supports
dataset import, validation, qualitative and quantitative analysis, evidence-grounded question
answering, reporting, and privacy-conscious governance.

## Why This Project Matters

Library assessment work often depends on scattered evidence: survey comments, usage statistics,
circulation exports, event data, instruction records, reference logs, e-resource reports, and
benchmark comparisons. Turning those files into clear findings for leadership can be slow,
repetitive, and difficult to audit. This project provides a local assessment workbench that helps
teams prepare data, analyze patterns, ask cited questions, and assemble reports while keeping human
review at the center of the workflow.

The application is intended as a local-first prototype and portfolio-ready workbench. It is not an
enterprise compliance platform and should not be treated as a substitute for institutional privacy,
security, FERPA, accessibility, or legal review.

## Key Capabilities

- Import CSV, TSV, TXT, Excel, and JSON assessment datasets.
- Normalize common library assessment data into analysis-ready tables.
- Validate files, detect duplicates, profile datasets, and track metadata readiness.
- Review PII signals and apply privacy-conscious redaction controls.
- Run qualitative workflows for sentiment, themes, representative quotes, and text feedback.
- Run quantitative workflows for trends, correlations, comparisons, distributions, and visualizations.
- Index uploaded records into ChromaDB for local semantic retrieval.
- Ask natural-language questions over indexed data using local RAG and citations.
- Draft leadership-oriented reports with evidence, methods, limitations, and recommendations.
- Use named local accounts with lightweight admin, analyst, and viewer roles.
- Track local logs, provenance, model status, and governance readiness.

## Privacy And Governance Note

The system is designed for local-first, privacy-conscious operation:

- SQLite stores application records locally.
- ChromaDB stores local retrieval indexes.
- Ollama provides local LLM inference when available.
- The default design avoids sending core assessment data to hosted AI services.
- RAG answers, report narratives, and AI-generated recommendations should be reviewed by a human
  before leadership use.

This project is FERPA-conscious, not a legal compliance guarantee. Institutions remain responsible
for their own policy review, access controls, retention rules, consent language, and legal
interpretation.

## Streamlit Workflow Overview

- **Home**: operational dashboard, system status, attention queue, and recommended next steps.
- **Data**: import, dataset management, PII review, metadata readiness, and indexing controls.
- **Analyze**: text feedback, metrics and trends, comparisons, charts, and modeling readiness.
- **Ask**: natural-language question workbench over active indexed datasets.
- **Reports**: leadership reports, projects, evidence handoff, dashboard planning, and methods materials.
- **Governance**: FAIR/CARE readiness and responsible-use reference material.
- **Admin**: admin-only users, model settings, PII rules, logs, backups, and system health surfaces.

## Supported Data Imports

The import UI accepts CSV, TSV, TXT, Excel `.xlsx`, and JSON files. Canonical CSV shapes remain the
safest path for direct upload:

| Dataset Type | Required Columns |
|---|---|
| Survey | `response_date`, `question`, `response_text` |
| Usage | `date`, `metric_name`, `metric_value` |
| Circulation | `checkout_date`, `material_type`, `patron_type` |

The broader importer also supports common library assessment domains:

- survey and feedback data
- usage statistics
- circulation and borrowing data
- e-resource and COUNTER-style usage reports
- spaces, room bookings, and gate counts
- instruction and learning assessment data
- reference, chat, and service interaction logs
- events and program attendance
- collection assessment data
- peer, ACRL, ARL, IPEDS, or benchmark comparison data

Sample CSV files are available in [test_data](test_data/README.md). Runtime databases, local vector
stores, logs, exports, and generated evaluation runs are intentionally ignored by Git.

## Repository Structure

```text
.
|-- config/              Environment-backed application settings
|-- data/                Runtime storage plus a few committed sample JSON fixtures
|-- docs/                Architecture, user, testing, data, and project documentation
|-- examples/            Small demonstration scripts
|-- models/              Placeholder for local model artifacts
|-- modules/             Core business logic, data, RAG, analysis, reports, logging
|-- scripts/             Setup and utility scripts
|-- test_data/           Sample CSV files for manual testing and demos
|-- tests/               Unit, integration, property, and manual smoke tests
|-- ui/                  Streamlit page modules and shared UI helpers
|-- streamlit_app.py     Main Streamlit entry point
|-- pyproject.toml       Project metadata and tool configuration
`-- requirements.txt     Runtime and development dependency list
```

## Requirements

- Supported Python: 3.10+
- Development target: Python 3.13
- Ollama installed and running for local LLM features
- Recommended local model: `llama3.2:3b`
- Recommended RAM: 16 GB or more

Some workflows can run without Ollama, but Ask answers and LLM-generated narratives require the
local Ollama service and model.

## Quick Start

```bash
git clone https://github.com/synnbad/Library-Assessment-Decision-Support-System.git
cd Library-Assessment-Decision-Support-System

python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
python -m textblob.download_corpora
ollama pull llama3.2:3b
python scripts/init_app.py
streamlit run streamlit_app.py
```

Open the Streamlit URL printed in the terminal, usually `http://localhost:8501`.

## Default Local Login Warning

The setup script creates a demo local admin account:

```text
username: admin
password: admin123
```

This credential is for local demo use only. Change it before importing real, sensitive, or
institution-owned data. Do not expose the app on a public network with the default credential.

## Configuration

Copy [.env.example](.env.example) to `.env` when local overrides are needed.

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

`EMBEDDING_LOCAL_FILES_ONLY=true` keeps embedding model loading local-first after the model is
available on the workstation.

## Testing And Validation

Run the checks locally:

```bash
python -m compileall modules ui tests
pytest
ruff check .
```

Latest local validation on 2026-04-28 used `python3` because `python` was not
available on PATH in this environment. Results: `python3 -m compileall modules ui
tests` passed, `python3 -m pytest` passed with 247 tests and one third-party
ChromaDB deprecation warning under Python 3.14.4, and `python3 -m ruff check .`
passed.

The test suite includes unit, integration, property, and manual smoke-test materials. Some workflows
depend on local services such as Ollama or a populated local database; failures should be
interpreted with the reported dependency or service context.

See [docs/TESTING.md](docs/TESTING.md) for the latest validation notes and recommended commands.

## Current Limitations

- Not a substitute for institutional FERPA, privacy, accessibility, security, or legal review.
- Local role model is lightweight and not equivalent to enterprise IAM or SSO.
- Requires local setup of Python dependencies, Ollama, and the selected local model.
- RAG output and AI-generated report language should be human-reviewed before leadership use.
- Local LLM quality and latency depend on workstation resources.
- The app is not a live BI platform; dashboard features are currently planning and handoff aids.
- Backup, restore, retention, and report approval workflows are design priorities but not yet
  complete enterprise controls.

## Roadmap

Recommended next steps focus on trust, governance, and operational polish:

- stronger role-based access controls
- configurable institution-specific PII rules
- explicit backup and restore workflows
- report approval, immutable snapshots, and versioning
- audit/log retention controls
- model endpoint allowlist
- evidence labels and citation traceability across Ask and Reports
- clearer generated-output review states
- stronger evaluation datasets for retrieval, sentiment, report quality, and usability

## Presentation And Demo Notes

The course/demo presentation deck is available at:

```text
docs/presentations/nlp_final_project_library_assessment_assistant.pptx
```

Screenshots are not currently committed. The table below identifies recommended demo assets for a
portfolio showcase without implying that those assets already exist in the repository.

| Demo Asset | Status |
|---|---|
| Home dashboard screenshot | Recommended before portfolio showcase |
| Data import and indexing screenshot | Recommended before portfolio showcase |
| Ask response with citations screenshot | Recommended before portfolio showcase |
| Report workspace screenshot | Recommended before portfolio showcase |
| Governance/Admin screenshot | Recommended before portfolio showcase |

## Documentation

- [Documentation index](docs/README.md)
- [Architecture](docs/ARCHITECTURE.md)
- [User guide](docs/USER_GUIDE.md)
- [Testing guide](docs/TESTING.md)
- [Data format guide](docs/DATA_FORMAT_GUIDE.md)
- [Dependency strategy](docs/DEPENDENCY_STRATEGY.md)
- [Local-first small-team design record](docs/LOCAL_FIRST_SMALL_TEAM_DESIGN_RECORD.md)
- [Streamlit UI design record](docs/STREAMLIT_UI_DESIGN_RECORD.md)
- [Changelog](docs/CHANGELOG.md)

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
