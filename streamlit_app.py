"""
FERPA-Compliant RAG Decision Support System
Main Streamlit Application

This is the entry point for the library assessment AI system.
Provides authentication, data upload, RAG query interface, qualitative analysis,
visualization, and report generation capabilities.
"""

import streamlit as st
from modules import auth


# Page configuration
st.set_page_config(
    page_title="Library Assessment Assistant",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)


def show_login_page():
    """Display login page with authentication form."""
    st.title("Library Assessment Assistant")
    st.markdown("### Welcome")
    st.markdown("Please log in to access the system.")
    
    # Create login form
    with st.form("login_form"):
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        submit = st.form_submit_button("Log In")
        
        if submit:
            if not username or not password:
                st.error("Please enter both username and password.")
            else:
                # Attempt authentication with rate limiting
                is_valid, error_msg = auth.authenticate(username, password)
                if is_valid:
                    auth.login_user(st.session_state, username)
                    st.success(f"Welcome, {username}!")
                    st.rerun()
                else:
                    # Display specific error message from rate limiting
                    st.error(error_msg or "Invalid username or password.")
    
    # First-time setup instructions
    st.markdown("---")
    st.markdown("#### First Time Setup")
    st.markdown("""
    If this is your first time using the system, you need to create a user account.
    Run the following command in your terminal:
    
    ```bash
    python -c "from modules.auth import create_user; create_user('your_username', 'your_password')"
    ```
    
    Replace `your_username` and `your_password` with your desired credentials.
    """)


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


def show_data_upload_page():
    """Display data upload page with CSV uploader and FAIR/CARE metadata."""
    from modules import csv_handler
    import json
    
    st.title("Data Upload")
    st.markdown("Upload CSV files containing library assessment data with FAIR/CARE metadata.")
    
    # Create tabs for upload and manage datasets
    tab1, tab2 = st.tabs(["Upload New Dataset", "Manage Datasets"])
    
    with tab1:
        st.markdown("### Upload New Dataset")
        
        st.info("Tip: Use the 'Auto-Fill Metadata' button to automatically populate metadata fields based on your dataset!")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type=['csv'],
            help="Upload a CSV file containing survey responses, usage statistics, or circulation data"
        )
        
        if uploaded_file is not None:
            # Dataset type selection
            dataset_type = st.selectbox(
                "Dataset Type",
                ["survey", "usage", "circulation"],
                help="Select the type of data in your CSV file"
            )
            
            # Show helpful information about dataset types
            dataset_info = {
                "survey": "Survey data with responses, feedback, or comments. Any column structure is accepted.",
                "usage": "Usage statistics with dates and metrics (visits, sessions, etc.). Any column structure is accepted.",
                "circulation": "Circulation data with checkout information. Any column structure is accepted."
            }
            st.caption(f"Info: {dataset_info[dataset_type]}")
            
            # Dataset name
            dataset_name = st.text_input(
                "Dataset Name",
                value=uploaded_file.name.replace('.csv', ''),
                help="A unique name for this dataset"
            )
            
            # Auto-detect metadata button
            col_auto1, col_auto2 = st.columns([1, 3])
            with col_auto1:
                auto_detect = st.button("Auto-Fill Metadata", help="Automatically detect metadata from the uploaded file")
            with col_auto2:
                if auto_detect:
                    st.info("Analyzing dataset to auto-fill metadata fields...")
            
            # Initialize session state for metadata if not exists
            if 'metadata_title' not in st.session_state:
                st.session_state.metadata_title = ""
            if 'metadata_description' not in st.session_state:
                st.session_state.metadata_description = ""
            if 'metadata_source' not in st.session_state:
                st.session_state.metadata_source = ""
            if 'metadata_keywords' not in st.session_state:
                st.session_state.metadata_keywords = ""
            
            # Auto-detect metadata if button clicked
            if auto_detect:
                try:
                    uploaded_file.seek(0)
                    df = csv_handler.parse_csv(uploaded_file)
                    auto_metadata = csv_handler.auto_detect_metadata(df, dataset_type, uploaded_file.name)
                    
                    st.session_state.metadata_title = auto_metadata.get('title', '')
                    st.session_state.metadata_description = auto_metadata.get('description', '')
                    st.session_state.metadata_source = auto_metadata.get('source', '')
                    st.session_state.metadata_keywords = ', '.join(auto_metadata.get('keywords', []))
                    
                    st.success("Metadata auto-filled! Review and edit as needed.")
                except UnicodeDecodeError as e:
                    st.warning("Unable to auto-detect metadata due to file encoding issues. Please fill in metadata manually.")
                    st.caption("Tip: Try saving your CSV file with UTF-8 encoding for better compatibility.")
                except Exception as e:
                    st.warning(f"Unable to auto-detect metadata: {str(e)}")
                    st.caption("You can still fill in the metadata fields manually below.")
            
            # FAIR/CARE Metadata Section
            st.markdown("#### FAIR/CARE Metadata")
            st.markdown("Provide metadata to support findability, accessibility, and responsible data use.")
            
            with st.expander("Metadata Fields", expanded=True):
                title = st.text_input(
                    "Title",
                    value=st.session_state.metadata_title,
                    help="Human-readable title for the dataset"
                )
                
                description = st.text_area(
                    "Description",
                    value=st.session_state.metadata_description,
                    help="Detailed description of dataset contents and purpose"
                )
                
                source = st.text_input(
                    "Source",
                    value=st.session_state.metadata_source,
                    help="Origin of the data (e.g., Qualtrics, ILS, manual entry)"
                )
                
                keywords_input = st.text_input(
                    "Keywords (comma-separated)",
                    value=st.session_state.metadata_keywords,
                    help="Keywords for findability (e.g., survey, undergraduate, spring 2024)"
                )
                
                usage_notes = st.text_area(
                    "Usage Notes",
                    help="Context and guidance for responsible reuse of this data"
                )
                
                ethical_considerations = st.text_area(
                    "Ethical Considerations",
                    help="Ethical use notes and any restrictions on data use"
                )
            
            # Validate and preview
            st.markdown("---")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                validate_button = st.button("Validate CSV", use_container_width=True)
            
            with col2:
                upload_button = st.button("Upload Dataset", type="primary", use_container_width=True)
            
            # Validation
            if validate_button or upload_button:
                # Calculate file hash
                file_content = uploaded_file.getvalue()
                file_hash = csv_handler.calculate_file_hash(file_content)
                uploaded_file.seek(0)
                
                # Check for duplicates
                duplicate = csv_handler.check_duplicate(file_hash)
                if duplicate:
                    st.warning(f"Warning: This dataset has already been uploaded (detected by file hash). Upload date: {duplicate['upload_date']}")
                    st.info("You can still upload it if you want to create a separate copy.")
                
                # Validate CSV
                is_valid, error_msg = csv_handler.validate_csv(uploaded_file, dataset_type)
                
                if not is_valid:
                    st.error(f"Error: {error_msg}")
                else:
                    st.success("CSV validation passed!")
                    
                    # Show preview
                    uploaded_file.seek(0)
                    df = csv_handler.parse_csv(uploaded_file)
                    
                    st.markdown("#### Preview")
                    st.dataframe(df.head(10), use_container_width=True)
                    st.caption(f"Showing first 10 rows of {len(df)} total rows")
                    
                    # Upload if button was clicked
                    if upload_button:
                        if not dataset_name:
                            st.error("Please provide a dataset name.")
                        else:
                            try:
                                # Prepare metadata
                                keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]
                                metadata = {
                                    'title': title if title else None,
                                    'description': description if description else None,
                                    'source': source if source else None,
                                    'keywords': keywords,
                                    'usage_notes': usage_notes if usage_notes else None,
                                    'ethical_considerations': ethical_considerations if ethical_considerations else None
                                }
                                
                                # Store dataset
                                uploaded_file.seek(0)
                                df = csv_handler.parse_csv(uploaded_file)
                                dataset_id = csv_handler.store_dataset(
                                    df,
                                    dataset_name,
                                    dataset_type,
                                    file_hash,
                                    metadata
                                )
                                
                                # Log access
                                from modules import auth
                                auth.log_access(
                                    st.session_state.username,
                                    f"Uploaded dataset: {dataset_name} (ID: {dataset_id})"
                                )
                                
                                st.success(f"Dataset uploaded successfully! Dataset ID: {dataset_id}")
                                st.balloons()
                                
                            except Exception as e:
                                st.error(f"Error uploading dataset: {str(e)}")
    
    with tab2:
        st.markdown("### Manage Datasets")
        
        # Get all datasets
        datasets = csv_handler.get_datasets()
        
        if not datasets:
            st.info("No datasets uploaded yet. Upload your first dataset in the 'Upload New Dataset' tab.")
        else:
            st.markdown(f"**Total Datasets:** {len(datasets)}")
            
            # Download data manifest button
            col1, col2 = st.columns([3, 1])
            with col2:
                manifest = csv_handler.generate_data_manifest()
                manifest_json = json.dumps(manifest, indent=2)
                st.download_button(
                    "Download Data Manifest",
                    data=manifest_json,
                    file_name="data_manifest.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            st.markdown("---")
            
            # Display each dataset
            for dataset in datasets:
                with st.expander(f"{dataset['name']} (ID: {dataset['id']})", expanded=False):
                    # Basic info
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Type", dataset['dataset_type'].title())
                    with col2:
                        st.metric("Rows", dataset['row_count'])
                    with col3:
                        st.metric("Uploaded", dataset['upload_date'][:10])

                    # Analysis Capabilities
                    caps = dataset.get('analysis_capabilities')
                    if caps and caps.get('analyses'):
                        st.markdown("#### Analysis Capabilities")
                        analyses = caps['analyses']
                        LABELS = {
                            "qualitative_sentiment": "Sentiment Analysis",
                            "qualitative_themes":    "Theme Extraction",
                            "correlation":           "Correlation",
                            "trend":                 "Trend Analysis",
                            "comparative":           "Comparative Analysis",
                            "distribution":          "Distribution Analysis",
                            "rag_query":             "Natural Language Query",
                        }
                        cols = st.columns(4)
                        for idx, (key, info) in enumerate(analyses.items()):
                            with cols[idx % 4]:
                                label = LABELS.get(key, key)
                                if info['available']:
                                    st.success(label)
                                else:
                                    st.error(label)
                        if caps.get('warnings'):
                            for w in caps['warnings']:
                                st.warning(w)
                        with st.expander("Details", expanded=False):
                            for key, info in analyses.items():
                                label = LABELS.get(key, key)
                                status = "[OK]" if info['available'] else "[N/A]"
                                st.markdown(f"{status} **{label}**: {info['reason']}")
                    elif not caps:
                        # Dataset uploaded before this feature - show re-evaluate button
                        if st.button("Evaluate Capabilities", key=f"eval_{dataset['id']}"):
                            try:
                                df_preview = csv_handler.get_preview(dataset['id'], n_rows=10000)
                                new_caps = csv_handler.evaluate_dataset_capabilities(
                                    df_preview, dataset['dataset_type'], dataset['id']
                                )
                                import json as _json
                                from modules.database import execute_update as _eu
                                _eu("UPDATE datasets SET analysis_capabilities = ? WHERE id = ?",
                                    (_json.dumps(new_caps), dataset['id']))
                                st.success("Capabilities evaluated - refresh to see results.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Could not evaluate: {e}")

                    # FAIR/CARE Metadata
                    st.markdown("#### Metadata")
                    
                    if dataset.get('title'):
                        st.markdown(f"**Title:** {dataset['title']}")
                    
                    if dataset.get('description'):
                        st.markdown(f"**Description:** {dataset['description']}")
                    
                    if dataset.get('source'):
                        st.markdown(f"**Source:** {dataset['source']}")
                    
                    if dataset.get('keywords'):
                        keywords_display = ', '.join(dataset['keywords'])
                        st.markdown(f"**Keywords:** {keywords_display}")
                    
                    if dataset.get('usage_notes'):
                        st.markdown(f"**Usage Notes:** {dataset['usage_notes']}")
                    
                    if dataset.get('ethical_considerations'):
                        st.markdown(f"**Ethical Considerations:** {dataset['ethical_considerations']}")
                    
                    st.markdown("---")
                    
                    # Action buttons
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        # Edit metadata button
                        if st.button(f"Edit Metadata", key=f"edit_{dataset['id']}"):
                            st.session_state[f"editing_{dataset['id']}"] = True
                    
                    with col2:
                        # Export CSV button
                        csv_data = csv_handler.export_dataset(dataset['id'], 'csv')
                        if csv_data:
                            st.download_button(
                                "Export CSV",
                                data=csv_data,
                                file_name=f"{dataset['name']}.csv",
                                mime="text/csv",
                                key=f"export_csv_{dataset['id']}"
                            )
                    
                    with col3:
                        # Export JSON button
                        json_data = csv_handler.export_dataset(dataset['id'], 'json')
                        if json_data:
                            st.download_button(
                                "Export JSON",
                                data=json_data,
                                file_name=f"{dataset['name']}.json",
                                mime="application/json",
                                key=f"export_json_{dataset['id']}"
                            )
                    
                    with col4:
                        # Delete button
                        if st.button(f"Delete", key=f"delete_{dataset['id']}", type="secondary"):
                            st.session_state[f"confirm_delete_{dataset['id']}"] = True
                    
                    # Edit metadata form
                    if st.session_state.get(f"editing_{dataset['id']}", False):
                        st.markdown("#### Edit Metadata")
                        with st.form(f"edit_form_{dataset['id']}"):
                            new_title = st.text_input("Title", value=dataset.get('title', ''))
                            new_description = st.text_area("Description", value=dataset.get('description', ''))
                            new_source = st.text_input("Source", value=dataset.get('source', ''))
                            
                            current_keywords = ', '.join(dataset.get('keywords', []))
                            new_keywords_input = st.text_input("Keywords (comma-separated)", value=current_keywords)
                            
                            new_usage_notes = st.text_area("Usage Notes", value=dataset.get('usage_notes', ''))
                            new_ethical = st.text_area("Ethical Considerations", value=dataset.get('ethical_considerations', ''))
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                save_button = st.form_submit_button("Save Changes", type="primary")
                            with col2:
                                cancel_button = st.form_submit_button("Cancel")
                            
                            if save_button:
                                new_keywords = [k.strip() for k in new_keywords_input.split(',') if k.strip()]
                                new_metadata = {
                                    'title': new_title if new_title else None,
                                    'description': new_description if new_description else None,
                                    'source': new_source if new_source else None,
                                    'keywords': new_keywords,
                                    'usage_notes': new_usage_notes if new_usage_notes else None,
                                    'ethical_considerations': new_ethical if new_ethical else None
                                }
                                
                                if csv_handler.update_dataset_metadata(dataset['id'], new_metadata):
                                    st.success("Metadata updated successfully!")
                                    st.session_state[f"editing_{dataset['id']}"] = False
                                    
                                    # Log access
                                    from modules import auth
                                    auth.log_access(
                                        st.session_state.username,
                                        f"Updated metadata for dataset: {dataset['name']} (ID: {dataset['id']})"
                                    )
                                    st.rerun()
                                else:
                                    st.error("Failed to update metadata.")
                            
                            if cancel_button:
                                st.session_state[f"editing_{dataset['id']}"] = False
                                st.rerun()
                    
                    # Delete confirmation
                    if st.session_state.get(f"confirm_delete_{dataset['id']}", False):
                        st.warning(f"Warning: Are you sure you want to delete '{dataset['name']}'? This action cannot be undone.")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"Yes, Delete", key=f"confirm_yes_{dataset['id']}", type="primary"):
                                if csv_handler.delete_dataset(dataset['id']):
                                    st.success(f"Dataset '{dataset['name']}' deleted successfully!")
                                    
                                    # Log access
                                    from modules import auth
                                    auth.log_access(
                                        st.session_state.username,
                                        f"Deleted dataset: {dataset['name']} (ID: {dataset['id']})"
                                    )
                                    
                                    st.session_state[f"confirm_delete_{dataset['id']}"] = False
                                    st.rerun()
                                else:
                                    st.error("Failed to delete dataset.")
                        with col2:
                            if st.button(f"Cancel", key=f"confirm_no_{dataset['id']}"):
                                st.session_state[f"confirm_delete_{dataset['id']}"] = False
                                st.rerun()


