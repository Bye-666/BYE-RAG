#!/usr/bin/env python3
"""
Evaluation script for RAG system.

Usage:
    python scripts/evaluate.py [options]
"""

import sys
import argparse
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.evaluation.evaluator import Evaluator
from src.evaluation.composite_evaluator import CompositeEvaluator


def load_golden_test_set(file_path: str) -> list:
    """Load golden test set from JSON file.

    Args:
        file_path: Path to test set file

    Returns:
        List of test cases
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Evaluate RAG system performance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate with default test set
  python scripts/evaluate.py

  # Evaluate with custom test set
  python scripts/evaluate.py --test-set data/test_golden.json

  # Output results to file
  python scripts/evaluate.py --output results.json
"""
    )

    parser.add_argument(
        '--test-set',
        type=str,
        default='data/test_golden.json',
        help='Path to golden test set'
    )

    parser.add_argument(
        '--output',
        type=str,
        help='Output file for results'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("RAG System Evaluation")
    print("=" * 60)
    print()

    # Initialize evaluator
    evaluator = CompositeEvaluator()

    # Load test set
    try:
        test_cases = load_golden_test_set(args.test_set)
        print(f"Loaded {len(test_cases)} test cases from {args.test_set}")
    except FileNotFoundError:
        print(f"Warning: Test set not found at {args.test_set}")
        print("Using sample test data...")
        test_cases = [
            {
                "query": "What is machine learning?",
                "retrieved": ["doc1", "doc2", "doc3"],
                "relevant": ["doc1", "doc2"]
            }
        ]

    print()
    print("Running evaluation...")
    print("-" * 60)

    # Run evaluation
    results = []
    for i, case in enumerate(test_cases, 1):
        print(f"[{i}/{len(test_cases)}] Evaluating: {case['query'][:50]}...")

        result = evaluator.evaluate_retrieval(
            query=case['query'],
            retrieved_docs=case['retrieved'],
            relevant_docs=case['relevant']
        )

        results.append(result)

    print()
    print("=" * 60)
    print("Evaluation Results")
    print("=" * 60)

    # Aggregate results
    if results:
        aggregate = results[0].get("aggregate", {})

        print()
        print(f"Average Precision: {aggregate.get('avg_precision', 0):.3f}")
        print(f"Average Recall:    {aggregate.get('avg_recall', 0):.3f}")
        print(f"Average F1 Score:  {aggregate.get('avg_f1', 0):.3f}")
        print()

    # Save results if output specified
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Results saved to: {args.output}")

    print("=" * 60)
    print("Evaluation complete")


if __name__ == '__main__':
    main()
