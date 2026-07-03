"""Tests for BatchProcessor."""

import pytest
from unittest.mock import Mock

from src.ingestion.batch_processor import BatchProcessor
from src.ingestion.types import Chunk, ChunkRecord
from src.ingestion.embedders.dense_encoder import DenseEncoder
from src.ingestion.embedders.sparse_encoder import BM25SparseEncoder


@pytest.fixture
def mock_dense_encoder():
    """Mock dense encoder."""
    encoder = Mock(spec=DenseEncoder)
    encoder.encode.return_value = [0.1, 0.2, 0.3]
    encoder.encode_batch.return_value = [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
        [0.7, 0.8, 0.9]
    ]
    return encoder


@pytest.fixture
def mock_sparse_encoder():
    """Mock sparse encoder."""
    encoder = Mock(spec=BM25SparseEncoder)
    encoder.encode.return_value = {"indices": [1, 2], "values": [1.5, 2.0]}
    return encoder


@pytest.fixture
def sample_chunk():
    """Sample chunk for testing."""
    return Chunk(
        id="chunk-1",
        text="Sample text for testing",
        doc_id="doc-1",
        chunk_index=0,
        metadata={"source": "test.pdf"}
    )


@pytest.fixture
def sample_chunks():
    """Multiple sample chunks."""
    return [
        Chunk(id="chunk-1", text="Text 1", doc_id="doc-1", chunk_index=0, metadata={}),
        Chunk(id="chunk-2", text="Text 2", doc_id="doc-1", chunk_index=1, metadata={}),
        Chunk(id="chunk-3", text="Text 3", doc_id="doc-1", chunk_index=2, metadata={})
    ]


def test_batch_processor_instantiation(mock_dense_encoder, mock_sparse_encoder):
    """BatchProcessor can be instantiated."""
    processor = BatchProcessor(mock_dense_encoder, mock_sparse_encoder)
    assert processor.dense_encoder == mock_dense_encoder
    assert processor.sparse_encoder == mock_sparse_encoder


def test_process_single_chunk(mock_dense_encoder, mock_sparse_encoder, sample_chunk):
    """Process single chunk into ChunkRecord."""
    processor = BatchProcessor(mock_dense_encoder, mock_sparse_encoder)
    
    record = processor.process(sample_chunk)
    
    assert isinstance(record, ChunkRecord)
    assert record.id == sample_chunk.id
    assert record.text == sample_chunk.text
    assert record.dense_vector == [0.1, 0.2, 0.3]
    assert record.sparse_vector == {"indices": [1, 2], "values": [1.5, 2.0]}
    assert record.metadata == sample_chunk.metadata


def test_process_calls_encoders(mock_dense_encoder, mock_sparse_encoder, sample_chunk):
    """Process calls both encoders."""
    processor = BatchProcessor(mock_dense_encoder, mock_sparse_encoder)
    
    processor.process(sample_chunk)
    
    mock_dense_encoder.encode.assert_called_once_with(sample_chunk.text)
    mock_sparse_encoder.encode.assert_called_once_with(sample_chunk.text)


def test_process_batch_multiple_chunks(mock_dense_encoder, mock_sparse_encoder, sample_chunks):
    """Process multiple chunks in batch."""
    processor = BatchProcessor(mock_dense_encoder, mock_sparse_encoder)
    
    records = processor.process_batch(sample_chunks)
    
    assert len(records) == 3
    assert all(isinstance(r, ChunkRecord) for r in records)
    assert records[0].id == "chunk-1"
    assert records[1].id == "chunk-2"
    assert records[2].id == "chunk-3"


def test_process_batch_calls_batch_encode(mock_dense_encoder, mock_sparse_encoder, sample_chunks):
    """Process batch uses batch encoding for dense vectors."""
    processor = BatchProcessor(mock_dense_encoder, mock_sparse_encoder)
    
    processor.process_batch(sample_chunks)
    
    # Dense encoder should use batch method
    mock_dense_encoder.encode_batch.assert_called_once()
    call_args = mock_dense_encoder.encode_batch.call_args[0][0]
    assert call_args == ["Text 1", "Text 2", "Text 3"]
    
    # Sparse encoder called per chunk
    assert mock_sparse_encoder.encode.call_count == 3


def test_process_batch_empty_list(mock_dense_encoder, mock_sparse_encoder):
    """Handle empty chunk list."""
    processor = BatchProcessor(mock_dense_encoder, mock_sparse_encoder)
    
    records = processor.process_batch([])
    
    assert records == []
    mock_dense_encoder.encode_batch.assert_not_called()
    mock_sparse_encoder.encode.assert_not_called()


def test_process_batch_preserves_metadata(mock_dense_encoder, mock_sparse_encoder):
    """Batch processing preserves chunk metadata."""
    chunks = [
        Chunk(
            id="chunk-1",
            text="Text",
            doc_id="doc-1",
            chunk_index=0,
            metadata={"key": "value", "page": 1}
        )
    ]
    
    processor = BatchProcessor(mock_dense_encoder, mock_sparse_encoder)
    records = processor.process_batch(chunks)
    
    assert records[0].metadata == {"key": "value", "page": 1}


def test_process_batch_vectors_aligned(mock_dense_encoder, mock_sparse_encoder, sample_chunks):
    """Vectors are correctly aligned with chunks."""
    processor = BatchProcessor(mock_dense_encoder, mock_sparse_encoder)
    
    records = processor.process_batch(sample_chunks)
    
    # First chunk gets first dense vector
    assert records[0].dense_vector == [0.1, 0.2, 0.3]
    # Second chunk gets second dense vector
    assert records[1].dense_vector == [0.4, 0.5, 0.6]
    # Third chunk gets third dense vector
    assert records[2].dense_vector == [0.7, 0.8, 0.9]


def test_process_preserves_chunk_structure(mock_dense_encoder, mock_sparse_encoder, sample_chunk):
    """Process preserves all chunk information."""
    processor = BatchProcessor(mock_dense_encoder, mock_sparse_encoder)
    
    record = processor.process(sample_chunk)
    
    assert record.id == sample_chunk.id
    assert record.text == sample_chunk.text
    assert record.metadata == sample_chunk.metadata


def test_process_batch_maintains_order(mock_dense_encoder, mock_sparse_encoder):
    """Batch processing maintains chunk order."""
    chunks = [
        Chunk(id=f"chunk-{i}", text=f"Text {i}", doc_id="doc", chunk_index=i, metadata={})
        for i in range(5)
    ]
    
    mock_dense_encoder.encode_batch.return_value = [[0.1] * 3] * 5
    
    processor = BatchProcessor(mock_dense_encoder, mock_sparse_encoder)
    records = processor.process_batch(chunks)
    
    for i, record in enumerate(records):
        assert record.id == f"chunk-{i}"
