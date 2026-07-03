"""Evaluator 抽象层"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseEvaluator(ABC):
    """Evaluator 抽象基类"""

    def __init__(self, **kwargs: Any):
        self.kwargs = kwargs

    @abstractmethod
    def evaluate(
        self,
        queries: List[str],
        contexts: List[List[str]],
        answers: List[str],
        ground_truths: List[str] = None,
        **kwargs: Any
    ) -> Dict[str, float]:
        """评估 RAG 系统

        Args:
            queries: 查询列表
            contexts: 检索到的上下文列表
            answers: 生成的答案列表
            ground_truths: 真实答案列表（可选）
            **kwargs: 其他参数

        Returns:
            评估指标字典
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
