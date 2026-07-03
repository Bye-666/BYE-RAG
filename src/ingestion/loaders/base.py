"""Base class for document loaders."""

from abc import ABC, abstractmethod
from typing import List
from pathlib import Path

from ..types import Document


class BaseLoader(ABC):
    """Abstract base class for document loaders.

    Loaders are responsible for reading files and converting them
    into Document objects for further processing.
    """

    @abstractmethod
    def load(self, file_path: str | Path) -> Document:
        """Load a single document from file.

        Args:
            file_path: Path to the document file

        Returns:
            Document object containing the loaded content

        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file format is not supported
        """
        pass

    def load_batch(self, file_paths: List[str | Path]) -> List[Document]:
        """Load multiple documents from files.

        Default implementation loads files sequentially.
        Subclasses can override for parallel loading.

        Args:
            file_paths: List of file paths to load

        Returns:
            List of Document objects
        """
        return [self.load(fp) for fp in file_paths]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
