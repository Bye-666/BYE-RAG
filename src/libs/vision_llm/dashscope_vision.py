"""DashScope (阿里云千问) Vision LLM 实现

支持的模型：
- qwen-vl-max: 最强视觉理解能力（默认）
- qwen-vl-plus: 速度更快，成本更低
"""
import os
from typing import Any, Optional, Union

from .base import BaseVisionLLM


class DashScopeVision(BaseVisionLLM):
    """DashScope Vision LLM 实现

    使用阿里云 DashScope API 调用千问视觉系列模型。
    """

    def __init__(
        self,
        model: str = "qwen-vl-max",
        api_key: Optional[str] = None,
        **kwargs: Any
    ):
        """初始化 DashScope Vision

        Args:
            model: 模型名称，默认 qwen-vl-max
            api_key: DashScope API Key，如果为 None 则从环境变量获取
            **kwargs: 其他参数
        """
        super().__init__(model=model, api_key=api_key, **kwargs)

        # 获取 API Key
        if self.api_key is None:
            self.api_key = os.environ.get("DASHSCOPE_API_KEY")

        if not self.api_key:
            raise ValueError(
                "DashScope API Key 未设置。请通过参数传入或设置环境变量 DASHSCOPE_API_KEY"
            )

        # 延迟导入
        try:
            import dashscope
            self.dashscope = dashscope
            self.dashscope.api_key = self.api_key
        except ImportError:
            raise ImportError(
                "dashscope 包未安装。请运行：pip install dashscope"
            )

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
                - bytes: 暂不支持（需要先转换为文件）
            prompt: 提示词，指导如何分析图像
            **kwargs: 其他生成参数

        Returns:
            图像分析结果（文本描述）

        Raises:
            Exception: API 调用失败时抛出异常
        """
        from dashscope import MultiModalConversation

        # 使用默认提示词
        if prompt is None:
            prompt = self.get_default_prompt()

        # 处理图像输入
        if isinstance(image, bytes):
            raise NotImplementedError(
                "暂不支持二进制数据，请先保存为文件或使用 URL"
            )

        # 构建消息
        messages = [
            {
                "role": "user",
                "content": [
                    {"image": image},  # 图像 URL 或本地路径
                    {"text": prompt}
                ]
            }
        ]

        # 合并参数
        generation_kwargs = {**self.kwargs, **kwargs}

        # 调用 API
        response = MultiModalConversation.call(
            model=self.model,
            messages=messages,
            **generation_kwargs
        )

        # 检查响应
        if response.status_code != 200:
            raise Exception(
                f"DashScope API 调用失败: {response.code} - {response.message}"
            )

        # 提取生成内容
        return response.output.choices[0].message.content[0]["text"]
