"""Sparse vector retrieval."""

from typing import List, Dict, Any, Optional
from ...libs.vector_store.base import BaseVectorStore


class SparseRetriever:
    """Retrieve documents using sparse vector (BM25) similarity.
    
    Uses BM25-based sparse vectors for keyword matching.
    """

    def __init__(self, vector_store: BaseVectorStore):
        """Initialize SparseRetriever.
        
        Args:
            vector_store: Vector store instance
        """
        self.vector_store = vector_store

    def retrieve(
        self,
        query_vector: Dict[str, List],
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve documents using sparse vector.
        
        Args:
            query_vector: Sparse query vector {"indices": [...], "values": [...]}
            top_k: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of retrieved documents with scores
        """
        results = self.vector_store.search_sparse(
            query_vector=query_vector,
            top_k=top_k,
            filter_dict=filter_dict
        )
        
        return results
