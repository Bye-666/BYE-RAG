"""Batch processing for chunk vectorization."""

from typing import List
from .types import Chunk, ChunkRecord
from .embedders.dense_encoder import DenseEncoder
from .embedders.sparse_encoder import BM25SparseEncoder


class BatchProcessor:
    """Process chunks in batches to generate dual vectors (dense + sparse).
    
    Coordinates dense and sparse encoding to produce ChunkRecords
    ready for vector store insertion.
    """

    def __init__(self, dense_encoder: DenseEncoder, sparse_encoder: BM25SparseEncoder):
        """Initialize BatchProcessor.
        
        Args:
            dense_encoder: Dense vector encoder
            sparse_encoder: Sparse vector encoder (BM25)
        """
        self.dense_encoder = dense_encoder
        self.sparse_encoder = sparse_encoder

    def process(self, chunk: Chunk) -> ChunkRecord:
        """Process single chunk into ChunkRecord with dual vectors.
        
        Args:
            chunk: Chunk to process
            
        Returns:
            ChunkRecord with dense and sparse vectors
        """
        # Generate dense vector
        dense_vector = self.dense_encoder.encode(chunk.text)
        
        # Generate sparse vector
        sparse_vector = self.sparse_encoder.encode(chunk.text)
        
        return ChunkRecord(
            id=chunk.id,
            text=chunk.text,
            dense_vector=dense_vector,
            sparse_vector=sparse_vector,
            metadata=chunk.metadata
        )

    def process_batch(self, chunks: List[Chunk]) -> List[ChunkRecord]:
        """Process multiple chunks in batch.
        
        Args:
            chunks: List of chunks to process
            
        Returns:
            List of ChunkRecords with dual vectors
        """
        if not chunks:
            return []
        
        # Extract texts
        texts = [chunk.text for chunk in chunks]
        
        # Batch encode dense vectors
        dense_vectors = self.dense_encoder.encode_batch(texts)
        
        # Encode sparse vectors (currently sequential)
        sparse_vectors = [self.sparse_encoder.encode(text) for text in texts]
        
        # Combine into ChunkRecords
        records = []
        for chunk, dense_vec, sparse_vec in zip(chunks, dense_vectors, sparse_vectors):
            record = ChunkRecord(
                id=chunk.id,
                text=chunk.text,
                dense_vector=dense_vec,
                sparse_vector=sparse_vec,
                metadata=chunk.metadata
            )
            records.append(record)
        
        return records
