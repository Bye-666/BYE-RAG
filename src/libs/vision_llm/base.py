"""Vision LLM 抽象层

定义 Vision LLM 的统一接口规范。
"""
from abc import ABC, abstractmethod
from typing import Any, Optional, Union


class BaseVisionLLM(ABC):
    """Vision LLM 抽象基类

    所有 Vision LLM 实现都应继承此类并实现抽象方法。
    """

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        **kwargs: Any
    ):
        """初始化 Vision LLM

        Args:
            model: 模型名称
            api_key: API 密钥
            **kwargs: 其他参数
        """
        self.model = model
        self.api_key = api_key
        self.kwargs = kwargs

    @abstractmethod
    def analyze_image(
        self,
        image: Union[str, bytes],
        prompt: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """分析图像并生成描述

        Args:
            image: 图像输入
                - str: 图像 URL 或本地文件路径
                - bytes: 图像二进制数据
            prompt: 提示词，指导如何分析图像（可选）
                - 如果为 None，使用默认提示词
            **kwargs: 其他生成参数（如 temperature, max_tokens）

        Returns:
            图像分析结果（文本描述）

        Raises:
            Exception: 调用 API 失败时抛出异常
        """
        pass

    def get_default_prompt(self) -> str:
        """获取默认提示词

        子类可以重写此方法提供自定义默认提示词。

        Returns:
            默认提示词
        """
        return "请详细描述这张图片的内容，包括主要对象、场景、文字等信息。"

    def __repr__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}(model={self.model})"
