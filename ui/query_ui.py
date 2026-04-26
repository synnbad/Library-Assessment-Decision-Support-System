"""
Query Interface UI Module

This module provides the RAG-powered natural language query interface.
Includes chat functionality, conversation context management, and citation display.
"""

import streamlit as st
from modules.rag_query import (
    DependencyUnavailableError,
    RAGQuery,
    get_rag_dependency_status,
)
from modules import auth, csv_handler, query_queue, workflow_insights
from modules import query_intelligence


def show_query_interface_page():
    """Display query interface page with chat interface and RAG functionality."""
    st.title("Query Interface")
    st.markdown("Ask questions about your library data in natural language.")
    
    # Initialize RAG engine in session state
    if 'rag_engine' not in st.session_state:
        try:
            st.session_state.rag_engine = RAGQuery()
        except DependencyUnavailableError as e:
            st.error("RAG query features are unavailable in this environment.")
            st.markdown(str(e))
            st.markdown("### Runtime dependency status")
            for status in get_rag_dependency_status().values():
                availability = "Available" if status["available"] else "Missing"
                st.markdown(f"- `{status['package']}`: {availability}")
            return
        except Exception as e:
            st.error(f"Failed to initialize RAG engine: {str(e)}")
            st.info("Please ensure ChromaDB and sentence-transformers are installed and configured.")
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

    # Show indexing status and let the user opt into the indexing work.
    datasets = csv_handler.get_datasets()
    indexed_datasets = []
    unindexed_datasets = []
    for ds in datasets:
        try:
            if rag_engine._is_dataset_indexed(ds['id']):
                indexed_datasets.append(ds)
            else:
                unindexed_datasets.append(ds)
        except Exception as e:
            st.warning(f"Could not check indexing status for dataset '{ds['name']}': {e}")

    if not datasets:
        st.info("Upload a dataset in the Data Upload page before using the query interface.")
    elif unindexed_datasets:
        st.warning(
            f"{len(unindexed_datasets)} dataset(s) still need indexing before they can be searched."
        )
        if st.button("Index Available Datasets", use_container_width=True):
            newly_indexed = []
            for ds in unindexed_datasets:
                try:
                    n = rag_engine.index_dataset(ds['id'])
                    if n > 0:
                        newly_indexed.append(f"{ds['name']} ({n} docs)")
                except Exception as e:
                    st.warning(f"Could not index dataset '{ds['name']}': {e}")
            if newly_indexed:
                st.success(f"Indexed datasets: {', '.join(newly_indexed)}")
            st.rerun()
    else:
        st.success(f"{len(indexed_datasets)} indexed dataset(s) are ready for querying.")

    dataset_profiles = _build_dataset_profiles(indexed_datasets or datasets)

    # Test Ollama connection
    is_connected, error_msg = rag_engine.test_ollama_connection()
    
    if not is_connected:
        st.warning(f"Ollama is unavailable: {error_msg}")
        st.markdown("""
        ### How to start Ollama:
        
        1. Open a terminal
        2. Run: `ollama serve`
        3. In another terminal, ensure the model is available: `ollama pull llama3.2:3b`
        4. Refresh this page
        
        For more information, visit: https://ollama.ai
        """)
    else:
        st.success("Connected to Ollama")

    has_indexed_data = len(indexed_datasets) > 0
    query_enabled = is_connected and has_indexed_data
    profile_query_enabled = bool(dataset_profiles)
    chat_enabled = query_enabled or profile_query_enabled
    
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
        st.metric("Model", rag_engine.model_name)

    if dataset_profiles:
        st.markdown("---")
        st.markdown("### Smart Starters")
        st.caption(query_intelligence.recommended_next_action(dataset_profiles, has_indexed_data=has_indexed_data))
        starter_questions = _starter_questions(dataset_profiles)
        if starter_questions:
            starter_cols = st.columns(2)
            for idx, question in enumerate(starter_questions):
                with starter_cols[idx % 2]:
                    if st.button(question, key=f"starter_question_{idx}", use_container_width=True):
                        query_queue.queue_question(st.session_state, question)
                        st.rerun()
    
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
                elif error_type == "ollama_model_missing":
                    st.error("Ollama Model Missing")
                elif error_type == "ollama_connection_failed":
                    st.error("Ollama Connection Failed")
                elif error_type == "query_not_ready":
                    st.warning("Query Search Not Ready")
                elif error_type == "exception":
                    st.error("Error")
            
            st.markdown(message["content"])

            if message["role"] == "assistant" and message.get("query_intent"):
                st.caption(f"Intent: {message['query_intent'].replace('_', ' ').title()}")
                if message.get("evidence"):
                    evidence = message["evidence"]
                    st.caption(f"Evidence: {evidence['label']} - {evidence['reason']}")
                if message.get("rewritten_query"):
                    with st.expander("Query Rewrite", expanded=False):
                        st.markdown(message["rewritten_query"])
                if st.button("Pin for Report", key=f"pin_message_{msg_idx}"):
                    previous_question = _previous_user_question(st.session_state.messages, msg_idx)
                    workflow_insights.pin_insight(
                        st.session_state,
                        previous_question,
                        message["content"],
                        username=st.session_state.username,
                    )
                    st.success("Pinned for Report Generation.")
            
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
                                query_queue.queue_question(st.session_state, suggestion)
                                st.rerun()
    
    if not has_indexed_data:
        st.info("Index at least one dataset on this page before asking questions that need source-row search.")
    if has_indexed_data and not is_connected:
        st.info("Querying is paused until Ollama is available.")

    _display_pending_question(chat_enabled, query_enabled)

    # Chat input
    chat_prompt = st.chat_input(
        "Ask a question about your library data...",
        disabled=not chat_enabled
    )
    pending_prompt = query_queue.consume_runnable_question(st.session_state) if chat_enabled else None
    prompt = pending_prompt or chat_prompt
    if prompt:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    query_plan = query_intelligence.classify_query(prompt, dataset_profiles)
                    rewritten_prompt = query_intelligence.rewrite_query(
                        prompt,
                        dataset_profiles,
                        query_plan["intent"],
                    )
                    st.caption(f"Intent: {query_plan['intent'].replace('_', ' ').title()}")
                    if rewritten_prompt != prompt:
                        with st.expander("Query Rewrite", expanded=False):
                            st.markdown(rewritten_prompt)

                    profile_answer = query_intelligence.answer_from_profiles(
                        prompt,
                        dataset_profiles,
                        query_plan["intent"],
                    )
                    if profile_answer is not None:
                        result = {
                            "answer": profile_answer,
                            "confidence": 1.0 if dataset_profiles else 0.0,
                            "citations": [],
                            "suggested_questions": [],
                            "processing_time_ms": 0,
                            "error_type": None,
                        }
                        workflow_insights.log_query_activity(
                            question=prompt,
                            answer=profile_answer,
                            confidence=result["confidence"],
                            session_id=st.session_state.query_session_id,
                            processing_time_ms=0,
                        )
                    elif not query_enabled:
                        result = {
                            "answer": (
                                "This question needs indexed source rows and a live Ollama connection. "
                                "I can still answer data inventory and data quality questions from the "
                                "uploaded dataset profiles."
                            ),
                            "confidence": 0.0,
                            "citations": [],
                            "suggested_questions": [
                                "What data do I have available?",
                                "What data quality issues should I know about?",
                            ],
                            "processing_time_ms": 0,
                            "error_type": "query_not_ready",
                        }
                    else:
                        # Query RAG engine
                        result = rag_engine.query(
                            question=rewritten_prompt,
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
                    elif error_type == "ollama_model_missing":
                        st.error("Ollama Model Missing")
                        st.markdown(result["answer"])
                    elif error_type == "ollama_connection_failed":
                        st.error("Ollama Connection Failed")
                        st.markdown(result["answer"])
                    elif error_type == "query_not_ready":
                        st.warning("Query Search Not Ready")
                        st.markdown(result["answer"])
                    else:
                        # Normal response
                        st.markdown(result["answer"])
                    
                    # Display citations
                    if result["citations"]:
                        with st.expander("Citations", expanded=False):
                            for citation in result["citations"]:
                                st.markdown(f"- **Source {citation['source_number']}**: Dataset ID {citation['dataset_id']} ({citation['dataset_type']}) - {citation.get('date', 'N/A')}")
                    
                    smart_suggestions = query_intelligence.suggest_followups(
                        prompt,
                        result.get("answer", ""),
                        dataset_profiles,
                        query_plan["intent"],
                    )
                    result["suggested_questions"] = _dedupe(
                        smart_suggestions + result.get("suggested_questions", [])
                    )[:5]

                    # Display suggested questions
                    if result["suggested_questions"]:
                        with st.expander("Suggested Follow-up Questions", expanded=False):
                            for i, suggestion in enumerate(result["suggested_questions"]):
                                if st.button(suggestion, key=f"suggestion_live_{len(st.session_state.messages)}_{i}"):
                                    query_queue.queue_question(st.session_state, suggestion)
                                    st.rerun()

                    evidence = query_intelligence.assess_evidence(
                        result.get("confidence", 0.0),
                        len(result.get("citations", [])),
                        query_plan["intent"],
                        prompt,
                        dataset_profiles,
                    )
                    
                    # Display processing time (only for successful queries)
                    if not error_type:
                        st.caption(
                            f"Processing time: {result['processing_time_ms']}ms | "
                            f"Evidence: {evidence['label']} ({evidence['score']:.0%})"
                        )
                        st.caption(evidence["reason"])
                    elif error_type == "query_not_ready":
                        st.caption(f"Evidence: {evidence['label']} - {evidence['reason']}")
                    else:
                        st.caption(f"Processing time: {result['processing_time_ms']}ms")
                    
                    # Add assistant message to chat history
                    assistant_message = {
                        "role": "assistant",
                        "content": result["answer"],
                        "citations": result["citations"],
                        "suggested_questions": result["suggested_questions"],
                        "error_type": error_type,
                        "query_intent": query_plan["intent"],
                        "rewritten_query": rewritten_prompt,
                        "evidence": evidence,
                    }
                    st.session_state.messages.append(assistant_message)
                    
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
        2. **Index Data**: Use the "Index Available Datasets" button on this page before searching
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


def _build_dataset_profiles(datasets):
    """Build query guidance profiles from stored dataset previews."""
    profiles = []
    for dataset in datasets:
        try:
            preview_df = csv_handler.get_preview(dataset["id"], n_rows=1000)
            if preview_df.empty:
                continue
            profiles.append(query_intelligence.build_profile_from_dataset_record(dataset, preview_df))
        except Exception:
            continue
    return profiles


def _starter_questions(profiles):
    """Collect a short, de-duplicated set of starter questions."""
    questions = []
    for profile in profiles[:3]:
        questions.extend(query_intelligence.suggest_questions(profile, limit=3))
    return _dedupe(questions)[:6]


def _display_pending_question(chat_enabled: bool, query_enabled: bool):
    """Show an editable queued question before it is submitted."""
    pending_question = st.session_state.get(query_queue.PENDING_QUERY_KEY)
    if not pending_question:
        return

    st.markdown("---")
    st.markdown("### Pending Question")
    st.caption("Suggested questions wait here so you can adjust them before the app searches your data.")
    edited_question = st.text_area(
        "Review or edit before running",
        value=pending_question,
        key="pending_query_editor",
        disabled=not chat_enabled,
    )
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("Run", type="primary", disabled=not chat_enabled, use_container_width=True):
            query_queue.update_pending_question(st.session_state, edited_question.strip())
            if query_queue.mark_pending_for_run(st.session_state):
                st.rerun()
    with col2:
        if st.button("Clear", use_container_width=True):
            query_queue.clear_pending_question(st.session_state)
            if "pending_query_editor" in st.session_state:
                del st.session_state["pending_query_editor"]
            st.rerun()
    with col3:
        if not chat_enabled:
            st.caption("Upload data before running this question.")
        elif not query_enabled:
            st.caption("Inventory and quality questions can run now. Source-row search still needs indexing and Ollama.")
        else:
            st.caption("Run will submit this question and keep the rewrite visible with the answer.")


def _previous_user_question(messages, assistant_index: int) -> str:
    """Find the nearest user prompt before an assistant message."""
    for message in reversed(messages[:assistant_index]):
        if message.get("role") == "user":
            return message.get("content", "")
    return ""


def _dedupe(items):
    """Return unique strings while preserving order."""
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            result.append(item)
            seen.add(item)
    return result
