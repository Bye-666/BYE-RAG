"""Tests for DenseEncoder."""

import pytest
from unittest.mock import Mock

from src.ingestion.embedders.dense_encoder import DenseEncoder
from src.libs.embedding.base import BaseEmbedding


class MockEmbedding(BaseEmbedding):
    """Mock embedding model for testing."""
    
    def __init__(self, dim: int = 768):
        self._dimension = dim
        self.call_count = 0
        
    @property
    def dimension(self) -> int:
        return self._dimension
        
    def encode(self, text: str) -> list[float]:
        self.call_count += 1
        return [0.1] * self._dimension
    
    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        self.call_count += len(texts)
        return [[0.1] * self._dimension for _ in texts]


def test_dense_encoder_instantiation():
    """DenseEncoder can be instantiated."""
    embedding = MockEmbedding()
    encoder = DenseEncoder(embedding)
    assert encoder.embedding_model == embedding
    assert encoder.dimension == 768


def test_dense_encoder_dimension_property():
    """Dimension property returns correct value."""
    embedding = MockEmbedding(dim=1024)
    encoder = DenseEncoder(embedding)
    assert encoder.dimension == 1024


def test_encode_single_text():
    """Encode single text successfully."""
    embedding = MockEmbedding(dim=768)
    encoder = DenseEncoder(embedding)
    
    vector = encoder.encode("Test text")
    
    assert isinstance(vector, list)
    assert len(vector) == 768
    assert all(isinstance(v, float) for v in vector)
    assert embedding.call_count == 1


def test_encode_returns_correct_dimension():
    """Encoded vector has correct dimension."""
    embedding = MockEmbedding(dim=512)
    encoder = DenseEncoder(embedding)
    
    vector = encoder.encode("Test")
    
    assert len(vector) == 512


def test_encode_empty_text():
    """Raise error for empty text."""
    embedding = MockEmbedding()
    encoder = DenseEncoder(embedding)
    
    with pytest.raises(ValueError, match="Cannot encode empty text"):
        encoder.encode("")


def test_encode_whitespace_only():
    """Raise error for whitespace-only text."""
    embedding = MockEmbedding()
    encoder = DenseEncoder(embedding)
    
    with pytest.raises(ValueError, match="Cannot encode empty text"):
        encoder.encode("   ")


def test_encode_failure_handling():
    """Handle encoding failures."""
    embedding = Mock(spec=BaseEmbedding)
    embedding.dimension = 768
    embedding.encode.side_effect = Exception("Embedding API error")
    
    encoder = DenseEncoder(embedding)
    
    with pytest.raises(ValueError, match="Failed to encode text"):
        encoder.encode("Test")


def test_encode_batch():
    """Encode multiple texts."""
    embedding = MockEmbedding(dim=768)
    encoder = DenseEncoder(embedding)
    
    texts = ["Text 1", "Text 2", "Text 3"]
    vectors = encoder.encode_batch(texts)
    
    assert len(vectors) == 3
    assert all(len(v) == 768 for v in vectors)
    assert embedding.call_count == 3


def test_encode_batch_empty_list():
    """Raise error for empty list."""
    embedding = MockEmbedding()
    encoder = DenseEncoder(embedding)
    
    with pytest.raises(ValueError, match="Cannot encode empty list"):
        encoder.encode_batch([])


def test_encode_batch_with_empty_text():
    """Raise error if any text in batch is empty."""
    embedding = MockEmbedding()
    encoder = DenseEncoder(embedding)
    
    texts = ["Valid text", "", "Another text"]
    
    with pytest.raises(ValueError, match="Text at index 1 is empty"):
        encoder.encode_batch(texts)


def test_encode_batch_with_whitespace():
    """Raise error if any text in batch is whitespace."""
    embedding = MockEmbedding()
    encoder = DenseEncoder(embedding)
    
    texts = ["Valid text", "   ", "Another text"]
    
    with pytest.raises(ValueError, match="Text at index 1 is empty"):
        encoder.encode_batch(texts)


def test_encode_batch_failure_handling():
    """Handle batch encoding failures."""
    embedding = Mock(spec=BaseEmbedding)
    embedding.dimension = 768
    embedding.encode_batch.side_effect = Exception("Batch API error")
    
    encoder = DenseEncoder(embedding)
    
    with pytest.raises(ValueError, match="Failed to encode batch"):
        encoder.encode_batch(["Text 1", "Text 2"])


def test_encode_batch_returns_correct_dimensions():
    """All vectors in batch have correct dimension."""
    embedding = MockEmbedding(dim=256)
    encoder = DenseEncoder(embedding)
    
    vectors = encoder.encode_batch(["A", "B", "C"])
    
    assert all(len(v) == 256 for v in vectors)


def test_encoder_uses_underlying_model():
    """Encoder delegates to underlying embedding model."""
    embedding = MockEmbedding()
    encoder = DenseEncoder(embedding)
    
    encoder.encode("Test")
    
    assert embedding.call_count == 1


def test_encoder_batch_uses_underlying_model():
    """Batch encoding delegates to underlying model."""
    embedding = MockEmbedding()
    encoder = DenseEncoder(embedding)
    
    encoder.encode_batch(["A", "B"])
    
    assert embedding.call_count == 2