def show_query_interface_page():
    """Display query interface page with chat interface and RAG functionality."""
    from modules.rag_query import RAGQuery
    from modules import auth, csv_handler
    
    st.title("Query Interface")
    st.markdown("Ask questions about your library data in natural language.")
    
    # Initialize RAG engine in session state
    if 'rag_engine' not in st.session_state:
        try:
            st.session_state.rag_engine = RAGQuery()
        except Exception as e:
            st.error(f"Failed to initialize RAG engine: {str(e)}")
            st.info("Please ensure ChromaDB is properly configured.")
            return
    
    # Initialize secure session ID for conversation context
    # Uses cryptographically secure token with username and timestamp
    if 'query_session_id' not in st.session_state:
        st.session_state.query_session_id = auth.get_secure_session_id(
            st.session_state, 
            st.session_state.username
        )
    else:
        # Validate existing session ID on each request
        is_valid, error_msg = auth.validate_session_id(
            st.session_state.query_session_id,
            st.session_state.username
        )
        if not is_valid:
            # Session invalid, create new one
            st.warning(f"Session validation failed: {error_msg}. Creating new session.")
            st.session_state.query_session_id = auth.get_secure_session_id(
                st.session_state,
                st.session_state.username
            )
    
    # Initialize message history in session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    rag_engine = st.session_state.rag_engine

    # Auto-index any datasets not yet in ChromaDB
    datasets = csv_handler.get_datasets()
    newly_indexed = []
    for ds in datasets:
        if not rag_engine._is_dataset_indexed(ds['id']):
            try:
                n = rag_engine.index_dataset(ds['id'])
                if n > 0:
                    newly_indexed.append(f"{ds['name']} ({n} docs)")
            except Exception as e:
                st.warning(f"Could not index dataset '{ds['name']}': {e}")
    if newly_indexed:
        st.info(f"Indexed datasets: {', '.join(newly_indexed)}")

    # Test Ollama connection
    is_connected, error_msg = rag_engine.test_ollama_connection()
    
    if not is_connected:
        st.error(f"Error: {error_msg}")
        st.markdown("""
        ### How to start Ollama:
        
        1. Open a terminal
        2. Run: `ollama serve`
        3. In another terminal, ensure the model is available: `ollama pull llama3.2:3b`
        4. Refresh this page
        
        For more information, visit: https://ollama.ai
        """)
        return
    
    # Show connection status
    st.success("Connected to Ollama")
    
    # Get conversation history
    conversation_history = rag_engine.get_conversation_history(st.session_state.query_session_id)
    context_size = len(conversation_history)
    
    # Display conversation context indicator
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.metric("Conversation Context", f"{context_size} turns")
    with col2:
        if st.button("Clear Context", use_container_width=True):
            rag_engine.clear_conversation(st.session_state.query_session_id)
            st.session_state.messages = []
            # Generate new secure session ID with username and timestamp
            st.session_state.query_session_id = auth.get_secure_session_id(
                st.session_state,
                st.session_state.username
            )
            
            # Log access
            auth.log_access(
                st.session_state.username,
                "Cleared query conversation context"
            )
            st.rerun()
    with col3:
        st.metric("Model", "Llama 3.2")
    
    st.markdown("---")
    
    # Display chat messages
    for msg_idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            # Check for error type in assistant messages
            if message["role"] == "assistant" and "error_type" in message:
                error_type = message.get("error_type")
                if error_type == "no_relevant_data":
                    st.warning("No Relevant Data Found")
                elif error_type == "context_too_large":
                    st.error("Context Too Large")
                elif error_type == "llm_timeout":
                    st.error("Response Generation Timed Out")
                elif error_type == "ollama_connection_failed":
                    st.error("Ollama Connection Failed")
                elif error_type == "exception":
                    st.error("Error")
            
            st.markdown(message["content"])
            
            # Display citations if present
            if message["role"] == "assistant" and "citations" in message:
                if message["citations"]:
                    with st.expander("Citations", expanded=False):
                        for citation in message["citations"]:
                            st.markdown(f"- **Source {citation['source_number']}**: Dataset ID {citation['dataset_id']} ({citation['dataset_type']}) - {citation.get('date', 'N/A')}")
            
            # Display suggested questions if present
            if message["role"] == "assistant" and "suggested_questions" in message:
                if message["suggested_questions"]:
                    with st.expander("Suggested Follow-up Questions", expanded=False):
                        for i, suggestion in enumerate(message["suggested_questions"]):
                            if st.button(suggestion, key=f"suggestion_{msg_idx}_{i}"):
                                # Add suggestion as user message and process it
                                st.session_state.messages.append({"role": "user", "content": suggestion})
                                st.rerun()
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your library data..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Query RAG engine
                    result = rag_engine.query(
                        question=prompt,
                        session_id=st.session_state.query_session_id,
                        username=st.session_state.username
                    )
                    
                    # Check for error types
                    error_type = result.get("error_type")
                    
                    if error_type == "no_relevant_data":
                        st.warning("No Relevant Data Found")
                        st.markdown(result["answer"])
                    elif error_type == "context_too_large":
                        st.error("Context Too Large")
                        st.markdown(result["answer"])
                    elif error_type == "llm_timeout":
                        st.error("Response Generation Timed Out")
                        st.markdown(result["answer"])
                    elif error_type == "ollama_connection_failed":
                        st.error("Ollama Connection Failed")
                        st.markdown(result["answer"])
                    else:
                        # Normal response
                        st.markdown(result["answer"])
                    
                    # Display citations
                    if result["citations"]:
                        with st.expander("Citations", expanded=False):
                            for citation in result["citations"]:
                                st.markdown(f"- **Source {citation['source_number']}**: Dataset ID {citation['dataset_id']} ({citation['dataset_type']}) - {citation.get('date', 'N/A')}")
                    
                    # Display suggested questions
                    if result["suggested_questions"]:
                        with st.expander("Suggested Follow-up Questions", expanded=False):
                            for i, suggestion in enumerate(result["suggested_questions"]):
                                if st.button(suggestion, key=f"suggestion_live_{len(st.session_state.messages)}_{i}"):
                                    # Add suggestion as user message
                                    st.session_state.messages.append({"role": "user", "content": suggestion})
                                    st.rerun()
                    
                    # Display processing time (only for successful queries)
                    if not error_type:
                        st.caption(f"Processing time: {result['processing_time_ms']}ms | Confidence: {result['confidence']:.2%}")
                    else:
                        st.caption(f"Processing time: {result['processing_time_ms']}ms")
                    
                    # Add assistant message to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result["answer"],
                        "citations": result["citations"],
                        "suggested_questions": result["suggested_questions"],
                        "error_type": error_type
                    })
                    
                    # Log access
                    auth.log_access(
                        st.session_state.username,
                        f"Query: {prompt[:100]}..."
                    )
                    
                except Exception as e:
                    error_message = f"Error processing query: {str(e)}"
                    st.error(error_message)
                    
                    # Check for specific error types
                    if "Ollama" in str(e) or "connection" in str(e).lower():
                        st.markdown("""
                        ### Ollama Connection Error
                        
                        The connection to Ollama was lost. Please:
                        1. Check that Ollama is still running (`ollama serve`)
                        2. Verify the model is available (`ollama list`)
                        3. Try your question again
                        """)
                    elif "ChromaDB" in str(e) or "vector" in str(e).lower():
                        st.markdown("""
                        ### Vector Store Error
                        
                        There was an issue with the vector database. Please:
                        1. Ensure you have uploaded and indexed datasets
                        2. Check that ChromaDB is properly initialized
                        3. Try restarting the application
                        """)
                    else:
                        st.markdown("""
                        ### General Error
                        
                        An unexpected error occurred. Please:
                        1. Try rephrasing your question
                        2. Ensure you have uploaded relevant data
                        3. Check the application logs for details
                        """)
                    
                    # Add error to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_message,
                        "citations": [],
                        "suggested_questions": [],
                        "error_type": "exception"
                    })
    
    # Help section
    st.markdown("---")
    with st.expander("How to use the Query Interface", expanded=False):
        st.markdown("""
        ### Getting Started
        
        1. **Upload Data**: First, upload your CSV files in the Data Upload section
        2. **Index Data**: The system automatically indexes uploaded data for searching
        3. **Ask Questions**: Type natural language questions about your data
        4. **Review Answers**: Answers include citations showing which data sources were used
        5. **Follow Up**: Use suggested questions or ask follow-up questions to explore further
        
        ### Example Questions
        
        - "What are the main themes in student feedback?"
        - "How has library usage changed over time?"
        - "What do students say about study spaces?"
        - "Which resources are most popular?"
        - "What is the overall sentiment of survey responses?"
        
        ### Conversation Context
        
        The system maintains context from your last 5 conversation turns, allowing you to ask
        follow-up questions without repeating information. Use the "Clear Context" button to
        start a fresh conversation.
        
        ### Citations
        
        Every answer includes citations showing which datasets and data points were used to
        generate the response. This ensures transparency and allows you to verify the information.
        """)
    
    st.markdown("---")
    st.caption("Tip: Be specific in your questions for better results. The system searches across all uploaded datasets.")


