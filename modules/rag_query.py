"""
RAG Query Module

This module implements Retrieval-Augmented Generation (RAG) for natural language
question answering about library assessment data using local LLM processing.

Key Features:
- Local LLM inference via Ollama (Llama 3.2 3B or Phi-3 Mini)
- Vector similarity search using ChromaDB (embedded mode)
- Sentence embeddings with all-MiniLM-L6-v2 (384 dimensions)
- Conversation context management (configurable window)
- Citation extraction from retrieved documents
- PII redaction on all outputs
- Comprehensive error handling with user-friendly messages
- Query performance tracking

RAG Pipeline:
1. User submits natural language question
2. Question embedded using sentence-transformers
3. ChromaDB retrieves top-k similar documents (default k=5)
4. Context + conversation history assembled
5. Context size validated (max 4000 tokens)
6. Ollama LLM generates answer with citations
7. PII redaction applied to output
8. Citations extracted from document metadata
9. Suggested follow-up questions generated
10. Answer + citations + suggestions returned

Error Handling:
- No relevant data: Suggests uploading data or rephrasing
- Context too large: Prompts to be more specific or clear context
- LLM timeout: Suggests simpler questions or checking resources
- Ollama connection failed: Provides setup instructions

Module Classes:
- RAGQuery: Main RAG engine class

Key Methods:
- __init__(): Initialize Ollama client and ChromaDB
- test_ollama_connection(): Verify Ollama is accessible
- index_documents(): Embed and store documents in ChromaDB
- index_dataset(): Index entire dataset for retrieval
- retrieve_relevant_docs(): Vector similarity search
- generate_answer(): LLM generation with context
- query(): End-to-end question answering
- clear_conversation(): Reset conversation context
- get_conversation_history(): Retrieve conversation turns

Database Tables Used:
- query_logs: Query history with performance metrics
- datasets: Dataset metadata for citations

Requirements Implemented:
- 2.1: Interpret natural language questions
- 2.2: Generate answers with citations
- 2.3: Maintain conversation context
- 2.4: Retrieve from ChromaDB vector store
- 2.5: Explain when data is missing
- 2.6: Display chat conversation
- 2.7: Run via Ollama with local models
- 6.1: Local LLM processing
- 6.5: PII redaction on outputs

Configuration (config/settings.py):
- OLLAMA_MODEL: LLM model name (default: llama3.2:3b)
- EMBEDDING_MODEL: Embedding model (default: all-MiniLM-L6-v2)
- CONTEXT_WINDOW_SIZE: Conversation turns to keep (default: 5)
- TOP_K_RETRIEVAL: Documents to retrieve (default: 5)
- MAX_CONTEXT_TOKENS: Token limit for context (default: 4000)
- LLM_GENERATION_TIMEOUT_SECONDS: Timeout for generation (default: 60)

Usage Example:
    # Initialize RAG engine
    rag = RAGQuery()
    
    # Check Ollama connection
    is_connected, error = rag.test_ollama_connection()
    if not is_connected:
        print(f"Error: {error}")
    
    # Index a dataset
    num_docs = rag.index_dataset(dataset_id=1)
    print(f"Indexed {num_docs} documents")
    
    # Query
    result = rag.query(
        question="What are the main themes in student feedback?",
        session_id="user_session_123",
        username="admin"
    )
    print(f"Answer: {result['answer']}")
    print(f"Citations: {result['citations']}")

Author: FERPA-Compliant RAG DSS Team
"""

import chromadb
from chromadb.config import Settings as ChromaSettings
import ollama
from sentence_transformers import SentenceTransformer
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
import signal
from contextlib import contextmanager
from modules.database import execute_query, execute_update
from modules.csv_handler import add_query_to_provenance
from modules.pii_detector import redact_pii
from config.settings import Settings


class TimeoutError(Exception):
    """Exception raised when an operation times out."""
    pass


@contextmanager
def timeout(seconds):
    """
    Context manager for timing out operations.
    
    Args:
        seconds: Timeout duration in seconds
        
    Raises:
        TimeoutError: If operation exceeds timeout
    """
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")
    
    # Set the signal handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        # Restore the old handler and cancel the alarm
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


