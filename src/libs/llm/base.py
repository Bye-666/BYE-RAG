"""LLM 抽象层

定义 LLM 的统一接口规范。
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Generator, List, Optional


class BaseLLM(ABC):
    """LLM 抽象基类

    所有 LLM 实现都应继承此类并实现抽象方法。
    """

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        **kwargs: Any
    ):
        """初始化 LLM

        Args:
            model: 模型名称
            api_key: API 密钥
            **kwargs: 其他参数（如 temperature, max_tokens 等）
        """
        self.model = model
        self.api_key = api_key
        self.kwargs = kwargs

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """同步生成文本

        Args:
            prompt: 用户输入提示词
            system_prompt: 系统提示词（可选）
            **kwargs: 其他生成参数（如 temperature, max_tokens）

        Returns:
            生成的文本内容

        Raises:
            Exception: 调用 API 失败时抛出异常
        """
        pass

    @abstractmethod
    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any
    ) -> Generator[str, None, None]:
        """流式生成文本

        Args:
            prompt: 用户输入提示词
            system_prompt: 系统提示词（可选）
            **kwargs: 其他生成参数

        Yields:
            生成的文本片段（增量内容）

        Raises:
            Exception: 调用 API 失败时抛出异常
        """
        pass

    def __repr__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}(model={self.model})"
