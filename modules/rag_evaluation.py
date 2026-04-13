"""
RAG Retrieval Quality Evaluation Module

This module implements evaluation metrics for assessing the quality of RAG
(Retrieval-Augmented Generation) retrieval performance in the Library Assessment
Decision Support System.

Key Features:
- Precision@k: Measures relevance of top-k retrieved documents
- Recall@k: Measures coverage of relevant documents in top-k results
- Mean Reciprocal Rank (MRR): Measures ranking quality of first relevant document
- Batch evaluation of test query sets
- Synthetic test query generation from datasets
- Database storage of evaluation results
- Historical evaluation tracking

Evaluation Metrics:
1. Precision@k = (# relevant docs in top k) / k
   - Measures what fraction of retrieved documents are relevant
   - Range: [0, 1], higher is better
   - Example: If 3 out of 5 retrieved docs are relevant, P@5 = 0.6

2. Recall@k = (# relevant docs in top k) / (total # relevant docs)
   - Measures what fraction of all relevant documents were retrieved
   - Range: [0, 1], higher is better
   - Example: If 3 out of 10 relevant docs are in top 5, R@5 = 0.3

3. MRR = 1 / (rank of first relevant document)
   - Measures how quickly users find a relevant document
   - Range: [0, 1], higher is better
   - Returns 0 if no relevant documents found
   - Example: First relevant doc at rank 3 → MRR = 1/3 = 0.333

Database Schema:
- rag_evaluations: Stores evaluation results with metrics and metadata

Module Classes:
- RAGEvaluator: Main evaluation engine class

Key Methods:
- calculate_precision_at_k(): Compute precision@k metric
- calculate_recall_at_k(): Compute recall@k metric
- calculate_mrr(): Compute Mean Reciprocal Rank
- evaluate_query_set(): Batch evaluation of test queries
- generate_synthetic_test_queries(): Create test queries from dataset
- store_evaluation_results(): Persist results to database
- get_evaluation_history(): Retrieve historical evaluations

Usage Example:
    from modules.rag_query import RAGQuery
    from modules.rag_evaluation import RAGEvaluator
    
    # Initialize RAG and evaluator
    rag = RAGQuery()
    evaluator = RAGEvaluator(rag)
    
    # Generate synthetic test queries
    test_queries = evaluator.generate_synthetic_test_queries(
        dataset_id=1,
        n_queries=10
    )
    
    # Evaluate retrieval quality
    results = evaluator.evaluate_query_set(test_queries)
    print(f"Average Precision@5: {results['avg_precision_at_5']:.3f}")
    print(f"Average Recall@5: {results['avg_recall_at_5']:.3f}")
    print(f"Average MRR: {results['avg_mrr']:.3f}")
    
    # Store results
    eval_id = evaluator.store_evaluation_results(results, "test_set_v1")
    
    # View history
    history = evaluator.get_evaluation_history(limit=10)
    for eval_record in history:
        print(f"{eval_record['test_set_name']}: P@5={eval_record['avg_precision_at_5']:.3f}")

Requirements Implemented:
- RAG retrieval quality measurement
- Precision@k calculation
- Recall@k calculation
- MRR calculation
- Batch evaluation support
- Synthetic test query generation
- Evaluation result persistence
- Historical tracking

Author: FERPA-Compliant RAG DSS Team
"""

from typing import List, Dict, Any, Set, Optional, Tuple
from datetime import datetime
import random
from modules.database import execute_query, execute_update, get_db_connection
from modules.logging_service import get_logger

logger = get_logger(__name__)


