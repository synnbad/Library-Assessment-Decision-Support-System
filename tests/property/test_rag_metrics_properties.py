"""
Property-Based Tests for RAG Retrieval Metrics

Feature: RAG Retrieval Quality Evaluation
Properties 2-4: Metric Calculation Correctness

Tests verify that RAG evaluation metrics (Precision@k, Recall@k, MRR)
are calculated correctly according to their mathematical definitions
across a wide range of inputs including edge cases.

Validates:
- Property 2: Precision@k calculation correctness
- Property 3: Recall@k calculation correctness  
- Property 4: MRR calculation correctness

Edge Cases Tested:
- k=0 (empty retrieval)
- Empty relevant document sets
- All documents relevant
- No documents relevant
- Single document cases
- Large k values
- Partial overlaps
"""

from hypothesis import given, settings, strategies as st, assume
from modules.rag_evaluation import RAGEvaluator


# ============================================================================
# Mock RAG Query for Testing
# ============================================================================

class MockRAGQuery:
    """Mock RAG query instance for testing evaluation metrics."""
    
    def __init__(self):
        """Initialize mock with empty document store."""
        self.documents = []
    
    def set_documents(self, doc_ids: list):
        """
        Set the documents that will be returned by retrieve_relevant_docs.
        
        Args:
            doc_ids: List of document IDs in retrieval order
        """
        self.documents = doc_ids
    
    def retrieve_relevant_docs(self, query: str, k: int = 5):
        """
        Mock retrieval that returns pre-configured documents.
        
        Args:
            query: Query string (ignored in mock)
            k: Number of documents to return
            
        Returns:
            List of mock document dicts with metadata
        """
        # Return top-k documents from configured list
        results = []
        for doc_id in self.documents[:k]:
            # Parse doc_id format: "ds{dataset_id}_row{source_row_id}"
            parts = doc_id.replace('ds', '').split('_row')
            if len(parts) == 2:
                dataset_id = parts[0]
                source_row_id = parts[1]
            else:
                dataset_id = '1'
                source_row_id = doc_id
            
            results.append({
                'text': f'Mock document {doc_id}',
                'metadata': {
                    'dataset_id': dataset_id,
                    'source_row_id': source_row_id
                }
            })
        
        return results


# ============================================================================
# Hypothesis Strategies
# ============================================================================

@st.composite
def doc_id_set(draw, min_size=0, max_size=20):
    """Generate a set of document IDs."""
    n_docs = draw(st.integers(min_value=min_size, max_value=max_size))
    doc_ids = set()
    for i in range(n_docs):
        dataset_id = draw(st.integers(min_value=1, max_value=5))
        row_id = draw(st.integers(min_value=1, max_value=100))
        doc_ids.add(f"ds{dataset_id}_row{row_id}")
    return doc_ids


@st.composite
def retrieval_scenario(draw):
    """
    Generate a retrieval scenario with retrieved and relevant documents.
    
    Returns:
        Tuple of (retrieved_doc_ids, relevant_doc_ids, k)
    """
    # Generate k value
    k = draw(st.integers(min_value=1, max_value=20))
    
    # Generate retrieved documents (at least k documents)
    n_retrieved = draw(st.integers(min_value=k, max_value=k + 10))
    retrieved_ids = []
    for i in range(n_retrieved):
        dataset_id = draw(st.integers(min_value=1, max_value=5))
        row_id = draw(st.integers(min_value=1, max_value=100))
        retrieved_ids.append(f"ds{dataset_id}_row{row_id}")
    
    # Generate relevant documents (subset may overlap with retrieved)
    n_relevant = draw(st.integers(min_value=1, max_value=15))
    relevant_ids = set()
    
    # Ensure some overlap for interesting test cases
    overlap_size = draw(st.integers(min_value=0, max_value=min(k, n_relevant)))
    for i in range(overlap_size):
        if i < len(retrieved_ids):
            relevant_ids.add(retrieved_ids[i])
    
    # Add additional relevant documents not in retrieved set
    while len(relevant_ids) < n_relevant:
        dataset_id = draw(st.integers(min_value=1, max_value=5))
        row_id = draw(st.integers(min_value=1, max_value=100))
        relevant_ids.add(f"ds{dataset_id}_row{row_id}")
    
    return retrieved_ids, relevant_ids, k


# ============================================================================
# Property 2: Precision@k Calculation Correctness
# ============================================================================