def show_qualitative_analysis_page():
    """Display qualitative analysis page with sentiment and theme analysis."""
    from modules import csv_handler, qualitative_analysis, visualization, auth
    import pandas as pd
    import json
    
    st.title("Qualitative Analysis")
    st.markdown("Analyze open-ended survey responses for sentiment and themes.")
    
    # Get available datasets
    datasets = csv_handler.get_datasets()

    if not datasets:
        st.info("No datasets available. Please upload data in the Data Upload section.")
        return

    # Classify datasets and build selector with hints
    def _label(d):
        info = csv_handler.classify_dataset_for_analysis(d)
        tag = "Recommended" if info['recommended'] == 'qualitative' else "Not ideal"
        return f"{d['name']} (ID: {d['id']}, {d['dataset_type']}) - {tag}"

    dataset_options = {_label(d): d['id'] for d in datasets}
    survey_datasets = [d for d in datasets if d['dataset_type'] == 'survey']

    # Default to first survey dataset if available
    default_label = next((_label(d) for d in survey_datasets), list(dataset_options.keys())[0])

    st.markdown("### Select Dataset")
    selected_label = st.selectbox(
        "Choose a dataset to analyze",
        options=list(dataset_options.keys()),
        index=list(dataset_options.keys()).index(default_label),
        key="analysis_dataset_selector"
    )

    selected_dataset_id = dataset_options[selected_label]
    selected_dataset = next(d for d in datasets if d['id'] == selected_dataset_id)
    analysis_info = csv_handler.classify_dataset_for_analysis(selected_dataset)

    # Show suitability banner
    if analysis_info['recommended'] == 'qualitative':
        st.success(analysis_info['reason'])
    else:
        st.warning(f"{analysis_info['reason']} Results may be limited.")

    # Display dataset info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Dataset", selected_dataset['name'])
    with col2:
        st.metric("Total Rows", selected_dataset['row_count'])
    with col3:
        st.metric("Upload Date", selected_dataset['upload_date'][:10])
    
    st.markdown("---")
    
    # Analysis options
    st.markdown("### Analysis Options")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        n_themes = st.slider(
            "Number of themes to identify",
            min_value=2,
            max_value=10,
            value=5,
            help="Select how many themes to extract from the responses"
        )
    
    with col2:
        st.markdown("")
        st.markdown("")
        analyze_button = st.button("Run Analysis", type="primary", use_container_width=True)
    
    # Run analysis
    if analyze_button:
        with st.spinner("Analyzing responses... This may take a moment."):
            try:
                sentiment_results = qualitative_analysis.analyze_dataset_sentiment(selected_dataset_id)
                theme_results = qualitative_analysis.extract_themes(selected_dataset_id, n_themes)
                
                st.session_state.analysis_results = {
                    'dataset_id': selected_dataset_id,
                    'dataset_name': selected_dataset['name'],
                    'sentiment': sentiment_results,
                    'themes': theme_results
                }
                
                auth.log_access(
                    st.session_state.username,
                    f"Performed qualitative analysis on dataset: {selected_dataset['name']} (ID: {selected_dataset_id})"
                )
                
                st.success("Analysis completed successfully!")
                
            except ValueError as e:
                st.error(f"{str(e)}")
                return
            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")
                return
    
    # Display results if available
    if 'analysis_results' in st.session_state and st.session_state.analysis_results['dataset_id'] == selected_dataset_id:
        results = st.session_state.analysis_results
        sentiment_results = results['sentiment']
        theme_results = results['themes']
        
        st.markdown("---")
        st.markdown("## Analysis Results")
        
        # Sentiment Analysis Section
        st.markdown("### Sentiment Distribution")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Responses", sentiment_results['total_responses'])
        with col2:
            st.metric("Positive", f"{sentiment_results['distribution']['positive']:.1%}")
        with col3:
            st.metric("Neutral", f"{sentiment_results['distribution']['neutral']:.1%}")
        with col4:
            st.metric("Negative", f"{sentiment_results['distribution']['negative']:.1%}")
        
        # Sentiment distribution chart
        sentiment_df = pd.DataFrame([
            {"Sentiment": "Positive", "Count": sentiment_results['distribution']['positive'] * sentiment_results['total_responses']},
            {"Sentiment": "Neutral", "Count": sentiment_results['distribution']['neutral'] * sentiment_results['total_responses']},
            {"Sentiment": "Negative", "Count": sentiment_results['distribution']['negative'] * sentiment_results['total_responses']}
        ])
        
        sentiment_chart = visualization.create_bar_chart(
            sentiment_df,
            x="Sentiment",
            y="Count",
            title="Sentiment Distribution",
            x_label="Sentiment Category",
            y_label="Number of Responses"
        )
        st.plotly_chart(sentiment_chart, use_container_width=True)
        
        # Theme Analysis Section
        st.markdown("---")
        st.markdown("### Identified Themes")
        
        st.markdown(f"**{len(theme_results['themes'])} themes identified from {theme_results['total_responses']} responses**")
        
        # Display each theme
        for theme in theme_results['themes']:
            with st.expander(f"**{theme['theme_name']}** ({theme['frequency']} responses, {theme['percentage']:.1f}%)", expanded=True):
                # Theme details
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown("**Keywords:**")
                    st.markdown(", ".join(theme['keywords']))
                    
                    st.markdown("**Frequency:**")
                    st.markdown(f"{theme['frequency']} responses ({theme['percentage']:.1f}%)")
                
                with col2:
                    st.markdown("**Sentiment Distribution:**")
                    st.markdown(f"- Positive: {theme['sentiment_distribution']['positive']:.1%}")
                    st.markdown(f"- Neutral: {theme['sentiment_distribution']['neutral']:.1%}")
                    st.markdown(f"- Negative: {theme['sentiment_distribution']['negative']:.1%}")
                
                # Representative quotes
                if theme['representative_quotes']:
                    st.markdown("**Representative Quotes:**")
                    for i, quote in enumerate(theme['representative_quotes'], 1):
                        st.markdown(f"{i}. *\"{quote}\"*")
        
        # Theme frequency chart
        st.markdown("---")
        st.markdown("### Theme Frequency Distribution")
        
        theme_df = pd.DataFrame([
            {"Theme": theme['theme_name'], "Frequency": theme['frequency']}
            for theme in theme_results['themes']
        ])
        
        theme_chart = visualization.create_bar_chart(
            theme_df,
            x="Theme",
            y="Frequency",
            title="Theme Frequency Distribution",
            x_label="Theme",
            y_label="Number of Responses"
        )
        st.plotly_chart(theme_chart, use_container_width=True)
        
        # Export section
        st.markdown("---")
        st.markdown("### Export Analysis Results")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Export themes to CSV
            theme_export_df = pd.DataFrame([
                {
                    "Theme": theme['theme_name'],
                    "Keywords": ", ".join(theme['keywords']),
                    "Frequency": theme['frequency'],
                    "Percentage": f"{theme['percentage']:.1f}%",
                    "Positive_Sentiment": f"{theme['sentiment_distribution']['positive']:.1%}",
                    "Neutral_Sentiment": f"{theme['sentiment_distribution']['neutral']:.1%}",
                    "Negative_Sentiment": f"{theme['sentiment_distribution']['negative']:.1%}"
                }
                for theme in theme_results['themes']
            ])
            
            csv_data = theme_export_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Export Themes (CSV)",
                data=csv_data,
                file_name=f"themes_{results['dataset_name']}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            # Export sentiment chart
            sentiment_chart_bytes = visualization.export_chart(sentiment_chart, "sentiment_distribution", format='html')
            st.download_button(
                "Export Sentiment Chart",
                data=sentiment_chart_bytes,
                file_name=f"sentiment_chart_{results['dataset_name']}.html",
                mime="text/html",
                use_container_width=True
            )
        
        with col3:
            # Export theme chart
            theme_chart_bytes = visualization.export_chart(theme_chart, "theme_frequency", format='html')
            st.download_button(
                "Export Theme Chart",
                data=theme_chart_bytes,
                file_name=f"theme_chart_{results['dataset_name']}.html",
                mime="text/html",
                use_container_width=True
            )
    
    # Help section
    st.markdown("---")
    with st.expander("How to use Qualitative Analysis", expanded=False):
        st.markdown("""
        ### Getting Started
        
        1. **Select Dataset**: Choose a survey dataset from the dropdown
        2. **Set Options**: Choose the number of themes to identify (2-10)
        3. **Run Analysis**: Click "Run Analysis" to perform sentiment and theme analysis
        4. **Review Results**: Examine sentiment distribution and identified themes
        5. **Export**: Download analysis results as CSV or charts as HTML
        
        ### Sentiment Analysis
        
        The system analyzes each response and categorizes it as:
        - **Positive**: Responses with positive sentiment (polarity > 0.1)
        - **Neutral**: Responses with neutral sentiment (polarity between -0.1 and 0.1)
        - **Negative**: Responses with negative sentiment (polarity < -0.1)
        
        ### Theme Identification
        
        The system uses TF-IDF keyword extraction and K-means clustering to identify
        recurring themes in the responses. For each theme, you'll see:
        - **Keywords**: Top keywords associated with the theme
        - **Frequency**: Number of responses in this theme
        - **Sentiment Distribution**: Sentiment breakdown for responses in this theme
        - **Representative Quotes**: Example responses that exemplify the theme
        
        ### Minimum Requirements
        
        - At least 10 responses are required for analysis
        - At least as many responses as themes requested (e.g., 5 responses for 5 themes)
        
        ### Export Options
        
        - **CSV Export**: Download theme data with keywords, frequencies, and sentiment
        - **Chart Export**: Download interactive HTML charts for presentations
        """)
    
    st.markdown("---")
    st.caption("Tip: Run analysis with different numbers of themes to find the optimal granularity for your data.")


