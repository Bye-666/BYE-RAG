"""文本分块器抽象层

定义文本分块器的统一接口规范。
"""
from abc import ABC, abstractmethod
from typing import Any, List, Optional


class BaseSplitter(ABC):
    """文本分块器抽象基类

    所有文本分块器实现都应继承此类并实现抽象方法。
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        **kwargs: Any
    ):
        """初始化文本分块器

        Args:
            chunk_size: 块大小（字符数或 token 数）
            chunk_overlap: 块之间的重叠（字符数或 token 数）
            **kwargs: 其他参数
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.kwargs = kwargs

    @abstractmethod
    def split(self, text: str, **kwargs: Any) -> List[str]:
        """将文本分割成块

        Args:
            text: 输入文本
            **kwargs: 其他分割参数

        Returns:
            文本块列表

        Raises:
            Exception: 分割失败时抛出异常
        """
        pass

    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"{self.__class__.__name__}("
            f"chunk_size={self.chunk_size}, "
            f"chunk_overlap={self.chunk_overlap})"
        )
