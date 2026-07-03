"""Tests for ImageCaptioner."""

import pytest
from pathlib import Path
from unittest.mock import Mock

from src.ingestion.transformers.image_captioner import ImageCaptioner
from src.libs.vision_llm.base import BaseVisionLLM


class MockVisionLLM(BaseVisionLLM):
    """Mock Vision LLM for testing."""
    
    def __init__(self, response: str = "A detailed image description"):
        self.response = response
        self.call_count = 0
        
    def analyze_image(self, image_path: str, prompt: str, **kwargs) -> str:
        self.call_count += 1
        return self.response


def test_image_captioner_instantiation():
    """ImageCaptioner can be instantiated."""
    vision_llm = MockVisionLLM()
    captioner = ImageCaptioner(vision_llm)
    assert captioner.vision_llm == vision_llm
    assert captioner.prompt_template is not None


def test_image_captioner_custom_prompt():
    """ImageCaptioner accepts custom prompt template."""
    vision_llm = MockVisionLLM()
    custom_prompt = "Describe this image briefly."
    captioner = ImageCaptioner(vision_llm, prompt_template=custom_prompt)
    assert captioner.prompt_template == custom_prompt


def test_caption_success(tmp_path):
    """Generate caption successfully."""
    # Create a dummy image file
    image_file = tmp_path / "test.jpg"
    image_file.write_bytes(b"fake image data")
    
    vision_llm = MockVisionLLM(response="A person standing in a park")
    captioner = ImageCaptioner(vision_llm)
    
    result = captioner.caption(image_file)
    
    assert result["caption"] == "A person standing in a park"
    assert result["image_path"] == str(image_file)
    assert result["image_name"] == "test.jpg"
    assert result["captioning_success"] is True
    assert vision_llm.call_count == 1


def test_caption_with_path_object(tmp_path):
    """Caption works with Path object."""
    image_file = tmp_path / "test.png"
    image_file.write_bytes(b"fake")
    
    vision_llm = MockVisionLLM()
    captioner = ImageCaptioner(vision_llm)
    
    result = captioner.caption(Path(image_file))
    
    assert result["captioning_success"] is True


def test_caption_with_string_path(tmp_path):
    """Caption works with string path."""
    image_file = tmp_path / "test.jpg"
    image_file.write_bytes(b"fake")
    
    vision_llm = MockVisionLLM()
    captioner = ImageCaptioner(vision_llm)
    
    result = captioner.caption(str(image_file))
    
    assert result["captioning_success"] is True


def test_caption_file_not_found():
    """Raise error when image file doesn't exist."""
    vision_llm = MockVisionLLM()
    captioner = ImageCaptioner(vision_llm)
    
    with pytest.raises(FileNotFoundError):
        captioner.caption("nonexistent.jpg")


def test_caption_with_additional_context(tmp_path):
    """Caption with additional context."""
    image_file = tmp_path / "test.jpg"
    image_file.write_bytes(b"fake")
    
    vision_llm = MockVisionLLM()
    captioner = ImageCaptioner(vision_llm)
    
    result = captioner.caption(image_file, additional_context="This is from a vacation album")
    
    assert result["captioning_success"] is True


def test_caption_failure_handling(tmp_path):
    """Handle captioning failures gracefully."""
    image_file = tmp_path / "test.jpg"
    image_file.write_bytes(b"fake")
    
    vision_llm = Mock(spec=BaseVisionLLM)
    vision_llm.analyze_image.side_effect = Exception("Vision API error")
    
    captioner = ImageCaptioner(vision_llm)
    result = captioner.caption(image_file)
    
    assert result["captioning_success"] is False
    assert result["caption"] == ""
    assert "Vision API error" in result["error"]


def test_build_prompt_without_context():
    """Build prompt without additional context."""
    vision_llm = MockVisionLLM()
    captioner = ImageCaptioner(vision_llm)
    
    prompt = captioner._build_prompt()
    
    assert "Analyze this image" in prompt
    assert "Additional context" not in prompt


def test_build_prompt_with_context():
    """Build prompt with additional context."""
    vision_llm = MockVisionLLM()
    captioner = ImageCaptioner(vision_llm)
    
    prompt = captioner._build_prompt(additional_context="From chapter 3")
    
    assert "Analyze this image" in prompt
    assert "From chapter 3" in prompt


def test_default_prompt():
    """Default prompt is comprehensive."""
    vision_llm = MockVisionLLM()
    captioner = ImageCaptioner(vision_llm)
    
    prompt = captioner._default_prompt()
    
    assert "Analyze this image" in prompt
    assert "description" in prompt.lower()


def test_caption_batch(tmp_path):
    """Caption multiple images."""
    # Create dummy images
    images = []
    for i in range(3):
        img = tmp_path / f"test_{i}.jpg"
        img.write_bytes(b"fake")
        images.append(img)
    
    vision_llm = MockVisionLLM()
    captioner = ImageCaptioner(vision_llm)
    
    results = captioner.caption_batch(images)
    
    assert len(results) == 3
    assert all(r["captioning_success"] for r in results)
    assert vision_llm.call_count == 3


def test_caption_batch_with_contexts(tmp_path):
    """Caption batch with contexts."""
    images = []
    for i in range(2):
        img = tmp_path / f"test_{i}.jpg"
        img.write_bytes(b"fake")
        images.append(img)
    
    contexts = ["Context 1", "Context 2"]
    
    vision_llm = MockVisionLLM()
    captioner = ImageCaptioner(vision_llm)
    
    results = captioner.caption_batch(images, contexts=contexts)
    
    assert len(results) == 2


def test_caption_batch_mismatched_lengths(tmp_path):
    """Raise error when images and contexts length mismatch."""
    image = tmp_path / "test.jpg"
    image.write_bytes(b"fake")
    
    vision_llm = MockVisionLLM()
    captioner = ImageCaptioner(vision_llm)
    
    with pytest.raises(ValueError, match="contexts must have same length"):
        captioner.caption_batch([image], contexts=["c1", "c2"])


def test_caption_result_structure(tmp_path):
    """Caption result has expected structure."""
    image_file = tmp_path / "test.jpg"
    image_file.write_bytes(b"fake")
    
    vision_llm = MockVisionLLM(response="Test caption")
    captioner = ImageCaptioner(vision_llm)
    
    result = captioner.caption(image_file)
    
    assert "caption" in result
    assert "image_path" in result
    assert "image_name" in result
    assert "captioning_success" in result


def test_caption_batch_partial_failure(tmp_path):
    """Handle partial failures in batch processing."""
    images = []
    for i in range(2):
        img = tmp_path / f"test_{i}.jpg"
        img.write_bytes(b"fake")
        images.append(img)
    
    # Mock that fails on second call
    vision_llm = Mock(spec=BaseVisionLLM)
    vision_llm.analyze_image.side_effect = ["Success", Exception("Error")]
    
    captioner = ImageCaptioner(vision_llm)
    results = captioner.caption_batch(images)
    
    assert len(results) == 2
    assert results[0]["captioning_success"] is True
    assert results[1]["captioning_success"] is False
