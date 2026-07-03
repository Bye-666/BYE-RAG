"""Dense Embedder

使用 Embedding 模型生成稠密向量。
"""
from typing import List

from ...libs.embedding.base import BaseEmbedding


class DenseEmbedder:
    """稠密向量编码器

    封装 Embedding 模型，批量生成向量。
    """

    def __init__(self, embedding: BaseEmbedding):
        """初始化编码器

        Args:
            embedding: Embedding 实例
        """
        self.embedding = embedding

    def encode(self, text: str) -> List[float]:
        """编码单个文本

        Args:
            text: 输入文本

        Returns:
            向量
        """
        return self.embedding.encode(text)

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """批量编码

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        return self.embedding.encode_batch(texts)
