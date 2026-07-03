"""Chunk refinement using LLM."""

from typing import Optional
from ..types import Chunk
from ...libs.llm.base import BaseLLM


class ChunkRefiner:
    """Refine text chunks using LLM for better quality.
    
    Uses LLM to:
    - Clean formatting issues
    - Fix sentence boundaries
    - Add context from surrounding text
    - Improve readability
    """

    def __init__(self, llm: BaseLLM, max_retries: int = 2):
        """Initialize ChunkRefiner.
        
        Args:
            llm: Language model for refinement
            max_retries: Maximum retry attempts on failure
        """
        self.llm = llm
        self.max_retries = max_retries

    def refine(self, chunk: Chunk, context: Optional[str] = None) -> Chunk:
        """Refine a single chunk.
        
        Args:
            chunk: Chunk to refine
            context: Optional surrounding context for better refinement
            
        Returns:
            Refined Chunk with improved text
        """
        prompt = self._build_prompt(chunk.text, context)
        
        for attempt in range(self.max_retries + 1):
            try:
                refined_text = self.llm.generate(
                    prompt=prompt,
                    max_tokens=len(chunk.text) * 2,  # Allow expansion
                    temperature=0.3  # Low temperature for consistency
                )
                
                # Create new chunk with refined text
                return Chunk(
                    id=chunk.id,
                    text=refined_text.strip(),
                    doc_id=chunk.doc_id,
                    chunk_index=chunk.chunk_index,
                    metadata={
                        **chunk.metadata,
                        "refined": True,
                        "original_length": len(chunk.text),
                        "refined_length": len(refined_text.strip())
                    }
                )
                
            except Exception as e:
                if attempt == self.max_retries:
                    # Return original chunk if all retries fail
                    chunk.metadata["refinement_failed"] = True
                    chunk.metadata["refinement_error"] = str(e)
                    return chunk
                continue
        
        return chunk

    def _build_prompt(self, text: str, context: Optional[str] = None) -> str:
        """Build refinement prompt.
        
        Args:
            text: Text to refine
            context: Optional surrounding context
            
        Returns:
            Formatted prompt for LLM
        """
        base_prompt = """Refine the following text chunk to improve its quality:

1. Fix formatting issues (extra spaces, broken sentences)
2. Ensure proper sentence boundaries
3. Maintain the original meaning and key information
4. Keep the text concise and clear

Text to refine:
{text}
"""
        
        if context:
            base_prompt = """Refine the following text chunk using the provided context:

Context (for reference):
{context}

Text to refine:
{text}

Instructions:
1. Fix formatting issues (extra spaces, broken sentences)
2. Use context to improve sentence boundaries if needed
3. Maintain the original meaning and key information
4. Keep the text concise and clear
"""
            return base_prompt.format(text=text, context=context)
        
        return base_prompt.format(text=text)

    def refine_batch(self, chunks: list[Chunk], contexts: Optional[list[Optional[str]]] = None) -> list[Chunk]:
        """Refine multiple chunks.
        
        Args:
            chunks: List of chunks to refine
            contexts: Optional list of contexts (same length as chunks)
            
        Returns:
            List of refined chunks
        """
        if contexts is None:
            contexts = [None] * len(chunks)
        
        if len(contexts) != len(chunks):
            raise ValueError("contexts must have same length as chunks")
        
        return [self.refine(chunk, ctx) for chunk, ctx in zip(chunks, contexts)]
