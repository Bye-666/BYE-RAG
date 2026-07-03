"""Reranker 抽象层

定义 Reranker 的统一接口规范。
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseReranker(ABC):
    """Reranker 抽象基类

    所有 Reranker 实现都应继承此类并实现抽象方法。
    """

    def __init__(self, model: str = None, **kwargs: Any):
        """初始化 Reranker

        Args:
            model: 模型名称
            **kwargs: 其他参数
        """
        self.model = model
        self.kwargs = kwargs

    @abstractmethod
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 10,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """对文档进行重排序

        Args:
            query: 查询文本
            documents: 文档列表，每个文档包含 id, text, score 等字段
            top_k: 返回结果数量
            **kwargs: 其他参数

        Returns:
            重排序后的文档列表（按相关性降序）

        Raises:
            Exception: 重排序失败时抛出异常
        """
        pass

    def __repr__(self) -> str:
        """字符串表示"""
        model_str = f"model={self.model}" if self.model else "no model"
        return f"{self.__class__.__name__}({model_str})"
