"""Tests for IngestionPipeline."""

import pytest
from pathlib import Path
from unittest.mock import Mock, call

from src.ingestion.pipeline import IngestionPipeline
from src.ingestion.types import Document, Chunk, ChunkRecord


@pytest.fixture
def mock_components():
    """Create mock pipeline components."""
    loader = Mock()
    loader.load.return_value = Document(
        id="doc-1",
        text="This is a test document with enough text to split into chunks.",
        source="test.pdf",
        metadata={"pages": 1}
    )

    splitter = Mock()
    splitter.split.return_value = [
        "This is a test document",
        "with enough text",
        "to split into chunks."
    ]

    batch_processor = Mock()
    batch_processor.process_batch.return_value = [
        ChunkRecord(
            id="chunk-1",
            text="text",
            dense_vector=[0.1],
            sparse_vector={"indices": [1], "values": [1.0]},
            metadata={}
        )
    ]

    vector_upserter = Mock()
    vector_upserter.upsert_batch.return_value = 3

    return loader, splitter, batch_processor, vector_upserter


def test_pipeline_instantiation(mock_components):
    """IngestionPipeline can be instantiated."""
    loader, splitter, processor, upserter = mock_components

    pipeline = IngestionPipeline(loader, splitter, processor, upserter)

    assert pipeline.loader == loader
    assert pipeline.splitter == splitter
    assert pipeline.batch_processor == processor
    assert pipeline.vector_upserter == upserter
    assert pipeline.batch_size == 32


def test_pipeline_custom_batch_size(mock_components):
    """Pipeline accepts custom batch size."""
    loader, splitter, processor, upserter = mock_components

    pipeline = IngestionPipeline(loader, splitter, processor, upserter, batch_size=10)

    assert pipeline.batch_size == 10


def test_ingest_file_success(mock_components, tmp_path):
    """Ingest file successfully."""
    loader, splitter, processor, upserter = mock_components
    file_path = tmp_path / "test.pdf"
    file_path.write_text("dummy")

    pipeline = IngestionPipeline(loader, splitter, processor, upserter)
    result = pipeline.ingest_file(file_path)

    assert result["success"] is True
    assert result["chunks_processed"] == 3
    assert str(file_path) in result["file"]


def test_ingest_file_calls_loader(mock_components, tmp_path):
    """Ingest file calls loader."""
    loader, splitter, processor, upserter = mock_components
    file_path = tmp_path / "test.pdf"
    file_path.write_text("dummy")

    pipeline = IngestionPipeline(loader, splitter, processor, upserter)
    pipeline.ingest_file(file_path)

    loader.load.assert_called_once()


def test_ingest_file_calls_splitter(mock_components, tmp_path):
    """Ingest file calls splitter with document text."""
    loader, splitter, processor, upserter = mock_components
    file_path = tmp_path / "test.pdf"
    file_path.write_text("dummy")

    pipeline = IngestionPipeline(loader, splitter, processor, upserter)
    pipeline.ingest_file(file_path)

    splitter.split.assert_called_once()
    call_args = splitter.split.call_args[0][0]
    assert "test document" in call_args


def test_ingest_file_calls_processor(mock_components, tmp_path):
    """Ingest file calls batch processor."""
    loader, splitter, processor, upserter = mock_components
    file_path = tmp_path / "test.pdf"
    file_path.write_text("dummy")

    pipeline = IngestionPipeline(loader, splitter, processor, upserter)
    pipeline.ingest_file(file_path)

    processor.process_batch.assert_called()


def test_ingest_file_calls_upserter(mock_components, tmp_path):
    """Ingest file calls vector upserter."""
    loader, splitter, processor, upserter = mock_components
    file_path = tmp_path / "test.pdf"
    file_path.write_text("dummy")

    pipeline = IngestionPipeline(loader, splitter, processor, upserter)
    pipeline.ingest_file(file_path)

    upserter.upsert_batch.assert_called()


