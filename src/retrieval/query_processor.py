"""Query processing and optimization."""

from typing import Dict, List, Any, Optional
from ..libs.llm.base import BaseLLM
from ..libs.embedding.base import BaseEmbedding
from ..ingestion.embedders.sparse_encoder import BM25SparseEncoder


class QueryProcessor:
    """Process and optimize queries for retrieval.
    
    Handles:
    - Query rewriting and expansion
    - Vector generation (dense + sparse)
    - Query optimization
    """

    def __init__(
        self,
        llm: Optional[BaseLLM] = None,
        embedding: BaseEmbedding = None,
        sparse_encoder: BM25SparseEncoder = None
    ):
        """Initialize QueryProcessor.
        
        Args:
            llm: Optional LLM for query rewriting
            embedding: Embedding model for dense vectors
            sparse_encoder: BM25 encoder for sparse vectors
        """
        self.llm = llm
        self.embedding = embedding
        self.sparse_encoder = sparse_encoder

    def process(self, query: str, rewrite: bool = False) -> Dict[str, Any]:
        """Process query into retrieval-ready format.
        
        Args:
            query: User query text
            rewrite: Whether to rewrite query using LLM
            
        Returns:
            Processed query dictionary with vectors and metadata
        """
        # Optionally rewrite query
        processed_text = query
        if rewrite and self.llm:
            processed_text = self._rewrite_query(query)
        
        # Generate vectors
        result = {
            "original_query": query,
            "processed_query": processed_text,
            "rewritten": rewrite and processed_text != query
        }
        
        # Dense vector
        if self.embedding:
            result["dense_vector"] = self.embedding.encode(processed_text)
        
        # Sparse vector
        if self.sparse_encoder:
            result["sparse_vector"] = self.sparse_encoder.encode(processed_text)
        
        return result

    def _rewrite_query(self, query: str) -> str:
        """Rewrite query for better retrieval.
        
        Args:
            query: Original query
            
        Returns:
            Rewritten query
        """
        prompt = f"""Rewrite the following query to improve retrieval results.
Make it more specific and add relevant context if needed.
Keep it concise (1-2 sentences).

Original query: {query}

Rewritten query:"""
        
        try:
            rewritten = self.llm.generate(prompt, max_tokens=100, temperature=0.3)
            return rewritten.strip()
        except Exception:
            # Fall back to original on error
            return query

    def expand_query(self, query: str, num_expansions: int = 3) -> List[str]:
        """Expand query into multiple variations.
        
        Args:
            query: Original query
            num_expansions: Number of query variations to generate
            
        Returns:
            List of query variations (including original)
        """
        if not self.llm:
            return [query]
        
        prompt = f"""Generate {num_expansions} alternative phrasings of this query.
Each should ask the same thing but use different words.

Original query: {query}

Alternative queries (one per line):"""
        
        try:
            response = self.llm.generate(prompt, max_tokens=200, temperature=0.7)
            lines = [line.strip() for line in response.strip().split('\n') if line.strip()]
            
            # Filter out numbered prefixes like "1. ", "2. "
            expansions = []
            for line in lines:
                # Remove common prefixes
                cleaned = line.lstrip('0123456789.-) ')
                if cleaned and len(cleaned) > 5:
                    expansions.append(cleaned)
            
            # Always include original
            if query not in expansions:
                expansions.insert(0, query)
            
            return expansions[:num_expansions + 1]
            
        except Exception:
            return [query]

    def process_batch(self, queries: List[str], rewrite: bool = False) -> List[Dict[str, Any]]:
        """Process multiple queries.
        
        Args:
            queries: List of queries
            rewrite: Whether to rewrite queries
            
        Returns:
            List of processed query dictionaries
        """
        return [self.process(q, rewrite=rewrite) for q in queries]
