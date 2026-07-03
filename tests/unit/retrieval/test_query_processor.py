"""Tests for QueryProcessor."""

import pytest
from unittest.mock import Mock

from src.retrieval.query_processor import QueryProcessor
from src.libs.llm.base import BaseLLM
from src.libs.embedding.base import BaseEmbedding
from src.ingestion.embedders.sparse_encoder import BM25SparseEncoder


class MockLLM(BaseLLM):
    """Mock LLM for testing."""

    def __init__(self, response="Rewritten query"):
        self.response = response
        self.call_count = 0

    def generate(self, prompt: str, **kwargs) -> str:
        self.call_count += 1
        return self.response

    def generate_stream(self, prompt: str, **kwargs):
        yield self.response


class MockEmbedding(BaseEmbedding):
    """Mock embedding for testing."""

    def __init__(self):
        super().__init__(model="mock")

    @property
    def dimension(self) -> int:
        return 128

    def encode(self, text: str) -> list[float]:
        return [0.1] * 128

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * 128 for _ in texts]


@pytest.fixture
def mock_components():
    """Create mock components."""
    llm = MockLLM()
    embedding = MockEmbedding()
    sparse_encoder = BM25SparseEncoder()
    sparse_encoder.fit(["sample text for training"])
    return llm, embedding, sparse_encoder


def test_query_processor_instantiation(mock_components):
    """QueryProcessor can be instantiated."""
    llm, embedding, sparse_encoder = mock_components
    processor = QueryProcessor(llm, embedding, sparse_encoder)

    assert processor.llm == llm
    assert processor.embedding == embedding
    assert processor.sparse_encoder == sparse_encoder


def test_query_processor_without_llm():
    """QueryProcessor works without LLM."""
    embedding = MockEmbedding()
    processor = QueryProcessor(embedding=embedding)

    assert processor.llm is None
    assert processor.embedding == embedding


def test_process_basic_query(mock_components):
    """Process basic query without rewriting."""
    llm, embedding, sparse_encoder = mock_components
    processor = QueryProcessor(llm, embedding, sparse_encoder)

    result = processor.process("test query")

    assert result["original_query"] == "test query"
    assert result["processed_query"] == "test query"
    assert result["rewritten"] is False
    assert "dense_vector" in result
    assert "sparse_vector" in result


def test_process_with_rewrite(mock_components):
    """Process query with rewriting enabled."""
    llm, embedding, sparse_encoder = mock_components
    processor = QueryProcessor(llm, embedding, sparse_encoder)

    result = processor.process("test query", rewrite=True)

    assert result["original_query"] == "test query"
    assert result["processed_query"] == "Rewritten query"
    assert result["rewritten"] is True
    assert llm.call_count == 1


def test_process_without_embedding():
    """Process query without embedding."""
    processor = QueryProcessor()

    result = processor.process("test query")

    assert "dense_vector" not in result
    assert "sparse_vector" not in result


def test_process_with_only_embedding():
    """Process query with only embedding."""
    embedding = MockEmbedding()
    processor = QueryProcessor(embedding=embedding)

    result = processor.process("test query")

    assert "dense_vector" in result
    assert len(result["dense_vector"]) == 128


def test_process_with_only_sparse_encoder():
    """Process query with only sparse encoder."""
    sparse_encoder = BM25SparseEncoder()
    sparse_encoder.fit(["test document"])
    processor = QueryProcessor(sparse_encoder=sparse_encoder)

    result = processor.process("test query")

    assert "sparse_vector" in result
    assert "indices" in result["sparse_vector"]
    assert "values" in result["sparse_vector"]


def test_rewrite_query_success(mock_components):
    """Query rewriting works."""
    llm, embedding, sparse_encoder = mock_components
    processor = QueryProcessor(llm, embedding, sparse_encoder)

    rewritten = processor._rewrite_query("original query")

    assert rewritten == "Rewritten query"


def test_rewrite_query_fallback_on_error():
    """Query rewriting falls back to original on error."""
    llm = Mock(spec=BaseLLM)
    llm.generate.side_effect = Exception("LLM error")

    processor = QueryProcessor(llm)
    rewritten = processor._rewrite_query("original query")

    assert rewritten == "original query"


def test_expand_query_without_llm():
    """Query expansion without LLM returns original."""
    processor = QueryProcessor()

    expansions = processor.expand_query("test query")

    assert expansions == ["test query"]


def test_expand_query_with_llm():
    """Query expansion generates variations."""
    llm = MockLLM(response="variation 1\nvariation 2\nvariation 3")
    processor = QueryProcessor(llm)

    expansions = processor.expand_query("test query", num_expansions=3)

    assert len(expansions) > 0
    assert "test query" in expansions  # Original included


def test_expand_query_cleans_prefixes():
    """Query expansion removes numbered prefixes."""
    llm = MockLLM(response="1. first variation\n2. second variation\n3. third variation")
    processor = QueryProcessor(llm)

    expansions = processor.expand_query("test query", num_expansions=3)

    # Should not have "1. ", "2. " prefixes
    assert all(not exp.startswith("1.") for exp in expansions)
    assert all(not exp.startswith("2.") for exp in expansions)


def test_expand_query_fallback_on_error():
    """Query expansion falls back to original on error."""
    llm = Mock(spec=BaseLLM)
    llm.generate.side_effect = Exception("Error")

    processor = QueryProcessor(llm)
    expansions = processor.expand_query("test query")

    assert expansions == ["test query"]


def test_process_batch():
    """Process multiple queries."""
    embedding = MockEmbedding()
    processor = QueryProcessor(embedding=embedding)

    queries = ["query 1", "query 2", "query 3"]
    results = processor.process_batch(queries)

    assert len(results) == 3
    assert all("original_query" in r for r in results)
    assert all("dense_vector" in r for r in results)


def test_process_batch_with_rewrite(mock_components):
    """Process batch with rewriting."""
    llm, embedding, sparse_encoder = mock_components
    processor = QueryProcessor(llm, embedding, sparse_encoder)

    queries = ["query 1", "query 2"]
    results = processor.process_batch(queries, rewrite=True)

    assert len(results) == 2
    assert all(r["rewritten"] for r in results)
    assert llm.call_count == 2


def test_process_generates_both_vectors(mock_components):
    """Process generates both dense and sparse vectors."""
    llm, embedding, sparse_encoder = mock_components
    processor = QueryProcessor(llm, embedding, sparse_encoder)

    result = processor.process("test query with words")

    assert "dense_vector" in result
    assert "sparse_vector" in result
    assert isinstance(result["dense_vector"], list)
    assert isinstance(result["sparse_vector"], dict)
