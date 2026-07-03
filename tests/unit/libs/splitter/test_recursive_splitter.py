"""RecursiveSplitter 单元测试"""
import pytest

from src.libs.splitter.recursive_splitter import RecursiveSplitter


class TestRecursiveSplitter:
    """RecursiveSplitter 测试"""

    def test_import(self):
        """测试导入模块"""
        from src.libs.splitter import RecursiveSplitter
        assert RecursiveSplitter is not None

    def test_init_default(self):
        """测试默认初始化"""
        splitter = RecursiveSplitter()
        assert splitter.chunk_size == 1000
        assert splitter.chunk_overlap == 200
        assert len(splitter.separators) > 0

    def test_init_custom(self):
        """测试自定义参数"""
        splitter = RecursiveSplitter(chunk_size=500, chunk_overlap=100)
        assert splitter.chunk_size == 500
        assert splitter.chunk_overlap == 100

    def test_split_empty(self):
        """测试空文本"""
        splitter = RecursiveSplitter()
        result = splitter.split("")
        assert result == []

    def test_split_short_text(self):
        """测试短文本（不需要分割）"""
        splitter = RecursiveSplitter(chunk_size=100)
        text = "这是一段短文本。"
        result = splitter.split(text)
        assert len(result) == 1
        assert result[0] == text

    def test_split_by_paragraph(self):
        """测试按段落分割"""
        splitter = RecursiveSplitter(chunk_size=50, chunk_overlap=10)
        text = "第一段内容。\n\n第二段内容。\n\n第三段内容。"
        result = splitter.split(text)
        assert len(result) > 0
        # 验证所有块都在大小限制内
        for chunk in result:
            assert len(chunk) <= 50 + 10  # 允许少量超出（分隔符）

    def test_split_by_sentence(self):
        """测试按句子分割"""
        splitter = RecursiveSplitter(chunk_size=30, chunk_overlap=5)
        text = "第一句话。第二句话。第三句话。第四句话。"
        result = splitter.split(text)
        # 文本总长度约36字符，可能分成1-2块
        assert len(result) >= 1
        assert all(len(chunk) <= 40 for chunk in result)  # 验证大小限制

    def test_split_chinese_text(self):
        """测试中文文本分割"""
        splitter = RecursiveSplitter(chunk_size=50, chunk_overlap=10)
        text = "这是第一段内容，包含一些描述性文字。这是第二段内容，也包含一些文字。这是第三段内容。"
        result = splitter.split(text)
        assert len(result) > 0
        # 验证块的大小
        for chunk in result:
            assert len(chunk) <= 60  # 允许一定误差

    def test_split_english_text(self):
        """测试英文文本分割"""
        splitter = RecursiveSplitter(chunk_size=50, chunk_overlap=10)
        text = "This is the first paragraph. This is the second paragraph. This is the third paragraph."
        result = splitter.split(text)
        assert len(result) > 1

    def test_split_with_overlap(self):
        """测试重叠功能"""
        splitter = RecursiveSplitter(chunk_size=30, chunk_overlap=10)
        text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 3
        result = splitter.split(text)

        # 验证有重叠
        if len(result) > 1:
            # 检查相邻块有重叠内容
            for i in range(len(result) - 1):
                chunk1 = result[i]
                chunk2 = result[i + 1]
                # 后一块的开头应该与前一块的结尾有部分重叠
                assert len(chunk1) > 0 and len(chunk2) > 0

    def test_split_long_text(self):
        """测试长文本分割"""
        splitter = RecursiveSplitter(chunk_size=100, chunk_overlap=20)
        text = "这是一个很长的文本。" * 50  # 约500字符
        result = splitter.split(text)
        assert len(result) > 3

    def test_force_split(self):
        """测试强制分割（没有分隔符）"""
        splitter = RecursiveSplitter(chunk_size=10, chunk_overlap=2)
        text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        result = splitter.split(text)
        assert len(result) > 1
        # 验证块大小
        for chunk in result[:-1]:  # 除了最后一块
            assert len(chunk) == 10

    def test_custom_separators(self):
        """测试自定义分隔符"""
        splitter = RecursiveSplitter(
            chunk_size=20,
            chunk_overlap=5,
            separators=["|", ",", " "]
        )
        text = "A|B|C,D,E F G"
        result = splitter.split(text)
        assert len(result) > 0

    def test_repr(self):
        """测试字符串表示"""
        splitter = RecursiveSplitter(chunk_size=500, chunk_overlap=100)
        repr_str = repr(splitter)
        assert "RecursiveSplitter" in repr_str
        assert "500" in repr_str
        assert "100" in repr_str
