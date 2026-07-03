"""PDF document loader using PyMuPDF."""

from pathlib import Path
from typing import Dict, Any, Optional
import hashlib

from .base import BaseLoader
from ..types import Document

# Optional import - PyMuPDF may not be installed
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    fitz = None


class PDFLoader(BaseLoader):
    """Loader for PDF documents using PyMuPDF (fitz).
    
    Requires PyMuPDF: pip install pymupdf
    """

    def __init__(self):
        """Initialize PDFLoader.
        
        Raises:
            ImportError: If PyMuPDF is not installed
        """
        if not HAS_PYMUPDF:
            raise ImportError(
                "PyMuPDF is required for PDFLoader. "
                "Install with: pip install pymupdf"
            )

    def load(self, file_path: str | Path) -> Document:
        """Load a PDF document.

        Args:
            file_path: Path to the PDF file

        Returns:
            Document object with extracted text and metadata

        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file is not a valid PDF
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if file_path.suffix.lower() != '.pdf':
            raise ValueError(f"Not a PDF file: {file_path}")

        try:
            doc = fitz.open(str(file_path))
            
            # Extract text from all pages
            text_parts = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                text_parts.append(page.get_text())
            
            text = "\n".join(text_parts)
            
            # Extract metadata
            metadata = self._extract_metadata(doc, file_path)
            
            doc.close()
            
            # Generate document ID from file path hash
            doc_id = hashlib.md5(str(file_path.absolute()).encode()).hexdigest()
            
            return Document(
                id=doc_id,
                text=text,
                source=str(file_path),
                metadata=metadata
            )
            
        except Exception as e:
            raise ValueError(f"Failed to load PDF {file_path}: {e}")

    def _extract_metadata(self, doc, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from PDF document.

        Args:
            doc: PyMuPDF document object
            file_path: Path to the PDF file

        Returns:
            Dictionary of metadata
        """
        metadata = {
            "filename": file_path.name,
            "page_count": len(doc),
            "file_size": file_path.stat().st_size,
        }
        
        # Extract PDF metadata if available
        pdf_metadata = doc.metadata
        if pdf_metadata:
            if pdf_metadata.get("title"):
                metadata["title"] = pdf_metadata["title"]
            if pdf_metadata.get("author"):
                metadata["author"] = pdf_metadata["author"]
            if pdf_metadata.get("subject"):
                metadata["subject"] = pdf_metadata["subject"]
            if pdf_metadata.get("creator"):
                metadata["creator"] = pdf_metadata["creator"]
        
        return metadata
