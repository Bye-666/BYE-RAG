#!/usr/bin/env python3
"""
Query script for RAG system.

Usage:
    python scripts/query.py "<your query>" [options]
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import Settings
from src.retrieval.query_processor import QueryProcessor
from src.retrieval.hybrid_search import HybridSearch
from src.retrieval.retrievers.dense_retriever import DenseRetriever
from src.retrieval.retrievers.sparse_retriever import SparseRetriever
from src.retrieval.reranker_module import RerankerModule
from src.ingestion.embedders.sparse_encoder import BM25SparseEncoder
from src.libs.loader import ComponentLoader


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Query the RAG system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic query
  python scripts/query.py "What is machine learning?"

  # Query with rewriting
  python scripts/query.py "What is ML?" --rewrite

  # Limit results
  python scripts/query.py "Python tutorial" --top-k 5

  # With reranking
  python scripts/query.py "Deep learning" --rerank
"""
    )

    parser.add_argument(
        'query',
        type=str,
        help='Query text'
    )

    parser.add_argument(
        '--config',
        type=str,
        default='config/settings.yaml',
        help='Config file path'
    )

    parser.add_argument(
        '--top-k',
        type=int,
        default=10,
        help='Number of results to return'
    )

    parser.add_argument(
        '--rewrite',
        action='store_true',
        help='Rewrite query using LLM'
    )

    parser.add_argument(
        '--rerank',
        action='store_true',
        help='Rerank results using reranker'
    )

    args = parser.parse_args()

    # Load config
    try:
        config = Settings.from_yaml(args.config)
    except Exception:
        config = Settings()

    print(f"Query: {args.query}\n")

    # Initialize components
    print("Initializing components...")

    try:
        component_loader = ComponentLoader(config)

        # LLM and Embedding
        llm = component_loader.get_llm() if args.rewrite else None
        embedding = component_loader.get_embedding()
        vector_store = component_loader.get_vector_store()
        reranker = component_loader.get_reranker() if args.rerank else None

        # Load BM25 encoder
        sparse_encoder_path = Path("data/db/bm25_encoder.pkl")
        if not sparse_encoder_path.exists():
            print(f"Error: BM25 encoder not found at {sparse_encoder_path}")
            print("Please run ingestion first: python scripts/ingest.py <documents>")
            sys.exit(1)

        sparse_encoder = BM25SparseEncoder.load(sparse_encoder_path)

        # Query processor
        query_processor = QueryProcessor(llm, embedding, sparse_encoder)

        # Retrievers
        dense_retriever = DenseRetriever(vector_store)
        sparse_retriever = SparseRetriever(vector_store)

        # Hybrid search
        hybrid_search = HybridSearch(dense_retriever, sparse_retriever)

        # Reranker
        reranker_module = RerankerModule(reranker)

        print("Components initialized\n")

    except Exception as e:
        print(f"Error initializing components: {e}")
        sys.exit(1)

    # Process query
    print("Processing query...")
    processed = query_processor.process(args.query, rewrite=args.rewrite)

    if processed.get("rewritten"):
        print(f"Rewritten query: {processed['processed_query']}\n")

    # Search
    print("Searching...")
    results = hybrid_search.search(
        dense_vector=processed["dense_vector"],
        sparse_vector=processed["sparse_vector"],
        top_k=args.top_k
    )

    print(f"Found {len(results)} results\n")

    # Rerank if requested
    if args.rerank and reranker:
        print("Reranking...")
        results = reranker_module.rerank(
            query=processed["processed_query"],
            results=results,
            top_k=args.top_k
        )
        print(f"Reranked to {len(results)} results\n")

    # Display results
    print("=" * 80)
    print("Results")
    print("=" * 80)

    for i, result in enumerate(results, 1):
        print(f"\n{i}. [{result['id']}]")
        print(f"   Text: {result.get('text', 'N/A')[:200]}...")

        if 'rrf_score' in result:
            print(f"   RRF Score: {result['rrf_score']:.4f}")

        if 'rerank_score' in result:
            print(f"   Rerank Score: {result['rerank_score']:.4f}")

        if 'metadata' in result:
            print(f"   Metadata: {result['metadata']}")

    print("\n" + "=" * 80)
    print(f"Query completed: {len(results)} results returned")


if __name__ == '__main__':
    main()
