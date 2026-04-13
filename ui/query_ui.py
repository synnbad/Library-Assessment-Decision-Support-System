"""
Query Interface UI Module

This module provides the RAG-powered natural language query interface.
Includes chat functionality, conversation context management, and citation display.
"""

import streamlit as st
from modules.rag_query import RAGQuery
from modules import auth, csv_handler


def show_query_interface_page():
    """Display query interface page with chat interface and RAG functionality."""
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