def show_visualizations_page():
    """Display visualizations page with chart generation and export."""
    from modules import csv_handler, visualization, auth
    import pandas as pd

    st.title("Visualizations")
    st.markdown("Generate charts to visualize trends and patterns in your library data.")

    datasets = csv_handler.get_datasets()
    if not datasets:
        st.info("No datasets available. Please upload data in the Data Upload section.")
        return

    # Smart dataset selector
    def _viz_label(d):
        caps = d.get('analysis_capabilities', {})
        analyses = caps.get('analyses', {}) if caps else {}
        stats = caps.get('stats', {}) if caps else {}
        n_num = len(stats.get('usable_numeric_cols', []))
        has_date = len(stats.get('date_cols', [])) > 0
        hints = []
        if d['dataset_type'] in ('usage', 'circulation'):
            if has_date: hints.append('trend')
            if n_num >= 1: hints.append('bar/pie')
        elif d['dataset_type'] == 'survey':
            hints.append('sentiment chart')
        tag = ', '.join(hints) if hints else d['dataset_type']
        return f"{d['name']} ({d['dataset_type']}) - {tag}"

    dataset_options = {_viz_label(d): d['id'] for d in datasets}
    st.markdown("### Select Dataset")
    selected_label = st.selectbox(
        "Choose a dataset to visualize",
        options=list(dataset_options.keys()),
        key="viz_dataset_selector"
    )
    selected_dataset_id = dataset_options[selected_label]
    selected_dataset = next(d for d in datasets if d['id'] == selected_dataset_id)
    
    # Display dataset info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Dataset", selected_dataset['name'])
    with col2:
        st.metric("Type", selected_dataset['dataset_type'].title())
    with col3:
        st.metric("Rows", selected_dataset['row_count'])

    st.markdown("---")

    # Load full dataset for column inspection
    try:
        preview_df = csv_handler.get_preview(selected_dataset_id, n_rows=selected_dataset['row_count'])

        if preview_df.empty:
            st.error("Unable to load dataset. Please try another dataset.")
            return

        available_columns = preview_df.columns.tolist()
        numeric_cols = preview_df.select_dtypes(include='number').columns.tolist()
        date_cols = [c for c in available_columns if any(t in c.lower() for t in ['date', 'time', 'period', 'month', 'year'])]
        text_cols = [c for c in available_columns if preview_df[c].dtype == object]

        # Auto-detect best chart type and columns
        dtype = selected_dataset['dataset_type']
        if dtype in ('usage', 'circulation') and date_cols and numeric_cols:
            default_chart = "Line Chart"
            default_x = date_cols[0]
            default_y = numeric_cols[0]
            st.info(f"Time series detected - Line Chart pre-selected using '{default_x}' vs '{default_y}'.")
        elif dtype in ('usage', 'circulation') and numeric_cols:
            default_chart = "Bar Chart"
            default_x = text_cols[0] if text_cols else available_columns[0]
            default_y = numeric_cols[0]
            st.info("Numeric data detected - Bar Chart pre-selected.")
        elif dtype == 'survey':
            default_chart = "Pie Chart"
            # For survey, sentiment column is best for pie; fall back to first text col
            sentiment_col = next((c for c in available_columns if 'sentiment' in c.lower()), None)
            default_x = sentiment_col or (text_cols[0] if text_cols else available_columns[0])
            default_y = numeric_cols[0] if numeric_cols else available_columns[0]
            st.info("Survey data detected - Pie Chart pre-selected for distribution view.")
        else:
            default_chart = "Bar Chart"
            default_x = available_columns[0]
            default_y = numeric_cols[0] if numeric_cols else available_columns[0]

        # Chart configuration
        st.markdown("### Chart Configuration")
        col1, col2 = st.columns([1, 1])
        with col1:
            chart_type = st.selectbox(
                "Chart Type",
                options=["Bar Chart", "Line Chart", "Pie Chart"],
                index=["Bar Chart", "Line Chart", "Pie Chart"].index(default_chart),
                help="Auto-selected based on dataset type - change if needed"
            )
        with col2:
            chart_title = st.text_input(
                "Chart Title",
                value=f"{selected_dataset['name']} - {chart_type}",
                help="Enter a title for your chart"
            )

        st.markdown("#### Select Columns")

        if chart_type == "Pie Chart":
            col1, col2 = st.columns(2)
            with col1:
                names_column = st.selectbox(
                    "Labels Column",
                    options=available_columns,
                    index=available_columns.index(default_x) if default_x in available_columns else 0,
                    help="Column containing category names"
                )
            with col2:
                val_opts = numeric_cols if numeric_cols else available_columns
                values_column = st.selectbox(
                    "Values Column",
                    options=val_opts,
                    help="Column containing numeric values"
                )
        else:
            col1, col2 = st.columns(2)
            with col1:
                x_column = st.selectbox(
                    "X-Axis Column",
                    options=available_columns,
                    index=available_columns.index(default_x) if default_x in available_columns else 0,
                    help="Column for x-axis"
                )
            with col2:
                y_opts = numeric_cols if numeric_cols else available_columns
                y_default = y_opts.index(default_y) if default_y in y_opts else 0
                y_column = st.selectbox(
                    "Y-Axis Column",
                    options=y_opts,
                    index=y_default,
                    help="Column for y-axis (numeric)"
                )
            with st.expander("Custom Axis Labels (Optional)", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    x_label = st.text_input("X-Axis Label", value="")
                with col2:
                    y_label = st.text_input("Y-Axis Label", value="")

        st.markdown("---")
        generate_button = st.button("Generate Chart", type="primary", use_container_width=True)

        if generate_button:
            with st.spinner("Generating chart..."):
                try:
                    if chart_type == "Pie Chart":
                        chart_data = preview_df[[names_column, values_column]].copy()
                        # If values column is not numeric, count occurrences
                        if not pd.api.types.is_numeric_dtype(chart_data[values_column]):
                            chart_data = chart_data.groupby(names_column).size().reset_index(name=values_column)
                        else:
                            chart_data = chart_data.groupby(names_column)[values_column].sum().reset_index()
                        fig = visualization.create_pie_chart(chart_data, values=values_column, names=names_column, title=chart_title)
                    else:
                        chart_data = preview_df[[x_column, y_column]].copy()
                        if chart_data[x_column].duplicated().any():
                            chart_data = chart_data.groupby(x_column)[y_column].sum().reset_index()
                        if chart_type == "Bar Chart":
                            fig = visualization.create_bar_chart(chart_data, x=x_column, y=y_column, title=chart_title,
                                x_label=x_label if x_label else None, y_label=y_label if y_label else None)
                        else:
                            fig = visualization.create_line_chart(chart_data, x=x_column, y=y_column, title=chart_title,
                                x_label=x_label if x_label else None, y_label=y_label if y_label else None)

                    st.session_state.current_chart = {
                        'figure': fig, 'title': chart_title, 'dataset_name': selected_dataset['name']
                    }
                    auth.log_access(st.session_state.username,
                        f"Generated {chart_type} for dataset: {selected_dataset['name']} (ID: {selected_dataset_id})")
                    st.success("Chart generated successfully!")

                except Exception as e:
                    st.error(f"Error generating chart: {str(e)}")

        if 'current_chart' in st.session_state:
            st.markdown("---")
            st.markdown("### Generated Chart")
            st.plotly_chart(st.session_state.current_chart['figure'], use_container_width=True)

            st.markdown("### Export Chart")
            col1, col2 = st.columns(2)
            with col1:
                try:
                    png_bytes = visualization.export_chart(st.session_state.current_chart['figure'],
                        st.session_state.current_chart['title'], format='png')
                    st.download_button("Download as PNG", data=png_bytes,
                        file_name=f"{st.session_state.current_chart['title']}.png",
                        mime="image/png", use_container_width=True)
                except Exception:
                    st.warning("PNG export not available. Use HTML instead.")
            with col2:
                html_bytes = visualization.export_chart(st.session_state.current_chart['figure'],
                    st.session_state.current_chart['title'], format='html')
                st.download_button("Download as HTML", data=html_bytes,
                    file_name=f"{st.session_state.current_chart['title']}.html",
                    mime="text/html", use_container_width=True)

    except Exception as e:
        st.error(f"Error loading dataset: {str(e)}")
        return
    
    # Help section
    st.markdown("---")
    with st.expander("How to use Visualizations", expanded=False):
        st.markdown("""
        ### Getting Started
        
        1. **Select Dataset**: Choose a dataset from the dropdown
        2. **Choose Chart Type**: Select bar chart, line chart, or pie chart
        3. **Configure Columns**: Select which columns to visualize
        4. **Generate**: Click "Generate Chart" to create the visualization
        5. **Export**: Download the chart as PNG or HTML
        
        ### Chart Types
        
        - **Bar Chart**: Best for comparing categorical data (e.g., usage by department)
        - **Line Chart**: Best for time series data (e.g., trends over time)
        - **Pie Chart**: Best for showing proportions (e.g., distribution of responses)
        
        ### Column Selection
        
        - **Bar/Line Charts**: Select X-axis (categories or time) and Y-axis (numeric values)
        - **Pie Charts**: Select Labels (category names) and Values (numeric values)
        - If your data has duplicate entries, they will be automatically aggregated
        
        ### Export Formats
        
        - **PNG**: Static image suitable for reports and presentations
        - **HTML**: Interactive chart that can be opened in a web browser
        
        ### Tips
        
        - Use descriptive chart titles to make your visualizations clear
        - For time series data, ensure your date column is properly formatted
        - Pie charts work best with 5-10 categories
        - Bar charts can handle more categories but may need rotation for readability
        """)
    
    st.markdown("---")
    st.caption("Tip: Use custom axis labels to make your charts more professional and easier to understand.")


def show_report_generation_page():
    """Display report generation page with report creation and export."""
    from modules import csv_handler, report_generator, auth
    import json

    st.title("Report Generation")
    st.markdown("Generate comprehensive reports with statistical summaries and narrative text.")

    datasets = csv_handler.get_datasets()
    if not datasets:
        st.info("No datasets available. Please upload data in the Data Upload section.")
        return

    # Smart dataset labels with capability hints
    def _report_label(d):
        caps = d.get('analysis_capabilities', {})
        analyses = caps.get('analyses', {}) if caps else {}
        badges = []
        if analyses.get('qualitative_sentiment', {}).get('available'): badges.append('qualitative')
        if analyses.get('correlation', {}).get('available'): badges.append('quantitative')
        if analyses.get('rag_query', {}).get('available'): badges.append('queryable')
        tag = ', '.join(badges) if badges else d['dataset_type']
        return f"{d['name']} ({d['dataset_type']}) - {tag}"

    dataset_options = {_report_label(d): d['id'] for d in datasets}

    # Auto-select all datasets by default
    all_labels = list(dataset_options.keys())

    st.markdown("### Report Configuration")
    selected_labels = st.multiselect(
        "Select Datasets to Include",
        options=all_labels,
        default=all_labels,
        help="All datasets are pre-selected. Remove any you don't need."
    )

    if not selected_labels:
        st.info("Please select at least one dataset to generate a report.")
        return

    selected_dataset_ids = [dataset_options[lbl] for lbl in selected_labels]
    selected_datasets = [d for d in datasets if d['id'] in selected_dataset_ids]

    # Auto-detect what options to enable
    has_qualitative = any(
        d.get('analysis_capabilities', {}) and
        d['analysis_capabilities'].get('analyses', {}).get('qualitative_sentiment', {}).get('available')
        for d in selected_datasets
    )
    has_quantitative = any(
        d.get('analysis_capabilities', {}) and
        d['analysis_capabilities'].get('analyses', {}).get('correlation', {}).get('available')
        for d in selected_datasets
    )
    has_viz_data = any(
        d.get('analysis_capabilities', {}) and
        (d['analysis_capabilities'].get('analyses', {}).get('trend', {}).get('available') or
         d['analysis_capabilities'].get('analyses', {}).get('distribution', {}).get('available'))
        for d in selected_datasets
    )

    # Show what was auto-detected
    if has_qualitative or has_quantitative or has_viz_data:
        detected = []
        if has_qualitative: detected.append("qualitative analysis")
        if has_quantitative: detected.append("quantitative analysis")
        if has_viz_data: detected.append("visualizations")
        st.success(f"Auto-detected: {', '.join(detected)} - options pre-checked below.")

    col1, col2, col3 = st.columns(3)
    with col1:
        include_visualizations = st.checkbox("Include Visualizations", value=has_viz_data,
            help="Auto-enabled when usage/circulation data is present")
    with col2:
        include_qualitative = st.checkbox("Include Qualitative Analysis", value=has_qualitative,
            help="Auto-enabled when survey data with text responses is present")
    with col3:
        include_quantitative = st.checkbox("Include Quantitative Analysis", value=has_quantitative,
            help="Auto-enabled when numeric usage/circulation data is present")

    custom_title = st.text_input("Custom Report Title (Optional)",
        placeholder="Leave blank for auto-generated title")

    # Show per-dataset capability summary
    with st.expander("Dataset Capability Summary", expanded=False):
        for d in selected_datasets:
            caps = d.get('analysis_capabilities', {})
            analyses = caps.get('analyses', {}) if caps else {}
            st.markdown(f"**{d['name']}** ({d['dataset_type']})")
            if analyses:
                available = [k for k, v in analyses.items() if v.get('available')]
                unavailable = [k for k, v in analyses.items() if not v.get('available')]
                if available:
                    st.markdown(f"  [OK] {', '.join(available)}")
                if unavailable:
                    st.markdown(f"  [N/A] {', '.join(unavailable)}")
            else:
                st.markdown("  _(capabilities not evaluated - re-upload to evaluate)_")

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        generate_button = st.button("Generate Report", type="primary", use_container_width=True)

    if generate_button:
        progress_bar = st.progress(0)
        status_text = st.empty()
        try:
            status_text.text("Creating report structure...")
            progress_bar.progress(20)

            report = report_generator.create_report(
                dataset_ids=selected_dataset_ids,
                include_viz=include_visualizations,
                include_qualitative=include_qualitative,
                include_quantitative=include_quantitative
            )

            if custom_title:
                report['title'] = custom_title

            progress_bar.progress(100)
            status_text.text("Report generated successfully!")
            st.session_state.current_report = report

            auth.log_access(st.session_state.username,
                f"Generated report for datasets: {', '.join([str(i) for i in selected_dataset_ids])}")
            st.success("Report generated successfully!")
            progress_bar.empty()
            status_text.empty()

        except ValueError as e:
            st.error(f"Error: {str(e)}")
            progress_bar.empty()
            status_text.empty()
            return
        except Exception as e:
            st.error(f"Error generating report: {str(e)}")
            progress_bar.empty()
            status_text.empty()
            return

    # Report preview
    if 'current_report' in st.session_state:
        report = st.session_state.current_report

        st.markdown("---")
        st.markdown("## Report Preview")
        st.markdown(f"# {report['title']}")
        st.markdown("---")

        with st.expander("Report Metadata", expanded=False):
            st.markdown(f"**Generated:** {report['metadata']['generated_at']}")
            st.markdown(f"**Author:** {report['metadata']['author']}")
            st.markdown(f"**Datasets:** {', '.join(report['metadata']['datasets'])}")

        st.markdown("## Executive Summary")
        st.markdown(report['executive_summary'])
        st.markdown("---")

        st.markdown("## Statistical Summaries")
        for summary in report['statistical_summaries']:
            st.markdown(f"### {summary['dataset_name']}")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Dataset Type", summary['dataset_type'].title())
            with col2:
                st.metric("Total Records", summary['row_count'])

            if summary.get('statistics'):
                st.markdown("#### Key Statistics")
                for metric_name, stats in summary['statistics'].items():
                    with st.expander(f"{metric_name}", expanded=False):
                        cols = st.columns(5)
                        if 'mean' in stats: cols[0].metric("Mean", f"{stats['mean']:.2f}")
                        if 'median' in stats: cols[1].metric("Median", f"{stats['median']:.2f}")
                        if 'std_dev' in stats: cols[2].metric("Std Dev", f"{stats['std_dev']:.2f}")
                        if 'count' in stats: cols[3].metric("Count", stats['count'])
                        if 'min' in stats and 'max' in stats:
                            cols[4].metric("Range", f"{stats['min']:.2f} - {stats['max']:.2f}")

            if summary.get('categorical_counts'):
                st.markdown("#### Categorical Distributions")
                for category_name, counts in summary['categorical_counts'].items():
                    with st.expander(f"{category_name}", expanded=False):
                        items = list(counts.items())
                        cols = st.columns(min(4, len(items)))
                        for i, (value, count) in enumerate(items):
                            cols[i % len(cols)].metric(str(value), count)
            st.markdown("---")

        if report.get('visualizations'):
            st.markdown("## Visualizations")
            for viz in report['visualizations']:
                st.markdown(f"### {viz['title']}")
                st.plotly_chart(viz['figure'], use_container_width=True)
            st.markdown("---")

        if report.get('qualitative_analysis'):
            st.markdown("## Qualitative Analysis")
            qual = report['qualitative_analysis']
            if qual.get('sentiment_distribution'):
                st.markdown("### Sentiment Distribution")
                sentiment_dist = qual['sentiment_distribution']
                total = sum(sentiment_dist.values())
                cols = st.columns(len(sentiment_dist))
                for i, (sentiment, count) in enumerate(sentiment_dist.items()):
                    pct = (count / total * 100) if total > 0 else 0
                    cols[i].metric(sentiment.title(), f"{count} ({pct:.1f}%)")
            st.markdown("---")

        if report.get('theme_summaries'):
            st.markdown("## Identified Themes")
            for theme in report['theme_summaries']:
                with st.expander(f"{theme['name']} ({theme['frequency']} occurrences)", expanded=False):
                    st.markdown(f"**Keywords:** {', '.join(theme['keywords'])}")
                    if theme.get('quotes'):
                        st.markdown("**Representative Quotes:**")
                        for quote in theme['quotes']:
                            st.markdown(f"> {quote}")
            st.markdown("---")

        if report.get('citations'):
            st.markdown("## Data Sources")
            for citation in report['citations']:
                st.markdown(f"- {citation}")
            st.markdown("---")

        st.markdown("## Export Report")
        col1, col2 = st.columns(2)
        with col1:
            try:
                md_bytes, _ = report_generator.export_report(report, format='markdown')
                st.download_button("Download as Markdown", data=md_bytes,
                    file_name=f"{report['title'].replace(' ', '_')}.md",
                    mime="text/markdown", use_container_width=True)
            except Exception as e:
                st.error(f"Error exporting Markdown: {str(e)}")
        
        with col2:
            # Export as PDF
            try:
                pdf_bytes, actual_format = report_generator.export_report(report, format='pdf')
                
                # Check if PDF export succeeded or fell back to Markdown
                if actual_format == 'markdown':
                    st.warning("PDF export failed. Downloading as Markdown instead.")
                    st.download_button(
                        "Download as Markdown (Fallback)",
                        data=pdf_bytes,
                        file_name=f"{report['title'].replace(' ', '_')}.md",
                        mime="text/markdown",
                        use_container_width=True,
                        help="PDF export failed, downloading as Markdown"
                    )
                else:
                    st.download_button(
                        "Download as PDF",
                        data=pdf_bytes,
                        file_name=f"{report['title'].replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        help="Download report as PDF file"
                    )
            except Exception as e:
                st.warning("PDF export not available. Please use Markdown export.")
                st.caption(f"Error: {str(e)}")
        
        # Display visualization warnings if any
        if report.get('metadata', {}).get('visualization_warnings'):
            st.markdown("---")
            st.warning("Visualization Warnings")
            st.caption("Some visualizations could not be generated due to insufficient data:")
            for warning in report['metadata']['visualization_warnings']:
                st.caption(f"- {warning}")
    
    # Help section
    st.markdown("---")
    with st.expander("How to use Report Generation", expanded=False):
        st.markdown("""
        ### Getting Started
        
        1. **Select Datasets**: Choose one or more datasets to include in the report
        2. **Configure Options**: 
           - Enable/disable visualizations
           - Enable/disable qualitative analysis (if available)
        3. **Custom Title**: Optionally provide a custom report title
        4. **Generate**: Click "Generate Report" to create the report
        5. **Preview**: Review the report preview on this page
        6. **Export**: Download the report as PDF or Markdown
        
        ### Report Components
        
        A complete report includes:
        - **Title and Metadata**: Report information and dataset details
        - **Executive Summary**: AI-generated narrative explaining key findings
        - **Statistical Summaries**: Descriptive statistics for each dataset
        - **Visualizations**: Charts and graphs (if enabled)
        - **Qualitative Analysis**: Sentiment and theme analysis (if enabled and available)
        - **Theme Summaries**: Identified themes with representative quotes
        - **Data Source Citations**: References to all datasets used
        
        ### Visualizations
        
        When enabled, the report automatically generates:
        - Sentiment distribution charts (for survey data)
        - Category distribution charts (for categorical data)
        - Other relevant visualizations based on data type
        
        ### Qualitative Analysis
        
        To include qualitative analysis:
        1. First run qualitative analysis on your survey datasets (Qualitative Analysis page)
        2. Enable "Include Qualitative Analysis" when generating the report
        3. The report will include sentiment distribution and identified themes
        
        ### Export Formats
        
        - **Markdown**: Text-based format, easy to edit and version control
        - **PDF**: Professional format suitable for sharing with stakeholders
        
        ### Performance
        
        Report generation typically completes within 2 minutes for datasets up to 1000 rows.
        Larger datasets may take longer, especially with visualizations enabled.
        
        ### Requirements
        
        - At least one dataset must be uploaded
        - For qualitative analysis, survey datasets with analysis results are required
        - PDF export requires reportlab library (falls back to Markdown if unavailable)
        """)
    
    st.markdown("---")
    st.caption("Tip: Generate multiple reports with different dataset combinations to compare findings across different data sources.")


def show_data_governance_page():
    """Display data governance documentation page with FAIR and CARE principles."""
    st.title("Data Governance")
    st.markdown("### Responsible Data Management for Library Assessment")
    
    st.markdown("""
    This system follows **FAIR** (Findable, Accessible, Interoperable, Reusable) and 
    **CARE** (Collective Benefit, Authority to Control, Responsibility, Ethics) principles 
    to ensure responsible and ethical management of library assessment data.
    """)
    
    # FAIR Principles Section
    st.markdown("---")
    st.markdown("## FAIR Principles")
    st.markdown("""
    FAIR principles ensure that research data is managed in ways that support discovery, 
    access, integration, and reuse by both humans and machines.
    """)
    
    with st.expander("**F - Findable**", expanded=False):
        st.markdown("""
        Data should be easy to find for both humans and computers.
        
        **How This System Implements Findability:**
        
        - **Rich Metadata**: Each dataset includes title, description, source, keywords, and upload date
        - **Unique Identifiers**: Every dataset has a unique ID for precise referencing
        - **Data Manifest**: Generate a comprehensive manifest listing all datasets with metadata
        - **Searchable Fields**: Metadata fields are stored in a searchable database
        - **Keywords**: Tag datasets with keywords to support discovery
        
        **Example:** When you upload a survey dataset, you can add keywords like "undergraduate", 
        "spring 2024", "user satisfaction" to make it easily discoverable later.
        """)
    
    with st.expander("**A - Accessible**", expanded=False):
        st.markdown("""
        Data should be accessible to authorized users through well-defined protocols.
        
        **How This System Implements Accessibility:**
        
        - **Authentication**: Password-protected access ensures only authorized users can view data
        - **Export Functionality**: Download datasets in standard formats (CSV, JSON)
        - **Clear Documentation**: User guides explain how to access and use the system
        - **Audit Logging**: All data access is logged with timestamps for transparency
        - **Local Access**: Data remains on your local machine, under your control
        
        **Example:** You can export any dataset as CSV or JSON to use in other analysis tools 
        like Excel, R, or Python.
        """)
    
    with st.expander("**I - Interoperable**", expanded=False):
        st.markdown("""
        Data should use standard formats and vocabularies to integrate with other systems.
        
        **How This System Implements Interoperability:**
        
        - **Standard Formats**: CSV and JSON export for compatibility with common tools
        - **SQLite Database**: Industry-standard database with documented schema
        - **JSON Metadata**: Machine-readable metadata format
        - **Pandas DataFrames**: Compatible with Python data science ecosystem
        - **Standard Visualizations**: Charts export as PNG and HTML for universal viewing
        
        **Example:** Export your analysis results as CSV to import into Tableau, Power BI, 
        or statistical software like SPSS or R.
        """)
    
    with st.expander("**R - Reusable**", expanded=False):
        st.markdown("""
        Data should be well-described and licensed so it can be reused in different contexts.
        
        **How This System Implements Reusability:**
        
        - **Data Provenance**: Track all transformations and analysis methods applied to data
        - **Usage Notes**: Document context and guidance for responsible reuse
        - **Source Information**: Record where data came from and how it was collected
        - **Ethical Considerations**: Document any restrictions or ethical guidelines
        - **Complete Metadata**: Comprehensive information supports informed reuse
        
        **Example:** The system tracks when you perform sentiment analysis, recording the method 
        (TextBlob), parameters, and timestamp so future users understand how results were generated.
        """)
    
    # CARE Principles Section
    st.markdown("---")
    st.markdown("## CARE Principles")
    st.markdown("""
    CARE principles complement FAIR by emphasizing people and purpose in data governance, 
    particularly for data about communities and individuals.
    """)
    
    with st.expander("**C - Collective Benefit**", expanded=False):
        st.markdown("""
        Data ecosystems should be designed to enable data to benefit the community it represents.
        
        **How This System Implements Collective Benefit:**
        
        - **Library Service Improvement**: Analysis results help improve library services for all users
        - **Usage Notes Field**: Document how data benefits the library community
        - **Report Generation**: Create reports that support institutional goals and decision-making
        - **Shared Insights**: Analysis results can be shared to benefit library assessment community
        - **Transparent Purpose**: Clear documentation of intended uses and benefits
        
        **Example:** Survey analysis revealing that students need more quiet study spaces can 
        lead to improvements that benefit the entire student community.
        """)
    
    with st.expander("**A - Authority to Control**", expanded=False):
        st.markdown("""
        People and communities should have authority over how their data is governed and used.
        
        **How This System Implements Authority to Control:**
        
        - **User Control**: You decide what data to upload, retain, or delete
        - **Metadata Editing**: Update context and usage restrictions at any time
        - **Dataset Deletion**: Remove datasets completely when no longer needed
        - **Local Processing**: Data never leaves your control - no external transmission
        - **Access Documentation**: Clear information about who can access data and what they can do
        - **Export Rights**: Download your data anytime in standard formats
        
        **Example:** You have complete control to delete any dataset, edit its metadata to add 
        usage restrictions, or export it for use elsewhere.
        """)
    
    with st.expander("**R - Responsibility**", expanded=False):
        st.markdown("""
        Those working with data have a responsibility to share how data is used and to nurture relationships.
        
        **How This System Implements Responsibility:**
        
        - **Ethical Considerations Field**: Document responsible use guidelines for each dataset
        - **Data Provenance Tracking**: Complete transparency about all transformations and analyses
        - **Audit Logging**: Every data access is logged for accountability
        - **PII Protection**: Automatic detection and redaction of personally identifiable information
        - **FERPA Compliance**: Student data protection built into system design
        - **Citation Requirements**: All reports include citations showing data sources used
        
        **Example:** When you run qualitative analysis, the system records exactly what method 
        was used, when, and by whom, creating a complete audit trail.
        """)
    
    with st.expander("**E - Ethics**", expanded=False):
        st.markdown("""
        Data practices should minimize harm and maximize benefit, respecting ethical norms and rights.
        
        **How This System Implements Ethics:**
        
        - **Privacy by Design**: Local-only processing ensures data never leaves your institution
        - **PII Redaction**: Automatic protection of personally identifiable information
        - **Ethical Use Documentation**: This page explains ethical principles and guidelines
        - **FERPA Compliance**: Full compliance with student data privacy regulations
        - **No External APIs**: No data sent to external services or AI providers
        - **Informed Use**: Clear documentation of data collection and use purposes
        
        **Example:** All AI processing happens locally via Ollama - student data never goes to 
        OpenAI, Google, or any external service.
        """)
    
    # Data Collection and Use Section
    st.markdown("---")
    st.markdown("## Data Collection and Use")
    
    with st.expander("**What Data Is Collected**", expanded=False):
        st.markdown("""
        This system collects and stores the following types of data:
        
        **Library Assessment Data:**
        - Survey responses (open-ended and structured feedback)
        - Usage statistics (circulation, database access, resource usage)
        - Circulation data (borrowing patterns, material types)
        
        **System Metadata:**
        - Dataset names, descriptions, and upload dates
        - User authentication information (usernames and hashed passwords)
        - Access logs (who accessed what data and when)
        - Analysis provenance (what analyses were performed and when)
        
        **Generated Data:**
        - Sentiment analysis results
        - Identified themes and keywords
        - Statistical summaries
        - Generated reports and visualizations
        
        **What Is NOT Collected:**
        - No telemetry or usage analytics sent to external services
        - No personally identifiable information beyond what you upload
        - No tracking of user behavior outside the system
        """)
    
    with st.expander("**How Data Is Used**", expanded=False):
        st.markdown("""
        Data in this system is used exclusively for library assessment purposes:
        
        **Primary Uses:**
        - **Question Answering**: RAG engine retrieves relevant data to answer your questions
        - **Qualitative Analysis**: Sentiment analysis and theme identification in survey responses
        - **Statistical Analysis**: Descriptive statistics and trend analysis
        - **Report Generation**: Creating comprehensive assessment reports for stakeholders
        - **Visualization**: Generating charts to communicate findings
        
        **Data Processing:**
        - All processing happens locally on your machine
        - AI/LLM processing uses locally-running Ollama (no external API calls)
        - Vector embeddings stored locally in ChromaDB
        - No data transmitted to external services
        
        **Data Retention:**
        - Data persists until you explicitly delete it
        - You control the lifecycle of all datasets
        - No automatic deletion or archiving
        
        **Data Sharing:**
        - Data is not shared with any external parties
        - You control all exports and report generation
        - Reports you generate can be shared at your discretion
        """)
    
    with st.expander("**Who Has Access**", expanded=False):
        st.markdown("""
        Access to data in this system is controlled and logged:
        
        **Access Control:**
        - **Authentication Required**: All users must log in with username and password
        - **Single-User System**: Designed for individual use on a local machine
        - **No Remote Access**: System runs locally, not accessible over network
        - **Password Protection**: Passwords hashed with bcrypt for security
        
        **Access Logging:**
        - Every data access operation is logged with timestamp
        - Logs include: username, action performed, and dataset accessed
        - Audit trail supports accountability and compliance
        - Logs stored in local SQLite database
        
        **User Permissions:**
        - All authenticated users have full access to all features
        - No role-based access control in MVP version
        - Users can view, analyze, export, and delete any dataset
        
        **Physical Access:**
        - Data stored on your local machine only
        - Physical security of the machine is your responsibility
        - Consider encrypting your hard drive for additional protection
        """)
    
    # Privacy Protections Section
    st.markdown("---")
    st.markdown("## Privacy Protections")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Local Processing
        
        **All data processing happens on your local machine:**
        
        - No external API calls
        - No cloud services
        - No data transmission
        - Complete data sovereignty
        
        **AI Processing:**
        - Ollama runs locally (Llama 3.2 3B)
        - ChromaDB in embedded mode
        - No OpenAI, Google, or other external AI services
        
        **Benefits:**
        - FERPA compliant by design
        - No internet required for processing
        - No subscription fees or API costs
        - Complete control over your data
        """)
    
    with col2:
        st.markdown("""
        ### PII Protection
        
        **Automatic protection of personal information:**
        
        - PII detection in outputs
        - Redaction of sensitive data
        - Flagging of potential privacy issues
        - FERPA compliance measures
        
        **Protected Information:**
        - Email addresses
        - Phone numbers
        - Social Security Numbers
        - Student IDs (when detected)
        
        **Best Practices:**
        - Remove PII before uploading data
        - Review outputs before sharing
        - Use aggregate data when possible
        - Follow institutional IRB guidelines
        """)
    
    st.markdown("""
    ### Access Logging and Audit Trail
    
    **Complete transparency and accountability:**
    
    - Every data access is logged with timestamp
    - User actions tracked (upload, query, analysis, export, delete)
    - Audit logs support compliance requirements
    - Logs stored securely in local database
    
    **Audit Log Information:**
    - Username of person performing action
    - Type of action (e.g., "Uploaded dataset", "Generated report")
    - Timestamp of action
    - Details about what data was accessed
    
    **Use Cases:**
    - Demonstrate FERPA compliance
    - Investigate data access questions
    - Support institutional audits
    - Track data usage patterns
    """)
    
    # Ethical Use Guidelines Section
    st.markdown("---")
    st.markdown("## Ethical Use Guidelines")
    
    st.markdown("""
    ### Principles for Responsible Library Assessment Data Use
    
    When using this system for library assessment, please follow these ethical guidelines:
    """)
    
    with st.expander("**1. Respect Privacy and Confidentiality**", expanded=False):
        st.markdown("""
        - Remove personally identifiable information before uploading data
        - Aggregate data when possible to protect individual privacy
        - Be cautious when sharing reports that might identify individuals
        - Follow your institution's IRB requirements for human subjects research
        - Consider whether consent was obtained for the intended use
        """)
    
    with st.expander("**2. Use Data for Intended Purposes Only**", expanded=False):
        st.markdown("""
        - Use data only for library assessment and service improvement
        - Do not repurpose data for unrelated uses without proper authorization
        - Respect any usage restrictions documented in dataset metadata
        - Consider the original context in which data was collected
        - Document intended purposes in the "Usage Notes" field
        """)
    
    with st.expander("**3. Maintain Data Quality and Integrity**", expanded=False):
        st.markdown("""
        - Ensure uploaded data is accurate and complete
        - Document any data cleaning or transformation steps
        - Preserve original data alongside processed versions
        - Be transparent about data limitations and biases
        - Use appropriate statistical methods for your data type
        """)
    
    with st.expander("**4. Provide Context and Avoid Misinterpretation**", expanded=False):
        st.markdown("""
        - Include sufficient context when sharing findings
        - Acknowledge limitations of AI-generated analysis
        - Verify important findings before making decisions
        - Consider multiple interpretations of qualitative data
        - Be cautious about causal claims from correlational data
        """)
    
    with st.expander("**5. Promote Equity and Avoid Harm**", expanded=False):
        st.markdown("""
        - Consider how findings might affect different user groups
        - Avoid reinforcing stereotypes or biases in interpretation
        - Use inclusive language in reports and documentation
        - Consider accessibility in visualizations and reports
        - Be mindful of power dynamics in data collection and use
        """)
    
    with st.expander("**6. Ensure Transparency and Accountability**", expanded=False):
        st.markdown("""
        - Document data sources and analysis methods
        - Maintain audit logs of data access and use
        - Be prepared to explain how findings were generated
        - Cite data sources appropriately in reports
        - Share methodological details with stakeholders
        """)
    
    # User Control Mechanisms Section
    st.markdown("---")
    st.markdown("## User Access and Control Mechanisms")
    
    st.markdown("""
    You have complete control over your data in this system. Here's what you can do:
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Data Management
        
        **Upload Control:**
        - Choose what data to upload
        - Add rich metadata (title, description, keywords)
        - Document usage notes and ethical considerations
        - Validate data before storing
        
        **Metadata Management:**
        - Edit metadata at any time
        - Update usage notes and restrictions
        - Add or modify keywords for findability
        - Document data provenance
        
        **Data Deletion:**
        - Delete any dataset completely
        - Cascade deletion removes all associated data
        - No recovery after deletion (permanent)
        - Deletion is logged in audit trail
        """)
    
    with col2:
        st.markdown("""
        ### Export and Portability
        
        **Dataset Export:**
        - Export any dataset as CSV or JSON
        - Download data manifest with all metadata
        - Take your data to other tools
        - No vendor lock-in
        
        **Analysis Export:**
        - Export analysis results as CSV
        - Download charts as PNG or HTML
        - Export reports as PDF or Markdown
        - Share findings on your terms
        
        **Complete Portability:**
        - All data in standard formats
        - SQLite database is portable
        - No proprietary formats
        - Easy migration to other systems
        """)
    
    st.markdown("""
    ### Access Control
    
    **Authentication:**
    - Password-protected access to all features
    - Secure password hashing (bcrypt)
    - Session management for security
    - Logout functionality
    
    **Audit and Monitoring:**
    - View access logs (feature can be added)
    - Track who accessed what data
    - Monitor system usage
    - Support compliance requirements
    
    **Data Sovereignty:**
    - All data stays on your machine
    - No external transmission
    - You control physical access
    - No cloud dependencies
    """)
    
    # Additional Resources Section
    st.markdown("---")
    st.markdown("## Additional Resources")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Learn More About FAIR
        
        - [GO FAIR Initiative](https://www.go-fair.org/)
        - [FAIR Principles](https://www.go-fair.org/fair-principles/)
        - [FAIR Data Maturity Model](https://www.go-fair.org/fair-principles/fairification-process/)
        
        ### Learn More About CARE
        
        - [CARE Principles for Indigenous Data Governance](https://www.gida-global.org/care)
        - [Global Indigenous Data Alliance](https://www.gida-global.org/)
        """)
    
    with col2:
        st.markdown("""
        ### Privacy and Compliance
        
        - [FERPA Overview (US Dept of Education)](https://www2.ed.gov/policy/gen/guid/fpco/ferpa/index.html)
        - [Library Privacy Guidelines (ALA)](https://www.ala.org/advocacy/privacy)
        - [Research Data Management](https://www.icpsr.umich.edu/web/pages/datamanagement/)
        
        ### Ethical Data Use
        
        - [Data Ethics Framework](https://www.gov.uk/government/publications/data-ethics-framework)
        - [Responsible Data Science](https://dataresponsibly.github.io/)
        """)
    
    st.markdown("---")
    st.markdown("""
    ### Questions or Concerns?
    
    If you have questions about data governance, privacy, or ethical use of this system, 
    please consult with your institution's:
    
    - Institutional Review Board (IRB)
    - Data Protection Officer
    - Library Administration
    - IT Security Team
    
    This system is designed to support responsible data practices, but institutional policies 
    and guidelines should always be followed.
    """)


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


