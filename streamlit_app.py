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
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)


def show_login_page():
    """Display login page with authentication form."""
    st.title("📚 Library Assessment Assistant")
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
                # Attempt authentication
                if auth.authenticate(username, password):
                    auth.login_user(st.session_state, username)
                    st.success(f"Welcome, {username}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
                    st.session_state.login_attempts += 1
                    
                    # Rate limiting after 5 failed attempts
                    if st.session_state.login_attempts >= 5:
                        st.warning("Too many failed login attempts. Please try again later.")
    
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
    # Sidebar with navigation and logout
    with st.sidebar:
        st.title("📚 Library Assessment")
        st.markdown(f"**User:** {st.session_state.username}")
        st.markdown("---")
        
        # Navigation menu
        page = st.radio(
            "Navigation",
            [
                "🏠 Home",
                "📤 Data Upload",
                "💬 Query Interface",
                "📊 Qualitative Analysis",
                "📈 Visualizations",
                "📄 Report Generation",
                "📋 Data Governance"
            ],
            key="navigation"
        )
        
        st.markdown("---")
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            auth.logout_user(st.session_state)
            st.rerun()
    
    # Main content area based on selected page
    if page == "🏠 Home":
        show_home_page()
    elif page == "📤 Data Upload":
        show_data_upload_page()
    elif page == "💬 Query Interface":
        show_query_interface_page()
    elif page == "📊 Qualitative Analysis":
        show_qualitative_analysis_page()
    elif page == "📈 Visualizations":
        show_visualizations_page()
    elif page == "📄 Report Generation":
        show_report_generation_page()
    elif page == "📋 Data Governance":
        show_data_governance_page()


def show_home_page():
    """Display home page with system overview."""
    st.title("📚 Library Assessment Assistant")
    st.markdown("### AI-Powered Decision Support System")
    
    st.markdown("""
    Welcome to the Library Assessment Assistant! This system helps you analyze library data
    using AI-powered natural language processing while maintaining FERPA compliance through
    local-only processing.
    
    #### Key Features
    
    - **📤 Data Upload**: Upload CSV files with survey responses, usage statistics, and circulation data
    - **💬 Query Interface**: Ask questions in plain English and get answers with citations
    - **📊 Qualitative Analysis**: Analyze open-ended responses for sentiment and themes
    - **📈 Visualizations**: Generate charts to visualize trends and patterns
    - **📄 Report Generation**: Create comprehensive reports with statistics and narratives
    - **📋 Data Governance**: Follow FAIR and CARE principles for responsible data management
    
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
        st.metric("Status", "🟢 Online")
    
    with col2:
        st.metric("Processing", "Local Only")
    
    with col3:
        st.metric("FERPA Compliant", "✓ Yes")


def show_data_upload_page():
    """Display data upload page with CSV uploader and FAIR/CARE metadata."""
    from modules import csv_handler
    import json
    
    st.title("📤 Data Upload")
    st.markdown("Upload CSV files containing library assessment data with FAIR/CARE metadata.")
    
    # Create tabs for upload and manage datasets
    tab1, tab2 = st.tabs(["📤 Upload New Dataset", "📋 Manage Datasets"])
    
    with tab1:
        st.markdown("### Upload New Dataset")
        
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
            
            # Dataset name
            dataset_name = st.text_input(
                "Dataset Name",
                value=uploaded_file.name.replace('.csv', ''),
                help="A unique name for this dataset"
            )
            
            # FAIR/CARE Metadata Section
            st.markdown("#### FAIR/CARE Metadata")
            st.markdown("Provide metadata to support findability, accessibility, and responsible data use.")
            
            with st.expander("📝 Metadata Fields", expanded=True):
                title = st.text_input(
                    "Title",
                    help="Human-readable title for the dataset"
                )
                
                description = st.text_area(
                    "Description",
                    help="Detailed description of dataset contents and purpose"
                )
                
                source = st.text_input(
                    "Source",
                    help="Origin of the data (e.g., Qualtrics, ILS, manual entry)"
                )
                
                keywords_input = st.text_input(
                    "Keywords (comma-separated)",
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
                validate_button = st.button("🔍 Validate CSV", use_container_width=True)
            
            with col2:
                upload_button = st.button("✅ Upload Dataset", type="primary", use_container_width=True)
            
            # Validation
            if validate_button or upload_button:
                # Calculate file hash
                file_content = uploaded_file.getvalue()
                file_hash = csv_handler.calculate_file_hash(file_content)
                uploaded_file.seek(0)
                
                # Check for duplicates
                duplicate = csv_handler.check_duplicate(file_hash)
                if duplicate:
                    st.warning(f"⚠️ This dataset has already been uploaded (detected by file hash). Upload date: {duplicate['upload_date']}")
                    st.info("You can still upload it if you want to create a separate copy.")
                
                # Validate CSV
                is_valid, error_msg = csv_handler.validate_csv(uploaded_file, dataset_type)
                
                if not is_valid:
                    st.error(f"❌ {error_msg}")
                else:
                    st.success("✅ CSV validation passed!")
                    
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
                                
                                st.success(f"🎉 Dataset uploaded successfully! Dataset ID: {dataset_id}")
                                st.balloons()
                                
                            except Exception as e:
                                st.error(f"❌ Error uploading dataset: {str(e)}")
    
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
                    "📥 Download Data Manifest",
                    data=manifest_json,
                    file_name="data_manifest.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            st.markdown("---")
            
            # Display each dataset
            for dataset in datasets:
                with st.expander(f"📊 {dataset['name']} (ID: {dataset['id']})", expanded=False):
                    # Basic info
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Type", dataset['dataset_type'].title())
                    with col2:
                        st.metric("Rows", dataset['row_count'])
                    with col3:
                        st.metric("Uploaded", dataset['upload_date'][:10])
                    
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
                        if st.button(f"✏️ Edit Metadata", key=f"edit_{dataset['id']}"):
                            st.session_state[f"editing_{dataset['id']}"] = True
                    
                    with col2:
                        # Export CSV button
                        csv_data = csv_handler.export_dataset(dataset['id'], 'csv')
                        if csv_data:
                            st.download_button(
                                "📥 Export CSV",
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
                                "📥 Export JSON",
                                data=json_data,
                                file_name=f"{dataset['name']}.json",
                                mime="application/json",
                                key=f"export_json_{dataset['id']}"
                            )
                    
                    with col4:
                        # Delete button
                        if st.button(f"🗑️ Delete", key=f"delete_{dataset['id']}", type="secondary"):
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
                                save_button = st.form_submit_button("💾 Save Changes", type="primary")
                            with col2:
                                cancel_button = st.form_submit_button("❌ Cancel")
                            
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
                                    st.success("✅ Metadata updated successfully!")
                                    st.session_state[f"editing_{dataset['id']}"] = False
                                    
                                    # Log access
                                    from modules import auth
                                    auth.log_access(
                                        st.session_state.username,
                                        f"Updated metadata for dataset: {dataset['name']} (ID: {dataset['id']})"
                                    )
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to update metadata.")
                            
                            if cancel_button:
                                st.session_state[f"editing_{dataset['id']}"] = False
                                st.rerun()
                    
                    # Delete confirmation
                    if st.session_state.get(f"confirm_delete_{dataset['id']}", False):
                        st.warning(f"⚠️ Are you sure you want to delete '{dataset['name']}'? This action cannot be undone.")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"✅ Yes, Delete", key=f"confirm_yes_{dataset['id']}", type="primary"):
                                if csv_handler.delete_dataset(dataset['id']):
                                    st.success(f"✅ Dataset '{dataset['name']}' deleted successfully!")
                                    
                                    # Log access
                                    from modules import auth
                                    auth.log_access(
                                        st.session_state.username,
                                        f"Deleted dataset: {dataset['name']} (ID: {dataset['id']})"
                                    )
                                    
                                    st.session_state[f"confirm_delete_{dataset['id']}"] = False
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to delete dataset.")
                        with col2:
                            if st.button(f"❌ Cancel", key=f"confirm_no_{dataset['id']}"):
                                st.session_state[f"confirm_delete_{dataset['id']}"] = False
                                st.rerun()


def show_query_interface_page():
    """Display query interface page with chat interface and RAG functionality."""
    from modules.rag_query import RAGQuery
    from modules import auth
    import uuid
    
    st.title("💬 Query Interface")
    st.markdown("Ask questions about your library data in natural language.")
    
    # Initialize RAG engine in session state
    if 'rag_engine' not in st.session_state:
        try:
            st.session_state.rag_engine = RAGQuery()
        except Exception as e:
            st.error(f"❌ Failed to initialize RAG engine: {str(e)}")
            st.info("Please ensure ChromaDB is properly configured.")
            return
    
    # Initialize session ID for conversation context
    if 'query_session_id' not in st.session_state:
        st.session_state.query_session_id = str(uuid.uuid4())
    
    # Initialize message history in session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Test Ollama connection
    rag_engine = st.session_state.rag_engine
    is_connected, error_msg = rag_engine.test_ollama_connection()
    
    if not is_connected:
        st.error(f"❌ {error_msg}")
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
    st.success("🟢 Connected to Ollama")
    
    # Get conversation history
    conversation_history = rag_engine.get_conversation_history(st.session_state.query_session_id)
    context_size = len(conversation_history)
    
    # Display conversation context indicator
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.metric("Conversation Context", f"{context_size} turns")
    with col2:
        if st.button("🗑️ Clear Context", use_container_width=True):
            rag_engine.clear_conversation(st.session_state.query_session_id)
            st.session_state.messages = []
            st.session_state.query_session_id = str(uuid.uuid4())
            
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
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            # Check for error type in assistant messages
            if message["role"] == "assistant" and "error_type" in message:
                error_type = message.get("error_type")
                if error_type == "no_relevant_data":
                    st.warning("⚠️ No Relevant Data Found")
                elif error_type == "context_too_large":
                    st.error("❌ Context Too Large")
                elif error_type == "llm_timeout":
                    st.error("⏱️ Response Generation Timed Out")
                elif error_type == "ollama_connection_failed":
                    st.error("❌ Ollama Connection Failed")
                elif error_type == "exception":
                    st.error("❌ Error")
            
            st.markdown(message["content"])
            
            # Display citations if present
            if message["role"] == "assistant" and "citations" in message:
                if message["citations"]:
                    with st.expander("📚 Citations", expanded=False):
                        for citation in message["citations"]:
                            st.markdown(f"- **Source {citation['source_number']}**: Dataset ID {citation['dataset_id']} ({citation['dataset_type']}) - {citation.get('date', 'N/A')}")
            
            # Display suggested questions if present
            if message["role"] == "assistant" and "suggested_questions" in message:
                if message["suggested_questions"]:
                    with st.expander("💡 Suggested Follow-up Questions", expanded=False):
                        for i, suggestion in enumerate(message["suggested_questions"]):
                            if st.button(suggestion, key=f"suggestion_{len(st.session_state.messages)}_{i}"):
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
                        st.warning("⚠️ No Relevant Data Found")
                        st.markdown(result["answer"])
                    elif error_type == "context_too_large":
                        st.error("❌ Context Too Large")
                        st.markdown(result["answer"])
                    elif error_type == "llm_timeout":
                        st.error("⏱️ Response Generation Timed Out")
                        st.markdown(result["answer"])
                    elif error_type == "ollama_connection_failed":
                        st.error("❌ Ollama Connection Failed")
                        st.markdown(result["answer"])
                    else:
                        # Normal response
                        st.markdown(result["answer"])
                    
                    # Display citations
                    if result["citations"]:
                        with st.expander("📚 Citations", expanded=False):
                            for citation in result["citations"]:
                                st.markdown(f"- **Source {citation['source_number']}**: Dataset ID {citation['dataset_id']} ({citation['dataset_type']}) - {citation.get('date', 'N/A')}")
                    
                    # Display suggested questions
                    if result["suggested_questions"]:
                        with st.expander("💡 Suggested Follow-up Questions", expanded=False):
                            for i, suggestion in enumerate(result["suggested_questions"]):
                                if st.button(suggestion, key=f"new_suggestion_{i}"):
                                    # Add suggestion as user message
                                    st.session_state.messages.append({"role": "user", "content": suggestion})
                                    st.rerun()
                    
                    # Display processing time (only for successful queries)
                    if not error_type:
                        st.caption(f"⏱️ Processing time: {result['processing_time_ms']}ms | Confidence: {result['confidence']:.2%}")
                    else:
                        st.caption(f"⏱️ Processing time: {result['processing_time_ms']}ms")
                    
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
                    error_message = f"❌ Error processing query: {str(e)}"
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
    with st.expander("ℹ️ How to use the Query Interface", expanded=False):
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
    st.caption("💡 Tip: Be specific in your questions for better results. The system searches across all uploaded datasets.")


def show_qualitative_analysis_page():
    """Display qualitative analysis page with sentiment and theme analysis."""
    from modules import csv_handler, qualitative_analysis, visualization, auth
    import pandas as pd
    import json
    
    st.title("📊 Qualitative Analysis")
    st.markdown("Analyze open-ended survey responses for sentiment and themes.")
    
    # Get available datasets
    datasets = csv_handler.get_datasets()
    survey_datasets = [d for d in datasets if d['dataset_type'] == 'survey']
    
    if not survey_datasets:
        st.info("No survey datasets available. Please upload survey data in the Data Upload section.")
        return
    
    # Dataset selector
    st.markdown("### Select Dataset")
    dataset_options = {f"{d['name']} (ID: {d['id']})": d['id'] for d in survey_datasets}
    selected_dataset_name = st.selectbox(
        "Choose a survey dataset to analyze",
        options=list(dataset_options.keys()),
        key="analysis_dataset_selector"
    )
    
    if not selected_dataset_name:
        return
    
    selected_dataset_id = dataset_options[selected_dataset_name]
    
    # Get dataset info
    selected_dataset = next(d for d in survey_datasets if d['id'] == selected_dataset_id)
    
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
        analyze_button = st.button("🔍 Run Analysis", type="primary", use_container_width=True)
    
    # Run analysis
    if analyze_button:
        with st.spinner("Analyzing responses... This may take a moment."):
            try:
                # Run sentiment analysis
                sentiment_results = qualitative_analysis.analyze_dataset_sentiment(selected_dataset_id)
                
                # Run theme extraction
                theme_results = qualitative_analysis.extract_themes(selected_dataset_id, n_themes)
                
                # Store results in session state
                st.session_state.analysis_results = {
                    'dataset_id': selected_dataset_id,
                    'dataset_name': selected_dataset['name'],
                    'sentiment': sentiment_results,
                    'themes': theme_results
                }
                
                # Log access
                auth.log_access(
                    st.session_state.username,
                    f"Performed qualitative analysis on dataset: {selected_dataset['name']} (ID: {selected_dataset_id})"
                )
                
                st.success("✅ Analysis completed successfully!")
                
            except ValueError as e:
                st.error(f"❌ {str(e)}")
                return
            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                return
    
    # Display results if available
    if 'analysis_results' in st.session_state and st.session_state.analysis_results['dataset_id'] == selected_dataset_id:
        results = st.session_state.analysis_results
        sentiment_results = results['sentiment']
        theme_results = results['themes']
        
        st.markdown("---")
        st.markdown("## Analysis Results")
        
        # Sentiment Analysis Section
        st.markdown("### 📈 Sentiment Distribution")
        
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
        st.markdown("### 🎯 Identified Themes")
        
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
        st.markdown("### 📊 Theme Frequency Distribution")
        
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
        st.markdown("### 📥 Export Analysis Results")
        
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
                "📄 Export Themes (CSV)",
                data=csv_data,
                file_name=f"themes_{results['dataset_name']}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            # Export sentiment chart
            sentiment_chart_bytes = visualization.export_chart(sentiment_chart, "sentiment_distribution", format='html')
            st.download_button(
                "📊 Export Sentiment Chart",
                data=sentiment_chart_bytes,
                file_name=f"sentiment_chart_{results['dataset_name']}.html",
                mime="text/html",
                use_container_width=True
            )
        
        with col3:
            # Export theme chart
            theme_chart_bytes = visualization.export_chart(theme_chart, "theme_frequency", format='html')
            st.download_button(
                "📊 Export Theme Chart",
                data=theme_chart_bytes,
                file_name=f"theme_chart_{results['dataset_name']}.html",
                mime="text/html",
                use_container_width=True
            )
    
    # Help section
    st.markdown("---")
    with st.expander("ℹ️ How to use Qualitative Analysis", expanded=False):
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
    st.caption("💡 Tip: Run analysis with different numbers of themes to find the optimal granularity for your data.")


def show_visualizations_page():
    """Display visualizations page with chart generation and export."""
    from modules import csv_handler, visualization, auth
    import pandas as pd
    
    st.title("📈 Visualizations")
    st.markdown("Generate charts to visualize trends and patterns in your library data.")
    
    # Get available datasets
    datasets = csv_handler.get_datasets()
    
    if not datasets:
        st.info("No datasets available. Please upload data in the Data Upload section.")
        return
    
    # Dataset selector
    st.markdown("### Select Dataset")
    dataset_options = {f"{d['name']} (ID: {d['id']})": d['id'] for d in datasets}
    selected_dataset_name = st.selectbox(
        "Choose a dataset to visualize",
        options=list(dataset_options.keys()),
        key="viz_dataset_selector"
    )
    
    if not selected_dataset_name:
        return
    
    selected_dataset_id = dataset_options[selected_dataset_name]
    
    # Get dataset info
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
    
    # Load dataset preview to get columns
    try:
        preview_df = csv_handler.get_preview(selected_dataset_id, n_rows=selected_dataset['row_count'])
        
        if preview_df.empty:
            st.error("Unable to load dataset. Please try another dataset.")
            return
        
        # Chart type selector
        st.markdown("### Chart Configuration")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            chart_type = st.selectbox(
                "Chart Type",
                options=["Bar Chart", "Line Chart", "Pie Chart"],
                help="Select the type of chart to generate"
            )
        
        with col2:
            chart_title = st.text_input(
                "Chart Title",
                value=f"{selected_dataset['name']} Visualization",
                help="Enter a title for your chart"
            )
        
        # Column selection based on chart type
        st.markdown("#### Select Columns")
        
        available_columns = preview_df.columns.tolist()
        
        if chart_type == "Pie Chart":
            col1, col2 = st.columns(2)
            with col1:
                names_column = st.selectbox(
                    "Labels Column",
                    options=available_columns,
                    help="Column containing category names"
                )
            with col2:
                values_column = st.selectbox(
                    "Values Column",
                    options=available_columns,
                    help="Column containing numeric values"
                )
        else:
            col1, col2 = st.columns(2)
            with col1:
                x_column = st.selectbox(
                    "X-Axis Column",
                    options=available_columns,
                    help="Column for x-axis"
                )
            with col2:
                y_column = st.selectbox(
                    "Y-Axis Column",
                    options=available_columns,
                    help="Column for y-axis (should be numeric)"
                )
            
            # Optional axis labels
            with st.expander("📝 Custom Axis Labels (Optional)", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    x_label = st.text_input("X-Axis Label", value="")
                with col2:
                    y_label = st.text_input("Y-Axis Label", value="")
        
        # Generate chart button
        st.markdown("---")
        generate_button = st.button("📊 Generate Chart", type="primary", use_container_width=True)
        
        if generate_button:
            with st.spinner("Generating chart..."):
                try:
                    # Validate columns and prepare data
                    if chart_type == "Pie Chart":
                        # Check if columns exist
                        if names_column not in preview_df.columns or values_column not in preview_df.columns:
                            st.error("Selected columns not found in dataset.")
                            return
                        
                        # Prepare data - aggregate if needed
                        chart_data = preview_df[[names_column, values_column]].copy()
                        chart_data = chart_data.groupby(names_column)[values_column].sum().reset_index()
                        
                        # Generate pie chart
                        fig = visualization.create_pie_chart(
                            chart_data,
                            values=values_column,
                            names=names_column,
                            title=chart_title
                        )
                    
                    else:
                        # Check if columns exist
                        if x_column not in preview_df.columns or y_column not in preview_df.columns:
                            st.error("Selected columns not found in dataset.")
                            return
                        
                        # Prepare data - aggregate if needed for bar/line charts
                        chart_data = preview_df[[x_column, y_column]].copy()
                        
                        # Try to aggregate if x-axis has duplicates
                        if chart_data[x_column].duplicated().any():
                            chart_data = chart_data.groupby(x_column)[y_column].sum().reset_index()
                        
                        # Generate chart based on type
                        if chart_type == "Bar Chart":
                            fig = visualization.create_bar_chart(
                                chart_data,
                                x=x_column,
                                y=y_column,
                                title=chart_title,
                                x_label=x_label if x_label else None,
                                y_label=y_label if y_label else None
                            )
                        else:  # Line Chart
                            fig = visualization.create_line_chart(
                                chart_data,
                                x=x_column,
                                y=y_column,
                                title=chart_title,
                                x_label=x_label if x_label else None,
                                y_label=y_label if y_label else None
                            )
                    
                    # Store chart in session state
                    st.session_state.current_chart = {
                        'figure': fig,
                        'title': chart_title,
                        'dataset_name': selected_dataset['name']
                    }
                    
                    # Log access
                    auth.log_access(
                        st.session_state.username,
                        f"Generated {chart_type} for dataset: {selected_dataset['name']} (ID: {selected_dataset_id})"
                    )
                    
                    st.success("✅ Chart generated successfully!")
                    
                except ValueError as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.info("Please ensure the selected columns contain appropriate data for the chart type.")
                except Exception as e:
                    st.error(f"❌ Error generating chart: {str(e)}")
        
        # Display chart if available
        if 'current_chart' in st.session_state:
            st.markdown("---")
            st.markdown("### Generated Chart")
            
            # Display the chart
            st.plotly_chart(st.session_state.current_chart['figure'], use_container_width=True)
            
            # Export options
            st.markdown("### 📥 Export Chart")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Export as PNG
                try:
                    png_bytes = visualization.export_chart(
                        st.session_state.current_chart['figure'],
                        st.session_state.current_chart['title'],
                        format='png'
                    )
                    st.download_button(
                        "📥 Download as PNG",
                        data=png_bytes,
                        file_name=f"{st.session_state.current_chart['title']}.png",
                        mime="image/png",
                        use_container_width=True
                    )
                except Exception as e:
                    st.warning("PNG export not available. Please use HTML export instead.")
            
            with col2:
                # Export as HTML
                html_bytes = visualization.export_chart(
                    st.session_state.current_chart['figure'],
                    st.session_state.current_chart['title'],
                    format='html'
                )
                st.download_button(
                    "📥 Download as HTML",
                    data=html_bytes,
                    file_name=f"{st.session_state.current_chart['title']}.html",
                    mime="text/html",
                    use_container_width=True
                )
    
    except Exception as e:
        st.error(f"❌ Error loading dataset: {str(e)}")
        return
    
    # Help section
    st.markdown("---")
    with st.expander("ℹ️ How to use Visualizations", expanded=False):
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
    st.caption("💡 Tip: Use custom axis labels to make your charts more professional and easier to understand.")


def show_report_generation_page():
    """Display report generation page with report creation and export."""
    from modules import csv_handler, report_generator, auth
    import json
    
    st.title("📄 Report Generation")
    st.markdown("Generate comprehensive reports with statistical summaries and narrative text.")
    
    # Get available datasets
    datasets = csv_handler.get_datasets()
    
    if not datasets:
        st.info("No datasets available. Please upload data in the Data Upload section.")
        return
    
    # Report configuration section
    st.markdown("### Report Configuration")
    
    # Multi-select for datasets
    dataset_options = {f"{d['name']} (ID: {d['id']})": d['id'] for d in datasets}
    selected_dataset_names = st.multiselect(
        "Select Datasets to Include",
        options=list(dataset_options.keys()),
        help="Choose one or more datasets to include in the report"
    )
    
    if not selected_dataset_names:
        st.info("Please select at least one dataset to generate a report.")
        return
    
    selected_dataset_ids = [dataset_options[name] for name in selected_dataset_names]
    
    # Report options
    col1, col2 = st.columns(2)
    
    with col1:
        include_visualizations = st.checkbox(
            "Include Visualizations",
            value=True,
            help="Add charts and graphs to the report"
        )
    
    with col2:
        include_qualitative = st.checkbox(
            "Include Qualitative Analysis",
            value=False,
            help="Include sentiment and theme analysis if available"
        )
    
    # Report title (optional)
    custom_title = st.text_input(
        "Custom Report Title (Optional)",
        placeholder="Leave blank for auto-generated title",
        help="Enter a custom title for your report"
    )
    
    st.markdown("---")
    
    # Generate report button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        generate_button = st.button("📊 Generate Report", type="primary", use_container_width=True)
    
    # Generate report
    if generate_button:
        # Progress indicator
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Create report structure
            status_text.text("Creating report structure...")
            progress_bar.progress(20)
            
            report = report_generator.create_report(
                dataset_ids=selected_dataset_ids,
                include_viz=include_visualizations,
                include_qualitative=include_qualitative
            )
            
            # Apply custom title if provided
            if custom_title:
                report['title'] = custom_title
            
            progress_bar.progress(60)
            status_text.text("Generating narrative text...")
            
            # Step 2: Store report in session state
            progress_bar.progress(100)
            status_text.text("Report generated successfully!")
            
            st.session_state.current_report = report
            
            # Log access
            auth.log_access(
                st.session_state.username,
                f"Generated report for datasets: {', '.join([str(id) for id in selected_dataset_ids])}"
            )
            
            st.success("✅ Report generated successfully!")
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
        except ValueError as e:
            st.error(f"❌ Error: {str(e)}")
            progress_bar.empty()
            status_text.empty()
            return
        except Exception as e:
            st.error(f"❌ Error generating report: {str(e)}")
            progress_bar.empty()
            status_text.empty()
            return
    
    # Display report preview if available
    if 'current_report' in st.session_state:
        report = st.session_state.current_report
        
        st.markdown("---")
        st.markdown("## Report Preview")
        
        # Report title
        st.markdown(f"# {report['title']}")
        st.markdown("---")
        
        # Metadata section
        with st.expander("📋 Report Metadata", expanded=False):
            st.markdown(f"**Generated:** {report['metadata']['generated_at']}")
            st.markdown(f"**Author:** {report['metadata']['author']}")
            st.markdown(f"**Datasets:** {', '.join(report['metadata']['datasets'])}")
            st.markdown(f"**Dataset IDs:** {', '.join([str(id) for id in report['metadata']['dataset_ids']])}")
        
        # Executive summary
        st.markdown("## Executive Summary")
        st.markdown(report['executive_summary'])
        st.markdown("---")
        
        # Statistical summaries
        st.markdown("## Statistical Summaries")
        
        for summary in report['statistical_summaries']:
            st.markdown(f"### {summary['dataset_name']}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Dataset Type", summary['dataset_type'].title())
            with col2:
                st.metric("Total Records", summary['row_count'])
            
            # Display statistics
            if summary.get('statistics'):
                st.markdown("#### Key Statistics")
                
                for metric_name, stats in summary['statistics'].items():
                    with st.expander(f"📊 {metric_name}", expanded=False):
                        cols = st.columns(5)
                        
                        if 'mean' in stats:
                            cols[0].metric("Mean", f"{stats['mean']:.2f}")
                        if 'median' in stats:
                            cols[1].metric("Median", f"{stats['median']:.2f}")
                        if 'std_dev' in stats:
                            cols[2].metric("Std Dev", f"{stats['std_dev']:.2f}")
                        if 'count' in stats:
                            cols[3].metric("Count", stats['count'])
                        if 'min' in stats and 'max' in stats:
                            cols[4].metric("Range", f"{stats['min']:.2f} - {stats['max']:.2f}")
            
            # Display categorical counts
            if summary.get('categorical_counts'):
                st.markdown("#### Categorical Distributions")
                
                for category_name, counts in summary['categorical_counts'].items():
                    with st.expander(f"📈 {category_name}", expanded=False):
                        # Display as columns
                        items = list(counts.items())
                        num_cols = min(4, len(items))
                        cols = st.columns(num_cols)
                        
                        for i, (value, count) in enumerate(items):
                            cols[i % num_cols].metric(str(value), count)
            
            st.markdown("---")
        
        # Visualizations
        if report.get('visualizations'):
            st.markdown("## Visualizations")
            st.markdown(f"**{len(report['visualizations'])} visualization(s) included**")
            
            for viz in report['visualizations']:
                st.markdown(f"### {viz['title']}")
                st.plotly_chart(viz['figure'], use_container_width=True)
            
            st.markdown("---")
        
        # Qualitative analysis
        if report.get('qualitative_analysis'):
            st.markdown("## Qualitative Analysis")
            qual = report['qualitative_analysis']
            
            if qual.get('sentiment_distribution'):
                st.markdown("### Sentiment Distribution")
                
                sentiment_dist = qual['sentiment_distribution']
                total = sum(sentiment_dist.values())
                
                cols = st.columns(len(sentiment_dist))
                for i, (sentiment, count) in enumerate(sentiment_dist.items()):
                    percentage = (count / total * 100) if total > 0 else 0
                    cols[i].metric(sentiment.title(), f"{count} ({percentage:.1f}%)")
            
            st.markdown("---")
        
        # Theme summaries
        if report.get('theme_summaries'):
            st.markdown("## Identified Themes")
            
            for theme in report['theme_summaries']:
                with st.expander(f"🎯 {theme['name']} ({theme['frequency']} occurrences)", expanded=False):
                    st.markdown(f"**Keywords:** {', '.join(theme['keywords'])}")
                    
                    if theme.get('quotes'):
                        st.markdown("**Representative Quotes:**")
                        for quote in theme['quotes']:
                            st.markdown(f"> {quote}")
            
            st.markdown("---")
        
        # Citations
        if report.get('citations'):
            st.markdown("## Data Sources")
            for citation in report['citations']:
                st.markdown(f"- {citation}")
            
            st.markdown("---")
        
        # Export section
        st.markdown("## 📥 Export Report")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Export as Markdown
            try:
                markdown_bytes, actual_format = report_generator.export_report(report, format='markdown')
                st.download_button(
                    "📄 Download as Markdown",
                    data=markdown_bytes,
                    file_name=f"{report['title'].replace(' ', '_')}.md",
                    mime="text/markdown",
                    use_container_width=True,
                    help="Download report as Markdown file"
                )
            except Exception as e:
                st.error(f"❌ Error exporting Markdown: {str(e)}")
        
        with col2:
            # Export as PDF
            try:
                pdf_bytes, actual_format = report_generator.export_report(report, format='pdf')
                
                # Check if PDF export succeeded or fell back to Markdown
                if actual_format == 'markdown':
                    st.warning("⚠️ PDF export failed. Downloading as Markdown instead.")
                    st.download_button(
                        "📄 Download as Markdown (Fallback)",
                        data=pdf_bytes,
                        file_name=f"{report['title'].replace(' ', '_')}.md",
                        mime="text/markdown",
                        use_container_width=True,
                        help="PDF export failed, downloading as Markdown"
                    )
                else:
                    st.download_button(
                        "📕 Download as PDF",
                        data=pdf_bytes,
                        file_name=f"{report['title'].replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        help="Download report as PDF file"
                    )
            except Exception as e:
                st.warning("⚠️ PDF export not available. Please use Markdown export.")
                st.caption(f"Error: {str(e)}")
    
    # Display visualization warnings if any
    if report.get('metadata', {}).get('visualization_warnings'):
        st.markdown("---")
        st.warning("⚠️ **Visualization Warnings**")
        st.caption("Some visualizations could not be generated due to insufficient data:")
        for warning in report['metadata']['visualization_warnings']:
            st.caption(f"• {warning}")
    
    # Help section
    st.markdown("---")
    with st.expander("ℹ️ How to use Report Generation", expanded=False):
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
    st.caption("💡 Tip: Generate multiple reports with different dataset combinations to compare findings across different data sources.")


def show_data_governance_page():
    """Display data governance documentation page with FAIR and CARE principles."""
    st.title("📋 Data Governance")
    st.markdown("### Responsible Data Management for Library Assessment")
    
    st.markdown("""
    This system follows **FAIR** (Findable, Accessible, Interoperable, Reusable) and 
    **CARE** (Collective Benefit, Authority to Control, Responsibility, Ethics) principles 
    to ensure responsible and ethical management of library assessment data.
    """)
    
    # FAIR Principles Section
    st.markdown("---")
    st.markdown("## 🔍 FAIR Principles")
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
    st.markdown("## 🤝 CARE Principles")
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
    st.markdown("## 📊 Data Collection and Use")
    
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
    st.markdown("## 🔒 Privacy Protections")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Local Processing
        
        **All data processing happens on your local machine:**
        
        - ✅ No external API calls
        - ✅ No cloud services
        - ✅ No data transmission
        - ✅ Complete data sovereignty
        
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
        
        - 🛡️ PII detection in outputs
        - 🛡️ Redaction of sensitive data
        - 🛡️ Flagging of potential privacy issues
        - 🛡️ FERPA compliance measures
        
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
    
    - 📝 Every data access is logged with timestamp
    - 📝 User actions tracked (upload, query, analysis, export, delete)
    - 📝 Audit logs support compliance requirements
    - 📝 Logs stored securely in local database
    
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
    st.markdown("## ⚖️ Ethical Use Guidelines")
    
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
    st.markdown("## 🎛️ User Access and Control Mechanisms")
    
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
    st.markdown("## 📚 Additional Resources")
    
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
    # Initialize session state for authentication
    auth.init_session_state(st.session_state)
    
    # Show login page or main app based on authentication status
    if auth.is_authenticated(st.session_state):
        show_main_app()
    else:
        show_login_page()


if __name__ == "__main__":
    main()
