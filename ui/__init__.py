"""
UI Module Package

This package contains modularized Streamlit UI components for the
Library Assessment Decision Support System.

Each module is responsible for rendering a specific page or section
of the application interface.

Modules:
- auth_ui: Authentication and login interface
- home_ui: Dashboard and system status
- data_upload_ui: CSV upload and dataset management
- query_ui: RAG chat interface
- qualitative_ui: Qualitative analysis interface
- quantitative_ui: Quantitative analysis interface
- visualization_ui: Chart generation interface
- report_ui: Report generation interface
- governance_ui: FAIR/CARE documentation interface
- logs_ui: Logs and monitoring interface
"""

__version__ = "1.0.0"
__all__ = [
    "auth_ui",
    "home_ui",
    "data_upload_ui",
    "query_ui",
    "qualitative_ui",
    "quantitative_ui",
    "visualization_ui",
    "report_ui",
    "governance_ui",
    "logs_ui",
]
