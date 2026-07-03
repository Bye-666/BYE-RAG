"""Tests for BM25SparseEncoder."""

import pytest
import tempfile
from pathlib import Path

from src.ingestion.embedders.sparse_encoder import BM25SparseEncoder


@pytest.fixture
def sample_documents():
    """Sample documents for training."""
    return [
        "the cat sat on the mat",
        "the dog played in the park",
        "cats and dogs are pets"
    ]


def test_bm25_encoder_instantiation():
    """BM25SparseEncoder can be instantiated."""
    encoder = BM25SparseEncoder()
    assert encoder.k1 == 1.5
    assert encoder.b == 0.75
    assert encoder.vocab == {}
    assert encoder.idf == {}


def test_bm25_encoder_custom_parameters():
    """BM25SparseEncoder accepts custom parameters."""
    encoder = BM25SparseEncoder(k1=2.0, b=0.5)
    assert encoder.k1 == 2.0
    assert encoder.b == 0.5


def test_fit_builds_vocabulary(sample_documents):
    """Fit builds vocabulary from documents."""
    encoder = BM25SparseEncoder()
    encoder.fit(sample_documents)
    
    assert len(encoder.vocab) > 0
    assert "cat" in encoder.vocab
    assert "dog" in encoder.vocab
    assert encoder.doc_count == 3


def test_fit_calculates_avgdl(sample_documents):
    """Fit calculates average document length."""
    encoder = BM25SparseEncoder()
    encoder.fit(sample_documents)
    
    assert encoder.avgdl > 0
    # Average length: (6 + 6 + 5) / 3 = 5.67
    assert 5 < encoder.avgdl < 6


def test_fit_calculates_idf(sample_documents):
    """Fit calculates IDF values."""
    encoder = BM25SparseEncoder()
    encoder.fit(sample_documents)
    
    assert len(encoder.idf) == len(encoder.vocab)
    # All IDF values should be positive
    assert all(idf > 0 for idf in encoder.idf.values())


def test_fit_empty_documents():
    """Raise error for empty document list."""
    encoder = BM25SparseEncoder()
    with pytest.raises(ValueError, match="Cannot fit on empty document list"):
        encoder.fit([])


def test_encode_returns_sparse_vector(sample_documents):
    """Encode returns sparse vector in correct format."""
    encoder = BM25SparseEncoder()
    encoder.fit(sample_documents)
    
    vector = encoder.encode("the cat sat")
    
    assert "indices" in vector
    assert "values" in vector
    assert isinstance(vector["indices"], list)
    assert isinstance(vector["values"], list)
    assert len(vector["indices"]) == len(vector["values"])


def test_encode_before_fit():
    """Raise error when encoding before fitting."""
    encoder = BM25SparseEncoder()
    with pytest.raises(RuntimeError, match="Encoder not fitted"):
        encoder.encode("test")


def test_encode_assigns_scores(sample_documents):
    """Encode assigns BM25 scores to terms."""
    encoder = BM25SparseEncoder()
    encoder.fit(sample_documents)
    
    vector = encoder.encode("cat dog")
    
    # Should have 2 terms
    assert len(vector["indices"]) == 2
    # All scores should be positive
    assert all(score > 0 for score in vector["values"])


def test_encode_unknown_terms(sample_documents):
    """Unknown terms are ignored in encoding."""
    encoder = BM25SparseEncoder()
    encoder.fit(sample_documents)
    
    vector = encoder.encode("unknown words here")
    
    # No known terms, empty vector
    assert len(vector["indices"]) == 0
    assert len(vector["values"]) == 0


def test_encode_mixed_known_unknown(sample_documents):
    """Encode handles mix of known and unknown terms."""
    encoder = BM25SparseEncoder()
    encoder.fit(sample_documents)
    
    vector = encoder.encode("cat unknown dog")
    
    # Only 'cat' and 'dog' should be encoded
    assert len(vector["indices"]) == 2


def test_tokenize_lowercases():
    """Tokenization converts to lowercase."""
    encoder = BM25SparseEncoder()
    tokens = encoder._tokenize("The Cat SAT")
    
    assert tokens == ["the", "cat", "sat"]


def test_tokenize_splits_on_whitespace():
    """Tokenization splits on whitespace."""
    encoder = BM25SparseEncoder()
    tokens = encoder._tokenize("a b c")
    
    assert tokens == ["a", "b", "c"]


def test_save_and_load(sample_documents, tmp_path):
    """Save and load encoder."""
    encoder = BM25SparseEncoder(k1=2.0, b=0.5)
    encoder.fit(sample_documents)
    
    save_path = tmp_path / "encoder.pkl"
    encoder.save(save_path)
    
    assert save_path.exists()
    
    loaded = BM25SparseEncoder.load(save_path)
    
    assert loaded.k1 == 2.0
    assert loaded.b == 0.5
    assert loaded.vocab == encoder.vocab
    assert loaded.idf == encoder.idf
    assert loaded.avgdl == encoder.avgdl
    assert loaded.doc_count == encoder.doc_count


def test_load_nonexistent_file():
    """Raise error when loading nonexistent file."""
    with pytest.raises(FileNotFoundError):
        BM25SparseEncoder.load("nonexistent.pkl")


def test_save_creates_directory(sample_documents, tmp_path):
    """Save creates parent directories if needed."""
    encoder = BM25SparseEncoder()
    encoder.fit(sample_documents)
    
    save_path = tmp_path / "subdir" / "encoder.pkl"
    encoder.save(save_path)
    
    assert save_path.exists()


def test_encode_consistency(sample_documents):
    """Same text produces same encoding."""
    encoder = BM25SparseEncoder()
    encoder.fit(sample_documents)
    
    text = "the cat"
    vector1 = encoder.encode(text)
    vector2 = encoder.encode(text)
    
    assert vector1["indices"] == vector2["indices"]
    assert vector1["values"] == vector2["values"]


def test_term_frequency_affects_score(sample_documents):
    """Higher term frequency produces higher score."""
    encoder = BM25SparseEncoder()
    encoder.fit(sample_documents)
    
    # Single occurrence
    vec1 = encoder.encode("cat")
    # Multiple occurrences
    vec2 = encoder.encode("cat cat cat")
    
    # Second should have higher score (though same term_id)
    assert vec2["values"][0] > vec1["values"][0]


def test_fit_with_duplicate_documents():
    """Fit handles duplicate documents correctly."""
    docs = ["same text", "same text", "different text"]
    encoder = BM25SparseEncoder()
    encoder.fit(docs)
    
    assert encoder.doc_count == 3
    assert "same" in encoder.vocab
    assert "different" in encoder.vocab
