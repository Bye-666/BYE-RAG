"""Tests for SparseRetriever."""

import pytest
from unittest.mock import Mock

from src.retrieval.retrievers.sparse_retriever import SparseRetriever
from src.libs.vector_store.base import BaseVectorStore


@pytest.fixture
def mock_vector_store():
    """Mock vector store."""
    store = Mock(spec=BaseVectorStore)
    store.search_sparse.return_value = [
        {"id": "doc1", "text": "Result 1", "score": 2.5},
        {"id": "doc2", "text": "Result 2", "score": 1.8},
        {"id": "doc3", "text": "Result 3", "score": 1.2}
    ]
    return store


def test_sparse_retriever_instantiation(mock_vector_store):
    """SparseRetriever can be instantiated."""
    retriever = SparseRetriever(mock_vector_store)
    assert retriever.vector_store == mock_vector_store


def test_retrieve_basic(mock_vector_store):
    """Retrieve documents successfully."""
    retriever = SparseRetriever(mock_vector_store)
    query_vector = {"indices": [1, 5, 10], "values": [2.0, 1.5, 1.0]}

    results = retriever.retrieve(query_vector, top_k=10)

    assert len(results) == 3
    assert results[0]["id"] == "doc1"
    assert results[0]["score"] == 2.5


def test_retrieve_calls_vector_store(mock_vector_store):
    """Retrieve calls vector store search_sparse."""
    retriever = SparseRetriever(mock_vector_store)
    query_vector = {"indices": [1, 2], "values": [1.0, 2.0]}

    retriever.retrieve(query_vector, top_k=5)

    mock_vector_store.search_sparse.assert_called_once_with(
        query_vector=query_vector,
        top_k=5,
        filter_dict=None
    )


def test_retrieve_with_top_k(mock_vector_store):
    """Retrieve respects top_k parameter."""
    retriever = SparseRetriever(mock_vector_store)
    query_vector = {"indices": [1], "values": [1.0]}

    retriever.retrieve(query_vector, top_k=15)

    call_kwargs = mock_vector_store.search_sparse.call_args[1]
    assert call_kwargs["top_k"] == 15


def test_retrieve_with_filters(mock_vector_store):
    """Retrieve applies metadata filters."""
    retriever = SparseRetriever(mock_vector_store)
    query_vector = {"indices": [1], "values": [1.0]}
    filters = {"type": "article", "status": "published"}

    retriever.retrieve(query_vector, top_k=10, filter_dict=filters)

    call_kwargs = mock_vector_store.search_sparse.call_args[1]
    assert call_kwargs["filter_dict"] == filters


def test_retrieve_returns_results_from_store(mock_vector_store):
    """Retrieve returns results from vector store."""
    retriever = SparseRetriever(mock_vector_store)
    query_vector = {"indices": [1], "values": [1.0]}

    results = retriever.retrieve(query_vector)

    assert results == mock_vector_store.search_sparse.return_value


def test_retrieve_with_empty_results(mock_vector_store):
    """Retrieve handles empty results."""
    mock_vector_store.search_sparse.return_value = []
    retriever = SparseRetriever(mock_vector_store)
    query_vector = {"indices": [1], "values": [1.0]}

    results = retriever.retrieve(query_vector)

    assert results == []


def test_retrieve_with_complex_sparse_vector(mock_vector_store):
    """Retrieve with complex sparse vector."""
    retriever = SparseRetriever(mock_vector_store)
    query_vector = {
        "indices": [1, 5, 10, 15, 20],
        "values": [3.0, 2.5, 2.0, 1.5, 1.0]
    }

    retriever.retrieve(query_vector, top_k=10)

    call_args = mock_vector_store.search_sparse.call_args
    assert call_args[1]["query_vector"] == query_vector
