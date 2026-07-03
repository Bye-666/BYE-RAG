"""End-to-end tests for ingestion pipeline."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock

from src.ingestion.pipeline import IngestionPipeline
from src.ingestion.loaders.base import BaseLoader
from src.ingestion.batch_processor import BatchProcessor
from src.ingestion.embedders.dense_encoder import DenseEncoder
from src.ingestion.embedders.sparse_encoder import BM25SparseEncoder
from src.ingestion.storage.vector_upserter import VectorUpserter
from src.ingestion.types import Document, Chunk, ChunkRecord
from src.libs.splitter.base import BaseSplitter
from src.libs.embedding.base import BaseEmbedding
from src.libs.vector_store.base import BaseVectorStore


class MockEmbedding(BaseEmbedding):
    """Mock embedding for testing."""

    def __init__(self):
        super().__init__(model="mock-model")

    @property
    def dimension(self) -> int:
        return 128

    def encode(self, text: str) -> list[float]:
        return [0.1] * 128

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * 128 for _ in texts]


class MockSplitter(BaseSplitter):
    """Mock splitter for testing."""
    
    def split(self, text: str) -> list[str]:
        # Simple split by sentence
        sentences = text.split('.')
        return [s.strip() + '.' for s in sentences if s.strip()]


class MockVectorStore(BaseVectorStore):
    """Mock vector store that stores in memory."""

    def __init__(self):
        self.records = []

    def upsert(self, ids, texts, dense_vectors, sparse_vectors, metadatas):
        for i in range(len(ids)):
            self.records.append({
                'id': ids[i],
                'text': texts[i],
                'dense_vector': dense_vectors[i],
                'sparse_vector': sparse_vectors[i],
                'metadata': metadatas[i]
            })

    def search(self, query_vector, top_k, filter_dict):
        return []

    def search_dense(self, query_vector, top_k, filter_dict=None):
        return []

    def search_sparse(self, query_vector, top_k, filter_dict=None):
        return []

    def get_by_ids(self, ids):
        return [r for r in self.records if r['id'] in ids]

    def delete(self, ids):
        self.records = [r for r in self.records if r['id'] not in ids]

    def count(self):
        return len(self.records)


class MockLoader(BaseLoader):
    """Mock loader for testing."""

    def load(self, file_path):
        return Document(
            id="test-doc-1",
            text="First sentence. Second sentence. Third sentence.",
            source=str(file_path),
            metadata={"test": True}
        )


@pytest.fixture
def test_file(tmp_path):
    """Create a test file."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("Test content for ingestion")
    return file_path


@pytest.fixture
def pipeline_components():
    """Create real pipeline components for E2E test."""
    loader = MockLoader()
    splitter = MockSplitter()
    
    embedding = MockEmbedding()
    dense_encoder = DenseEncoder(embedding)
    
    sparse_encoder = BM25SparseEncoder()
    # Train on sample documents
    sparse_encoder.fit([
        "First sentence. Second sentence.",
        "Third sentence. Fourth sentence."
    ])
    
    batch_processor = BatchProcessor(dense_encoder, sparse_encoder)
    
    vector_store = MockVectorStore()
    vector_upserter = VectorUpserter(vector_store)
    
    pipeline = IngestionPipeline(
        loader=loader,
        splitter=splitter,
        batch_processor=batch_processor,
        vector_upserter=vector_upserter,
        batch_size=10
    )
    
    return pipeline, vector_store


def test_e2e_single_file_ingestion(pipeline_components, test_file):
    """Test complete ingestion of single file."""
    pipeline, vector_store = pipeline_components
    
    result = pipeline.ingest_file(test_file)
    
    # Should succeed
    assert result["success"] is True
    assert result["chunks_processed"] > 0
    
    # Data should be in vector store
    assert vector_store.count() > 0


def test_e2e_pipeline_creates_vectors(pipeline_components, test_file):
    """Verify vectors are created with correct format."""
    pipeline, vector_store = pipeline_components
    
    pipeline.ingest_file(test_file)
    
    records = vector_store.records
    assert len(records) > 0
    
    # Check first record structure
    record = records[0]
    assert 'id' in record
    assert 'text' in record
    assert 'dense_vector' in record
    assert 'sparse_vector' in record
    
    # Dense vector should have correct dimension
    assert len(record['dense_vector']) == 128
    
    # Sparse vector should have correct format
    assert 'indices' in record['sparse_vector']
    assert 'values' in record['sparse_vector']


def test_e2e_multiple_files(pipeline_components, tmp_path):
    """Test ingestion of multiple files."""
    pipeline, vector_store = pipeline_components
    
    files = []
    for i in range(3):
        f = tmp_path / f"test{i}.txt"
        f.write_text(f"Content {i}")
        files.append(f)
    
    result = pipeline.ingest_files(files)
    
    assert result["total_files"] == 3
    assert result["successful"] == 3
    assert result["failed"] == 0
    assert vector_store.count() > 0


def test_e2e_metadata_preserved(pipeline_components, test_file):
    """Test that metadata is preserved through pipeline."""
    pipeline, vector_store = pipeline_components
    
    pipeline.ingest_file(test_file)
    
    records = vector_store.records
    # All records should have source metadata
    assert all('metadata' in r for r in records)
    assert all(r['metadata'].get('test') is True for r in records)


def test_e2e_chunks_have_correct_structure(pipeline_components, test_file):
    """Test that chunks are properly structured."""
    pipeline, vector_store = pipeline_components
    
    pipeline.ingest_file(test_file)
    
    records = vector_store.records
    
    # Check IDs follow pattern
    for i, record in enumerate(records):
        assert 'test-doc-1_chunk_' in record['id']
    
    # Check texts are non-empty
    assert all(record['text'].strip() for record in records)


def test_e2e_with_progress_callback(pipeline_components, test_file):
    """Test that progress callback is called."""
    pipeline, vector_store = pipeline_components
    
    progress_calls = []
    
    def track_progress(stage, current, total):
        progress_calls.append((stage, current, total))
    
    pipeline.ingest_file(test_file, progress_callback=track_progress)
    
    # Should have received progress updates
    assert len(progress_calls) > 0
    
    # Should have loading, splitting, processing stages
    stages = [call[0] for call in progress_calls]
    assert 'loading' in stages
    assert 'splitting' in stages
    assert 'processing' in stages


def test_e2e_error_handling(pipeline_components, tmp_path):
    """Test error handling in E2E flow."""
    pipeline, vector_store = pipeline_components

    # Make loader raise an error
    original_load = pipeline.loader.load
    pipeline.loader.load = lambda file_path: (_ for _ in ()).throw(Exception("Load failed"))

    result = pipeline.ingest_file(tmp_path / "any_file.txt")

    assert result["success"] is False
    assert "error" in result


def test_e2e_batch_processing(pipeline_components, test_file):
    """Test that batching works correctly."""
    pipeline, vector_store = pipeline_components
    pipeline.batch_size = 2  # Small batch size
    
    pipeline.ingest_file(test_file)
    
    # Should still process all chunks despite small batch size
    assert vector_store.count() > 0
