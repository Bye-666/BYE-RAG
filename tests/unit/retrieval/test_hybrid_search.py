"""Tests for HybridSearch."""

import pytest
from unittest.mock import Mock

from src.retrieval.hybrid_search import HybridSearch
from src.retrieval.retrievers.dense_retriever import DenseRetriever
from src.retrieval.retrievers.sparse_retriever import SparseRetriever


@pytest.fixture
def mock_retrievers():
    """Create mock retrievers."""
    dense_retriever = Mock(spec=DenseRetriever)
    dense_retriever.retrieve.return_value = [
        {"id": "doc1", "text": "Dense result 1", "score": 0.9},
        {"id": "doc2", "text": "Dense result 2", "score": 0.8},
        {"id": "doc3", "text": "Dense result 3", "score": 0.7}
    ]

    sparse_retriever = Mock(spec=SparseRetriever)
    sparse_retriever.retrieve.return_value = [
        {"id": "doc2", "text": "Sparse result 2", "score": 2.5},
        {"id": "doc4", "text": "Sparse result 4", "score": 2.0},
        {"id": "doc1", "text": "Sparse result 1", "score": 1.5}
    ]

    return dense_retriever, sparse_retriever


def test_hybrid_search_instantiation(mock_retrievers):
    """HybridSearch can be instantiated."""
    dense_retriever, sparse_retriever = mock_retrievers

    search = HybridSearch(dense_retriever, sparse_retriever)

    assert search.dense_retriever == dense_retriever
    assert search.sparse_retriever == sparse_retriever
    assert search.rrf_fusion.k == 60


def test_hybrid_search_custom_rrf_k(mock_retrievers):
    """HybridSearch accepts custom RRF k."""
    dense_retriever, sparse_retriever = mock_retrievers

    search = HybridSearch(dense_retriever, sparse_retriever, rrf_k=100)

    assert search.rrf_fusion.k == 100


def test_search_basic(mock_retrievers):
    """Basic hybrid search."""
    dense_retriever, sparse_retriever = mock_retrievers
    search = HybridSearch(dense_retriever, sparse_retriever)

    dense_vector = [0.1] * 128
    sparse_vector = {"indices": [1, 2], "values": [1.0, 2.0]}

    results = search.search(dense_vector, sparse_vector, top_k=10)

    assert len(results) <= 10
    assert all("id" in r for r in results)
    assert all("rrf_score" in r for r in results)


def test_search_calls_both_retrievers(mock_retrievers):
    """Search calls both dense and sparse retrievers."""
    dense_retriever, sparse_retriever = mock_retrievers
    search = HybridSearch(dense_retriever, sparse_retriever)

    dense_vector = [0.1] * 128
    sparse_vector = {"indices": [1], "values": [1.0]}

    search.search(dense_vector, sparse_vector, top_k=5)

    # Should call both retrievers with expanded top_k (5 * 2 = 10)
    dense_retriever.retrieve.assert_called_once()
    sparse_retriever.retrieve.assert_called_once()

    # Check expanded retrieval_k
    dense_call = dense_retriever.retrieve.call_args[1]
    assert dense_call["top_k"] == 10  # top_k * 2


def test_search_expands_retrieval_k(mock_retrievers):
    """Search expands retrieval top_k for better fusion."""
    dense_retriever, sparse_retriever = mock_retrievers
    search = HybridSearch(dense_retriever, sparse_retriever)

    dense_vector = [0.1] * 128
    sparse_vector = {"indices": [1], "values": [1.0]}

    search.search(dense_vector, sparse_vector, top_k=10)

    # Should retrieve top_k * 2 from each retriever
    dense_call = dense_retriever.retrieve.call_args[1]
    sparse_call = sparse_retriever.retrieve.call_args[1]

    assert dense_call["top_k"] == 20
    assert sparse_call["top_k"] == 20


