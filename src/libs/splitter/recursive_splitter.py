"""递归文本分块器

基于分隔符优先级递归分割文本，确保块大小在限制范围内。
"""
from typing import Any, List

from .base import BaseSplitter


class RecursiveSplitter(BaseSplitter):
    """递归文本分块器

    按照分隔符优先级递归分割文本：
    1. 段落分隔符 (\\n\\n)
    2. 句子分隔符 (。！？\\n)
    3. 单词分隔符 (空格)
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: List[str] = None,
        **kwargs: Any
    ):
        """初始化递归分块器

        Args:
            chunk_size: 块大小（字符数）
            chunk_overlap: 块之间的重叠（字符数）
            separators: 分隔符列表（优先级从高到低）
            **kwargs: 其他参数
        """
        super().__init__(chunk_size=chunk_size, chunk_overlap=chunk_overlap, **kwargs)

        # 默认分隔符（中英文通用）
        if separators is None:
            self.separators = [
                "\n\n",  # 段落分隔
                "\n",    # 行分隔
                "。",    # 中文句号
                "！",    # 中文感叹号
                "？",    # 中文问号
                ".",     # 英文句号
                "!",     # 英文感叹号
                "?",     # 英文问号
                " ",     # 空格
                ""       # 字符级分割（最后手段）
            ]
        else:
            self.separators = separators

    def split(self, text: str, **kwargs: Any) -> List[str]:
        """将文本递归分割成块

        Args:
            text: 输入文本
            **kwargs: 其他分割参数

        Returns:
            文本块列表
        """
        if not text:
            return []

        return self._split_recursive(text, self.separators)

    def _split_recursive(self, text: str, separators: List[str]) -> List[str]:
        """递归分割文本

        Args:
            text: 输入文本
            separators: 当前可用的分隔符列表

        Returns:
            文本块列表
        """
        # 如果文本已经足够小，直接返回
        if len(text) <= self.chunk_size:
            return [text] if text else []

        # 如果没有更多分隔符，强制切分
        if not separators:
            return self._force_split(text)

        # 尝试使用当前分隔符分割
        separator = separators[0]
        remaining_separators = separators[1:]

        # 空分隔符表示字符级分割
        if separator == "":
            return self._force_split(text)

        # 按分隔符分割
        splits = text.split(separator)

        # 如果分隔符不存在，尝试下一个
        if len(splits) == 1:
            return self._split_recursive(text, remaining_separators)

        # 合并分割后的片段
        chunks = []
        current_chunk = []
        current_length = 0

        for i, split in enumerate(splits):
            # 重新添加分隔符（除了最后一个）
            if i < len(splits) - 1:
                split_with_sep = split + separator
            else:
                split_with_sep = split

            split_length = len(split_with_sep)

            # 如果单个片段就超过限制，递归分割
            if split_length > self.chunk_size:
                # 先保存当前累积的块
                if current_chunk:
                    chunks.append("".join(current_chunk))
                    current_chunk = []
                    current_length = 0

                # 递归分割大片段
                sub_chunks = self._split_recursive(split_with_sep, remaining_separators)
                chunks.extend(sub_chunks)
                continue

            # 如果加入当前片段会超过限制
            if current_length + split_length > self.chunk_size:
                # 保存当前块
                if current_chunk:
                    chunks.append("".join(current_chunk))

                # 计算重叠部分
                overlap_text = self._get_overlap(current_chunk)
                current_chunk = [overlap_text] if overlap_text else []
                current_length = len(overlap_text)

            # 加入当前片段
            current_chunk.append(split_with_sep)
            current_length += split_length

        # 保存最后一个块
        if current_chunk:
            chunks.append("".join(current_chunk))

        return chunks

    def _force_split(self, text: str) -> List[str]:
        """强制按字符数分割

        Args:
            text: 输入文本

        Returns:
            文本块列表
        """
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size
            chunks.append(text[start:end])
            start = end - self.chunk_overlap

        return chunks

    def _get_overlap(self, chunks: List[str]) -> str:
        """获取重叠部分

        Args:
            chunks: 当前块列表

        Returns:
            重叠文本
        """
        if not chunks:
            return ""

        full_text = "".join(chunks)
        if len(full_text) <= self.chunk_overlap:
            return full_text

        return full_text[-self.chunk_overlap:]
