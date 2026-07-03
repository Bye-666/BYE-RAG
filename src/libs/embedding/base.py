"""Embedding 抽象层

定义 Embedding 的统一接口规范。
"""
from abc import ABC, abstractmethod
from typing import Any, List, Optional


class BaseEmbedding(ABC):
    """Embedding 抽象基类

    所有 Embedding 实现都应继承此类并实现抽象方法。
    """

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        **kwargs: Any
    ):
        """初始化 Embedding

        Args:
            model: 模型名称
            api_key: API 密钥
            **kwargs: 其他参数
        """
        self.model = model
        self.api_key = api_key
        self.kwargs = kwargs

    @abstractmethod
    def encode(self, text: str, **kwargs: Any) -> List[float]:
        """编码单个文本为向量

        Args:
            text: 输入文本
            **kwargs: 其他编码参数

        Returns:
            向量（浮点数列表）

        Raises:
            Exception: 调用 API 失败时抛出异常
        """
        pass

    @abstractmethod
    def encode_batch(
        self,
        texts: List[str],
        **kwargs: Any
    ) -> List[List[float]]:
        """批量编码文本为向量

        Args:
            texts: 输入文本列表
            **kwargs: 其他编码参数

        Returns:
            向量列表

        Raises:
            Exception: 调用 API 失败时抛出异常
        """
        pass

    @property
    def dimension(self) -> int:
        """向量维度

        子类应该重写此属性返回实际维度。

        Returns:
            向量维度
        """
        raise NotImplementedError("子类必须实现 dimension 属性")

    def __repr__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}(model={self.model})"