@settings(max_examples=100)
@given(scenario=retrieval_scenario())
def test_precision_at_k_correctness(scenario):
    """
    Property 2: Precision@k calculation correctness
    
    Verify that precision@k is calculated correctly according to the formula:
    Precision@k = (# relevant docs in top k) / k
    
    Test across 100 random scenarios with varying k, retrieved docs, and relevant docs.
    """
    retrieved_ids, relevant_ids, k = scenario
    
    # Setup mock RAG
    mock_rag = MockRAGQuery()
    mock_rag.set_documents(retrieved_ids)
    
    # Create evaluator
    evaluator = RAGEvaluator(mock_rag)
    
    # Calculate precision@k
    precision = evaluator.calculate_precision_at_k(
        query="test query",
        relevant_doc_ids=relevant_ids,
        k=k
    )
    
    # Manually calculate expected precision
    top_k_retrieved = set(retrieved_ids[:k])
    relevant_in_top_k = len(top_k_retrieved.intersection(relevant_ids))
    expected_precision = relevant_in_top_k / k
    
    # Verify precision matches expected value
    assert abs(precision - expected_precision) < 1e-9, \
        f"Precision@{k} incorrect: got {precision}, expected {expected_precision}"
    
    # Verify precision is in valid range [0, 1]
    assert 0.0 <= precision <= 1.0, \
        f"Precision@{k} out of range: {precision}"


@settings(max_examples=100)
@given(
    retrieved_ids=st.lists(
        st.text(min_size=5, max_size=20, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            blacklist_characters='_'
        )).map(lambda x: f"ds1_row{x}"),
        min_size=1,
        max_size=20,
        unique=True
    ),
    k=st.integers(min_value=1, max_value=20)
)
def test_precision_at_k_all_relevant(retrieved_ids, k):
    """
    Property 2: Precision@k when all retrieved documents are relevant.
    
    When all top-k documents are relevant, precision@k should equal 1.0.
    """
    assume(len(retrieved_ids) >= k)
    
    # All retrieved documents are relevant
    relevant_ids = set(retrieved_ids)
    
    # Setup mock RAG
    mock_rag = MockRAGQuery()
    mock_rag.set_documents(retrieved_ids)
    
    # Create evaluator
    evaluator = RAGEvaluator(mock_rag)
    
    # Calculate precision@k
    precision = evaluator.calculate_precision_at_k(
        query="test query",
        relevant_doc_ids=relevant_ids,
        k=k
    )
    
    # Should be 1.0 since all retrieved docs are relevant
    assert abs(precision - 1.0) < 1e-9, \
        f"Precision@{k} should be 1.0 when all docs relevant, got {precision}"


@settings(max_examples=100)
@given(
    retrieved_ids=st.lists(
        st.text(min_size=5, max_size=20, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            blacklist_characters='_'
        )).map(lambda x: f"ds1_row{x}"),
        min_size=1,
        max_size=20,
        unique=True
    ),
    k=st.integers(min_value=1, max_value=20)
)
def test_precision_at_k_none_relevant(retrieved_ids, k):
    """
    Property 2: Precision@k when no retrieved documents are relevant.
    
    When no top-k documents are relevant, precision@k should equal 0.0.
    """
    assume(len(retrieved_ids) >= k)
    
    # No retrieved documents are relevant (disjoint sets)
    relevant_ids = {f"ds99_row{i}" for i in range(10)}
    
    # Setup mock RAG
    mock_rag = MockRAGQuery()
    mock_rag.set_documents(retrieved_ids)
    
    # Create evaluator
    evaluator = RAGEvaluator(mock_rag)
    
    # Calculate precision@k
    precision = evaluator.calculate_precision_at_k(
        query="test query",
        relevant_doc_ids=relevant_ids,
        k=k
    )
    
    # Should be 0.0 since no retrieved docs are relevant
    assert abs(precision - 0.0) < 1e-9, \
        f"Precision@{k} should be 0.0 when no docs relevant, got {precision}"


def test_precision_at_k_edge_case_k_zero():
    """
    Property 2: Precision@k edge case when k=0.
    
    When k=0, precision should be 0.0 (no documents retrieved).
    """
    mock_rag = MockRAGQuery()
    mock_rag.set_documents(['ds1_row1', 'ds1_row2'])
    
    evaluator = RAGEvaluator(mock_rag)
    
    precision = evaluator.calculate_precision_at_k(
        query="test query",
        relevant_doc_ids={'ds1_row1'},
        k=0
    )
    
    assert precision == 0.0, \
        f"Precision@0 should be 0.0, got {precision}"


