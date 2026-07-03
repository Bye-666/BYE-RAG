"""Reranking module for retrieval results."""

from typing import List, Dict, Any, Optional
from ..libs.reranker.base import BaseReranker


class RerankerModule:
    """Rerank retrieval results using reranker model.
    
    Provides optional reranking layer to improve result quality.
    """

    def __init__(self, reranker: Optional[BaseReranker] = None):
        """Initialize RerankerModule.
        
        Args:
            reranker: Optional reranker instance
        """
        self.reranker = reranker

    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Rerank results based on query relevance.
        
        Args:
            query: Query text
            results: Retrieved results to rerank
            top_k: Optional number of top results to return
            
        Returns:
            Reranked results
        """
        if not self.reranker or not results:
            return results[:top_k] if top_k else results
        
        # Extract texts for reranking
        texts = [result.get('text', '') for result in results]
        
        # Get reranking scores
        scores = self.reranker.rerank(query, texts)
        
        # Combine scores with results
        reranked = []
        for result, score in zip(results, scores):
            reranked_result = {**result, 'rerank_score': score}
            reranked.append(reranked_result)
        
        # Sort by rerank score
        reranked.sort(key=lambda x: x['rerank_score'], reverse=True)
        
        # Return top_k if specified
        if top_k:
            return reranked[:top_k]
        
        return reranked
