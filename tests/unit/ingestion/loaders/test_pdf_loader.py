"""Tests for PDFLoader."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import hashlib

from src.ingestion.types import Document


@pytest.fixture
def mock_pymupdf():
    """Mock PyMuPDF module."""
    with patch.dict('sys.modules', {'fitz': MagicMock()}):
        yield


@pytest.fixture
def mock_pdf_doc():
    """Create a mock PyMuPDF document."""
    doc = MagicMock()
    doc.__len__ = Mock(return_value=2)
    
    page1 = Mock()
    page1.get_text.return_value = "Page 1 content"
    
    page2 = Mock()
    page2.get_text.return_value = "Page 2 content"
    
    doc.__getitem__ = Mock(side_effect=[page1, page2])
    doc.metadata = {
        "title": "Test Document",
        "author": "Test Author",
        "subject": "Test Subject"
    }
    doc.close = Mock()
    
    return doc


@patch('src.ingestion.loaders.pdf_loader.HAS_PYMUPDF', True)
@patch('src.ingestion.loaders.pdf_loader.fitz', MagicMock())
def test_pdf_loader_instantiation():
    """PDFLoader can be instantiated when PyMuPDF is available."""
    from src.ingestion.loaders.pdf_loader import PDFLoader
    loader = PDFLoader()
    assert loader is not None


def test_pdf_loader_missing_dependency():
    """PDFLoader raises ImportError when PyMuPDF is not installed."""
    with patch('src.ingestion.loaders.pdf_loader.HAS_PYMUPDF', False):
        from src.ingestion.loaders.pdf_loader import PDFLoader
        with pytest.raises(ImportError, match="PyMuPDF is required"):
            PDFLoader()


@patch('src.ingestion.loaders.pdf_loader.HAS_PYMUPDF', True)
@patch('src.ingestion.loaders.pdf_loader.fitz', MagicMock())
def test_pdf_loader_file_not_found():
    """Loading non-existent file raises FileNotFoundError."""
    from src.ingestion.loaders.pdf_loader import PDFLoader
    loader = PDFLoader()
    with pytest.raises(FileNotFoundError):
        loader.load("nonexistent.pdf")


@patch('src.ingestion.loaders.pdf_loader.HAS_PYMUPDF', True)
@patch('src.ingestion.loaders.pdf_loader.fitz', MagicMock())
def test_pdf_loader_invalid_file_type(tmp_path):
    """Loading non-PDF file raises ValueError."""
    from src.ingestion.loaders.pdf_loader import PDFLoader
    
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("dummy")
    
    loader = PDFLoader()
    with pytest.raises(ValueError, match="Not a PDF file"):
        loader.load(txt_file)


@patch('src.ingestion.loaders.pdf_loader.HAS_PYMUPDF', True)
def test_pdf_loader_load_success(mock_pdf_doc, tmp_path):
    """Successfully load a PDF file."""
    from src.ingestion.loaders.pdf_loader import PDFLoader
    
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_text("dummy")
    
    with patch('src.ingestion.loaders.pdf_loader.fitz') as mock_fitz:
        mock_fitz.open.return_value = mock_pdf_doc
        
        loader = PDFLoader()
        doc = loader.load(pdf_file)
        
        assert isinstance(doc, Document)
        assert "Page 1 content" in doc.text
        assert "Page 2 content" in doc.text
        assert doc.source == str(pdf_file)
        assert doc.metadata["page_count"] == 2
        assert doc.metadata["filename"] == "test.pdf"
        assert doc.metadata["title"] == "Test Document"
        assert doc.metadata["author"] == "Test Author"
        
        mock_pdf_doc.close.assert_called_once()


@patch('src.ingestion.loaders.pdf_loader.HAS_PYMUPDF', True)
def test_pdf_loader_metadata_extraction(tmp_path):
    """Metadata is correctly extracted."""
    from src.ingestion.loaders.pdf_loader import PDFLoader
    
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_text("dummy")
    
    mock_doc = MagicMock()
    mock_doc.__len__ = Mock(return_value=1)
    page = Mock()
    page.get_text.return_value = "Content"
    mock_doc.__getitem__ = Mock(return_value=page)
    mock_doc.metadata = {
        "title": "My Title",
        "author": "My Author",
        "creator": "My Creator"
    }
    mock_doc.close = Mock()
    
    with patch('src.ingestion.loaders.pdf_loader.fitz') as mock_fitz:
        mock_fitz.open.return_value = mock_doc
        
        loader = PDFLoader()
        doc = loader.load(pdf_file)
        
        assert doc.metadata["title"] == "My Title"
        assert doc.metadata["author"] == "My Author"
        assert doc.metadata["creator"] == "My Creator"
        assert doc.metadata["page_count"] == 1


@patch('src.ingestion.loaders.pdf_loader.HAS_PYMUPDF', True)
def test_pdf_loader_empty_metadata(tmp_path):
    """Handle PDF with no metadata."""
    from src.ingestion.loaders.pdf_loader import PDFLoader
    
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_text("dummy")
    
    mock_doc = MagicMock()
    mock_doc.__len__ = Mock(return_value=1)
    page = Mock()
    page.get_text.return_value = "Content"
    mock_doc.__getitem__ = Mock(return_value=page)
    mock_doc.metadata = {}
    mock_doc.close = Mock()
    
    with patch('src.ingestion.loaders.pdf_loader.fitz') as mock_fitz:
        mock_fitz.open.return_value = mock_doc
        
        loader = PDFLoader()
        doc = loader.load(pdf_file)
        
        assert "page_count" in doc.metadata
        assert "filename" in doc.metadata
        assert "file_size" in doc.metadata


@patch('src.ingestion.loaders.pdf_loader.HAS_PYMUPDF', True)
def test_pdf_loader_id_generation(tmp_path):
    """Document ID is consistently generated from file path."""
    from src.ingestion.loaders.pdf_loader import PDFLoader
    
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_text("dummy")
    
    # Create fresh mock for each call
    def create_mock_doc():
        mock_doc = MagicMock()
        mock_doc.__len__ = Mock(return_value=2)
        page1 = Mock()
        page1.get_text.return_value = "Page 1"
        page2 = Mock()
        page2.get_text.return_value = "Page 2"
        mock_doc.__getitem__ = Mock(side_effect=[page1, page2])
        mock_doc.metadata = {}
        mock_doc.close = Mock()
        return mock_doc
    
    with patch('src.ingestion.loaders.pdf_loader.fitz') as mock_fitz:
        mock_fitz.open.side_effect = [create_mock_doc(), create_mock_doc()]
        
        loader = PDFLoader()
        doc1 = loader.load(pdf_file)
        doc2 = loader.load(pdf_file)
        
        assert doc1.id == doc2.id
        
        expected_id = hashlib.md5(str(pdf_file.absolute()).encode()).hexdigest()
        assert doc1.id == expected_id


@patch('src.ingestion.loaders.pdf_loader.HAS_PYMUPDF', True)
def test_pdf_loader_handles_exception(tmp_path):
    """Handle exception during PDF loading."""
    from src.ingestion.loaders.pdf_loader import PDFLoader
    
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_text("dummy")
    
    with patch('src.ingestion.loaders.pdf_loader.fitz') as mock_fitz:
        mock_fitz.open.side_effect = Exception("PDF corrupted")
        
        loader = PDFLoader()
        with pytest.raises(ValueError, match="Failed to load PDF"):
            loader.load(pdf_file)
