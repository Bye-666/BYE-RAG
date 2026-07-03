"""Metadata enrichment using LLM."""

import json
from typing import Dict, Any, List
from ..types import Chunk
from ...libs.llm.base import BaseLLM


class MetadataEnricher:
    """Enrich chunk metadata using LLM.
    
    Extracts structured metadata such as:
    - Keywords
    - Topics/categories
    - Summary
    - Entity mentions
    """

    def __init__(self, llm: BaseLLM, fields: List[str] = None):
        """Initialize MetadataEnricher.
        
        Args:
            llm: Language model for metadata extraction
            fields: List of metadata fields to extract. 
                   Default: ["keywords", "topics", "summary"]
        """
        self.llm = llm
        self.fields = fields or ["keywords", "topics", "summary"]

    def enrich(self, chunk: Chunk) -> Chunk:
        """Enrich a chunk with metadata.
        
        Args:
            chunk: Chunk to enrich
            
        Returns:
            Chunk with enriched metadata
        """
        prompt = self._build_extraction_prompt(chunk.text, self.fields)
        
        try:
            response = self.llm.generate(
                prompt=prompt,
                max_tokens=500,
                temperature=0.2
            )
            
            # Parse JSON response
            extracted = self._parse_response(response)
            
            # Merge with existing metadata
            enriched_metadata = {
                **chunk.metadata,
                **extracted,
                "metadata_enriched": True
            }
            
            return Chunk(
                id=chunk.id,
                text=chunk.text,
                doc_id=chunk.doc_id,
                chunk_index=chunk.chunk_index,
                metadata=enriched_metadata
            )
            
        except Exception as e:
            # Return original chunk on failure
            chunk.metadata["enrichment_failed"] = True
            chunk.metadata["enrichment_error"] = str(e)
            return chunk

    def _build_extraction_prompt(self, text: str, fields: List[str]) -> str:
        """Build metadata extraction prompt.
        
        Args:
            text: Text to extract metadata from
            fields: Metadata fields to extract
            
        Returns:
            Formatted prompt
        """
        field_descriptions = {
            "keywords": "Extract 3-5 important keywords",
            "topics": "Identify 1-3 main topics or categories",
            "summary": "Write a one-sentence summary",
            "entities": "Extract named entities (people, places, organizations)",
            "sentiment": "Classify sentiment (positive, negative, neutral)"
        }
        
        field_list = "\n".join([
            f"- {field}: {field_descriptions.get(field, 'Extract relevant information')}"
            for field in fields
        ])
        
        return f"""Extract structured metadata from the following text.

Text:
{text}

Extract the following metadata fields:
{field_list}

Return ONLY a valid JSON object with the extracted metadata. Use the field names as keys.
Example format: {{"keywords": ["word1", "word2"], "topics": ["topic1"], "summary": "..."}}

JSON:"""

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured metadata.
        
        Args:
            response: LLM response text
            
        Returns:
            Parsed metadata dictionary
        """
        # Try to find JSON in response
        response = response.strip()
        
        # Handle markdown code blocks
        if response.startswith("```"):
            lines = response.split("\n")
            response = "\n".join(lines[1:-1]) if len(lines) > 2 else response
            response = response.replace("```json", "").replace("```", "").strip()
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from text
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(response[start:end])
            raise ValueError(f"Could not parse JSON from response: {response[:100]}")

    def enrich_batch(self, chunks: List[Chunk]) -> List[Chunk]:
        """Enrich multiple chunks.
        
        Args:
            chunks: List of chunks to enrich
            
        Returns:
            List of enriched chunks
        """
        return [self.enrich(chunk) for chunk in chunks]
