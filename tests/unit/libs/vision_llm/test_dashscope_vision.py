"""DashScope Vision LLM 单元测试"""
import os
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_dashscope():
    """Mock dashscope 模块"""
    mock_module = MagicMock()
    mock_module.MultiModalConversation = MagicMock()
    with patch.dict("sys.modules", {"dashscope": mock_module}):
        yield mock_module


class TestDashScopeVision:
    """DashScopeVision 测试"""

    def test_import(self):
        """测试导入模块"""
        from src.libs.vision_llm.dashscope_vision import DashScopeVision
        assert DashScopeVision is not None

    def test_init_with_api_key(self, mock_dashscope):
        """测试使用 API Key 初始化"""
        from src.libs.vision_llm.dashscope_vision import DashScopeVision
        vision = DashScopeVision(api_key="test-key")
        assert vision.api_key == "test-key"
        assert vision.model == "qwen-vl-max"

    def test_init_from_env(self, mock_dashscope):
        """测试从环境变量获取 API Key"""
        os.environ["DASHSCOPE_API_KEY"] = "env-test-key"
        try:
            from src.libs.vision_llm.dashscope_vision import DashScopeVision
            vision = DashScopeVision()
            assert vision.api_key == "env-test-key"
        finally:
            del os.environ["DASHSCOPE_API_KEY"]

    def test_init_without_api_key(self, mock_dashscope):
        """测试未设置 API Key 时抛出异常"""
        if "DASHSCOPE_API_KEY" in os.environ:
            del os.environ["DASHSCOPE_API_KEY"]

        from src.libs.vision_llm.dashscope_vision import DashScopeVision
        with pytest.raises(ValueError, match="API Key 未设置"):
            DashScopeVision()

    def test_analyze_image_with_url(self, mock_dashscope):
        """测试分析图像（URL）"""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.output.choices = [
            MagicMock(message=MagicMock(content=[{"text": "图像描述结果"}]))
        ]
        mock_dashscope.MultiModalConversation.call.return_value = mock_response

        from src.libs.vision_llm.dashscope_vision import DashScopeVision

        vision = DashScopeVision(api_key="test-key")
        result = vision.analyze_image("https://example.com/image.jpg")

        assert result == "图像描述结果"
        mock_dashscope.MultiModalConversation.call.assert_called_once()

    def test_analyze_image_with_local_path(self, mock_dashscope):
        """测试分析图像（本地路径）"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.output.choices = [
            MagicMock(message=MagicMock(content=[{"text": "本地图像描述"}]))
        ]
        mock_dashscope.MultiModalConversation.call.return_value = mock_response

        from src.libs.vision_llm.dashscope_vision import DashScopeVision

        vision = DashScopeVision(api_key="test-key")
        result = vision.analyze_image("/path/to/image.jpg")

        assert result == "本地图像描述"
        mock_dashscope.MultiModalConversation.call.assert_called_once()

    def test_analyze_image_with_custom_prompt(self, mock_dashscope):
        """测试使用自定义提示词"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.output.choices = [
            MagicMock(message=MagicMock(content=[{"text": "自定义分析结果"}]))
        ]
        mock_dashscope.MultiModalConversation.call.return_value = mock_response

        from src.libs.vision_llm.dashscope_vision import DashScopeVision

        vision = DashScopeVision(api_key="test-key")
        result = vision.analyze_image(
            "https://example.com/image.jpg",
            prompt="请识别图中的文字"
        )

        assert result == "自定义分析结果"
        # 验证消息包含自定义提示词
        call_args = mock_dashscope.MultiModalConversation.call.call_args
        messages = call_args.kwargs["messages"]
        assert messages[0]["content"][1]["text"] == "请识别图中的文字"

    def test_analyze_image_with_bytes(self, mock_dashscope):
        """测试二进制数据输入（暂不支持）"""
        from src.libs.vision_llm.dashscope_vision import DashScopeVision

        vision = DashScopeVision(api_key="test-key")

        with pytest.raises(NotImplementedError, match="暂不支持二进制数据"):
            vision.analyze_image(b"image_bytes")

    def test_analyze_image_api_error(self, mock_dashscope):
        """测试 API 调用失败"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.code = "InvalidParameter"
        mock_response.message = "参数错误"
        mock_dashscope.MultiModalConversation.call.return_value = mock_response

        from src.libs.vision_llm.dashscope_vision import DashScopeVision

        vision = DashScopeVision(api_key="test-key")

        with pytest.raises(Exception, match="API 调用失败"):
            vision.analyze_image("https://example.com/image.jpg")

    def test_get_default_prompt(self, mock_dashscope):
        """测试默认提示词"""
        from src.libs.vision_llm.dashscope_vision import DashScopeVision

        vision = DashScopeVision(api_key="test-key")
        default_prompt = vision.get_default_prompt()

        assert "描述" in default_prompt or "内容" in default_prompt

    def test_repr(self, mock_dashscope):
        """测试字符串表示"""
        from src.libs.vision_llm.dashscope_vision import DashScopeVision
        vision = DashScopeVision(model="qwen-vl-plus", api_key="test-key")
        assert "DashScopeVision" in repr(vision)
        assert "qwen-vl-plus" in repr(vision)

    def test_custom_model(self, mock_dashscope):
        """测试使用自定义模型"""
        from src.libs.vision_llm.dashscope_vision import DashScopeVision
        vision = DashScopeVision(model="qwen-vl-plus", api_key="test-key")
        assert vision.model == "qwen-vl-plus"
