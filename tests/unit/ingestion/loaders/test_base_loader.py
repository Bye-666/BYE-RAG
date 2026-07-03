"""Tests for BaseLoader abstract class."""

import pytest
from pathlib import Path

from src.ingestion.loaders.base import BaseLoader
from src.ingestion.types import Document


class ConcreteLoader(BaseLoader):
    """Concrete implementation for testing."""

    def load(self, file_path: str | Path) -> Document:
        """Load a document."""
        return Document(
            id=str(file_path),
            text=f"Content from {file_path}",
            source=str(file_path),
            metadata={"loader": "ConcreteLoader"}
        )


def test_baseloader_is_abstract():
    """BaseLoader cannot be instantiated directly."""
    with pytest.raises(TypeError):
        BaseLoader()


def test_concrete_loader_can_be_instantiated():
    """Concrete implementation can be instantiated."""
    loader = ConcreteLoader()
    assert isinstance(loader, BaseLoader)


def test_load_single_file():
    """Test loading a single file."""
    loader = ConcreteLoader()
    doc = loader.load("test.txt")

    assert isinstance(doc, Document)
    assert doc.id == "test.txt"
    assert doc.source == "test.txt"
    assert "Content from test.txt" in doc.text


def test_load_with_path_object():
    """Test loading with Path object."""
    loader = ConcreteLoader()
    doc = loader.load(Path("test.pdf"))

    assert isinstance(doc, Document)
    assert "test.pdf" in doc.id


def test_load_batch():
    """Test loading multiple files."""
    loader = ConcreteLoader()
    file_paths = ["file1.txt", "file2.txt", "file3.txt"]
    docs = loader.load_batch(file_paths)

    assert len(docs) == 3
    assert all(isinstance(doc, Document) for doc in docs)
    assert docs[0].id == "file1.txt"
    assert docs[1].id == "file2.txt"
    assert docs[2].id == "file3.txt"


def test_load_batch_with_path_objects():
    """Test load_batch with Path objects."""
    loader = ConcreteLoader()
    file_paths = [Path("file1.txt"), Path("file2.txt")]
    docs = loader.load_batch(file_paths)

    assert len(docs) == 2
    assert all(isinstance(doc, Document) for doc in docs)


def test_loader_repr():
    """Test string representation."""
    loader = ConcreteLoader()
    assert repr(loader) == "ConcreteLoader()"
