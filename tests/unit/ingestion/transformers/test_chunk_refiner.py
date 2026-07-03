"""Tests for ChunkRefiner."""

import pytest
from unittest.mock import Mock

from src.ingestion.transformers.chunk_refiner import ChunkRefiner
from src.ingestion.types import Chunk
from src.libs.llm.base import BaseLLM


class MockLLM(BaseLLM):
    """Mock LLM for testing."""
    
    def __init__(self, response: str = "Refined text"):
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
        text="This is   a text  with   formatting issues.",
        doc_id="doc-1",
        chunk_index=0,
        metadata={"source": "test"}
    )


def test_chunk_refiner_instantiation():
    """ChunkRefiner can be instantiated."""
    llm = MockLLM()
    refiner = ChunkRefiner(llm)
    assert refiner.llm == llm
    assert refiner.max_retries == 2


def test_chunk_refiner_custom_retries():
    """ChunkRefiner accepts custom max_retries."""
    llm = MockLLM()
    refiner = ChunkRefiner(llm, max_retries=5)
    assert refiner.max_retries == 5


def test_refine_basic(sample_chunk):
    """Refine a chunk successfully."""
    llm = MockLLM(response="This is a text with proper formatting.")
    refiner = ChunkRefiner(llm)
    
    refined = refiner.refine(sample_chunk)
    
    assert isinstance(refined, Chunk)
    assert refined.id == sample_chunk.id
    assert refined.doc_id == sample_chunk.doc_id
    assert refined.chunk_index == sample_chunk.chunk_index
    assert refined.text == "This is a text with proper formatting."
    assert refined.metadata["refined"] is True
    assert refined.metadata["source"] == "test"
    assert llm.call_count == 1


def test_refine_with_context(sample_chunk):
    """Refine a chunk with context."""
    llm = MockLLM(response="Refined with context")
    refiner = ChunkRefiner(llm)
    
    context = "Previous paragraph content for reference."
    refined = refiner.refine(sample_chunk, context=context)
    
    assert refined.text == "Refined with context"
    assert "context" in refiner._build_prompt(sample_chunk.text, context).lower()


def test_refine_metadata_tracking(sample_chunk):
    """Metadata tracks refinement info."""
    llm = MockLLM(response="Short")
    refiner = ChunkRefiner(llm)
    
    refined = refiner.refine(sample_chunk)
    
    assert refined.metadata["refined"] is True
    assert refined.metadata["original_length"] == len(sample_chunk.text)
    assert refined.metadata["refined_length"] == 5  # len("Short")


def test_refine_failure_handling(sample_chunk):
    """Handle LLM failures gracefully."""
    llm = Mock(spec=BaseLLM)
    llm.generate.side_effect = Exception("LLM error")
    
    refiner = ChunkRefiner(llm, max_retries=1)
    refined = refiner.refine(sample_chunk)
    
    # Should return original chunk on failure
    assert refined.id == sample_chunk.id
    assert refined.text == sample_chunk.text
    assert refined.metadata.get("refinement_failed") is True
    assert "LLM error" in refined.metadata.get("refinement_error", "")
    assert llm.generate.call_count == 2  # Initial + 1 retry


def test_refine_retry_logic(sample_chunk):
    """Retry logic works correctly."""
    llm = Mock(spec=BaseLLM)
    # Fail twice, succeed on third attempt
    llm.generate.side_effect = [
        Exception("Error 1"),
        Exception("Error 2"),
        "Success on third try"
    ]
    
    refiner = ChunkRefiner(llm, max_retries=2)
    refined = refiner.refine(sample_chunk)
    
    assert refined.text == "Success on third try"
    assert llm.generate.call_count == 3


def test_build_prompt_without_context():
    """Build prompt without context."""
    llm = MockLLM()
    refiner = ChunkRefiner(llm)
    
    prompt = refiner._build_prompt("Test text")
    
    assert "Test text" in prompt
    assert "Refine" in prompt
    assert "Context" not in prompt


def test_build_prompt_with_context():
    """Build prompt with context."""
    llm = MockLLM()
    refiner = ChunkRefiner(llm)
    
    prompt = refiner._build_prompt("Test text", context="Previous content")
    
    assert "Test text" in prompt
    assert "Previous content" in prompt
    assert "Context" in prompt


def test_refine_batch():
    """Refine multiple chunks."""
    llm = MockLLM(response="Refined")
    refiner = ChunkRefiner(llm)
    
    chunks = [
        Chunk(id=f"chunk-{i}", text=f"Text {i}", doc_id="doc-1", chunk_index=i, metadata={})
        for i in range(3)
    ]
    
    refined_chunks = refiner.refine_batch(chunks)
    
    assert len(refined_chunks) == 3
    assert all(c.text == "Refined" for c in refined_chunks)
    assert llm.call_count == 3


def test_refine_batch_with_contexts():
    """Refine batch with contexts."""
    llm = MockLLM(response="Refined")
    refiner = ChunkRefiner(llm)
    
    chunks = [
        Chunk(id=f"chunk-{i}", text=f"Text {i}", doc_id="doc-1", chunk_index=i, metadata={})
        for i in range(2)
    ]
    contexts = ["Context 1", "Context 2"]
    
    refined_chunks = refiner.refine_batch(chunks, contexts=contexts)
    
    assert len(refined_chunks) == 2


def test_refine_batch_mismatched_lengths():
    """Raise error when chunks and contexts length mismatch."""
    llm = MockLLM()
    refiner = ChunkRefiner(llm)
    
    chunks = [
        Chunk(id="chunk-1", text="Text", doc_id="doc-1", chunk_index=0, metadata={})
    ]
    contexts = ["Context 1", "Context 2"]
    
    with pytest.raises(ValueError, match="contexts must have same length"):
        refiner.refine_batch(chunks, contexts=contexts)


def test_refine_preserves_chunk_id(sample_chunk):
    """Refined chunk preserves original ID."""
    llm = MockLLM(response="New text")
    refiner = ChunkRefiner(llm)
    
    refined = refiner.refine(sample_chunk)
    
    assert refined.id == sample_chunk.id
    assert refined.doc_id == sample_chunk.doc_id
    assert refined.chunk_index == sample_chunk.chunk_index
