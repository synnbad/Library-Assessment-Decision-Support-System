# Testing And Validation

This project uses unit, integration, property-based, and manual smoke-test material
to validate the Library Assessment Decision Support System. The suite is intended
to support local development and submission review; it is not a certification of
institutional production readiness.

## Recommended Local Checks

Run these commands from the repository root:

```bash
python -m compileall modules ui tests
pytest
ruff check .
```

If the environment uses multiple Python versions, prefer the interpreter for the
active virtual environment:

```bash
python --version
python -m pytest
python -m ruff check .
```

## Python Version Policy

- Supported Python: 3.10+
- Development target: Python 3.13
- Tool target versions: Python 3.10 syntax compatibility

The project should avoid syntax that requires Python newer than 3.10 unless the
supported version policy is deliberately changed.

## Test Organization

```text
tests/
|-- unit/          Unit tests for modules and edge cases
|-- integration/   Workflow and cross-module tests
|-- property/      Hypothesis/property-based tests
`-- manual/        Manual UI and smoke-test scripts
```

## Running Focused Tests

```bash
pytest tests/unit/
pytest tests/integration/
pytest tests/property/
pytest tests/unit/test_data_importer.py
pytest tests/unit/test_query_intelligence.py
```

Manual tests under `tests/manual/` are helper scripts and notes for UI verification;
they are not a replacement for reviewing the running Streamlit app.

## Services And Local State

Some workflows depend on local services or runtime state:

- Ollama must be running for generated Ask answers and LLM-written narratives.
- The configured local model, usually `llama3.2:3b`, must be pulled before LLM tests
  can exercise generation paths.
- ChromaDB indexes live under `data/chroma_db/` and are intentionally not committed.
- SQLite runtime state lives in `data/library.db` and is intentionally not committed.

When a test fails, note whether the cause is a missing dependency, unavailable local
service, missing model, import error, assertion failure, or stale runtime data.

## Coverage

Coverage can be collected locally:

```bash
pytest --cov=modules --cov=ui --cov-report=term-missing
pytest --cov=modules --cov=ui --cov-report=html
```

Do not treat historical coverage numbers as current. Re-run coverage in the active
environment before reporting it.

## Latest Validation Notes

Last updated: 2026-04-28.

The current validation command set is:

```bash
python -m compileall modules ui tests
pytest
ruff check .
```

In the latest local validation, the `python` command was not available on PATH, so
the commands were run with `python3` instead.

```text
Python: Python 3.14.4 in this environment; project policy remains Python 3.10+
compileall: python3 -m compileall modules ui tests passed
pytest: python3 -m pytest passed, 247 passed, 1 warning, 187.77s
ruff: python3 -m ruff check . passed
warning: ChromaDB emits a Python 3.14 deprecation warning for asyncio.iscoroutinefunction
```

Record the actual output in pull requests or submission notes. If a command cannot
run in the local environment, report the exact reason instead of substituting old
test counts.

## Manual Streamlit Smoke Check

After automated checks, run:

```bash
streamlit run streamlit_app.py
```

Recommended smoke path:

1. Log in with a local test account.
2. Open Home and confirm system status renders.
3. Import or inspect sample data in Data.
4. Confirm Data > Indexing shows indexed datasets as ready.
5. Run one qualitative and one quantitative analysis where supported.
6. Ask a scoped question against indexed data and review citations.
7. Generate or preview a report draft.
8. Review Governance and Admin surfaces for expected role visibility.

## Reporting Results

Use this format in release notes, PRs, or submissions:

```text
Python:
compileall:
pytest:
ruff:
Streamlit smoke check:
Known limitations:
```

Avoid stale claims such as old pass counts or coverage percentages unless they are
clearly dated and reproduced in the current environment.
