"""向量存储抽象层

定义向量存储的统一接口规范。
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseVectorStore(ABC):
    """向量存储抽象基类

    所有向量存储实现都应继承此类并实现抽象方法。
    支持双向量检索（Dense + Sparse）。
    """

    def __init__(self, collection_name: str, **kwargs: Any):
        """初始化向量存储

        Args:
            collection_name: 集合名称
            **kwargs: 其他参数
        """
        self.collection_name = collection_name
        self.kwargs = kwargs

    @abstractmethod
    def upsert(
        self,
        ids: List[str],
        texts: List[str],
        dense_vectors: List[List[float]],
        sparse_vectors: List[Dict[str, Any]],
        metadata: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any
    ) -> None:
        """插入或更新向量

        Args:
            ids: 文档 ID 列表
            texts: 文本内容列表
            dense_vectors: 稠密向量列表
            sparse_vectors: 稀疏向量列表（格式：{"indices": [...], "values": [...]}）
            metadata: 元数据列表
            **kwargs: 其他参数
        """
        pass

    @abstractmethod
    def search_dense(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filter_expr: Optional[str] = None,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """稠密向量检索

        Args:
            query_vector: 查询向量
            top_k: 返回结果数量
            filter_expr: 过滤表达式
            **kwargs: 其他参数

        Returns:
            检索结果列表，每个结果包含：id, text, score, metadata
        """
        pass

    @abstractmethod
    def search_sparse(
        self,
        query_vector: Dict[str, Any],
        top_k: int = 10,
        filter_expr: Optional[str] = None,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """稀疏向量检索

        Args:
            query_vector: 查询向量（格式：{"indices": [...], "values": [...]}）
            top_k: 返回结果数量
            filter_expr: 过滤表达式
            **kwargs: 其他参数

        Returns:
            检索结果列表，每个结果包含：id, text, score, metadata
        """
        pass

    @abstractmethod
    def get_by_ids(self, ids: List[str], **kwargs: Any) -> List[Dict[str, Any]]:
        """根据 ID 获取记录

        Args:
            ids: 文档 ID 列表
            **kwargs: 其他参数

        Returns:
            记录列表
        """
        pass

    @abstractmethod
    def delete(self, ids: List[str], **kwargs: Any) -> None:
        """删除记录

        Args:
            ids: 文档 ID 列表
            **kwargs: 其他参数
        """
        pass

    @abstractmethod
    def count(self, **kwargs: Any) -> int:
        """获取记录总数

        Args:
            **kwargs: 其他参数

        Returns:
            记录数量
        """
        pass

    def __repr__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}(collection_name={self.collection_name})"
