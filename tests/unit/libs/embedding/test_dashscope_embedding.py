"""DashScope Embedding 单元测试"""
import os
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_dashscope():
    """Mock dashscope 模块"""
    mock_module = MagicMock()
    mock_module.TextEmbedding = MagicMock()
    with patch.dict("sys.modules", {"dashscope": mock_module}):
        yield mock_module


class TestDashScopeEmbedding:
    """DashScopeEmbedding 测试"""

    def test_import(self):
        """测试导入模块"""
        from src.libs.embedding.dashscope_embedding import DashScopeEmbedding
        assert DashScopeEmbedding is not None

    def test_init_with_api_key(self, mock_dashscope):
        """测试使用 API Key 初始化"""
        from src.libs.embedding.dashscope_embedding import DashScopeEmbedding
        emb = DashScopeEmbedding(api_key="test-key")
        assert emb.api_key == "test-key"
        assert emb.model == "text-embedding-v4"

    def test_init_from_env(self, mock_dashscope):
        """测试从环境变量获取 API Key"""
        os.environ["DASHSCOPE_API_KEY"] = "env-test-key"
        try:
            from src.libs.embedding.dashscope_embedding import DashScopeEmbedding
            emb = DashScopeEmbedding()
            assert emb.api_key == "env-test-key"
        finally:
            del os.environ["DASHSCOPE_API_KEY"]

    def test_init_without_api_key(self, mock_dashscope):
        """测试未设置 API Key 时抛出异常"""
        if "DASHSCOPE_API_KEY" in os.environ:
            del os.environ["DASHSCOPE_API_KEY"]

        from src.libs.embedding.dashscope_embedding import DashScopeEmbedding
        with pytest.raises(ValueError, match="API Key 未设置"):
            DashScopeEmbedding()

    def test_encode_success(self, mock_dashscope):
        """测试编码单个文本成功"""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.output.embeddings = [
            MagicMock(embedding=[0.1, 0.2, 0.3])
        ]
        mock_dashscope.TextEmbedding.call.return_value = mock_response

        from src.libs.embedding.dashscope_embedding import DashScopeEmbedding

        emb = DashScopeEmbedding(api_key="test-key")
        result = emb.encode("测试文本")

        assert result == [0.1, 0.2, 0.3]
        mock_dashscope.TextEmbedding.call.assert_called_once()

    def test_encode_batch_success(self, mock_dashscope):
        """测试批量编码成功"""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.output.embeddings = [
            MagicMock(embedding=[0.1, 0.2]),
            MagicMock(embedding=[0.3, 0.4])
        ]
        mock_dashscope.TextEmbedding.call.return_value = mock_response

        from src.libs.embedding.dashscope_embedding import DashScopeEmbedding

        emb = DashScopeEmbedding(api_key="test-key")
        result = emb.encode_batch(["文本1", "文本2"])

        assert result == [[0.1, 0.2], [0.3, 0.4]]
        mock_dashscope.TextEmbedding.call.assert_called_once()

    def test_encode_api_error(self, mock_dashscope):
        """测试 API 调用失败"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.code = "InvalidParameter"
        mock_response.message = "参数错误"
        mock_dashscope.TextEmbedding.call.return_value = mock_response

        from src.libs.embedding.dashscope_embedding import DashScopeEmbedding

        emb = DashScopeEmbedding(api_key="test-key")

        with pytest.raises(Exception, match="API 调用失败"):
            emb.encode("测试")

    def test_dimension_v4(self, mock_dashscope):
        """测试 v4 模型维度"""
        from src.libs.embedding.dashscope_embedding import DashScopeEmbedding
        emb = DashScopeEmbedding(model="text-embedding-v4", api_key="test-key")
        assert emb.dimension == 2048

    def test_dimension_v2(self, mock_dashscope):
        """测试 v2 模型维度"""
        from src.libs.embedding.dashscope_embedding import DashScopeEmbedding
        emb = DashScopeEmbedding(model="text-embedding-v2", api_key="test-key")
        assert emb.dimension == 1536

    def test_dimension_v1(self, mock_dashscope):
        """测试 v1 模型维度"""
        from src.libs.embedding.dashscope_embedding import DashScopeEmbedding
        emb = DashScopeEmbedding(model="text-embedding-v1", api_key="test-key")
        assert emb.dimension == 1536

    def test_dimension_unknown_model(self, mock_dashscope):
        """测试未知模型使用默认维度"""
        from src.libs.embedding.dashscope_embedding import DashScopeEmbedding
        emb = DashScopeEmbedding(model="unknown-model", api_key="test-key")
        assert emb.dimension == 2048  # 默认维度

    def test_repr(self, mock_dashscope):
        """测试字符串表示"""
        from src.libs.embedding.dashscope_embedding import DashScopeEmbedding
        emb = DashScopeEmbedding(model="text-embedding-v2", api_key="test-key")
        assert "DashScopeEmbedding" in repr(emb)
        assert "text-embedding-v2" in repr(emb)
