"""Unit tests for EvalRunner."""

import pytest
import json
import tempfile
from pathlib import Path
from src.evaluation.eval_runner import EvalRunner
from src.evaluation.composite_evaluator import CompositeEvaluator
from src.evaluation.ragas_evaluator import RagasEvaluator


@pytest.fixture
def sample_test_set():
    """Create a sample test set."""
    return {
        "name": "Test Set",
        "test_cases": [
            {
                "id": "test_001",
                "question": "What is AI?",
                "answer": "AI is artificial intelligence.",
                "contexts": ["AI stands for artificial intelligence."],
                "ground_truth": "AI is artificial intelligence.",
                "retrieved_docs": ["doc1", "doc2"],
                "relevant_docs": ["doc1", "doc3"]
            },
            {
                "id": "test_002",
                "question": "What is ML?",
                "answer": "ML is machine learning.",
                "contexts": ["ML is machine learning."],
                "ground_truth": "ML is machine learning.",
                "retrieved_docs": ["doc2", "doc3"],
                "relevant_docs": ["doc2", "doc4"]
            }
        ]
    }


@pytest.fixture
def temp_test_set_file(sample_test_set):
    """Create a temporary test set file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(sample_test_set, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


def test_eval_runner_init():
    """Test EvalRunner initialization."""
    runner = EvalRunner()
    assert runner is not None
    assert runner.composite_evaluator is not None


def test_load_test_set(temp_test_set_file):
    """Test loading test set from file."""
    runner = EvalRunner()
    num_cases = runner.load_test_set(temp_test_set_file)

    assert num_cases == 2
    assert len(runner.test_data) == 2


def test_load_test_set_list_format():
    """Test loading test set in list format."""
    test_data = [
        {"question": "Q1", "answer": "A1", "contexts": ["C1"]},
        {"question": "Q2", "answer": "A2", "contexts": ["C2"]}
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(test_data, f)
        temp_path = f.name

    try:
        runner = EvalRunner()
        num_cases = runner.load_test_set(temp_path)

        assert num_cases == 2
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_load_nonexistent_file():
    """Test loading non-existent file."""
    runner = EvalRunner()

    with pytest.raises(FileNotFoundError):
        runner.load_test_set("nonexistent.json")


def test_create_test_set_template():
    """Test creating test set template."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "template.json"

        runner = EvalRunner()
        runner.create_test_set_template(str(output_path))

        assert output_path.exists()

        # Verify structure
        with open(output_path, 'r', encoding='utf-8') as f:
            template = json.load(f)

        assert "test_cases" in template
        assert len(template["test_cases"]) > 0


def test_run_evaluation(temp_test_set_file):
    """Test running evaluation."""
    composite = CompositeEvaluator()
    ragas_eval = RagasEvaluator()
    composite.set_ragas_evaluator(ragas_eval)

    runner = EvalRunner(composite_evaluator=composite)
    runner.load_test_set(temp_test_set_file)

    results = runner.run_evaluation()

    assert "summary" in results
    assert "individual_results" in results
    assert results["num_test_cases"] == 2
    assert len(runner.results) == 2


def test_run_evaluation_without_loading():
    """Test running evaluation without loading data."""
    runner = EvalRunner()

    with pytest.raises(ValueError):
        runner.run_evaluation()


def test_run_evaluation_retrieval_only(temp_test_set_file):
    """Test evaluation with retrieval only."""
    runner = EvalRunner()
    runner.load_test_set(temp_test_set_file)

    results = runner.run_evaluation(include_generation=False)

    assert "summary" in results
    assert len(runner.results) == 2


def test_run_evaluation_generation_only(temp_test_set_file):
    """Test evaluation with generation only."""
    composite = CompositeEvaluator()
    ragas_eval = RagasEvaluator()
    composite.set_ragas_evaluator(ragas_eval)

    runner = EvalRunner(composite_evaluator=composite)
    runner.load_test_set(temp_test_set_file)

    results = runner.run_evaluation(include_retrieval=False)

    assert "summary" in results
    assert len(runner.results) == 2


def test_save_results(temp_test_set_file):
    """Test saving evaluation results."""
    runner = EvalRunner()
    runner.load_test_set(temp_test_set_file)
    runner.run_evaluation()

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "results.json"

        runner.save_results(str(output_path))

        assert output_path.exists()

        # Verify structure
        with open(output_path, 'r', encoding='utf-8') as f:
            saved_results = json.load(f)

        assert "summary" in saved_results
        assert "individual_results" in saved_results


def test_save_results_without_running():
    """Test saving results without running evaluation."""
    runner = EvalRunner()

    with pytest.raises(ValueError):
        runner.save_results("output.json")


def test_get_results(temp_test_set_file):
    """Test getting results."""
    runner = EvalRunner()
    runner.load_test_set(temp_test_set_file)
    runner.run_evaluation()

    results = runner.get_results()

    assert isinstance(results, list)
    assert len(results) == 2


def test_get_summary(temp_test_set_file):
    """Test getting summary."""
    runner = EvalRunner()
    runner.load_test_set(temp_test_set_file)
    runner.run_evaluation()

    summary = runner.get_summary()

    assert isinstance(summary, dict)
    assert "num_cases" in summary