def test_precision_at_k_edge_case_empty_relevant():
    """
    Property 2: Precision@k edge case when relevant set is empty.
    
    When no documents are relevant, precision should be 0.0.
    """
    mock_rag = MockRAGQuery()
    mock_rag.set_documents(['ds1_row1', 'ds1_row2', 'ds1_row3'])
    
    evaluator = RAGEvaluator(mock_rag)
    
    precision = evaluator.calculate_precision_at_k(
        query="test query",
        relevant_doc_ids=set(),  # Empty relevant set
        k=3
    )
    
    assert precision == 0.0, \
        f"Precision@3 should be 0.0 when relevant set empty, got {precision}"


# ============================================================================
# Property 3: Recall@k Calculation Correctness
# ============================================================================

@settings(max_examples=100)
@given(scenario=retrieval_scenario())
def test_recall_at_k_correctness(scenario):
    """
    Property 3: Recall@k calculation correctness
    
    Verify that recall@k is calculated correctly according to the formula:
    Recall@k = (# relevant docs in top k) / (total # relevant docs)
    
    Test across 100 random scenarios with varying k, retrieved docs, and relevant docs.
    """
    retrieved_ids, relevant_ids, k = scenario
    
    # Setup mock RAG
    mock_rag = MockRAGQuery()
    mock_rag.set_documents(retrieved_ids)
    
    # Create evaluator
    evaluator = RAGEvaluator(mock_rag)
    
    # Calculate recall@k
    recall = evaluator.calculate_recall_at_k(
        query="test query",
        relevant_doc_ids=relevant_ids,
        k=k
    )
    
    # Manually calculate expected recall
    top_k_retrieved = set(retrieved_ids[:k])
    relevant_in_top_k = len(top_k_retrieved.intersection(relevant_ids))
    expected_recall = relevant_in_top_k / len(relevant_ids)
    
    # Verify recall matches expected value
    assert abs(recall - expected_recall) < 1e-9, \
        f"Recall@{k} incorrect: got {recall}, expected {expected_recall}"
    
    # Verify recall is in valid range [0, 1]
    assert 0.0 <= recall <= 1.0, \
        f"Recall@{k} out of range: {recall}"


@settings(max_examples=100)
@given(
    n_docs=st.integers(min_value=1, max_value=20),
    k=st.integers(min_value=1, max_value=20)
)
def test_recall_at_k_all_relevant_retrieved(n_docs, k):
    """
    Property 3: Recall@k when all relevant documents are in top-k.
    
    When all relevant documents are retrieved in top-k, recall@k should equal 1.0.
    """
    assume(k >= n_docs)
    
    # Create documents
    doc_ids = [f"ds1_row{i}" for i in range(n_docs)]
    relevant_ids = set(doc_ids)
    
    # Setup mock RAG (all relevant docs at top)
    mock_rag = MockRAGQuery()
    mock_rag.set_documents(doc_ids + [f"ds2_row{i}" for i in range(10)])
    
    # Create evaluator
    evaluator = RAGEvaluator(mock_rag)
    
    # Calculate recall@k
    recall = evaluator.calculate_recall_at_k(
        query="test query",
        relevant_doc_ids=relevant_ids,
        k=k
    )
    
    # Should be 1.0 since all relevant docs are in top-k
    assert abs(recall - 1.0) < 1e-9, \
        f"Recall@{k} should be 1.0 when all relevant docs retrieved, got {recall}"


@settings(max_examples=100)
@given(
    n_relevant=st.integers(min_value=1, max_value=20),
    k=st.integers(min_value=1, max_value=20)
)
def test_recall_at_k_none_relevant_retrieved(n_relevant, k):
    """
    Property 3: Recall@k when no relevant documents are in top-k.
    
    When no relevant documents are retrieved in top-k, recall@k should equal 0.0.
    """
    # Create disjoint sets
    retrieved_ids = [f"ds1_row{i}" for i in range(k + 5)]
    relevant_ids = {f"ds99_row{i}" for i in range(n_relevant)}
    
    # Setup mock RAG
    mock_rag = MockRAGQuery()
    mock_rag.set_documents(retrieved_ids)
    
    # Create evaluator
    evaluator = RAGEvaluator(mock_rag)
    
    # Calculate recall@k
    recall = evaluator.calculate_recall_at_k(
        query="test query",
        relevant_doc_ids=relevant_ids,
        k=k
    )
    
    # Should be 0.0 since no relevant docs are retrieved
    assert abs(recall - 0.0) < 1e-9, \
        f"Recall@{k} should be 0.0 when no relevant docs retrieved, got {recall}"


