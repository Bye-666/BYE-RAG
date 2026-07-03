"""Tests for RerankerModule."""

import pytest
from unittest.mock import Mock

from src.retrieval.reranker_module import RerankerModule
from src.libs.reranker.base import BaseReranker


@pytest.fixture
def mock_reranker():
    """Mock reranker."""
    reranker = Mock(spec=BaseReranker)
    reranker.rerank.return_value = [0.9, 0.7, 0.5]
    return reranker


@pytest.fixture
def sample_results():
    """Sample retrieval results."""
    return [
        {"id": "doc1", "text": "Result 1", "score": 0.8},
        {"id": "doc2", "text": "Result 2", "score": 0.7},
        {"id": "doc3", "text": "Result 3", "score": 0.6}
    ]


def test_reranker_module_instantiation():
    """RerankerModule can be instantiated."""
    module = RerankerModule()
    assert module.reranker is None


def test_reranker_module_with_reranker(mock_reranker):
    """RerankerModule accepts reranker."""
    module = RerankerModule(mock_reranker)
    assert module.reranker == mock_reranker


def test_rerank_without_reranker(sample_results):
    """Rerank without reranker returns original order."""
    module = RerankerModule()

    reranked = module.rerank("query", sample_results)

    assert reranked == sample_results


def test_rerank_with_reranker(mock_reranker, sample_results):
    """Rerank with reranker reorders results."""
    module = RerankerModule(mock_reranker)

    reranked = module.rerank("test query", sample_results)

    # Should call reranker
    mock_reranker.rerank.assert_called_once()

    # Should have rerank_score
    assert all("rerank_score" in r for r in reranked)

    # Should be sorted by rerank_score
    assert reranked[0]["rerank_score"] == 0.9
    assert reranked[1]["rerank_score"] == 0.7
    assert reranked[2]["rerank_score"] == 0.5


def test_rerank_calls_reranker_with_texts(mock_reranker, sample_results):
    """Rerank passes texts to reranker."""
    module = RerankerModule(mock_reranker)

    module.rerank("test query", sample_results)

    call_args = mock_reranker.rerank.call_args
    query = call_args[0][0]
    texts = call_args[0][1]

    assert query == "test query"
    assert texts == ["Result 1", "Result 2", "Result 3"]


def test_rerank_preserves_metadata(mock_reranker, sample_results):
    """Rerank preserves original result metadata."""
    module = RerankerModule(mock_reranker)

    reranked = module.rerank("query", sample_results)

    # Original fields should be preserved
    assert all("id" in r for r in reranked)
    assert all("text" in r for r in reranked)
    assert all("score" in r for r in reranked)


def test_rerank_with_top_k(mock_reranker, sample_results):
    """Rerank returns only top_k results."""
    module = RerankerModule(mock_reranker)

    reranked = module.rerank("query", sample_results, top_k=2)

    assert len(reranked) == 2
    assert reranked[0]["rerank_score"] == 0.9
    assert reranked[1]["rerank_score"] == 0.7


def test_rerank_without_reranker_with_top_k(sample_results):
    """Rerank without reranker respects top_k."""
    module = RerankerModule()

    reranked = module.rerank("query", sample_results, top_k=2)

    assert len(reranked) == 2
    assert reranked == sample_results[:2]


def test_rerank_with_empty_results(mock_reranker):
    """Rerank with empty results."""
    module = RerankerModule(mock_reranker)

    reranked = module.rerank("query", [])

    assert reranked == []
    mock_reranker.rerank.assert_not_called()


def test_rerank_sorts_by_rerank_score(mock_reranker):
    """Rerank sorts by rerank score descending."""
    mock_reranker.rerank.return_value = [0.3, 0.8, 0.5]
    module = RerankerModule(mock_reranker)

    results = [
        {"id": "doc1", "text": "Text 1"},
        {"id": "doc2", "text": "Text 2"},
        {"id": "doc3", "text": "Text 3"}
    ]

    reranked = module.rerank("query", results)

    # Should be sorted: doc2 (0.8), doc3 (0.5), doc1 (0.3)
    assert reranked[0]["id"] == "doc2"
    assert reranked[1]["id"] == "doc3"
    assert reranked[2]["id"] == "doc1"


def test_rerank_handles_missing_text_field():
    """Rerank handles results with missing text field."""
    mock_reranker = Mock(spec=BaseReranker)
    mock_reranker.rerank.return_value = [0.9, 0.8]
    module = RerankerModule(mock_reranker)

    results = [
        {"id": "doc1"},  # No text field
        {"id": "doc2", "text": "Text 2"}
    ]

    reranked = module.rerank("query", results)

    # Should pass empty string for missing text
    call_args = mock_reranker.rerank.call_args[0][1]
    assert call_args == ["", "Text 2"]
