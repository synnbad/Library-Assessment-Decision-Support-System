"""
FERPA-Compliant RAG Decision Support System
Main Streamlit Application

This is the entry point for the library assessment AI system.
Provides authentication, data upload, RAG query interface, qualitative analysis,
visualization, and report generation capabilities.
"""

from importlib import import_module

import streamlit as st
from config.settings import Settings
from modules import auth


PAGE_REGISTRY = {
    "Home": ("ui.home_ui", "show_home_page"),
    "Data Upload": ("ui.data_upload_ui", "show_data_upload_page"),
    "Query Interface": ("ui.query_ui", "show_query_interface_page"),
    "Qualitative Analysis": ("ui.qualitative_ui", "show_qualitative_analysis_page"),
    "Quantitative Analysis": ("ui.quantitative_ui", "show_quantitative_analysis_page"),
    "Visualizations": ("ui.visualization_ui", "show_visualizations_page"),
    "Assessment Workspace": ("ui.assessment_workflow_ui", "show_assessment_workflow_page"),
    "Report Generation": ("ui.report_ui", "show_report_generation_page"),
    "Data Governance": ("ui.governance_ui", "show_data_governance_page"),
    "Logs & Monitoring": ("ui.logs_ui", "show_logs_page"),
}


# Page configuration
st.set_page_config(
    page_title="Library Assessment Assistant",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)


def _render_ui(module_name: str, function_name: str) -> None:
    """Import and render a UI module on demand."""
    try:
        module = import_module(module_name)
        render_fn = getattr(module, function_name)
    except ModuleNotFoundError as exc:
        missing = exc.name or "a required dependency"
        st.error(f"This feature is unavailable because `{missing}` is not installed.")
        st.info("Run `pip install -r requirements.txt` and restart Streamlit to enable the full system.")
        return
    except Exception as exc:
        st.error(f"Failed to load this page: {exc}")
        return

    render_fn()


def _handle_logout() -> None:
    """Log out the current user and clear page-specific session state."""
    for key in ("query_session_id", "messages", "rag_engine"):
        if key in st.session_state:
            del st.session_state[key]

    auth.logout_user(st.session_state)
    st.rerun()


def show_main_app():
    """Display main application interface with navigation."""
    # Sidebar with navigation
    with st.sidebar:
        st.title("Library Assessment")
        st.markdown(f"**User:** {st.session_state.username}")
        if st.button("Logout", use_container_width=True):
            _handle_logout()
        st.markdown("---")

        # Navigation menu
        page = st.radio(
            "Navigation",
            list(PAGE_REGISTRY.keys()),
            key="navigation"
        )

    module_name, function_name = PAGE_REGISTRY[page]
    _render_ui(module_name, function_name)


def main():
    """Main application entry point."""
    from modules.database import init_database, migrate_database

    try:
        init_database()
    except Exception as exc:
        st.error(f"Database initialization failed: {exc}")
        return

    try:
        migrate_database()
    except Exception as exc:
        st.warning(f"Database migration could not be completed automatically: {exc}")

    # Initialize session state for authentication
    auth.init_session_state(st.session_state)

    if not auth.is_authenticated(st.session_state):
        if Settings.ENABLE_DEMO_LOGIN:
            auth.login_user(st.session_state, Settings.DEMO_USERNAME)
            st.warning(
                f"Demo login mode is enabled for `{Settings.DEMO_USERNAME}`. "
                "Disable `ENABLE_DEMO_LOGIN` to require real authentication."
            )
        else:
            _render_ui("ui.auth_ui", "show_login_page")
            return

    show_main_app()


if __name__ == "__main__":
    main()