def test_recall_at_k_edge_case_empty_relevant():
    """
    Property 3: Recall@k edge case when relevant set is empty.
    
    When no documents are relevant, recall should be 0.0.
    """
    mock_rag = MockRAGQuery()
    mock_rag.set_documents(['ds1_row1', 'ds1_row2', 'ds1_row3'])
    
    evaluator = RAGEvaluator(mock_rag)
    
    recall = evaluator.calculate_recall_at_k(
        query="test query",
        relevant_doc_ids=set(),  # Empty relevant set
        k=3
    )
    
    assert recall == 0.0, \
        f"Recall@3 should be 0.0 when relevant set empty, got {recall}"


def test_recall_at_k_edge_case_single_relevant():
    """
    Property 3: Recall@k edge case with single relevant document.
    
    When there's only one relevant document:
    - Recall should be 1.0 if it's in top-k
    - Recall should be 0.0 if it's not in top-k
    """
    # Case 1: Single relevant doc is retrieved
    mock_rag = MockRAGQuery()
    mock_rag.set_documents(['ds1_row1', 'ds1_row2', 'ds1_row3'])
    
    evaluator = RAGEvaluator(mock_rag)
    
    recall = evaluator.calculate_recall_at_k(
        query="test query",
        relevant_doc_ids={'ds1_row1'},  # First doc is relevant
        k=3
    )
    
    assert abs(recall - 1.0) < 1e-9, \
        f"Recall@3 should be 1.0 when single relevant doc retrieved, got {recall}"
    
    # Case 2: Single relevant doc is not retrieved
    recall = evaluator.calculate_recall_at_k(
        query="test query",
        relevant_doc_ids={'ds99_row99'},  # Not in retrieved set
        k=3
    )
    
    assert abs(recall - 0.0) < 1e-9, \
        f"Recall@3 should be 0.0 when single relevant doc not retrieved, got {recall}"


# ============================================================================
# Property 4: MRR Calculation Correctness
# ============================================================================

@settings(max_examples=100)
@given(
    n_docs=st.integers(min_value=1, max_value=20),
    first_relevant_rank=st.integers(min_value=1, max_value=20)
)
def test_mrr_correctness(n_docs, first_relevant_rank):
    """
    Property 4: MRR calculation correctness
    
    Verify that MRR is calculated correctly according to the formula:
    MRR = 1 / (rank of first relevant document)
    
    Test across 100 random scenarios with varying document counts and ranks.
    """
    assume(first_relevant_rank <= n_docs)
    
    # Create documents with first relevant at specific rank
    retrieved_ids = []
    for i in range(n_docs):
        retrieved_ids.append(f"ds1_row{i}")
    
    # Mark document at first_relevant_rank as relevant (1-indexed)
    relevant_doc_id = retrieved_ids[first_relevant_rank - 1]
    relevant_ids = {relevant_doc_id}
    
    # Setup mock RAG
    mock_rag = MockRAGQuery()
    mock_rag.set_documents(retrieved_ids)
    
    # Create evaluator
    evaluator = RAGEvaluator(mock_rag)
    
    # Calculate MRR
    mrr = evaluator.calculate_mrr(
        query="test query",
        relevant_doc_ids=relevant_ids
    )
    
    # Expected MRR = 1 / rank
    expected_mrr = 1.0 / first_relevant_rank
    
    # Verify MRR matches expected value
    assert abs(mrr - expected_mrr) < 1e-9, \
        f"MRR incorrect: got {mrr}, expected {expected_mrr} (rank={first_relevant_rank})"
    
    # Verify MRR is in valid range (0, 1]
    assert 0.0 < mrr <= 1.0, \
        f"MRR out of range: {mrr}"


@settings(max_examples=100)
@given(n_docs=st.integers(min_value=1, max_value=20))
def test_mrr_first_document_relevant(n_docs):
    """
    Property 4: MRR when first document is relevant.
    
    When the first retrieved document is relevant, MRR should equal 1.0.
    """
    # Create documents
    retrieved_ids = [f"ds1_row{i}" for i in range(n_docs)]
    
    # First document is relevant
    relevant_ids = {retrieved_ids[0]}
    
    # Setup mock RAG
    mock_rag = MockRAGQuery()
    mock_rag.set_documents(retrieved_ids)
    
    # Create evaluator
    evaluator = RAGEvaluator(mock_rag)
    
    # Calculate MRR
    mrr = evaluator.calculate_mrr(
        query="test query",
        relevant_doc_ids=relevant_ids
    )
    
    # Should be 1.0 since first doc is relevant
    assert abs(mrr - 1.0) < 1e-9, \
        f"MRR should be 1.0 when first doc relevant, got {mrr}"