def test_ingest_file_with_progress_callback(mock_components, tmp_path):
    """Progress callback is called during ingestion."""
    loader, splitter, processor, upserter = mock_components
    file_path = tmp_path / "test.pdf"
    file_path.write_text("dummy")

    callback = Mock()

    pipeline = IngestionPipeline(loader, splitter, processor, upserter)
    pipeline.ingest_file(file_path, progress_callback=callback)

    # Should be called for loading, splitting, processing stages
    assert callback.call_count > 0
    assert any("loading" in str(c) for c in callback.call_args_list)


def test_ingest_file_handles_error(mock_components, tmp_path):
    """Ingest file handles errors gracefully."""
    loader, splitter, processor, upserter = mock_components
    loader.load.side_effect = Exception("Load failed")

    file_path = tmp_path / "test.pdf"
    file_path.write_text("dummy")

    pipeline = IngestionPipeline(loader, splitter, processor, upserter)
    result = pipeline.ingest_file(file_path)

    assert result["success"] is False
    assert "error" in result
    assert "Load failed" in result["error"]


def test_ingest_files_multiple(mock_components, tmp_path):
    """Ingest multiple files."""
    loader, splitter, processor, upserter = mock_components

    files = []
    for i in range(3):
        f = tmp_path / f"test{i}.pdf"
        f.write_text("dummy")
        files.append(f)

    pipeline = IngestionPipeline(loader, splitter, processor, upserter)
    result = pipeline.ingest_files(files)

    assert result["total_files"] == 3
    assert result["successful"] == 3
    assert result["failed"] == 0


def test_ingest_files_with_failures(mock_components, tmp_path):
    """Handle partial failures in batch ingestion."""
    loader, splitter, processor, upserter = mock_components

    # Make second file fail
    loader.load.side_effect = [
        Document(id="1", text="text", source="1", metadata={}),
        Exception("Failed"),
        Document(id="3", text="text", source="3", metadata={})
    ]

    files = []
    for i in range(3):
        f = tmp_path / f"test{i}.pdf"
        f.write_text("dummy")
        files.append(f)

    pipeline = IngestionPipeline(loader, splitter, processor, upserter)
    result = pipeline.ingest_files(files)

    assert result["total_files"] == 3
    assert result["successful"] == 2
    assert result["failed"] == 1


def test_split_document_creates_chunks(mock_components):
    """Split document creates proper Chunk objects."""
    loader, splitter, processor, upserter = mock_components

    doc = Document(
        id="doc-1",
        text="Full text",
        source="test.pdf",
        metadata={"key": "value"}
    )

    pipeline = IngestionPipeline(loader, splitter, processor, upserter)
    chunks = pipeline._split_document(doc)

    assert len(chunks) == 3
    assert all(isinstance(c, Chunk) for c in chunks)
    assert chunks[0].doc_id == "doc-1"
    assert chunks[0].chunk_index == 0
    assert chunks[1].chunk_index == 1


def test_split_document_preserves_metadata(mock_components):
    """Split document preserves document metadata."""
    loader, splitter, processor, upserter = mock_components

    doc = Document(
        id="doc-1",
        text="text",
        source="test.pdf",
        metadata={"author": "Test"}
    )

    pipeline = IngestionPipeline(loader, splitter, processor, upserter)
    chunks = pipeline._split_document(doc)

    assert chunks[0].metadata["author"] == "Test"


def test_ingest_file_respects_batch_size(mock_components, tmp_path):
    """Pipeline respects batch size setting."""
    loader, splitter, processor, upserter = mock_components

    # Create many chunks
    splitter.split.return_value = [f"chunk {i}" for i in range(10)]

    file_path = tmp_path / "test.pdf"
    file_path.write_text("dummy")

    pipeline = IngestionPipeline(loader, splitter, processor, upserter, batch_size=3)
    pipeline.ingest_file(file_path)

    # Should process in batches of 3: [3, 3, 3, 1]
    assert processor.process_batch.call_count == 4
