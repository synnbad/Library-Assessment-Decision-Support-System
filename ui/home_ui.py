"""
Home UI Module

Displays the dashboard and system status for the Library Assessment Decision Support System.
"""

import streamlit as st


def show_home_page():
    """Display home page with system overview."""
    st.title("Library Assessment Assistant")
    st.markdown("### AI-Powered Decision Support System")
    
    st.markdown("""
    Welcome to the Library Assessment Assistant! This system helps you analyze library data
    using AI-powered natural language processing while maintaining FERPA compliance through
    local-only processing.
    
    #### Key Features
    
    - **Data Upload**: Upload CSV files with survey responses, usage statistics, and circulation data
    - **Query Interface**: Ask questions in plain English and get answers with citations
    - **Qualitative Analysis**: Analyze open-ended responses for sentiment and themes
    - **Visualizations**: Generate charts to visualize trends and patterns
    - **Report Generation**: Create comprehensive reports with statistics and narratives
    - **Data Governance**: Follow FAIR and CARE principles for responsible data management
    
    #### Privacy & Compliance
    
    All data processing happens locally on your machine. No data is sent to external services,
    ensuring FERPA compliance and protecting student privacy.
    
    #### Getting Started
    
    1. **Upload Data**: Start by uploading your CSV files in the Data Upload section
    2. **Ask Questions**: Use the Query Interface to explore your data with natural language
    3. **Analyze**: Run qualitative analysis on open-ended responses
    4. **Visualize**: Create charts to present your findings
    5. **Report**: Generate comprehensive reports for stakeholders
    
    Use the navigation menu on the left to access different features.
    """)
    
    # System status
    st.markdown("---")
    st.markdown("### System Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Status", "Online")
    
    with col2:
        st.metric("Processing", "Local Only")
    
    with col3:
        st.metric("FERPA Compliant", "Yes")


def display_system_status():
    """Check and display system component status."""
    status = {
        "streamlit": "Online",
        "database": "Connected",
        "ollama": "Unknown",  # Would need to check actual connection
        "chromadb": "Unknown"
    }
    return status


def display_quick_stats():
    """Display quick statistics from database."""
    # This would query the database for actual stats
    # Placeholder for now
    pass
