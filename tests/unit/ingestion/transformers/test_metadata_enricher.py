"""Tests for MetadataEnricher."""

import pytest
import json
from unittest.mock import Mock

from src.ingestion.transformers.metadata_enricher import MetadataEnricher
from src.ingestion.types import Chunk
from src.libs.llm.base import BaseLLM


class MockLLM(BaseLLM):
    """Mock LLM for testing."""
    
    def __init__(self, response: str):
        self.response = response
        self.call_count = 0
        
    def generate(self, prompt: str, **kwargs) -> str:
        self.call_count += 1
        return self.response
    
    def generate_stream(self, prompt: str, **kwargs):
        yield self.response


@pytest.fixture
def sample_chunk():
    """Create a sample chunk for testing."""
    return Chunk(
        id="chunk-1",
        text="Python is a high-level programming language. It was created by Guido van Rossum.",
        doc_id="doc-1",
        chunk_index=0,
        metadata={"source": "test.pdf"}
    )


@pytest.fixture
def sample_metadata():
    """Sample metadata response."""
    return {
        "keywords": ["Python", "programming", "language"],
        "topics": ["Software Development"],
        "summary": "Introduction to Python programming language"
    }


def test_metadata_enricher_instantiation():
    """MetadataEnricher can be instantiated."""
    llm = MockLLM(response="{}")
    enricher = MetadataEnricher(llm)
    assert enricher.llm == llm
    assert enricher.fields == ["keywords", "topics", "summary"]


def test_metadata_enricher_custom_fields():
    """MetadataEnricher accepts custom fields."""
    llm = MockLLM(response="{}")
    enricher = MetadataEnricher(llm, fields=["keywords", "entities"])
    assert enricher.fields == ["keywords", "entities"]


def test_enrich_basic(sample_chunk, sample_metadata):
    """Enrich a chunk successfully."""
    llm = MockLLM(response=json.dumps(sample_metadata))
    enricher = MetadataEnricher(llm)
    
    enriched = enricher.enrich(sample_chunk)
    
    assert isinstance(enriched, Chunk)
    assert enriched.id == sample_chunk.id
    assert enriched.text == sample_chunk.text
    assert enriched.metadata["keywords"] == ["Python", "programming", "language"]
    assert enriched.metadata["topics"] == ["Software Development"]
    assert enriched.metadata["metadata_enriched"] is True
    assert enriched.metadata["source"] == "test.pdf"  # Preserves original
    assert llm.call_count == 1


def test_enrich_preserves_existing_metadata(sample_chunk):
    """Enrichment preserves existing metadata."""
    metadata = {"keywords": ["test"]}
    llm = MockLLM(response=json.dumps(metadata))
    enricher = MetadataEnricher(llm)
    
    enriched = enricher.enrich(sample_chunk)
    
    assert enriched.metadata["source"] == "test.pdf"
    assert enriched.metadata["keywords"] == ["test"]


def test_enrich_with_markdown_json_response(sample_chunk, sample_metadata):
    """Handle JSON wrapped in markdown code blocks."""
    response = f"```json\n{json.dumps(sample_metadata)}\n```"
    llm = MockLLM(response=response)
    enricher = MetadataEnricher(llm)
    
    enriched = enricher.enrich(sample_chunk)
    
    assert enriched.metadata["keywords"] == ["Python", "programming", "language"]


def test_enrich_with_text_before_json(sample_chunk, sample_metadata):
    """Extract JSON from response with extra text."""
    response = f"Here is the metadata:\n{json.dumps(sample_metadata)}\nDone."
    llm = MockLLM(response=response)
    enricher = MetadataEnricher(llm)
    
    enriched = enricher.enrich(sample_chunk)
    
    assert enriched.metadata["keywords"] == ["Python", "programming", "language"]


def test_enrich_failure_handling(sample_chunk):
    """Handle enrichment failures gracefully."""
    llm = Mock(spec=BaseLLM)
    llm.generate.side_effect = Exception("LLM error")
    
    enricher = MetadataEnricher(llm)
    enriched = enricher.enrich(sample_chunk)
    
    assert enriched.id == sample_chunk.id
    assert enriched.text == sample_chunk.text
    assert enriched.metadata.get("enrichment_failed") is True
    assert "LLM error" in enriched.metadata.get("enrichment_error", "")


def test_enrich_invalid_json_handling(sample_chunk):
    """Handle invalid JSON response."""
    llm = MockLLM(response="This is not valid JSON")
    enricher = MetadataEnricher(llm)
    
    enriched = enricher.enrich(sample_chunk)
    
    assert enriched.metadata.get("enrichment_failed") is True


def test_build_extraction_prompt():
    """Build extraction prompt correctly."""
    llm = MockLLM(response="{}")
    enricher = MetadataEnricher(llm, fields=["keywords", "summary"])
    
    prompt = enricher._build_extraction_prompt("Test text", ["keywords", "summary"])
    
    assert "Test text" in prompt
    assert "keywords" in prompt
    assert "summary" in prompt
    assert "JSON" in prompt


def test_parse_response_valid_json(sample_metadata):
    """Parse valid JSON response."""
    llm = MockLLM(response="{}")
    enricher = MetadataEnricher(llm)
    
    result = enricher._parse_response(json.dumps(sample_metadata))
    
    assert result == sample_metadata


def test_parse_response_markdown_json(sample_metadata):
    """Parse JSON in markdown code blocks."""
    llm = MockLLM(response="{}")
    enricher = MetadataEnricher(llm)
    
    response = f"```json\n{json.dumps(sample_metadata)}\n```"
    result = enricher._parse_response(response)
    
    assert result == sample_metadata


def test_parse_response_with_prefix(sample_metadata):
    """Parse JSON with text prefix."""
    llm = MockLLM(response="{}")
    enricher = MetadataEnricher(llm)
    
    response = f"Here is the result: {json.dumps(sample_metadata)}"
    result = enricher._parse_response(response)
    
    assert result == sample_metadata


def test_parse_response_invalid():
    """Raise error for unparseable response."""
    llm = MockLLM(response="{}")
    enricher = MetadataEnricher(llm)
    
    with pytest.raises(ValueError, match="Could not parse JSON"):
        enricher._parse_response("No JSON here at all")


def test_enrich_batch(sample_metadata):
    """Enrich multiple chunks."""
    llm = MockLLM(response=json.dumps(sample_metadata))
    enricher = MetadataEnricher(llm)
    
    chunks = [
        Chunk(id=f"chunk-{i}", text=f"Text {i}", doc_id="doc-1", chunk_index=i, metadata={})
        for i in range(3)
    ]
    
    enriched_chunks = enricher.enrich_batch(chunks)
    
    assert len(enriched_chunks) == 3
    assert all(c.metadata.get("metadata_enriched") for c in enriched_chunks)
    assert llm.call_count == 3


def test_enrich_preserves_chunk_structure(sample_chunk):
    """Enrichment preserves chunk structure."""
    metadata = {"keywords": ["test"]}
    llm = MockLLM(response=json.dumps(metadata))
    enricher = MetadataEnricher(llm)
    
    enriched = enricher.enrich(sample_chunk)
    
    assert enriched.id == sample_chunk.id
    assert enriched.text == sample_chunk.text
    assert enriched.doc_id == sample_chunk.doc_id
    assert enriched.chunk_index == sample_chunk.chunk_index
