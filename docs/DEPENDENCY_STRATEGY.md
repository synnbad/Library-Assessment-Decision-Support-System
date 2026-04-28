# Dependency Strategy

Last reviewed: 2026-04-19

## Current Policy

The project currently uses broad lower-bound dependency ranges in `requirements.txt`
and `pyproject.toml`. The supported Python range is 3.10+, with Python 3.13 used as
the current development target. Broad ranges keep installation flexible, but they
also mean new upstream releases can change runtime behavior without any code change
in this repository.

Keep this policy only if every dependency update is followed by:

```bash
pytest
```

The current verified baseline is:

- Python: 3.13.5 (development target; supported range is 3.10+)
- Streamlit: 1.52.2
- ChromaDB: 1.5.7
- sentence-transformers: 5.4.1
- transformers: 4.55.2
- torch: 2.8.0+cpu
- pandas: 2.3.3
- numpy: 2.2.2
- scikit-learn: 1.7.1
- scipy: 1.16.1
- plotly: 6.5.0
- Ollama app: 0.20.7
- Ollama model: llama3.2:3b

## Local-First Model Loading

Runtime model downloads should be avoided for FERPA/privacy and reliability reasons.
The app defaults to:

```env
EMBEDDING_LOCAL_FILES_ONLY=true
```

This forces `sentence-transformers/all-MiniLM-L6-v2` to load from the local Hugging
Face cache. If the model is not cached, install it during environment setup rather
than letting the app download it during use.

## Upgrade Workflow

1. Update dependencies in a branch.
2. Run `pip install -r requirements.txt` in a clean environment.
3. Ensure Ollama is running and `llama3.2:3b` is installed.
4. Run `pytest`.
5. Run one backend smoke flow: upload/store data, index, query, and export a report.
6. If model-loading behavior changes, keep `EMBEDDING_LOCAL_FILES_ONLY=true` and fix
   local cache setup instead of enabling runtime network calls.

## Optional Dependency Notes

Some features degrade gracefully when optional packages are missing:

- `reportlab`: PDF export falls back to Markdown when unavailable.
- `statsmodels`: advanced quantitative/time-series analysis may be unavailable.
- enhanced transformer sentiment: disabled unless `ENABLE_ENHANCED_SENTIMENT=true`.

If those features are required in production, verify the packages are installed in
the active runtime, not only listed in dependency files.
