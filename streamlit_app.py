"""
FERPA-Compliant RAG Decision Support System
Main Streamlit Application

This is the entry point for the library assessment AI system.
Provides authentication, data upload, RAG query interface, qualitative analysis,
visualization, and report generation capabilities.
"""

import streamlit as st
from modules import auth

# Import UI modules
from ui.auth_ui import show_login_page
from ui.home_ui import show_home_page
from ui.data_upload_ui import show_data_upload_page
from ui.query_ui import show_query_interface_page
from ui.qualitative_ui import show_qualitative_analysis_page
from ui.quantitative_ui import show_quantitative_analysis_page
from ui.visualization_ui import show_visualizations_page
from ui.report_ui import show_report_generation_page
from ui.governance_ui import show_data_governance_page
from ui.logs_ui import show_logs_page


# Page configuration
st.set_page_config(
    page_title="Library Assessment Assistant",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)


def show_main_app():
    """Display main application interface with navigation."""
    # Sidebar with navigation
    with st.sidebar:
        st.title("Library Assessment")
        st.markdown("---")
        
        # Navigation menu
        page = st.radio(
            "Navigation",
            [
                "Home",
                "Data Upload",
                "Query Interface",
                "Qualitative Analysis",
                "Quantitative Analysis",
                "Visualizations",
                "Report Generation",
                "Data Governance",
                "Logs & Monitoring"
            ],
            key="navigation"
        )
    
    # Main content area based on selected page
    if page == "Home":
        show_home_page()
    elif page == "Data Upload":
        show_data_upload_page()
    elif page == "Query Interface":
        show_query_interface_page()
    elif page == "Qualitative Analysis":
        show_qualitative_analysis_page()
    elif page == "Quantitative Analysis":
        show_quantitative_analysis_page()
    elif page == "Visualizations":
        show_visualizations_page()
    elif page == "Report Generation":
        show_report_generation_page()
    elif page == "Data Governance":
        show_data_governance_page()
    elif page == "Logs & Monitoring":
        show_logs_page()


def main():
    """Main application entry point."""
    # Run any pending DB migrations
    from modules.database import migrate_database
    try:
        migrate_database()
    except Exception:
        pass  # Non-fatal - app still works without migration

    # Initialize session state for authentication
    auth.init_session_state(st.session_state)
    
    # Auto-login with default user for development
    if not auth.is_authenticated(st.session_state):
        auth.login_user(st.session_state, "demo_user")
    
    # Show main app directly (authentication disabled for development)
    show_main_app()


if __name__ == "__main__":
    main()