def test_search_applies_filters(mock_retrievers):
    """Search applies metadata filters to both retrievers."""
    dense_retriever, sparse_retriever = mock_retrievers
    search = HybridSearch(dense_retriever, sparse_retriever)

    dense_vector = [0.1] * 128
    sparse_vector = {"indices": [1], "values": [1.0]}
    filters = {"category": "tech", "year": 2024}

    search.search(dense_vector, sparse_vector, top_k=10, filter_dict=filters)

    # Both retrievers should receive filters
    dense_call = dense_retriever.retrieve.call_args[1]
    sparse_call = sparse_retriever.retrieve.call_args[1]

    assert dense_call["filter_dict"] == filters
    assert sparse_call["filter_dict"] == filters


def test_search_returns_top_k_results(mock_retrievers):
    """Search returns exactly top_k results."""
    dense_retriever, sparse_retriever = mock_retrievers
    search = HybridSearch(dense_retriever, sparse_retriever)

    dense_vector = [0.1] * 128
    sparse_vector = {"indices": [1], "values": [1.0]}

    results = search.search(dense_vector, sparse_vector, top_k=2)

    # Should return only top 2 after fusion
    assert len(results) == 2


def test_search_fuses_results_with_rrf(mock_retrievers):
    """Search fuses results using RRF."""
    dense_retriever, sparse_retriever = mock_retrievers
    search = HybridSearch(dense_retriever, sparse_retriever)

    dense_vector = [0.1] * 128
    sparse_vector = {"indices": [1], "values": [1.0]}

    results = search.search(dense_vector, sparse_vector, top_k=10)

    # Results should have RRF scores
    assert all("rrf_score" in r for r in results)

    # Results should be sorted by RRF score
    scores = [r["rrf_score"] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_search_handles_overlapping_docs(mock_retrievers):
    """Search handles documents appearing in both retrievers."""
    dense_retriever, sparse_retriever = mock_retrievers
    search = HybridSearch(dense_retriever, sparse_retriever)

    dense_vector = [0.1] * 128
    sparse_vector = {"indices": [1], "values": [1.0]}

    results = search.search(dense_vector, sparse_vector, top_k=10)

    # doc1 and doc2 appear in both retrievers
    # They should have higher RRF scores
    ids = [r["id"] for r in results]

    # doc1 and doc2 should be near the top due to overlap
    assert "doc1" in ids[:3] or "doc2" in ids[:3]


def test_search_with_empty_sparse_results():
    """Search with empty sparse results."""
    dense_retriever = Mock(spec=DenseRetriever)
    dense_retriever.retrieve.return_value = [
        {"id": "doc1", "text": "Result 1"}
    ]

    sparse_retriever = Mock(spec=SparseRetriever)
    sparse_retriever.retrieve.return_value = []

    search = HybridSearch(dense_retriever, sparse_retriever)

    dense_vector = [0.1] * 128
    sparse_vector = {"indices": [1], "values": [1.0]}

    results = search.search(dense_vector, sparse_vector, top_k=10)

    # Should still return results from dense only
    assert len(results) == 1
    assert results[0]["id"] == "doc1"


def test_search_with_empty_dense_results():
    """Search with empty dense results."""
    dense_retriever = Mock(spec=DenseRetriever)
    dense_retriever.retrieve.return_value = []

    sparse_retriever = Mock(spec=SparseRetriever)
    sparse_retriever.retrieve.return_value = [
        {"id": "doc1", "text": "Result 1"}
    ]

    search = HybridSearch(dense_retriever, sparse_retriever)

    dense_vector = [0.1] * 128
    sparse_vector = {"indices": [1], "values": [1.0]}

    results = search.search(dense_vector, sparse_vector, top_k=10)

    # Should still return results from sparse only
    assert len(results) == 1
    assert results[0]["id"] == "doc1"


def test_search_preserves_result_metadata(mock_retrievers):
    """Search preserves result metadata through fusion."""
    dense_retriever, sparse_retriever = mock_retrievers
    search = HybridSearch(dense_retriever, sparse_retriever)

    dense_vector = [0.1] * 128
    sparse_vector = {"indices": [1], "values": [1.0]}

    results = search.search(dense_vector, sparse_vector, top_k=10)

    # Original fields should be preserved
    assert all("text" in r for r in results)
    assert all("id" in r for r in results)
