"""Vector store upserting for chunk records."""

from typing import List
from ..types import ChunkRecord
from ...libs.vector_store.base import BaseVectorStore


class VectorUpserter:
    """Upload chunk records to vector store.
    
    Handles batch insertion of dual-vector records into Milvus.
    """

    def __init__(self, vector_store: BaseVectorStore):
        """Initialize VectorUpserter.
        
        Args:
            vector_store: Vector store instance (MilvusStore)
        """
        self.vector_store = vector_store

    def upsert(self, record: ChunkRecord) -> bool:
        """Insert single record into vector store.
        
        Args:
            record: ChunkRecord to insert
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.vector_store.upsert(
                ids=[record.id],
                texts=[record.text],
                dense_vectors=[record.dense_vector],
                sparse_vectors=[record.sparse_vector],
                metadata=[record.metadata]
            )
            return True
        except Exception as e:
            # Log error but don't raise to allow batch processing to continue
            print(f"Failed to upsert record {record.id}: {e}")
            return False

    def upsert_batch(self, records: List[ChunkRecord]) -> int:
        """Insert multiple records into vector store.
        
        Args:
            records: List of ChunkRecords to insert
            
        Returns:
            Number of successfully inserted records
        """
        if not records:
            return 0
        
        try:
            # Extract fields from records
            ids = [r.id for r in records]
            texts = [r.text for r in records]
            dense_vectors = [r.dense_vector for r in records]
            sparse_vectors = [r.sparse_vector for r in records]
            metadatas = [r.metadata for r in records]
            
            # Batch upsert
            self.vector_store.upsert(
                ids=ids,
                texts=texts,
                dense_vectors=dense_vectors,
                sparse_vectors=sparse_vectors,
                metadata=metadatas
            )
            return len(records)
            
        except Exception as e:
            # If batch fails, try individual inserts
            print(f"Batch upsert failed: {e}. Attempting individual inserts...")
            success_count = 0
            for record in records:
                if self.upsert(record):
                    success_count += 1
            return success_count
