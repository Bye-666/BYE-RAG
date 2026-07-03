"""Hybrid search combining dense and sparse retrieval."""

from typing import List, Dict, Any, Optional
from .retrievers.dense_retriever import DenseRetriever
from .retrievers.sparse_retriever import SparseRetriever
from .fusion.rrf_fusion import RRFFusion


class HybridSearch:
    """Hybrid retrieval combining dense and sparse search with RRF fusion.
    
    Implements the complete hybrid search pipeline:
    1. Dense vector search (semantic)
    2. Sparse vector search (keyword)
    3. RRF fusion for result combination
    """

    def __init__(
        self,
        dense_retriever: DenseRetriever,
        sparse_retriever: SparseRetriever,
        rrf_k: int = 60
    ):
        """Initialize HybridSearch.
        
        Args:
            dense_retriever: Dense vector retriever
            sparse_retriever: Sparse vector retriever
            rrf_k: RRF constant parameter
        """
        self.dense_retriever = dense_retriever
        self.sparse_retriever = sparse_retriever
        self.rrf_fusion = RRFFusion(k=rrf_k)

    def search(
        self,
        dense_vector: List[float],
        sparse_vector: Dict[str, List],
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Hybrid search with dense and sparse vectors.
        
        Args:
            dense_vector: Dense query vector
            sparse_vector: Sparse query vector
            top_k: Number of final results
            filter_dict: Optional metadata filters
            
        Returns:
            Fused and ranked results
        """
        # Retrieve with expanded top_k for better fusion
        retrieval_k = top_k * 2
        
        # 1. Dense retrieval
        dense_results = self.dense_retriever.retrieve(
            query_vector=dense_vector,
            top_k=retrieval_k,
            filter_dict=filter_dict
        )
        
        # 2. Sparse retrieval
        sparse_results = self.sparse_retriever.retrieve(
            query_vector=sparse_vector,
            top_k=retrieval_k,
            filter_dict=filter_dict
        )
        
        # 3. RRF fusion
        fused_results = self.rrf_fusion.fuse(dense_results, sparse_results)
        
        # 4. Return top_k results
        return fused_results[:top_k]