class RAGEvaluator:
    """Evaluates retrieval quality for RAG system."""
    
    def __init__(self, rag_query_instance):
        """
        Initialize evaluator with RAG query instance.
        
        Args:
            rag_query_instance: Instance of RAGQuery class to evaluate
        """
        self.rag = rag_query_instance
        self._ensure_evaluation_table()
    
    def _ensure_evaluation_table(self) -> None:
        """Create rag_evaluations table if it doesn't exist."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rag_evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_set_name TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    n_queries INTEGER,
                    avg_precision_at_5 REAL,
                    avg_recall_at_5 REAL,
                    avg_mrr REAL,
                    query_details TEXT,
                    notes TEXT
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_rag_evaluations_timestamp 
                ON rag_evaluations(timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_rag_evaluations_test_set 
                ON rag_evaluations(test_set_name)
            """)
    
    def calculate_precision_at_k(
        self,
        query: str,
        relevant_doc_ids: Set[str],
        k: int = 5
    ) -> float:
        """
        Calculate precision@k for a query.
        
        Precision@k measures what fraction of the top-k retrieved documents
        are relevant to the query.
        
        Formula: Precision@k = (# relevant docs in top k) / k
        
        Args:
            query: Natural language query string
            relevant_doc_ids: Set of document IDs that are relevant to the query
            k: Number of top documents to consider (default: 5)
            
        Returns:
            Precision@k score in range [0.0, 1.0]
            Returns 0.0 if k=0 or no documents retrieved
            
        Example:
            >>> relevant = {'doc1', 'doc3', 'doc5'}
            >>> precision = evaluator.calculate_precision_at_k(
            ...     "What are usage trends?",
            ...     relevant,
            ...     k=5
            ... )
            >>> # If retrieved docs are ['doc1', 'doc2', 'doc3', 'doc4', 'doc5']
            >>> # Then 2 out of 5 are relevant → precision = 0.4
        """
        if k <= 0:
            return 0.0
        
        # Retrieve top-k documents
        retrieved_docs = self.rag.retrieve_relevant_docs(query, k=k)
        
        if not retrieved_docs:
            return 0.0
        
        # Extract document IDs from retrieved results
        retrieved_ids = set()
        for doc in retrieved_docs:
            # Document ID format: "ds{dataset_id}_row{source_row_id}"
            metadata = doc.get('metadata', {})
            dataset_id = metadata.get('dataset_id', '')
            source_row_id = metadata.get('source_row_id', '')
            if dataset_id and source_row_id:
                doc_id = f"ds{dataset_id}_row{source_row_id}"
                retrieved_ids.add(doc_id)
        
        # Count relevant documents in top-k
        relevant_in_top_k = len(retrieved_ids.intersection(relevant_doc_ids))
        
        # Calculate precision@k
        precision = relevant_in_top_k / k
        
        return precision
    
    def calculate_recall_at_k(
        self,
        query: str,
        relevant_doc_ids: Set[str],
        k: int = 5
    ) -> float:
        """
        Calculate recall@k for a query.
        
        Recall@k measures what fraction of all relevant documents are found
        in the top-k retrieved documents.
        
        Formula: Recall@k = (# relevant docs in top k) / (total # relevant docs)
        
        Args:
            query: Natural language query string
            relevant_doc_ids: Set of document IDs that are relevant to the query
            k: Number of top documents to consider (default: 5)
            
        Returns:
            Recall@k score in range [0.0, 1.0]
            Returns 0.0 if no relevant documents exist
            Returns 1.0 if all relevant documents are in top-k
            
        Example:
            >>> relevant = {'doc1', 'doc3', 'doc5', 'doc7', 'doc9'}  # 5 relevant docs
            >>> recall = evaluator.calculate_recall_at_k(
            ...     "What are usage trends?",
            ...     relevant,
            ...     k=5
            ... )
            >>> # If retrieved docs contain ['doc1', 'doc3'] (2 relevant)
            >>> # Then recall = 2/5 = 0.4
        """
        if not relevant_doc_ids:
            return 0.0
        
        # Retrieve top-k documents
        retrieved_docs = self.rag.retrieve_relevant_docs(query, k=k)
        
        if not retrieved_docs:
            return 0.0
        
        # Extract document IDs from retrieved results
        retrieved_ids = set()
        for doc in retrieved_docs:
            metadata = doc.get('metadata', {})
            dataset_id = metadata.get('dataset_id', '')
            source_row_id = metadata.get('source_row_id', '')
            if dataset_id and source_row_id:
                doc_id = f"ds{dataset_id}_row{source_row_id}"
                retrieved_ids.add(doc_id)
        
        # Count relevant documents in top-k
        relevant_in_top_k = len(retrieved_ids.intersection(relevant_doc_ids))
        
        # Calculate recall@k
        recall = relevant_in_top_k / len(relevant_doc_ids)
        
        return recall
    
    def calculate_mrr(
        self,
        query: str,
        relevant_doc_ids: Set[str]
    ) -> float:
        """
        Calculate Mean Reciprocal Rank (MRR) for a query.
        
        MRR measures how quickly users find a relevant document by computing
        the reciprocal of the rank of the first relevant document.
        
        Formula: MRR = 1 / (rank of first relevant document)
        Returns 0 if no relevant documents are found.
        
        Args:
            query: Natural language query string
            relevant_doc_ids: Set of document IDs that are relevant to the query
            
        Returns:
            MRR score in range [0.0, 1.0]
            Returns 1.0 if first document is relevant
            Returns 0.5 if second document is relevant
            Returns 0.0 if no relevant documents found
            
        Example:
            >>> relevant = {'doc3', 'doc5'}
            >>> mrr = evaluator.calculate_mrr(
            ...     "What are usage trends?",
            ...     relevant
            ... )
            >>> # If retrieved docs are ['doc1', 'doc2', 'doc3', ...]
            >>> # First relevant doc is at rank 3 → MRR = 1/3 = 0.333
        """
        if not relevant_doc_ids:
            return 0.0
        
        # Retrieve documents (use larger k to find first relevant)
        retrieved_docs = self.rag.retrieve_relevant_docs(query, k=20)
        
        if not retrieved_docs:
            return 0.0
        
        # Find rank of first relevant document
        for rank, doc in enumerate(retrieved_docs, start=1):
            metadata = doc.get('metadata', {})
            dataset_id = metadata.get('dataset_id', '')
            source_row_id = metadata.get('source_row_id', '')
            if dataset_id and source_row_id:
                doc_id = f"ds{dataset_id}_row{source_row_id}"
                if doc_id in relevant_doc_ids:
                    # Found first relevant document
                    return 1.0 / rank
        
        # No relevant documents found
        return 0.0
    
    def evaluate_query_set(
        self,
        test_queries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate a set of test queries with ground truth.
        
        Args:
            test_queries: List of dicts with keys:
                - 'query': Natural language query string
                - 'relevant_doc_ids': Set of relevant document IDs
                
        Returns:
            Dict with evaluation results:
                - 'n_queries': Number of queries evaluated
                - 'avg_precision_at_5': Average precision@5 across queries
                - 'avg_recall_at_5': Average recall@5 across queries
                - 'avg_mrr': Average MRR across queries
                - 'query_results': List of per-query results
                
        Example:
            >>> test_queries = [
            ...     {
            ...         'query': 'What are usage trends?',
            ...         'relevant_doc_ids': {'ds1_row5', 'ds1_row10'}
            ...     },
            ...     {
            ...         'query': 'What do patrons say?',
            ...         'relevant_doc_ids': {'ds2_row3', 'ds2_row7'}
            ...     }
            ... ]
            >>> results = evaluator.evaluate_query_set(test_queries)
            >>> print(f"Average Precision@5: {results['avg_precision_at_5']:.3f}")
        """
        if not test_queries:
            return {
                'n_queries': 0,
                'avg_precision_at_5': 0.0,
                'avg_recall_at_5': 0.0,
                'avg_mrr': 0.0,
                'query_results': []
            }
        
        query_results = []
        total_precision = 0.0
        total_recall = 0.0
        total_mrr = 0.0
        
        for test_query in test_queries:
            query = test_query['query']
            relevant_doc_ids = test_query['relevant_doc_ids']
            
            # Calculate metrics for this query
            precision = self.calculate_precision_at_k(query, relevant_doc_ids, k=5)
            recall = self.calculate_recall_at_k(query, relevant_doc_ids, k=5)
            mrr = self.calculate_mrr(query, relevant_doc_ids)
            
            query_results.append({
                'query': query,
                'precision_at_5': precision,
                'recall_at_5': recall,
                'mrr': mrr
            })
            
            total_precision += precision
            total_recall += recall
            total_mrr += mrr
        
        n_queries = len(test_queries)
        
        return {
            'n_queries': n_queries,
            'avg_precision_at_5': total_precision / n_queries,
            'avg_recall_at_5': total_recall / n_queries,
            'avg_mrr': total_mrr / n_queries,
            'query_results': query_results
        }
    
    def generate_synthetic_test_queries(
        self,
        dataset_id: int,
        n_queries: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Generate synthetic test queries from dataset.
        
        Creates test queries by sampling documents from the dataset and using
        them as ground truth relevant documents. Generates natural language
        queries based on document content.
        
        Args:
            dataset_id: Dataset identifier to generate queries from
            n_queries: Number of test queries to generate (default: 10)
            
        Returns:
            List of test query dicts with keys:
                - 'query': Generated natural language query
                - 'relevant_doc_ids': Set of relevant document IDs
                
        Example:
            >>> test_queries = evaluator.generate_synthetic_test_queries(
            ...     dataset_id=1,
            ...     n_queries=5
            ... )
            >>> for tq in test_queries:
            ...     print(f"Query: {tq['query']}")
            ...     print(f"Relevant docs: {len(tq['relevant_doc_ids'])}")
        """
        # Get dataset type
        datasets = execute_query(
            "SELECT dataset_type FROM datasets WHERE id = ?",
            (dataset_id,)
        )
        
        if not datasets:
            logger.warning(f"Dataset {dataset_id} not found")
            return []
        
        dataset_type = datasets[0]['dataset_type']
        
        test_queries = []
        
        if dataset_type == 'survey':
            # Sample survey responses
            rows = execute_query(
                """
                SELECT id, question, response_text
                FROM survey_responses
                WHERE dataset_id = ? AND response_text IS NOT NULL
                ORDER BY RANDOM()
                LIMIT ?
                """,
                (dataset_id, n_queries)
            )
            
            for row in rows:
                # Generate query from question
                question = row.get('question', '')
                if question:
                    query = f"What do respondents say about {question.lower()}?"
                else:
                    query = "What are the main themes in survey responses?"
                
                # Mark this document as relevant
                doc_id = f"ds{dataset_id}_row{row['id']}"
                
                test_queries.append({
                    'query': query,
                    'relevant_doc_ids': {doc_id}
                })
        
        elif dataset_type in ['usage', 'circulation']:
            # Sample usage/circulation records
            rows = execute_query(
                """
                SELECT id, metric_name, category
                FROM usage_statistics
                WHERE dataset_id = ?
                ORDER BY RANDOM()
                LIMIT ?
                """,
                (dataset_id, n_queries)
            )
            
            for row in rows:
                metric_name = row.get('metric_name', 'metric')
                category = row.get('category', '')
                
                # Generate query based on metric
                if dataset_type == 'circulation':
                    if category:
                        query = f"What are the circulation patterns for {category} patrons?"
                    else:
                        query = f"What are the trends for {metric_name}?"
                else:
                    query = f"What are the usage statistics for {metric_name}?"
                
                # Mark this document as relevant
                doc_id = f"ds{dataset_id}_row{row['id']}"
                
                test_queries.append({
                    'query': query,
                    'relevant_doc_ids': {doc_id}
                })
        
        return test_queries
    
    def store_evaluation_results(
        self,
        results: Dict[str, Any],
        test_set_name: str,
        notes: Optional[str] = None
    ) -> int:
        """
        Store evaluation results in database.
        
        Args:
            results: Evaluation results dict from evaluate_query_set()
            test_set_name: Name/identifier for this test set
            notes: Optional notes about this evaluation
            
        Returns:
            Evaluation ID (database row ID)
            
        Example:
            >>> results = evaluator.evaluate_query_set(test_queries)
            >>> eval_id = evaluator.store_evaluation_results(
            ...     results,
            ...     "baseline_v1",
            ...     notes="Initial baseline evaluation"
            ... )
            >>> print(f"Stored evaluation with ID: {eval_id}")
        """
        import json
        
        eval_id = execute_update(
            """
            INSERT INTO rag_evaluations (
                test_set_name,
                n_queries,
                avg_precision_at_5,
                avg_recall_at_5,
                avg_mrr,
                query_details,
                notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                test_set_name,
                results['n_queries'],
                results['avg_precision_at_5'],
                results['avg_recall_at_5'],
                results['avg_mrr'],
                json.dumps(results.get('query_results', [])),
                notes
            )
        )
        
        logger.info(
            f"Stored RAG evaluation results: {test_set_name} "
            f"(P@5={results['avg_precision_at_5']:.3f}, "
            f"R@5={results['avg_recall_at_5']:.3f}, "
            f"MRR={results['avg_mrr']:.3f})",
            extra={
                "operation": "store_evaluation_results",
                "test_set_name": test_set_name,
                "eval_id": eval_id
            }
        )
        
        return eval_id
    
    def get_evaluation_history(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve historical evaluation results.
        
        Args:
            limit: Maximum number of evaluations to retrieve (default: 10)
            
        Returns:
            List of evaluation result dicts with keys:
                - 'id': Evaluation ID
                - 'test_set_name': Test set name
                - 'timestamp': Evaluation timestamp
                - 'n_queries': Number of queries evaluated
                - 'avg_precision_at_5': Average precision@5
                - 'avg_recall_at_5': Average recall@5
                - 'avg_mrr': Average MRR
                - 'notes': Optional notes
                
        Example:
            >>> history = evaluator.get_evaluation_history(limit=5)
            >>> for eval_record in history:
            ...     print(f"{eval_record['test_set_name']}: "
            ...           f"P@5={eval_record['avg_precision_at_5']:.3f}")
        """
        evaluations = execute_query(
            """
            SELECT 
                id,
                test_set_name,
                timestamp,
                n_queries,
                avg_precision_at_5,
                avg_recall_at_5,
                avg_mrr,
                notes
            FROM rag_evaluations
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,)
        )
        
        return evaluations
