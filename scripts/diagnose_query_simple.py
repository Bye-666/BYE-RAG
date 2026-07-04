"""Simplified diagnostic script that tests query functionality in one pass.

Usage:
    python scripts/diagnose_query_simple.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    """Run query diagnostic."""
    print("RAG Query Diagnostic Tool")
    print("=" * 50)

    try:
        from src.config.settings import Settings
        from src.libs.loader import ComponentLoader
        from src.ingestion.embedders.sparse_encoder import BM25SparseEncoder
        from src.retrieval.query_processor import QueryProcessor
        from src.retrieval.retrievers.dense_retriever import DenseRetriever
        from src.retrieval.retrievers.sparse_retriever import SparseRetriever
        from src.retrieval.hybrid_search import HybridSearch

        # Check BM25 encoder
        print("\n1. Checking BM25 Encoder...")
        encoder_path = Path("data/db/bm25_encoder.pkl")
        if not encoder_path.exists():
            print(f"[FAILED] BM25 encoder not found: {encoder_path}")
            return False
        print(f"[OK] BM25 encoder found")

        # Load config and components
        print("\n2. Loading components...")
        config = Settings.from_yaml("config/settings.yaml")
        loader = ComponentLoader(config)

        embedding = loader.get_embedding()
        vector_store = loader.get_vector_store()
        sparse_encoder = BM25SparseEncoder.load(encoder_path)

        print("[OK] Components loaded")

        # Check vector store stats
        print("\n3. Checking vector store...")
        stats = vector_store.get_collection_stats()
        row_count = stats.get("row_count", 0)
        print(f"[OK] Collection: {config.get('vector_store.collection_name')}")
        print(f"[OK] Total documents: {row_count}")

        if row_count == 0:
            print("[WARNING] No documents in collection!")
            return False

        # Initialize retrievers
        print("\n4. Initializing retrievers...")
        query_processor = QueryProcessor(None, embedding, sparse_encoder)
        dense_retriever = DenseRetriever(vector_store)
        sparse_retriever = SparseRetriever(vector_store)
        hybrid_search = HybridSearch(dense_retriever, sparse_retriever)
        print("[OK] Retrievers initialized")

        # Test query
        test_query = "扫地机器人怎么用"
        print(f"\n5. Testing query: '{test_query}'")

        # Process query
        processed = query_processor.process(test_query, rewrite=False)
        print(f"[OK] Query processed")
        print(f"  - Dense vector dim: {len(processed['dense_vector'])}")

        sparse_vec = processed['sparse_vector']
        if isinstance(sparse_vec, dict):
            print(f"  - Sparse vector terms: {len(sparse_vec)}")
            if len(sparse_vec) > 0:
                # Show some sample terms
                sample_terms = list(sparse_vec.items())[:3]
                print(f"  - Sample terms: {sample_terms}")

        # Test dense retrieval
        print("\n6. Testing dense retrieval...")
        dense_results = dense_retriever.retrieve(
            query_vector=processed["dense_vector"],
            top_k=5
        )
        print(f"[RESULT] Dense retrieval: {len(dense_results)} results")
        if dense_results:
            for i, result in enumerate(dense_results[:2], 1):
                print(f"  {i}. Score: {result.get('score', 0):.4f}")
                print(f"     Text: {result.get('text', '')[:80]}...")

        # Test sparse retrieval
        print("\n7. Testing sparse retrieval...")
        sparse_results = sparse_retriever.retrieve(
            query_vector=processed["sparse_vector"],
            top_k=5
        )
        print(f"[RESULT] Sparse retrieval: {len(sparse_results)} results")
        if sparse_results:
            for i, result in enumerate(sparse_results[:2], 1):
                print(f"  {i}. Score: {result.get('score', 0):.4f}")
                print(f"     Text: {result.get('text', '')[:80]}...")

        # Test hybrid search
        print("\n8. Testing hybrid search...")
        results = hybrid_search.search(
            dense_vector=processed["dense_vector"],
            sparse_vector=processed["sparse_vector"],
            top_k=5,
            enable_trace=False
        )

        print(f"\n{'='*50}")
        print(f"[RESULT] Hybrid search: {len(results)} results")
        print(f"{'='*50}")

        if len(results) > 0:
            print("\nTop results:")
            for i, result in enumerate(results, 1):
                text_preview = result.get("text", "")[:120]
                score = result.get("rrf_score", 0)
                print(f"\n{i}. RRF Score: {score:.4f}")
                print(f"   Text: {text_preview}...")

            print(f"\n[SUCCESS] Query functionality is working!")
            return True
        else:
            print("\n[WARNING] No results found")
            print("Possible reasons:")
            print("  - Query terms don't match document content")
            print("  - Documents might not be properly indexed")
            return False

    except Exception as e:
        print(f"\n[FAILED] Error during diagnostic: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[Interrupted]")
        sys.exit(1)
