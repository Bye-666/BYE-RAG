"""End-to-end system tests for RAG pipeline."""

import pytest
from unittest.mock import Mock, patch

from src.config.settings import Settings
from src.retrieval.query_processor import QueryProcessor
from src.retrieval.hybrid_search import HybridSearch
from src.ingestion.pipeline import IngestionPipeline


class TestSystemE2E:
    """System-level end-to-end tests."""

    def test_system_imports(self):
        """All core modules can be imported."""
        # Config
        from src.config.settings import Settings

        # Libs
        from src.libs.llm.base import BaseLLM
        from src.libs.embedding.base import BaseEmbedding
        from src.libs.vector_store.base import BaseVectorStore
        from src.libs.splitter.base import BaseSplitter

        # Ingestion
        from src.ingestion.pipeline import IngestionPipeline
        from src.ingestion.loaders.base import BaseLoader
        from src.ingestion.embedders.dense_encoder import DenseEncoder
        from src.ingestion.embedders.sparse_encoder import BM25SparseEncoder

        # Retrieval
        from src.retrieval.query_processor import QueryProcessor
        from src.retrieval.hybrid_search import HybridSearch
        from src.retrieval.retrievers.dense_retriever import DenseRetriever
        from src.retrieval.retrievers.sparse_retriever import SparseRetriever
        from src.retrieval.fusion.rrf_fusion import RRFFusion

        # MCP Server
        from src.mcp_server.server import MCPServer

        # Infrastructure
        from src.trace.tracer import Tracer
        from src.dashboard.app import Dashboard
        from src.evaluation.evaluator import Evaluator

        assert True  # All imports succeeded


    def test_config_loading(self):
        """Configuration system works."""
        config = Settings()
        assert config is not None
        # Settings object exists and can be instantiated


    def test_query_processor_pipeline(self):
        """Query processor pipeline works."""
        from src.ingestion.embedders.sparse_encoder import BM25SparseEncoder
        from src.libs.embedding.base import BaseEmbedding

        # Mock embedding
        class MockEmbedding(BaseEmbedding):
            def __init__(self):
                super().__init__(model="mock")

            @property
            def dimension(self):
                return 128

            def encode(self, text):
                return [0.1] * 128

            def encode_batch(self, texts):
                return [[0.1] * 128 for _ in texts]

        # Mock sparse encoder
        sparse_encoder = BM25SparseEncoder()
        sparse_encoder.fit(["test document"])

        embedding = MockEmbedding()

        processor = QueryProcessor(None, embedding, sparse_encoder)
        result = processor.process("test query")

        assert "dense_vector" in result
        assert "sparse_vector" in result
        assert result["processed_query"] == "test query"


    def test_hybrid_search_pipeline(self):
        """Hybrid search pipeline works."""
        from src.retrieval.retrievers.dense_retriever import DenseRetriever
        from src.retrieval.retrievers.sparse_retriever import SparseRetriever
        from src.libs.vector_store.base import BaseVectorStore

        # Mock vector store
        class MockVectorStore(BaseVectorStore):
            def __init__(self):
                pass  # Skip base init

            def search_dense(self, query_vector, top_k, filter_dict=None):
                return [{"id": "doc1", "text": "Result 1", "score": 0.9}]

            def search_sparse(self, query_vector, top_k, filter_dict=None):
                return [{"id": "doc2", "text": "Result 2", "score": 2.0}]

            def get_by_ids(self, ids):
                return []

            def upsert(self, ids, texts, dense_vectors, sparse_vectors, metadatas):
                pass

            def delete(self, ids):
                pass

            def count(self):
                return 0

        vector_store = MockVectorStore()
        dense_retriever = DenseRetriever(vector_store)
        sparse_retriever = SparseRetriever(vector_store)

        hybrid_search = HybridSearch(dense_retriever, sparse_retriever)

        results = hybrid_search.search(
            dense_vector=[0.1] * 128,
            sparse_vector={"indices": [1], "values": [1.0]},
            top_k=10
        )

        assert len(results) > 0
        assert "rrf_score" in results[0]


    def test_trace_system(self):
        """Trace system works."""
        from src.trace.tracer import Tracer

        tracer = Tracer()
        tracer.start_trace("trace-1", "query")
        tracer.add_step("retrieval", {"results": 5})
        tracer.end_trace(result="success")

        traces = tracer.get_traces()
        assert len(traces) == 1
        assert traces[0]["trace_id"] == "trace-1"


    def test_dashboard_metrics(self):
        """Dashboard metrics work."""
        from src.dashboard.app import Dashboard

        dashboard = Dashboard()
        dashboard.log_query("test query", 5, 0.5)
        dashboard.log_ingestion("file.pdf", 10, True)

        stats = dashboard.get_stats()
        assert stats["total_queries"] == 1
        assert stats["total_ingestions"] == 1


    def test_evaluation_metrics(self):
        """Evaluation metrics work."""
        from src.evaluation.evaluator import Evaluator

        evaluator = Evaluator()
        result = evaluator.evaluate_retrieval(
            "query",
            ["doc1", "doc2"],
            ["doc1", "doc2"]
        )

        assert result["precision"] == 1.0
        assert result["recall"] == 1.0
        assert result["f1"] == 1.0


    @pytest.mark.asyncio
    async def test_mcp_server_tools(self):
        """MCP Server tools work."""
        from src.mcp_server.server import MCPServer

        server = MCPServer()

        # Test tool handlers
        ingest_result = await server._handle_ingest({"file_path": "test.pdf"})
        assert len(ingest_result) == 1

        query_result = await server._handle_query({"query": "test"})
        assert len(query_result) == 1

        list_result = await server._handle_list_documents({})
        assert len(list_result) == 1
