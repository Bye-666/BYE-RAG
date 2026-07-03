"""Loader 抽象层"""
from abc import ABC, abstractmethod
from typing import List

from ..types import Document


class BaseLoader(ABC):
    """文档加载器抽象基类"""

    @abstractmethod
    def load(self, file_path: str) -> Document:
        """加载单个文件

        Args:
            file_path: 文件路径

        Returns:
            Document 对象
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
