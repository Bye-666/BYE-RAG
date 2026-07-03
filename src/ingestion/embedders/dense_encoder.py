"""Dense vector encoding using embedding models."""

from typing import List
from ...libs.embedding.base import BaseEmbedding


class DenseEncoder:
    """Encode text into dense vectors using embedding models.
    
    Wraps an embedding model to provide consistent encoding interface
    for the ingestion pipeline.
    """

    def __init__(self, embedding_model: BaseEmbedding):
        """Initialize DenseEncoder.
        
        Args:
            embedding_model: Embedding model for encoding
        """
        self.embedding_model = embedding_model
        self._dimension = embedding_model.dimension

    @property
    def dimension(self) -> int:
        """Get embedding dimension.
        
        Returns:
            Vector dimension
        """
        return self._dimension

    def encode(self, text: str) -> List[float]:
        """Encode single text into dense vector.
        
        Args:
            text: Text to encode
            
        Returns:
            Dense vector as list of floats
            
        Raises:
            ValueError: If text is empty or encoding fails
        """
        if not text or not text.strip():
            raise ValueError("Cannot encode empty text")
        
        try:
            vector = self.embedding_model.encode(text)
            return vector
        except Exception as e:
            raise ValueError(f"Failed to encode text: {e}")

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Encode multiple texts into dense vectors.
        
        Args:
            texts: List of texts to encode
            
        Returns:
            List of dense vectors
            
        Raises:
            ValueError: If any text is empty or encoding fails
        """
        if not texts:
            raise ValueError("Cannot encode empty list")
        
        # Check for empty texts
        for i, text in enumerate(texts):
            if not text or not text.strip():
                raise ValueError(f"Text at index {i} is empty")
        
        try:
            vectors = self.embedding_model.encode_batch(texts)
            return vectors
        except Exception as e:
            raise ValueError(f"Failed to encode batch: {e}")