class RAGQuery:
    """RAG query engine for natural language question answering."""
    
    def __init__(self):
        """Initialize RAG engine with Ollama and ChromaDB."""
        self.ollama_url = Settings.OLLAMA_URL
        self.model_name = Settings.OLLAMA_MODEL
        self.embedding_model_name = Settings.EMBEDDING_MODEL
        self.top_k = Settings.TOP_K_RETRIEVAL
        self.context_window = Settings.CONTEXT_WINDOW_SIZE
        self.llm_timeout = Settings.LLM_GENERATION_TIMEOUT_SECONDS
        self.max_context_tokens = Settings.MAX_CONTEXT_TOKENS
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        
        # Initialize ChromaDB in embedded mode
        self.chroma_client = chromadb.PersistentClient(
            path=Settings.CHROMA_DB_PATH,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="assessment_documents",
            metadata={"description": "Library assessment data for RAG"}
        )
        
        # Conversation history storage
        self.conversation_histories = {}
    
    def test_ollama_connection(self) -> Tuple[bool, Optional[str]]:
        """
        Test connection to Ollama server.
        
        Returns:
            Tuple of (is_connected, error_message)
        """
        try:
            # Try to list models
            ollama.list()
            return True, None
        except Exception as e:
            return False, f"Cannot connect to Ollama: {str(e)}"
    
    def index_documents(
        self,
        texts: List[str],
        metadata_list: List[Dict[str, Any]]
    ) -> None:
        """
        Embed and store documents in ChromaDB.
        
        Args:
            texts: List of text documents to index
            metadata_list: List of metadata dicts for each document
        """
        if not texts:
            return
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(texts).tolist()
        
        # Generate IDs
        ids = [f"doc_{i}_{datetime.now().timestamp()}" for i in range(len(texts))]
        
        # Add to ChromaDB
        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadata_list,
            ids=ids
        )
    
    def index_dataset(self, dataset_id: int) -> int:
        """
        Index a dataset in ChromaDB for RAG retrieval.
        
        Args:
            dataset_id: Dataset identifier
            
        Returns:
            Number of documents indexed
        """
        # Get dataset info
        datasets = execute_query(
            "SELECT dataset_type FROM datasets WHERE id = ?",
            (dataset_id,)
        )
        
        if not datasets:
            return 0
        
        dataset_type = datasets[0]['dataset_type']
        
        # Get data to index
        if dataset_type == "survey":
            rows = execute_query(
                """
                SELECT id, response_date, question, response_text
                FROM survey_responses
                WHERE dataset_id = ? AND response_text IS NOT NULL
                """,
                (dataset_id,)
            )
            
            texts = []
            metadata_list = []
            
            for row in rows:
                # Create searchable text combining question and response
                text = f"Question: {row['question']}\nResponse: {row['response_text']}"
                texts.append(text)
                
                metadata_list.append({
                    "dataset_id": str(dataset_id),
                    "dataset_type": dataset_type,
                    "source_row_id": str(row['id']),
                    "date": row['response_date'] or "",
                    "question": row['question']
                })
        
        else:  # usage or circulation
            rows = execute_query(
                """
                SELECT id, date, metric_name, metric_value, category
                FROM usage_statistics
                WHERE dataset_id = ?
                """,
                (dataset_id,)
            )
            
            texts = []
            metadata_list = []
            
            for row in rows:
                text = f"{row['metric_name']}: {row['metric_value']} on {row['date']}"
                if row['category']:
                    text += f" (Category: {row['category']})"
                texts.append(text)
                
                metadata_list.append({
                    "dataset_id": str(dataset_id),
                    "dataset_type": dataset_type,
                    "source_row_id": str(row['id']),
                    "date": row['date'] or "",
                    "metric_name": row['metric_name']
                })
        
        # Index documents
        if texts:
            self.index_documents(texts, metadata_list)
        
        return len(texts)
    
    def retrieve_relevant_docs(
        self,
        question: str,
        k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve top-k relevant documents from ChromaDB.
        
        Args:
            question: Natural language question
            k: Number of documents to retrieve (uses Settings.TOP_K_RETRIEVAL if not provided)
            
        Returns:
            List of retrieved documents with metadata
        """
        if k is None:
            k = self.top_k
        
        # Query ChromaDB
        results = self.collection.query(
            query_texts=[question],
            n_results=k
        )
        
        # Format results
        documents = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                documents.append({
                    "text": doc,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": results['distances'][0][i] if results['distances'] else None
                })
        
        return documents
    
    def _estimate_token_count(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation).
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        # Rough approximation: 1 token ≈ 4 characters
        return len(text) // 4
    
    def _check_context_size(self, context: str, question: str, history: List[Dict[str, str]]) -> Tuple[bool, int]:
        """
        Check if context size is within limits.
        
        Args:
            context: Retrieved context
            question: User question
            history: Conversation history
            
        Returns:
            Tuple of (is_within_limit, estimated_tokens)
        """
        # Build full prompt to estimate size
        prompt = "You are a helpful library assessment assistant. Answer questions based on the provided data.\n\n"
        
        if history:
            prompt += "Previous conversation:\n"
            for turn in history[-self.context_window:]:
                prompt += f"Q: {turn['question']}\nA: {turn['answer']}\n\n"
        
        prompt += f"Relevant data:\n{context}\n\n"
        prompt += f"Question: {question}\n\n"
        prompt += "Answer (include specific data points and cite sources):"
        
        estimated_tokens = self._estimate_token_count(prompt)
        is_within_limit = estimated_tokens <= self.max_context_tokens
        
        return is_within_limit, estimated_tokens
    
    def generate_answer(
        self,
        question: str,
        context: str,
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """
        Generate answer using Ollama LLM with context.
        
        Args:
            question: User's question
            context: Retrieved context from documents
            conversation_history: Previous conversation turns
            
        Returns:
            Generated answer
            
        Raises:
            TimeoutError: If generation exceeds timeout
            RuntimeError: If Ollama generation fails
        """
        # Build prompt with context and history
        prompt = "You are a helpful library assessment assistant. Answer questions based on the provided data.\n\n"
        
        # Add conversation history
        if conversation_history:
            prompt += "Previous conversation:\n"
            for turn in conversation_history[-self.context_window:]:
                prompt += f"Q: {turn['question']}\nA: {turn['answer']}\n\n"
        
        # Add context
        prompt += f"Relevant data:\n{context}\n\n"
        
        # Add current question
        prompt += f"Question: {question}\n\n"
        prompt += "Answer (include specific data points and cite sources):"
        
        # Call Ollama with timeout
        try:
            # Note: signal.alarm only works on Unix systems
            # For Windows compatibility, we rely on Ollama's internal timeout
            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    "num_predict": 500,  # Limit response length
                }
            )
            return response['response']
        except Exception as e:
            error_msg = str(e).lower()
            if "timeout" in error_msg or "timed out" in error_msg:
                raise TimeoutError(f"Response generation timed out after {self.llm_timeout} seconds")
            else:
                raise RuntimeError(f"Ollama generation failed: {str(e)}")
    
    def query(
        self,
        question: str,
        session_id: Optional[str] = None,
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Answer natural language question about library data.
        
        Args:
            question: Natural language question
            session_id: Optional session ID for conversation context
            username: Optional username for provenance tracking
            
        Returns:
            Dict with keys: answer, confidence, citations, suggested_questions, processing_time_ms, error_type
            
        Raises:
            TimeoutError: If LLM generation times out
            ValueError: If context is too large
        """
        start_time = datetime.now()
        
        # Retrieve relevant documents
        docs = self.retrieve_relevant_docs(question)
        
        if not docs:
            return {
                "answer": "I couldn't find relevant data to answer your question. Available datasets can be viewed in the Data Upload page. Please upload data or rephrase your question.",
                "confidence": 0.0,
                "citations": [],
                "suggested_questions": [
                    "What datasets are currently available?",
                    "Can you help me understand the data format?",
                    "What types of questions can you answer?"
                ],
                "processing_time_ms": int((datetime.now() - start_time).total_seconds() * 1000),
                "error_type": "no_relevant_data"
            }
        
        # Build context from retrieved documents
        context = "\n\n".join([f"Source {i+1}: {doc['text']}" for i, doc in enumerate(docs)])
        
        # Get conversation history
        history = self.conversation_histories.get(session_id, [])
        
        # Check context size before generation
        is_within_limit, estimated_tokens = self._check_context_size(context, question, history)
        
        if not is_within_limit:
            return {
                "answer": f"Your question requires too much context ({estimated_tokens} tokens, limit is {self.max_context_tokens}). Please be more specific or break it into smaller questions. Try:\n\n- Asking about a specific dataset or time period\n- Focusing on one aspect of the data\n- Clearing conversation context if you're asking a new topic",
                "confidence": 0.0,
                "citations": [],
                "suggested_questions": [
                    "Can you summarize the main findings?",
                    "What are the key themes?",
                    "Show me statistics for [specific metric]"
                ],
                "processing_time_ms": int((datetime.now() - start_time).total_seconds() * 1000),
                "error_type": "context_too_large"
            }
        
        # Generate answer
        try:
            answer = self.generate_answer(question, context, history)
        except TimeoutError as e:
            return {
                "answer": f"Response generation timed out. Please try:\n\n- Asking a simpler question\n- Being more specific about what you want to know\n- Checking system resources (CPU/memory)\n- Clearing conversation context to reduce processing load",
                "confidence": 0.0,
                "citations": [],
                "suggested_questions": [
                    "What is the average [metric]?",
                    "How many responses mention [topic]?",
                    "Show me a summary of [dataset]"
                ],
                "processing_time_ms": int((datetime.now() - start_time).total_seconds() * 1000),
                "error_type": "llm_timeout"
            }
        except RuntimeError as e:
            # Handle Ollama connection failures gracefully
            return {
                "answer": f"Cannot connect to Ollama. Please ensure Ollama is running locally.\n\n**How to start Ollama:**\n\n1. Open a terminal\n2. Run: `ollama serve`\n3. In another terminal, verify the model is available: `ollama list`\n4. If the model is not listed, pull it: `ollama pull {self.model_name}`\n5. Try your question again\n\n**Error details:** {str(e)}",
                "confidence": 0.0,
                "citations": [],
                "suggested_questions": [
                    "Check Ollama status",
                    "Verify model availability",
                    "Review connection settings"
                ],
                "processing_time_ms": int((datetime.now() - start_time).total_seconds() * 1000),
                "error_type": "ollama_connection_failed"
            }
        
        # Redact PII from answer before returning (Requirement 6.5)
        answer, pii_counts = redact_pii(answer)
        
        # Extract citations from metadata
        citations = []
        dataset_ids = set()
        for i, doc in enumerate(docs):
            meta = doc['metadata']
            dataset_id = meta.get('dataset_id')
            if dataset_id:
                dataset_ids.add(int(dataset_id))
                citations.append({
                    "source_number": i + 1,
                    "dataset_id": dataset_id,
                    "dataset_type": meta.get('dataset_type'),
                    "date": meta.get('date')
                })
        
        # Update conversation history
        if session_id:
            if session_id not in self.conversation_histories:
                self.conversation_histories[session_id] = []
            self.conversation_histories[session_id].append({
                "question": question,
                "answer": answer
            })
        
        # Calculate confidence (simple heuristic based on retrieval distances)
        avg_distance = sum(doc.get('distance', 1.0) for doc in docs) / len(docs)
        confidence = max(0.0, min(1.0, 1.0 - avg_distance))
        
        # Generate suggested questions
        suggested_questions = self._generate_suggested_questions(question, docs)
        
        # Calculate processing time
        processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Log query
        execute_update(
            """
            INSERT INTO query_logs (question, answer, confidence, citations, session_id, processing_time_ms)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (question, answer, confidence, str(citations), session_id, processing_time_ms)
        )
        
        # Update provenance for accessed datasets
        if username:
            for dataset_id in dataset_ids:
                add_query_to_provenance(dataset_id, question, username)
        
        return {
            "answer": answer,
            "confidence": confidence,
            "citations": citations,
            "suggested_questions": suggested_questions,
            "processing_time_ms": processing_time_ms,
            "error_type": None
        }
    
    def _generate_suggested_questions(
        self,
        current_question: str,
        retrieved_docs: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate suggested follow-up questions.
        
        Args:
            current_question: Current question asked
            retrieved_docs: Documents retrieved for current question
            
        Returns:
            List of suggested questions
        """
        suggestions = []
        
        # Extract dataset types from retrieved docs
        dataset_types = set()
        for doc in retrieved_docs:
            dtype = doc['metadata'].get('dataset_type')
            if dtype:
                dataset_types.add(dtype)
        
        # Generate type-specific suggestions
        if 'survey' in dataset_types:
            suggestions.extend([
                "What are the main themes in the survey responses?",
                "What is the overall sentiment of the responses?",
                "Can you show me some example responses?"
            ])
        
        if 'usage' in dataset_types:
            suggestions.extend([
                "What are the usage trends over time?",
                "Which resources are most popular?",
                "How does usage compare across categories?"
            ])
        
        if 'circulation' in dataset_types:
            suggestions.extend([
                "What are the circulation patterns?",
                "Which material types are most checked out?",
                "How does circulation vary by patron type?"
            ])
        
        # Return up to 3 suggestions
        return suggestions[:3]
    
    def clear_conversation(self, session_id: str) -> None:
        """
        Clear conversation history for a session.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.conversation_histories:
            del self.conversation_histories[session_id]
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of conversation turns
        """
        return self.conversation_histories.get(session_id, [])


# Add missing import
from typing import Tuple
