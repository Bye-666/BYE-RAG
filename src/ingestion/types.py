"""Ingestion Pipeline 核心数据类型

定义数据摄取流程中的核心数据结构。
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Document:
    """文档数据类

    表示加载后的原始文档。
    """
    id: str
    text: str
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"Document(id={self.id}, source={self.source}, text_len={len(self.text)})"


@dataclass
class Chunk:
    """文本块数据类

    表示文档分块后的片段。
    """
    id: str
    text: str
    doc_id: str
    chunk_index: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"Chunk(id={self.id}, doc_id={self.doc_id}, index={self.chunk_index}, text_len={len(self.text)})"


@dataclass
class ChunkRecord:
    """Chunk 记录数据类

    表示向量化后准备存储的完整记录。
    """
    id: str
    text: str
    dense_vector: List[float]
    sparse_vector: Dict[str, Any]  # {"indices": [...], "values": [...]}
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"ChunkRecord(id={self.id}, dense_dim={len(self.dense_vector)}, sparse_dim={len(self.sparse_vector.get('indices', []))})"