def show_quantitative_analysis_page():
    """Display quantitative analysis page with statistical analysis and LLM interpretations."""
    from modules import csv_handler, quantitative_analysis, auth
    import pandas as pd
    import time
    
    st.title("Quantitative Analysis")
    st.markdown("Perform advanced statistical analysis with AI-powered interpretations.")
    
    # Get available datasets
    datasets = csv_handler.get_datasets()
    
    if not datasets:
        st.info("No datasets available. Please upload data in the Data Upload section.")
        return

    # Classify and label datasets
    def _label(d):
        info = csv_handler.classify_dataset_for_analysis(d)
        tag = "Recommended" if info['recommended'] == 'quantitative' else "Not ideal"
        return f"{d['name']} (ID: {d['id']}, {d['dataset_type']}) - {tag}"

    dataset_options = {_label(d): d['id'] for d in datasets}
    quant_datasets = [d for d in datasets if d['dataset_type'] in ('usage', 'circulation')]
    default_label = next((_label(d) for d in quant_datasets), list(dataset_options.keys())[0])

    # Dataset selector
    st.markdown("### Select Dataset")
    selected_label = st.selectbox(
        "Choose a dataset to analyze",
        options=list(dataset_options.keys()),
        index=list(dataset_options.keys()).index(default_label),
        key="quant_dataset_selector"
    )
    
    selected_dataset_id = dataset_options[selected_label]
    selected_dataset = next(d for d in datasets if d['id'] == selected_dataset_id)
    analysis_info = csv_handler.classify_dataset_for_analysis(selected_dataset)

    # Show suitability banner
    if analysis_info['recommended'] == 'quantitative':
        st.success(analysis_info['reason'])
    else:
        st.warning(f"{analysis_info['reason']} Consider using a usage or circulation dataset instead.")
    
    # Display dataset info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Dataset", selected_dataset['name'])
    with col2:
        st.metric("Total Rows", selected_dataset['row_count'])
    with col3:
        st.metric("Type", selected_dataset['dataset_type'])
    
    st.markdown("---")
    
    # Analysis type selector
    st.markdown("### Select Analysis Type")
    analysis_type = st.selectbox(
        "Choose the type of analysis to perform",
        options=[
            "Correlation Analysis",
            "Trend Analysis",
            "Comparative Analysis",
            "Distribution Analysis"
        ],
        key="analysis_type_selector"
    )
    
    # Analysis-specific parameters
    st.markdown("### Configure Parameters")
    
    if analysis_type == "Correlation Analysis":
        st.markdown("**Correlation Analysis** identifies relationships between numeric variables.")
        
        method = st.selectbox(
            "Correlation Method",
            options=["pearson", "spearman", "kendall"],
            help="Pearson: linear relationships (normal data), Spearman: monotonic relationships (non-normal data), Kendall: ordinal data"
        )
        
        analyze_button = st.button("Run Correlation Analysis", type="primary", use_container_width=True)
        
        if analyze_button:
            with st.spinner("Analyzing correlations... This may take a moment."):
                start_time = time.time()
                try:
                    # Run correlation analysis
                    results = quantitative_analysis.calculate_correlation(
                        dataset_id=selected_dataset_id,
                        method=method
                    )
                    
                    # Generate interpretation
                    interpretation_results = quantitative_analysis.generate_interpretation(
                        analysis_type='correlation',
                        results=results,
                        context={'dataset_name': selected_dataset['name']}
                    )
                    
                    # Generate insights
                    insights_results = quantitative_analysis.generate_insights(
                        dataset_id=selected_dataset_id,
                        analysis_results=results,
                        context={'dataset_name': selected_dataset['name'], 'dataset_type': selected_dataset['dataset_type']}
                    )
                    
                    # Generate recommendations
                    recommendations_results = quantitative_analysis.generate_recommendations(
                        analysis_type='correlation',
                        analysis_results=results,
                        context={'dataset_name': selected_dataset['name'], 'dataset_type': selected_dataset['dataset_type']}
                    )
                    
                    # Combine results
                    results['interpretation'] = interpretation_results.get('interpretation')
                    results['insights'] = insights_results.get('insights')
                    results['recommendations'] = recommendations_results.get('recommendations')
                    
                    # Store analysis in database
                    analysis_id = quantitative_analysis.store_analysis_results(
                        dataset_id=selected_dataset_id,
                        analysis_type='correlation',
                        parameters={'method': method},
                        results=results
                    )
                    
                    execution_time = time.time() - start_time
                    
                    # Store in session state
                    st.session_state.quant_results = {
                        'analysis_id': analysis_id,
                        'analysis_type': 'correlation',
                        'results': results,
                        'execution_time': execution_time
                    }
                    
                    # Log access
                    auth.log_access(
                        st.session_state.username,
                        f"Performed correlation analysis on dataset: {selected_dataset['name']} (ID: {selected_dataset_id})"
                    )
                    
                    st.success(f"Analysis completed in {execution_time:.2f} seconds! (Analysis ID: {analysis_id})")
                    
                except ValueError as e:
                    st.error(f"{str(e)}")
                    return
                except Exception as e:
                    st.error(f"Error during analysis: {str(e)}")
                    return
    
    elif analysis_type == "Trend Analysis":
        st.markdown("**Trend Analysis** identifies patterns and forecasts future values in time series data.")
        
        # Get column names from dataset
        try:
            df = quantitative_analysis._load_dataset_data(selected_dataset_id)
            columns = df.columns.tolist()
            
            date_column = st.selectbox(
                "Date Column",
                options=columns,
                help="Select the column containing dates or time periods"
            )
            
            numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
            value_column = st.selectbox(
                "Value Column",
                options=numeric_columns,
                help="Select the numeric column to analyze for trends"
            )
            
            analyze_button = st.button("Run Trend Analysis", type="primary", use_container_width=True)
            
            if analyze_button:
                with st.spinner("Analyzing trends... This may take a moment."):
                    start_time = time.time()
                    try:
                        # Run trend analysis
                        results = quantitative_analysis.calculate_trend(
                            dataset_id=selected_dataset_id,
                            date_column=date_column,
                            value_column=value_column
                        )
                        
                        # Generate interpretation
                        interpretation_results = quantitative_analysis.generate_interpretation(
                            analysis_type='trend',
                            results=results,
                            context={'dataset_name': selected_dataset['name']}
                        )
                        
                        # Generate insights
                        insights_results = quantitative_analysis.generate_insights(
                            dataset_id=selected_dataset_id,
                            analysis_results=results,
                            context={'dataset_name': selected_dataset['name'], 'dataset_type': selected_dataset['dataset_type']}
                        )
                        
                        # Generate recommendations
                        recommendations_results = quantitative_analysis.generate_recommendations(
                            analysis_type='trend',
                            analysis_results=results,
                            context={'dataset_name': selected_dataset['name'], 'dataset_type': selected_dataset['dataset_type']}
                        )
                        
                        # Combine results
                        results['interpretation'] = interpretation_results.get('interpretation')
                        results['insights'] = insights_results.get('insights')
                        results['recommendations'] = recommendations_results.get('recommendations')
                        
                        # Store analysis in database
                        analysis_id = quantitative_analysis.store_analysis_results(
                            dataset_id=selected_dataset_id,
                            analysis_type='trend',
                            parameters={'date_column': date_column, 'value_column': value_column},
                            results=results
                        )
                        
                        execution_time = time.time() - start_time
                        
                        # Store in session state
                        st.session_state.quant_results = {
                            'analysis_id': analysis_id,
                            'analysis_type': 'trend',
                            'results': results,
                            'execution_time': execution_time
                        }
                        
                        # Log access
                        auth.log_access(
                            st.session_state.username,
                            f"Performed trend analysis on dataset: {selected_dataset['name']} (ID: {selected_dataset_id})"
                        )
                        
                        st.success(f"Analysis completed in {execution_time:.2f} seconds! (Analysis ID: {analysis_id})")
                        
                    except ValueError as e:
                        st.error(f"{str(e)}")
                        return
                    except Exception as e:
                        st.error(f"Error during analysis: {str(e)}")
                        return
                        
        except Exception as e:
            st.error(f"Could not load dataset columns: {str(e)}")
            return
    
    elif analysis_type == "Comparative Analysis":
        st.markdown("**Comparative Analysis** compares metrics across different groups or categories.")
        
        # Get column names from dataset
        try:
            df = quantitative_analysis._load_dataset_data(selected_dataset_id)
            columns = df.columns.tolist()
            
            numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
            value_column = st.selectbox(
                "Value Column",
                options=numeric_columns,
                help="Select the numeric column to compare across groups"
            )
            
            group_column = st.selectbox(
                "Group Column",
                options=columns,
                help="Select the column containing group labels"
            )
            
            test_type = st.selectbox(
                "Statistical Test",
                options=["auto", "t-test", "mann-whitney", "anova", "kruskal-wallis"],
                help="Auto: automatically selects based on number of groups and normality"
            )
            
            analyze_button = st.button("Run Comparative Analysis", type="primary", use_container_width=True)
            
            if analyze_button:
                with st.spinner("Comparing groups... This may take a moment."):
                    start_time = time.time()
                    try:
                        # Run comparative analysis
                        results = quantitative_analysis.perform_comparative_analysis(
                            dataset_id=selected_dataset_id,
                            value_column=value_column,
                            group_column=group_column,
                            test_type=None if test_type == "auto" else test_type
                        )
                        
                        # Generate interpretation
                        interpretation_results = quantitative_analysis.generate_interpretation(
                            analysis_type='comparative',
                            results=results,
                            context={'dataset_name': selected_dataset['name']}
                        )
                        
                        # Generate insights
                        insights_results = quantitative_analysis.generate_insights(
                            dataset_id=selected_dataset_id,
                            analysis_results=results,
                            context={'dataset_name': selected_dataset['name'], 'dataset_type': selected_dataset['dataset_type']}
                        )
                        
                        # Generate recommendations
                        recommendations_results = quantitative_analysis.generate_recommendations(
                            analysis_type='comparative',
                            analysis_results=results,
                            context={'dataset_name': selected_dataset['name'], 'dataset_type': selected_dataset['dataset_type']}
                        )
                        
                        # Combine results
                        results['interpretation'] = interpretation_results.get('interpretation')
                        results['insights'] = insights_results.get('insights')
                        results['recommendations'] = recommendations_results.get('recommendations')
                        
                        # Store analysis in database
                        analysis_id = quantitative_analysis.store_analysis_results(
                            dataset_id=selected_dataset_id,
                            analysis_type='comparative',
                            parameters={'value_column': value_column, 'group_column': group_column, 'test_type': test_type},
                            results=results
                        )
                        
                        execution_time = time.time() - start_time
                        
                        # Store in session state
                        st.session_state.quant_results = {
                            'analysis_id': analysis_id,
                            'analysis_type': 'comparative',
                            'results': results,
                            'execution_time': execution_time
                        }
                        
                        # Log access
                        auth.log_access(
                            st.session_state.username,
                            f"Performed comparative analysis on dataset: {selected_dataset['name']} (ID: {selected_dataset_id})"
                        )
                        
                        st.success(f"Analysis completed in {execution_time:.2f} seconds! (Analysis ID: {analysis_id})")
                        
                    except ValueError as e:
                        st.error(f"{str(e)}")
                        return
                    except Exception as e:
                        st.error(f"Error during analysis: {str(e)}")
                        return
                        
        except Exception as e:
            st.error(f"Could not load dataset columns: {str(e)}")
            return
    
    elif analysis_type == "Distribution Analysis":
        st.markdown("**Distribution Analysis** examines data distributions and detects outliers.")
        
        # Get column names from dataset
        try:
            df = quantitative_analysis._load_dataset_data(selected_dataset_id)
            numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
            
            column = st.selectbox(
                "Column to Analyze",
                options=numeric_columns,
                help="Select the numeric column to analyze"
            )
            
            outlier_method = st.selectbox(
                "Outlier Detection Method",
                options=["iqr", "zscore"],
                help="IQR: Interquartile range method (robust to skewed data), Z-score: Standard deviation method (assumes normal distribution)"
            )
            
            analyze_button = st.button("Run Distribution Analysis", type="primary", use_container_width=True)
            
            if analyze_button:
                with st.spinner("Analyzing distribution... This may take a moment."):
                    start_time = time.time()
                    try:
                        # Run distribution analysis
                        results = quantitative_analysis.analyze_distribution(
                            dataset_id=selected_dataset_id,
                            column=column,
                            outlier_method=outlier_method
                        )
                        
                        # Generate interpretation
                        interpretation_results = quantitative_analysis.generate_interpretation(
                            analysis_type='distribution',
                            results=results,
                            context={'dataset_name': selected_dataset['name']}
                        )
                        
                        # Generate insights
                        insights_results = quantitative_analysis.generate_insights(
                            dataset_id=selected_dataset_id,
                            analysis_results=results,
                            context={'dataset_name': selected_dataset['name'], 'dataset_type': selected_dataset['dataset_type']}
                        )
                        
                        # Generate recommendations
                        recommendations_results = quantitative_analysis.generate_recommendations(
                            analysis_type='distribution',
                            analysis_results=results,
                            context={'dataset_name': selected_dataset['name'], 'dataset_type': selected_dataset['dataset_type']}
                        )
                        
                        # Combine results
                        results['interpretation'] = interpretation_results.get('interpretation')
                        results['insights'] = insights_results.get('insights')
                        results['recommendations'] = recommendations_results.get('recommendations')
                        
                        # Store analysis in database
                        analysis_id = quantitative_analysis.store_analysis_results(
                            dataset_id=selected_dataset_id,
                            analysis_type='distribution',
                            parameters={'column': column, 'outlier_method': outlier_method},
                            results=results
                        )
                        
                        execution_time = time.time() - start_time
                        
                        # Store in session state
                        st.session_state.quant_results = {
                            'analysis_id': analysis_id,
                            'analysis_type': 'distribution',
                            'results': results,
                            'execution_time': execution_time
                        }
                        
                        # Log access
                        auth.log_access(
                            st.session_state.username,
                            f"Performed distribution analysis on dataset: {selected_dataset['name']} (ID: {selected_dataset_id})"
                        )
                        
                        st.success(f"Analysis completed in {execution_time:.2f} seconds! (Analysis ID: {analysis_id})")
                        
                    except ValueError as e:
                        st.error(f"{str(e)}")
                        return
                    except Exception as e:
                        st.error(f"Error during analysis: {str(e)}")
                        return
                        
        except Exception as e:
            st.error(f"Could not load dataset columns: {str(e)}")
            return
    
    # Display results if available
    if 'quant_results' in st.session_state:
        results_data = st.session_state.quant_results
        results = results_data['results']
        analysis_type_key = results_data['analysis_type']
        
        st.markdown("---")
        st.markdown("## Analysis Results")
        
        # Performance metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Analysis ID", results_data['analysis_id'])
        with col2:
            st.metric("Execution Time", f"{results_data['execution_time']:.2f}s")
        
        # Statistical Results
        st.markdown("### Statistical Results")
        
        if analysis_type_key == 'correlation':
            st.markdown(f"**Method:** {results['method'].capitalize()}")
            st.markdown(f"**Observations:** {results['n_observations']}")
            st.markdown(f"**Variables:** {results['n_variables']}")
            
            if results.get('top_correlations'):
                st.markdown("**Top Correlations:**")
                corr_df = pd.DataFrame(results['top_correlations'][:10])
                corr_df['significant'] = corr_df['significant'].map({True: 'Yes', False: 'No'})
                st.dataframe(corr_df[['variable1', 'variable2', 'correlation', 'p_value', 'significant']], use_container_width=True)
                
                # Visualization
                try:
                    fig = quantitative_analysis.create_correlation_heatmap(results)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"Could not generate visualization: {str(e)}")
        
        elif analysis_type_key == 'trend':
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Trend Direction", results['trend_direction'].capitalize())
            with col2:
                st.metric("R-squared", f"{results['r_squared']:.3f}")
            with col3:
                st.metric("Seasonal Pattern", "Yes" if results.get('seasonal_pattern') else "No")
            
            # Visualization
            try:
                fig = quantitative_analysis.create_trend_chart(results)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not generate visualization: {str(e)}")
        
        elif analysis_type_key == 'comparative':
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Test Type", results['test_type'])
            with col2:
                st.metric("P-value", f"{results['p_value']:.4f}")
            with col3:
                st.metric("Significant", "Yes" if results.get('significant') else "No")
            
            if results.get('group_statistics'):
                st.markdown("**Group Statistics:**")
                group_df = pd.DataFrame(results['group_statistics']).T
                st.dataframe(group_df, use_container_width=True)
                
                # Visualization
                try:
                    fig = quantitative_analysis.create_comparison_boxplot(results)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"Could not generate visualization: {str(e)}")
        
        elif analysis_type_key == 'distribution':
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Skewness", f"{results['skewness']:.3f}")
            with col2:
                st.metric("Kurtosis", f"{results['kurtosis']:.3f}")
            with col3:
                st.metric("Normal", "Yes" if results.get('is_normal') else "No")
            with col4:
                st.metric("Outliers", results['n_outliers'])
            
            # Visualization
            try:
                fig = quantitative_analysis.create_distribution_histogram(results)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not generate visualization: {str(e)}")
        
        # LLM-Generated Content
        if results.get('interpretation'):
            st.markdown("### Interpretation")
            st.markdown(results['interpretation'])
        
        if results.get('insights'):
            st.markdown("### Insights")
            st.markdown(results['insights'])
        
        if results.get('recommendations'):
            st.markdown("### Recommendations")
            st.markdown(results['recommendations'])
        
        # Export section
        st.markdown("---")
        st.markdown("### Export Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Export to CSV
            if st.button("Export Statistical Results (CSV)", use_container_width=True):
                # Create export dataframe based on analysis type
                if analysis_type_key == 'correlation' and results.get('top_correlations'):
                    export_df = pd.DataFrame(results['top_correlations'])
                elif analysis_type_key == 'comparative' and results.get('group_statistics'):
                    export_df = pd.DataFrame(results['group_statistics']).T
                else:
                    export_df = pd.DataFrame([results])
                
                csv = export_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"quantitative_analysis_{results_data['analysis_id']}.csv",
                    mime="text/csv"
                )
        
        with col2:
            # Export full report
            if st.button("Export Full Report (JSON)", use_container_width=True):
                import json
                json_str = json.dumps(results, indent=2, default=str)
                st.download_button(
                    label="Download JSON",
                    data=json_str,
                    file_name=f"quantitative_analysis_{results_data['analysis_id']}.json",
                    mime="application/json"
                )


