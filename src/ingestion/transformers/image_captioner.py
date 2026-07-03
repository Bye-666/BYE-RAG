"""Image captioning using Vision LLM."""

from pathlib import Path
from typing import Dict, Any, List
from ...libs.vision_llm.base import BaseVisionLLM


class ImageCaptioner:
    """Generate textual descriptions for images using Vision LLM.
    
    Converts images to searchable text by generating captions,
    enabling text-based retrieval of visual content.
    """

    def __init__(self, vision_llm: BaseVisionLLM, prompt_template: str = None):
        """Initialize ImageCaptioner.
        
        Args:
            vision_llm: Vision language model for image analysis
            prompt_template: Optional custom prompt template
        """
        self.vision_llm = vision_llm
        self.prompt_template = prompt_template or self._default_prompt()

    def caption(self, image_path: str | Path, additional_context: str = None) -> Dict[str, Any]:
        """Generate caption for an image.
        
        Args:
            image_path: Path to the image file
            additional_context: Optional context to guide captioning
            
        Returns:
            Dictionary with caption and metadata
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Build prompt
        prompt = self._build_prompt(additional_context)
        
        try:
            # Analyze image
            result = self.vision_llm.analyze_image(
                image_path=str(image_path),
                prompt=prompt
            )
            
            return {
                "caption": result,
                "image_path": str(image_path),
                "image_name": image_path.name,
                "captioning_success": True
            }
            
        except Exception as e:
            return {
                "caption": "",
                "image_path": str(image_path),
                "image_name": image_path.name,
                "captioning_success": False,
                "error": str(e)
            }

    def caption_batch(self, image_paths: List[str | Path], contexts: List[str] = None) -> List[Dict[str, Any]]:
        """Generate captions for multiple images.
        
        Args:
            image_paths: List of image file paths
            contexts: Optional list of contexts (same length as image_paths)
            
        Returns:
            List of caption dictionaries
        """
        if contexts is None:
            contexts = [None] * len(image_paths)
        
        if len(contexts) != len(image_paths):
            raise ValueError("contexts must have same length as image_paths")
        
        return [
            self.caption(img_path, ctx)
            for img_path, ctx in zip(image_paths, contexts)
        ]

    def _build_prompt(self, additional_context: str = None) -> str:
        """Build caption generation prompt.
        
        Args:
            additional_context: Optional additional context
            
        Returns:
            Formatted prompt
        """
        if additional_context:
            return f"{self.prompt_template}\n\nAdditional context: {additional_context}"
        return self.prompt_template

    def _default_prompt(self) -> str:
        """Default captioning prompt.
        
        Returns:
            Default prompt text
        """
        return """Analyze this image and provide a detailed description.

Include:
1. Main subjects or objects in the image
2. Actions or activities shown
3. Setting or environment
4. Notable details or characteristics

Provide a comprehensive but concise description (2-3 sentences)."""
