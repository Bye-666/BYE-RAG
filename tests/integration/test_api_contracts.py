"""Contract tests for API interfaces."""

import pytest
from src.retrieval.query_processor import QueryProcessor
from src.retrieval.hybrid_search import HybridSearch
from src.ingestion.pipeline import IngestionPipeline


class TestAPIContracts:
    """Contract tests for key API interfaces."""

    def test_query_processor_contract(self):
        """QueryProcessor has required interface."""
        # Check class exists and has required methods
        assert hasattr(QueryProcessor, '__init__')
        assert hasattr(QueryProcessor, 'process')
        assert hasattr(QueryProcessor, 'expand_query')


    def test_hybrid_search_contract(self):
        """HybridSearch has required interface."""
        assert hasattr(HybridSearch, '__init__')
        assert hasattr(HybridSearch, 'search')


    def test_ingestion_pipeline_contract(self):
        """IngestionPipeline has required interface."""
        assert hasattr(IngestionPipeline, '__init__')
        assert hasattr(IngestionPipeline, 'ingest_file')
        assert hasattr(IngestionPipeline, 'ingest_files')


    def test_query_processor_process_returns_dict(self):
        """QueryProcessor.process returns dict with required keys."""
        from unittest.mock import Mock

        mock_embedding = Mock()
        mock_embedding.encode.return_value = [0.1] * 128

        processor = QueryProcessor(embedding=mock_embedding)
        result = processor.process("test")

        # Check return type and keys
        assert isinstance(result, dict)
        assert "original_query" in result
        assert "processed_query" in result
        assert "dense_vector" in result


    def test_hybrid_search_search_returns_list(self):
        """HybridSearch.search returns list of results."""
        from unittest.mock import Mock
        from src.retrieval.retrievers.dense_retriever import DenseRetriever
        from src.retrieval.retrievers.sparse_retriever import SparseRetriever

        mock_store = Mock()
        mock_store.search_dense.return_value = []
        mock_store.search_sparse.return_value = []

        dense_retriever = DenseRetriever(mock_store)
        sparse_retriever = SparseRetriever(mock_store)

        search = HybridSearch(dense_retriever, sparse_retriever)
        results = search.search(
            dense_vector=[0.1] * 128,
            sparse_vector={"indices": [1], "values": [1.0]},
            top_k=10
        )

        # Check return type
        assert isinstance(results, list)