@settings(max_examples=100)
@given(n_docs=st.integers(min_value=1, max_value=20))
def test_mrr_no_relevant_documents(n_docs):
    """
    Property 4: MRR when no documents are relevant.
    
    When no retrieved documents are relevant, MRR should equal 0.0.
    """
    # Create documents
    retrieved_ids = [f"ds1_row{i}" for i in range(n_docs)]
    
    # No documents are relevant (disjoint set)
    relevant_ids = {f"ds99_row{i}" for i in range(5)}
    
    # Setup mock RAG
    mock_rag = MockRAGQuery()
    mock_rag.set_documents(retrieved_ids)
    
    # Create evaluator
    evaluator = RAGEvaluator(mock_rag)
    
    # Calculate MRR
    mrr = evaluator.calculate_mrr(
        query="test query",
        relevant_doc_ids=relevant_ids
    )
    
    # Should be 0.0 since no docs are relevant
    assert abs(mrr - 0.0) < 1e-9, \
        f"MRR should be 0.0 when no docs relevant, got {mrr}"


def test_mrr_edge_case_empty_relevant():
    """
    Property 4: MRR edge case when relevant set is empty.
    
    When no documents are relevant, MRR should be 0.0.
    """
    mock_rag = MockRAGQuery()
    mock_rag.set_documents(['ds1_row1', 'ds1_row2', 'ds1_row3'])
    
    evaluator = RAGEvaluator(mock_rag)
    
    mrr = evaluator.calculate_mrr(
        query="test query",
        relevant_doc_ids=set()  # Empty relevant set
    )
    
    assert mrr == 0.0, \
        f"MRR should be 0.0 when relevant set empty, got {mrr}"


def test_mrr_edge_case_single_relevant_at_various_ranks():
    """
    Property 4: MRR edge case with single relevant document at various ranks.
    
    Test MRR calculation for a single relevant document at different positions.
    """
    retrieved_ids = [f"ds1_row{i}" for i in range(10)]
    
    mock_rag = MockRAGQuery()
    mock_rag.set_documents(retrieved_ids)
    
    evaluator = RAGEvaluator(mock_rag)
    
    # Test various ranks
    test_cases = [
        (1, 1.0),      # Rank 1 → MRR = 1.0
        (2, 0.5),      # Rank 2 → MRR = 0.5
        (3, 1/3),      # Rank 3 → MRR = 0.333...
        (5, 0.2),      # Rank 5 → MRR = 0.2
        (10, 0.1),     # Rank 10 → MRR = 0.1
    ]
    
    for rank, expected_mrr in test_cases:
        relevant_ids = {retrieved_ids[rank - 1]}
        
        mrr = evaluator.calculate_mrr(
            query="test query",
            relevant_doc_ids=relevant_ids
        )
        
        assert abs(mrr - expected_mrr) < 1e-9, \
            f"MRR should be {expected_mrr} for rank {rank}, got {mrr}"


@settings(max_examples=100)
@given(
    n_docs=st.integers(min_value=2, max_value=20),
    first_rank=st.integers(min_value=1, max_value=10),
    second_rank=st.integers(min_value=2, max_value=20)
)
def test_mrr_multiple_relevant_uses_first(n_docs, first_rank, second_rank):
    """
    Property 4: MRR with multiple relevant documents uses first rank.
    
    When multiple documents are relevant, MRR should use the rank of the
    FIRST relevant document encountered.
    """
    assume(first_rank < second_rank)
    assume(second_rank <= n_docs)
    
    # Create documents
    retrieved_ids = [f"ds1_row{i}" for i in range(n_docs)]
    
    # Mark two documents as relevant
    relevant_ids = {
        retrieved_ids[first_rank - 1],
        retrieved_ids[second_rank - 1]
    }
    
    # Setup mock RAG
    mock_rag = MockRAGQuery()
    mock_rag.set_documents(retrieved_ids)
    
    # Create evaluator
    evaluator = RAGEvaluator(mock_rag)
    
    # Calculate MRR
    mrr = evaluator.calculate_mrr(
        query="test query",
        relevant_doc_ids=relevant_ids
    )
    
    # Expected MRR based on FIRST relevant document
    expected_mrr = 1.0 / first_rank
    
    # Verify MRR uses first rank
    assert abs(mrr - expected_mrr) < 1e-9, \
        f"MRR should use first rank {first_rank}, got {mrr} (expected {expected_mrr})"
