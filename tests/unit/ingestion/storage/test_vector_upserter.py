"""Tests for VectorUpserter."""

import pytest
from unittest.mock import Mock

from src.ingestion.storage.vector_upserter import VectorUpserter
from src.ingestion.types import ChunkRecord
from src.libs.vector_store.base import BaseVectorStore


@pytest.fixture
def mock_vector_store():
    """Mock vector store."""
    store = Mock(spec=BaseVectorStore)
    store.upsert.return_value = None
    return store


@pytest.fixture
def sample_record():
    """Sample chunk record."""
    return ChunkRecord(
        id="rec-1",
        text="Sample text",
        dense_vector=[0.1, 0.2, 0.3],
        sparse_vector={"indices": [1, 2], "values": [1.5, 2.0]},
        metadata={"source": "test"}
    )


@pytest.fixture
def sample_records():
    """Multiple sample records."""
    return [
        ChunkRecord(
            id=f"rec-{i}",
            text=f"Text {i}",
            dense_vector=[0.1 * i, 0.2 * i, 0.3 * i],
            sparse_vector={"indices": [i], "values": [float(i)]},
            metadata={"index": i}
        )
        for i in range(3)
    ]


def test_vector_upserter_instantiation(mock_vector_store):
    """VectorUpserter can be instantiated."""
    upserter = VectorUpserter(mock_vector_store)
    assert upserter.vector_store == mock_vector_store


def test_upsert_single_record(mock_vector_store, sample_record):
    """Upsert single record successfully."""
    upserter = VectorUpserter(mock_vector_store)
    
    result = upserter.upsert(sample_record)
    
    assert result is True
    mock_vector_store.upsert.assert_called_once()
    
    # Verify call arguments
    call_kwargs = mock_vector_store.upsert.call_args[1]
    assert call_kwargs["ids"] == ["rec-1"]
    assert call_kwargs["texts"] == ["Sample text"]
    assert call_kwargs["dense_vectors"] == [[0.1, 0.2, 0.3]]
    assert call_kwargs["sparse_vectors"] == [{"indices": [1, 2], "values": [1.5, 2.0]}]
    assert call_kwargs["metadatas"] == [{"source": "test"}]


def test_upsert_failure_handling(mock_vector_store, sample_record, capsys):
    """Handle upsert failure gracefully."""
    mock_vector_store.upsert.side_effect = Exception("DB error")
    
    upserter = VectorUpserter(mock_vector_store)
    result = upserter.upsert(sample_record)
    
    assert result is False
    captured = capsys.readouterr()
    assert "Failed to upsert record rec-1" in captured.out


def test_upsert_batch_multiple_records(mock_vector_store, sample_records):
    """Upsert multiple records in batch."""
    upserter = VectorUpserter(mock_vector_store)
    
    count = upserter.upsert_batch(sample_records)
    
    assert count == 3
    mock_vector_store.upsert.assert_called_once()
    
    # Verify batch call
    call_kwargs = mock_vector_store.upsert.call_args[1]
    assert len(call_kwargs["ids"]) == 3
    assert call_kwargs["ids"] == ["rec-0", "rec-1", "rec-2"]


def test_upsert_batch_empty_list(mock_vector_store):
    """Handle empty record list."""
    upserter = VectorUpserter(mock_vector_store)
    
    count = upserter.upsert_batch([])
    
    assert count == 0
    mock_vector_store.upsert.assert_not_called()


def test_upsert_batch_extracts_fields_correctly(mock_vector_store, sample_records):
    """Batch upsert extracts all fields correctly."""
    upserter = VectorUpserter(mock_vector_store)
    
    upserter.upsert_batch(sample_records)
    
    call_kwargs = mock_vector_store.upsert.call_args[1]
    
    # Check texts
    assert call_kwargs["texts"] == ["Text 0", "Text 1", "Text 2"]
    
    # Check dense vectors
    assert len(call_kwargs["dense_vectors"]) == 3
    
    # Check sparse vectors
    assert len(call_kwargs["sparse_vectors"]) == 3
    
    # Check metadata
    assert call_kwargs["metadatas"][0] == {"index": 0}
    assert call_kwargs["metadatas"][1] == {"index": 1}


def test_upsert_batch_fallback_on_failure(mock_vector_store, sample_records, capsys):
    """Fall back to individual inserts on batch failure."""
    # Batch fails, individual succeeds
    mock_vector_store.upsert.side_effect = [
        Exception("Batch failed"),
        None, None, None  # Individual inserts succeed
    ]
    
    upserter = VectorUpserter(mock_vector_store)
    count = upserter.upsert_batch(sample_records)
    
    # Should attempt individual inserts
    assert count == 3
    assert mock_vector_store.upsert.call_count == 4  # 1 batch + 3 individual
    
    captured = capsys.readouterr()
    assert "Batch upsert failed" in captured.out
    assert "Attempting individual inserts" in captured.out


def test_upsert_batch_partial_success_in_fallback(mock_vector_store, sample_records, capsys):
    """Handle partial success in fallback mode."""
    # Batch fails, then individual: success, fail, success
    mock_vector_store.upsert.side_effect = [
        Exception("Batch failed"),
        None,  # rec-0 succeeds
        Exception("rec-1 failed"),
        None   # rec-2 succeeds
    ]
    
    upserter = VectorUpserter(mock_vector_store)
    count = upserter.upsert_batch(sample_records)
    
    assert count == 2  # 2 out of 3 succeeded


def test_upsert_preserves_record_data(mock_vector_store, sample_record):
    """Upsert preserves all record data."""
    upserter = VectorUpserter(mock_vector_store)
    upserter.upsert(sample_record)
    
    call_kwargs = mock_vector_store.upsert.call_args[1]
    
    # All fields preserved
    assert call_kwargs["ids"][0] == sample_record.id
    assert call_kwargs["texts"][0] == sample_record.text
    assert call_kwargs["dense_vectors"][0] == sample_record.dense_vector
    assert call_kwargs["sparse_vectors"][0] == sample_record.sparse_vector
    assert call_kwargs["metadatas"][0] == sample_record.metadata
