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
4. PII redaction applied to retrieved documents (prevents LLM paraphrasing)
5. Context + conversation history assembled
6. Context size validated (max 4000 tokens)
7. Ollama LLM generates answer with citations
8. PII redaction applied to output (defense in depth)
9. Citations extracted from document metadata
10. Suggested follow-up questions generated
11. Answer + citations + suggestions returned

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
from modules.logging_service import get_logger, log_operation

logger = get_logger(__name__)


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
        
        # Use stable IDs based on dataset_id + source_row_id to prevent duplicates
        ids = [
            f"ds{meta.get('dataset_id', 'x')}_row{meta.get('source_row_id', i)}"
            for i, meta in enumerate(metadata_list)
        ]
        
        # Add to ChromaDB
        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadata_list,
            ids=ids
        )
    
    def _is_dataset_indexed(self, dataset_id: int) -> bool:
        """Check if a dataset already has documents in ChromaDB."""
        results = self.collection.get(
            where={"dataset_id": str(dataset_id)},
            limit=1
        )
        return len(results['ids']) > 0

    def index_dataset(self, dataset_id: int) -> int:
        """
        Index a dataset in ChromaDB for RAG retrieval.
        Skips indexing if the dataset is already indexed (deduplication).
        Tracks indexing status in database.
        
        Args:
            dataset_id: Dataset identifier
            
        Returns:
            Number of documents indexed (0 if already indexed)
        """
        # Skip if already indexed
        if self._is_dataset_indexed(dataset_id):
            return 0

        # Update status to in_progress
        execute_update(
            "UPDATE datasets SET indexing_status = 'in_progress' WHERE id = ?",
            (dataset_id,)
        )

        try:
            # Get dataset info
            datasets = execute_query(
                "SELECT dataset_type, column_names FROM datasets WHERE id = ?",
                (dataset_id,)
            )
            
            if not datasets:
                execute_update(
                    "UPDATE datasets SET indexing_status = 'failed', indexing_error = ? WHERE id = ?",
                    ("Dataset not found", dataset_id)
                )
                return 0
            
            dataset_type = datasets[0]['dataset_type']
            
            texts = []
            metadata_list = []

            # Get data to index
            if dataset_type == "survey":
                rows = execute_query(
                    """
                    SELECT id, response_date, question, response_text
                    FROM survey_responses
                    WHERE dataset_id = ? AND response_text IS NOT NULL AND response_text != ''
                    """,
                    (dataset_id,)
                )
                
                for row in rows:
                    parts = []
                    if row.get('question'):
                        parts.append(f"Survey question: {row['question']}")
                    if row.get('response_text'):
                        parts.append(f"Patron feedback response: {row['response_text']}")
                    if not parts:
                        continue
                    text = "\n".join(parts)
                    texts.append(text)
                    metadata_list.append({
                        "dataset_id": str(dataset_id),
                        "dataset_type": dataset_type,
                        "source_row_id": str(row['id']),
                        "date": str(row.get('response_date') or ""),
                        "question": str(row.get('question') or "")
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
                
                for row in rows:
                    metric = row.get('metric_name') or 'metric'
                    value = row.get('metric_value') or 0
                    date = row.get('date') or ''
                    category = row.get('category') or ''

                    if dataset_type == 'circulation':
                        # Make circulation text semantically rich for retrieval
                        text = f"Circulation checkout: {metric} material checked out on {date}"
                        if category:
                            text += f" by {category} patron"
                    else:
                        text = f"{metric}: {value} on {date}"
                        if category:
                            text += f" (Category: {category})"

                    texts.append(text)
                    metadata_list.append({
                        "dataset_id": str(dataset_id),
                        "dataset_type": dataset_type,
                        "source_row_id": str(row['id']),
                        "date": str(date),
                        "metric_name": str(metric)
                    })
            
            # Index in batches to avoid memory issues
            if texts:
                batch_size = 100
                for i in range(0, len(texts), batch_size):
                    self.index_documents(texts[i:i+batch_size], metadata_list[i:i+batch_size])
            
            # Update status to completed
            from datetime import datetime
            execute_update(
                "UPDATE datasets SET indexing_status = 'completed', indexed_at = ?, indexing_error = NULL WHERE id = ?",
                (datetime.now().isoformat(), dataset_id)
            )
            
            return len(texts)
            
        except Exception as e:
            # Update status to failed with error message
            error_msg = str(e)[:500]  # Limit error message length
            execute_update(
                "UPDATE datasets SET indexing_status = 'failed', indexing_error = ? WHERE id = ?",
                (error_msg, dataset_id)
            )
            logger.error(
                f"Failed to index dataset {dataset_id}: {error_msg}",
                extra={"operation": "index_dataset", "dataset_id": dataset_id, "error": error_msg}
            )
            raise
    
    def retrieve_relevant_docs(
        self,
        question: str,
        k: Optional[int] = None,
        distance_threshold: float = 1.45
    ) -> List[Dict[str, Any]]:
        """
        Retrieve top-k relevant documents from ChromaDB.
        
        Args:
            question: Natural language question
            k: Number of documents to retrieve (uses Settings.TOP_K_RETRIEVAL if not provided)
            distance_threshold: Max distance to consider a doc relevant (lower = stricter)
            
        Returns:
            List of retrieved documents with metadata, filtered by relevance
            Note: PII is redacted from document text before returning
        """
        if k is None:
            k = self.top_k
        
        # Check collection has documents
        count = self.collection.count()
        if count == 0:
            return []

        # Retrieve more candidates to ensure cross-dataset coverage
        n_candidates = min(k * 3, count)
        results = self.collection.query(
            query_texts=[question],
            n_results=n_candidates
        )
        
        # Format results, filtering by distance threshold and redacting PII
        documents = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                distance = results['distances'][0][i] if results['distances'] else None
                if distance is not None and distance > distance_threshold:
                    continue
                
                # Redact PII from retrieved document text before adding to context
                # This prevents LLM from paraphrasing PII in source data
                redacted_text, _ = redact_pii(doc)
                
                documents.append({
                    "text": redacted_text,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": distance
                })

        # Return top-k after filtering
        return documents[:k]
    
    def _estimate_token_count(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation).
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        # Rough approximation: 1 token ~= 4 characters
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
        
        Raises:
            ConnectionError: If Ollama process crashes or is unreachable
            TimeoutError: If generation exceeds timeout (30 seconds)
            RuntimeError: For other Ollama failures
        """
        # Build a natural, conversational system prompt
        system_prompt = (
            "You are a library assessment assistant. Answer questions about library data "
            "in a clear, conversational tone. Ground every answer in the provided data. "
            "Cite sources by number. Be concise."
        )

        prompt_parts = [system_prompt, ""]

        # Add conversation history for context continuity
        if conversation_history:
            prompt_parts.append("--- Previous conversation ---")
            for turn in conversation_history[-self.context_window:]:
                prompt_parts.append(f"User: {turn['question']}")
                prompt_parts.append(f"Assistant: {turn['answer']}")
            prompt_parts.append("")

        # Add retrieved data context
        prompt_parts.append("--- Relevant data from your library datasets ---")
        prompt_parts.append(context)
        prompt_parts.append("")

        # Rephrase the question naturally if it looks like a keyword search
        prompt_parts.append(f"User question: {question}")
        prompt_parts.append("")
        prompt_parts.append("Answer concisely using the data above. Cite source numbers.")

        prompt = "\n".join(prompt_parts)

        try:
            # Import httpx for timeout configuration (ollama uses httpx internally)
            import httpx
            
            # Create a custom client with 30-second timeout
            client = ollama.Client(
                host=self.ollama_url,
                timeout=httpx.Timeout(30.0, connect=5.0)  # 30s for generation, 5s for connection
            )
            
            response = client.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    "num_predict": 400,       # Enough for a good answer, faster than 600
                    "num_ctx": 4096,          # Cap context window - model default is 131k which is slow
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "top_k": 40,              # Limit vocabulary search per token
                    "repeat_penalty": 1.1,    # Reduce repetition without extra compute
                },
                keep_alive="5m"
            )
            return response['response']
        except (ConnectionError, ConnectionRefusedError, ConnectionResetError) as e:
            # Ollama process crashed or is not running
            logger.error(
                f"Ollama connection error: {str(e)}",
                extra={"operation": "generate_answer", "error": str(e)}
            )
            raise ConnectionError(f"Ollama process is not responding. Please restart Ollama: {str(e)}")
        except httpx.ConnectError as e:
            # Network-level connection error (httpx library)
            logger.error(
                f"Ollama network connection error: {str(e)}",
                extra={"operation": "generate_answer", "error": str(e)}
            )
            raise ConnectionError(f"Cannot connect to Ollama server. Please ensure Ollama is running: {str(e)}")
        except (httpx.ReadTimeout, httpx.TimeoutException) as e:
            # Request timeout
            logger.error(
                f"Ollama request timeout: {str(e)}",
                extra={"operation": "generate_answer", "error": str(e)}
            )
            raise TimeoutError(f"Ollama request timed out after 30 seconds")
        except Exception as e:
            error_msg = str(e).lower()
            # Check for timeout-related errors in message
            if "timeout" in error_msg or "timed out" in error_msg:
                logger.error(
                    f"Ollama timeout: {str(e)}",
                    extra={"operation": "generate_answer", "error": str(e)}
                )
                raise TimeoutError(f"Response generation timed out after 30 seconds")
            # Check for connection-related errors in message
            elif any(keyword in error_msg for keyword in ["connection", "refused", "reset", "unreachable", "broken pipe"]):
                logger.error(
                    f"Ollama connection error detected in message: {str(e)}",
                    extra={"operation": "generate_answer", "error": str(e)}
                )
                raise ConnectionError(f"Ollama connection lost. Please restart Ollama: {str(e)}")
            else:
                logger.error(
                    f"Ollama generation failed: {str(e)}",
                    extra={"operation": "generate_answer", "error": str(e)}
                )
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
        logger.info("RAG query started", extra={"operation": "rag_query", "user": username or "unknown"})
        
        # Retrieve relevant documents
        docs = self.retrieve_relevant_docs(question)
        
        if not docs:
            return {
                "answer": (
                    "I couldn't find anything in your uploaded datasets that relates to that question. "
                    "This could mean the data hasn't been uploaded yet, or the question uses terms "
                    "that don't appear in the data.\n\n"
                    "Try rephrasing - for example, instead of 'patron satisfaction' try 'how do patrons feel' "
                    "or 'what do survey responses say'. You can also check what's available in the Data Upload page."
                ),
                "confidence": 0.0,
                "citations": [],
                "suggested_questions": [
                    "What data do I have available?",
                    "What do patrons say about library services?",
                    "Show me a summary of usage statistics",
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
        except ConnectionError as e:
            # Handle Ollama connection failures gracefully (crashes, not running, etc.)
            return {
                "answer": f"**Ollama Connection Error**\n\nThe Ollama service is not responding. This usually means Ollama has crashed or is not running.\n\n**To fix this:**\n\n1. Open a terminal\n2. Start Ollama: `ollama serve`\n3. In another terminal, verify the model is available: `ollama list`\n4. If the model '{self.model_name}' is not listed, pull it: `ollama pull {self.model_name}`\n5. Try your question again\n\n**Error details:** {str(e)}",
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
        except TimeoutError as e:
            return {
                "answer": f"**Request Timeout**\n\nThe response generation timed out after 30 seconds. Please try:\n\n- Asking a simpler question\n- Being more specific about what you want to know\n- Checking system resources (CPU/memory)\n- Clearing conversation context to reduce processing load\n\n**Error details:** {str(e)}",
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
            # Handle other Ollama failures
            return {
                "answer": f"**Ollama Error**\n\nAn error occurred while generating the response.\n\n**Error details:** {str(e)}\n\nPlease check:\n- Ollama is running: `ollama serve`\n- Model is available: `ollama list`\n- System resources (CPU/memory)",
                "confidence": 0.0,
                "citations": [],
                "suggested_questions": [
                    "Check Ollama status",
                    "Verify model availability",
                    "Review system resources"
                ],
                "processing_time_ms": int((datetime.now() - start_time).total_seconds() * 1000),
                "error_type": "ollama_error"
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
        
        logger.info(
            "RAG query completed in %dms (confidence=%.2f)",
            processing_time_ms, confidence,
            extra={"operation": "rag_query", "duration_ms": processing_time_ms, "user": username or "unknown"},
        )
        
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
        """Generate contextual follow-up questions based on what was just asked."""
        suggestions = []
        q = current_question.lower()

        dataset_types = {doc['metadata'].get('dataset_type') for doc in retrieved_docs}

        # Context-aware follow-ups based on the question content
        if any(w in q for w in ['theme', 'topic', 'about', 'say', 'mention', 'feedback']):
            suggestions.append("Which theme has the most negative sentiment?")
            suggestions.append("Can you show me some example quotes from the top theme?")

        if any(w in q for w in ['trend', 'over time', 'change', 'increase', 'decrease', 'grow']):
            suggestions.append("What month had the highest usage?")
            suggestions.append("Is the trend continuing or leveling off?")

        if any(w in q for w in ['satisfaction', 'happy', 'rating', 'score', 'feel']):
            suggestions.append("What are patrons most dissatisfied with?")
            suggestions.append("How does satisfaction compare across different questions?")

        if any(w in q for w in ['circulation', 'checkout', 'borrow', 'material', 'book']):
            suggestions.append("Which patron type checks out the most materials?")
            suggestions.append("What material types are most popular?")

        if any(w in q for w in ['usage', 'visit', 'traffic', 'popular', 'busy']):
            suggestions.append("Which days or periods have the highest usage?")
            suggestions.append("How does digital resource usage compare to physical visits?")

        # Dataset-type fallbacks if no question-specific suggestions matched
        if not suggestions:
            if 'survey' in dataset_types:
                suggestions.extend([
                    "What are the main themes in the survey responses?",
                    "What percentage of responses are positive?",
                ])
            if 'usage' in dataset_types:
                suggestions.extend([
                    "What are the usage trends over time?",
                    "Which metrics are most correlated?",
                ])
            if 'circulation' in dataset_types:
                suggestions.extend([
                    "Which material types are checked out most often?",
                    "How does circulation vary by patron type?",
                ])

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
