"""Tests for Evaluator."""

import pytest

from src.evaluation.evaluator import Evaluator


def test_evaluator_instantiation():
    """Evaluator can be instantiated."""
    evaluator = Evaluator()
    assert evaluator.evaluations == []


def test_evaluate_retrieval_perfect():
    """Evaluate perfect retrieval."""
    evaluator = Evaluator()

    result = evaluator.evaluate_retrieval(
        query="test",
        retrieved_docs=["doc1", "doc2", "doc3"],
        relevant_docs=["doc1", "doc2", "doc3"]
    )

    assert result["precision"] == 1.0
    assert result["recall"] == 1.0
    assert result["f1"] == 1.0


def test_evaluate_retrieval_partial():
    """Evaluate partial retrieval."""
    evaluator = Evaluator()

    result = evaluator.evaluate_retrieval(
        query="test",
        retrieved_docs=["doc1", "doc2", "doc3"],
        relevant_docs=["doc1", "doc4"]
    )

    # Precision: 1/3 (only doc1 is relevant)
    assert abs(result["precision"] - 1/3) < 0.001
    # Recall: 1/2 (got doc1 but not doc4)
    assert result["recall"] == 0.5
    # F1: 2 * (1/3 * 1/2) / (1/3 + 1/2) = 2/5 = 0.4
    assert abs(result["f1"] - 0.4) < 0.001


def test_evaluate_retrieval_no_relevant():
    """Evaluate retrieval with no relevant docs."""
    evaluator = Evaluator()

    result = evaluator.evaluate_retrieval(
        query="test",
        retrieved_docs=["doc1", "doc2"],
        relevant_docs=["doc3", "doc4"]
    )

    assert result["precision"] == 0.0
    assert result["recall"] == 0.0
    assert result["f1"] == 0.0


def test_evaluate_retrieval_empty_retrieved():
    """Evaluate with no retrieved docs."""
    evaluator = Evaluator()

    result = evaluator.evaluate_retrieval(
        query="test",
        retrieved_docs=[],
        relevant_docs=["doc1", "doc2"]
    )

    assert result["precision"] == 0.0
    assert result["recall"] == 0.0


def test_get_average_metrics_empty():
    """Get average metrics with no evaluations."""
    evaluator = Evaluator()

    metrics = evaluator.get_average_metrics()

    assert metrics["avg_precision"] == 0.0
    assert metrics["avg_recall"] == 0.0
    assert metrics["avg_f1"] == 0.0


def test_get_average_metrics():
    """Get average metrics across evaluations."""
    evaluator = Evaluator()

    evaluator.evaluate_retrieval("q1", ["d1"], ["d1"])  # Perfect
    evaluator.evaluate_retrieval("q2", ["d1", "d2"], ["d1"])  # 0.5 precision, 1.0 recall

    metrics = evaluator.get_average_metrics()

    # Avg precision: (1.0 + 0.5) / 2 = 0.75
    assert metrics["avg_precision"] == 0.75
    # Avg recall: (1.0 + 1.0) / 2 = 1.0
    assert metrics["avg_recall"] == 1.0
    assert metrics["total_evaluations"] == 2


def test_get_evaluations():
    """Get all evaluation results."""
    evaluator = Evaluator()

    evaluator.evaluate_retrieval("q1", ["d1"], ["d1"])
    evaluator.evaluate_retrieval("q2", ["d2"], ["d2"])

    evals = evaluator.get_evaluations()

    assert len(evals) == 2
    assert evals[0]["query"] == "q1"
    assert evals[1]["query"] == "q2"


def test_clear():
    """Clear all evaluations."""
    evaluator = Evaluator()

    evaluator.evaluate_retrieval("q1", ["d1"], ["d1"])
    evaluator.clear()

    assert evaluator.evaluations == []
    metrics = evaluator.get_average_metrics()
    assert metrics["avg_precision"] == 0.0
