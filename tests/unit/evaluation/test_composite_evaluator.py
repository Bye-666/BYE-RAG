"""Unit tests for CompositeEvaluator."""

import pytest
from src.evaluation.composite_evaluator import CompositeEvaluator
from src.evaluation.evaluator import Evaluator
from src.evaluation.ragas_evaluator import RagasEvaluator


def test_composite_evaluator_init():
    """Test CompositeEvaluator initialization."""
    evaluator = CompositeEvaluator()
    assert evaluator is not None
    assert evaluator.base_evaluator is not None


def test_add_evaluator():
    """Test adding evaluators."""
    composite = CompositeEvaluator()
    basic_eval = Evaluator()

    composite.add_evaluator(basic_eval)
    assert len(composite.evaluators) == 1


def test_set_ragas_evaluator():
    """Test setting RagasEvaluator."""
    composite = CompositeEvaluator()
    ragas_eval = RagasEvaluator()

    composite.set_ragas_evaluator(ragas_eval)
    assert composite.ragas_evaluator is not None


def test_evaluate_retrieval():
    """Test retrieval evaluation."""
    composite = CompositeEvaluator()

    query = "What is AI?"
    retrieved = ["doc1", "doc2", "doc3"]
    relevant = ["doc1", "doc2", "doc4"]

    result = composite.evaluate_retrieval(query, retrieved, relevant)

    assert isinstance(result, dict)
    assert "base" in result
    assert "aggregate" in result


def test_evaluate_generation():
    """Test generation evaluation."""
    composite = CompositeEvaluator()
    ragas_eval = RagasEvaluator()
    composite.set_ragas_evaluator(ragas_eval)

    question = "What is machine learning?"
    answer = "Machine learning is AI."
    contexts = ["ML is part of AI."]

    result = composite.evaluate_generation(question, answer, contexts)

    assert isinstance(result, dict)
    assert "ragas" in result
    assert "ragas_available" in result


def test_evaluate_generation_without_ragas():
    """Test generation evaluation without RagasEvaluator."""
    composite = CompositeEvaluator()

    question = "What is Python?"
    answer = "Python is a language."
    contexts = ["Python is a programming language."]

    result = composite.evaluate_generation(question, answer, contexts)

    assert isinstance(result, dict)
    assert result["ragas_available"] is False


def test_evaluate_end_to_end():
    """Test end-to-end evaluation."""
    composite = CompositeEvaluator()
    ragas_eval = RagasEvaluator()
    composite.set_ragas_evaluator(ragas_eval)

    query = "What is AI?"
    answer = "AI is artificial intelligence."
    retrieved = ["doc1", "doc2"]
    relevant = ["doc1", "doc3"]
    contexts = ["AI is artificial intelligence."]

    result = composite.evaluate_end_to_end(
        query, answer, retrieved, relevant, contexts
    )

    assert isinstance(result, dict)
    assert "retrieval" in result
    assert "generation" in result
    assert "overall" in result


def test_evaluate_batch():
    """Test batch evaluation."""
    composite = CompositeEvaluator()
    ragas_eval = RagasEvaluator()
    composite.set_ragas_evaluator(ragas_eval)

    questions = ["Q1?", "Q2?"]
    answers = ["A1", "A2"]
    contexts_list = [["C1"], ["C2"]]

    result = composite.evaluate_batch(questions, answers, contexts_list)

    assert isinstance(result, dict)
    assert "num_samples" in result
    assert result["num_samples"] == 2


def test_multiple_evaluators():
    """Test with multiple basic evaluators."""
    composite = CompositeEvaluator()

    # Add multiple evaluators
    eval1 = Evaluator()
    eval2 = Evaluator()

    composite.add_evaluator(eval1)
    composite.add_evaluator(eval2)

    query = "Test query"
    retrieved = ["doc1"]
    relevant = ["doc1"]

    result = composite.evaluate_retrieval(query, retrieved, relevant)

    # Should have base + 2 additional evaluators
    assert "base" in result
    assert "evaluator_0" in result
    assert "evaluator_1" in result
    assert "aggregate" in result


def test_overall_score_computation():
    """Test overall score computation."""
    composite = CompositeEvaluator()
    ragas_eval = RagasEvaluator()
    composite.set_ragas_evaluator(ragas_eval)

    query = "Test"
    answer = "Answer"
    retrieved = ["doc1"]
    relevant = ["doc1"]
    contexts = ["Context"]

    result = composite.evaluate_end_to_end(
        query, answer, retrieved, relevant, contexts
    )

    assert "overall" in result
    assert "overall_score" in result["overall"]
    assert isinstance(result["overall"]["overall_score"], float)
