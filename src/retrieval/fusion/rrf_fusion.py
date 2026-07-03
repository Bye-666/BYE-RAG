"""RRF (Reciprocal Rank Fusion) algorithm implementation."""

from typing import List, Dict, Any


class RRFFusion:
    """Reciprocal Rank Fusion for combining multiple retrieval results.
    
    RRF formula: score(d) = sum(1 / (k + rank(d))) for each ranker
    where k is a constant (typically 60) and rank starts from 1.
    """

    def __init__(self, k: int = 60):
        """Initialize RRFFusion.
        
        Args:
            k: RRF constant parameter (default: 60)
        """
        self.k = k

    def fuse(
        self,
        dense_results: List[Dict[str, Any]],
        sparse_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Fuse dense and sparse retrieval results using RRF.
        
        Args:
            dense_results: Results from dense retrieval
            sparse_results: Results from sparse retrieval
            
        Returns:
            Fused and re-ranked results
        """
        scores = {}
        
        # Accumulate scores from dense results
        for rank, hit in enumerate(dense_results, start=1):
            chunk_id = hit['id']
            scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (self.k + rank)
        
        # Accumulate scores from sparse results
        for rank, hit in enumerate(sparse_results, start=1):
            chunk_id = hit['id']
            scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (self.k + rank)
        
        # Sort by fused scores
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        
        # Build result list with complete information
        id_to_hit = {}
        for hit in dense_results + sparse_results:
            if hit['id'] not in id_to_hit:
                id_to_hit[hit['id']] = hit
        
        # Construct final results with RRF scores
        fused_results = []
        for chunk_id in sorted_ids:
            result = {**id_to_hit[chunk_id], 'rrf_score': scores[chunk_id]}
            fused_results.append(result)
        
        return fused_results

    def fuse_multiple(
        self,
        *result_lists: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Fuse multiple retrieval result lists.
        
        Args:
            *result_lists: Variable number of result lists
            
        Returns:
            Fused and re-ranked results
        """
        if len(result_lists) == 0:
            return []
        
        if len(result_lists) == 1:
            return result_lists[0]
        
        scores = {}
        
        # Accumulate scores from all result lists
        for results in result_lists:
            for rank, hit in enumerate(results, start=1):
                chunk_id = hit['id']
                scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (self.k + rank)
        
        # Sort by fused scores
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        
        # Build result map
        id_to_hit = {}
        for results in result_lists:
            for hit in results:
                if hit['id'] not in id_to_hit:
                    id_to_hit[hit['id']] = hit
        
        # Construct final results
        fused_results = []
        for chunk_id in sorted_ids:
            result = {**id_to_hit[chunk_id], 'rrf_score': scores[chunk_id]}
            fused_results.append(result)
        
        return fused_results