def show_logs_page():
    """Logs & Monitoring dashboard - application logs, errors, performance, and audit trail."""
    import pandas as pd
    from modules.logging_service import get_recent_logs, get_error_summary, get_operation_stats, get_access_log_summary

    st.title("Logs & Monitoring")
    st.markdown("Real-time visibility into application activity, errors, and performance.")

    # Controls
    col_h, col_r = st.columns([4, 1])
    with col_r:
        if st.button("Refresh", use_container_width=True):
            st.rerun()

    hours = st.select_slider(
        "Time window",
        options=[1, 6, 12, 24, 48, 168],
        value=24,
        format_func=lambda h: f"Last {h}h" if h < 168 else "Last 7 days",
    )

    tab_overview, tab_logs, tab_errors, tab_perf, tab_audit = st.tabs(
        ["Overview", "Application Logs", "Errors", "Performance", "Audit Trail"]
    )

    # Overview
    with tab_overview:
        logs = get_recent_logs(limit=500)
        errors = get_error_summary(hours=hours)
        ops = get_operation_stats(hours=hours)

        total = len(logs)
        err_count = sum(r["count"] for r in errors)
        warn_count = sum(1 for l in logs if l.get("level") == "WARNING")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Log Entries", total)
        c2.metric("Errors (window)", err_count, delta=None)
        c3.metric("Warnings (all)", warn_count)
        c4.metric("Operations Tracked", len(ops))

        if ops:
            st.markdown("#### Operation Summary")
            ops_df = pd.DataFrame(ops)
            st.dataframe(ops_df, use_container_width=True, hide_index=True)

        if errors:
            st.markdown("#### Error Breakdown by Module")
            err_df = pd.DataFrame(errors)
            st.dataframe(err_df, use_container_width=True, hide_index=True)
        else:
            st.success(f"No errors in the last {hours}h.")

    # Application Logs
    with tab_logs:
        col_lv, col_mod = st.columns(2)
        with col_lv:
            level_filter = st.selectbox(
                "Level", ["All", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            )
        with col_mod:
            module_filter = st.text_input("Module contains", placeholder="e.g. csv_handler")

        logs = get_recent_logs(
            limit=300,
            level=None if level_filter == "All" else level_filter,
            module=module_filter or None,
        )

        if not logs:
            st.info("No log entries match the current filters.")
        else:
            df = pd.DataFrame(logs)[["timestamp", "level", "module", "function", "message"]]
            # Colour-code level column
            def _colour(val):
                colours = {"ERROR": "background-color:#ffd6d6", "CRITICAL": "background-color:#ff9999",
                           "WARNING": "background-color:#fff3cd", "INFO": "", "DEBUG": "color:#888"}
                return colours.get(val, "")
            st.dataframe(
                df.style.map(_colour, subset=["level"]),
                use_container_width=True,
                hide_index=True,
            )

            # Download
            st.download_button(
                "Download as CSV",
                data=df.to_csv(index=False),
                file_name="app_logs.csv",
                mime="text/csv",
            )

    # Errors
    with tab_errors:
        error_logs = get_recent_logs(limit=200, level="ERROR")
        critical_logs = get_recent_logs(limit=50, level="CRITICAL")
        all_errors = critical_logs + error_logs

        if not all_errors:
            st.success("No errors recorded.")
        else:
            for entry in all_errors[:50]:
                with st.expander(
                    f"[{entry['level']}] {entry['timestamp'][:19]}  -  {entry['module']}.{entry['function']}",
                    expanded=False,
                ):
                    st.markdown(f"**Message:** {entry['message']}")
                    if entry.get("exception"):
                        st.code(entry["exception"], language="python")
                    if entry.get("context"):
                        st.json(entry["context"])

    # Performance
    with tab_perf:
        ops = get_operation_stats(hours=hours)
        if not ops:
            st.info("No performance data yet. Operations are tracked automatically once you use the app.")
        else:
            df = pd.DataFrame(ops)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Bar chart of avg duration
            try:
                import plotly.express as px
                fig = px.bar(
                    df,
                    x="operation",
                    y="avg_ms",
                    error_y=None,
                    labels={"avg_ms": "Avg duration (ms)", "operation": "Operation"},
                    title=f"Average Operation Duration (last {hours}h)",
                    color="avg_ms",
                    color_continuous_scale="Blues",
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception:
                pass

    # Audit Trail
    with tab_audit:
        audit = get_access_log_summary(hours=hours)
        if not audit:
            st.info("No audit events in the selected window.")
        else:
            df = pd.DataFrame(audit)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button(
                "Download Audit Log",
                data=df.to_csv(index=False),
                file_name="audit_log.csv",
                mime="text/csv",
            )

    # Log file links
    st.markdown("---")
    st.markdown("#### Log Files on Disk")
    from modules.logging_service import APP_LOG_FILE, ERROR_LOG_FILE
    st.code(f"Application log : {APP_LOG_FILE}\nErrors only     : {ERROR_LOG_FILE}")


if __name__ == "__main__":
    main()
