"""Libs 层集成测试

测试 Factory 和 Loader 的集成功能。
"""
import pytest


class TestLibsIntegration:
    """Libs 层集成测试"""

    def test_component_factory_exists(self):
        """测试 ComponentFactory 存在"""
        from src.libs.factory import ComponentFactory
        assert ComponentFactory is not None

    def test_component_loader_exists(self):
        """测试 ComponentLoader 存在"""
        from src.libs.loader import ComponentLoader
        assert ComponentLoader is not None

    def test_factory_has_create_methods(self):
        """测试 Factory 包含所有创建方法"""
        from src.libs.factory import ComponentFactory

        required_methods = [
            "create_llm",
            "create_embedding",
            "create_vision_llm",
            "create_vector_store",
            "create_splitter",
            "create_reranker"
        ]

        for method in required_methods:
            assert hasattr(ComponentFactory, method)
            assert callable(getattr(ComponentFactory, method))

    def test_loader_has_get_methods(self):
        """测试 Loader 包含所有获取方法"""
        from src.libs.loader import ComponentLoader

        required_methods = [
            "get_llm",
            "get_embedding",
            "get_vision_llm",
            "get_vector_store",
            "get_splitter",
            "get_reranker"
        ]

        for method in required_methods:
            assert hasattr(ComponentLoader, method)

    def test_all_base_classes_importable(self):
        """测试所有基类可导入"""
        from src.libs.llm.base import BaseLLM
        from src.libs.embedding.base import BaseEmbedding
        from src.libs.vision_llm.base import BaseVisionLLM
        from src.libs.splitter.base import BaseSplitter
        from src.libs.vector_store.base import BaseVectorStore
        from src.libs.reranker.base import BaseReranker
        from src.libs.evaluator.base import BaseEvaluator

        assert all([
            BaseLLM, BaseEmbedding, BaseVisionLLM,
            BaseSplitter, BaseVectorStore, BaseReranker, BaseEvaluator
        ])

    def test_all_implementations_importable(self):
        """测试所有实现类可导入"""
        from src.libs.llm.dashscope_llm import DashScopeLLM
        from src.libs.embedding.dashscope_embedding import DashScopeEmbedding
        from src.libs.vision_llm.dashscope_vision import DashScopeVision
        from src.libs.splitter.recursive_splitter import RecursiveSplitter
        from src.libs.vector_store.milvus_store import MilvusStore
        from src.libs.reranker.cross_encoder import CrossEncoderReranker

        assert all([
            DashScopeLLM, DashScopeEmbedding, DashScopeVision,
            RecursiveSplitter, MilvusStore, CrossEncoderReranker
        ])
