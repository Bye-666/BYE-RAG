"""Evaluation runner for Golden Test Set.

Manages test data and runs comprehensive evaluations.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from .composite_evaluator import CompositeEvaluator
from .ragas_evaluator import RagasEvaluator


class EvalRunner:
    """Run evaluations on Golden Test Sets.

    Loads test data, executes evaluations, and generates reports.
    """

    def __init__(
        self,
        composite_evaluator: Optional[CompositeEvaluator] = None,
        test_set_path: Optional[str] = None
    ):
        """Initialize EvalRunner.

        Args:
            composite_evaluator: CompositeEvaluator instance
            test_set_path: Path to golden test set JSON file
        """
        self.composite_evaluator = composite_evaluator or CompositeEvaluator()
        self.test_set_path = test_set_path
        self.test_data: List[Dict[str, Any]] = []
        self.results: List[Dict[str, Any]] = []

    def load_test_set(self, test_set_path: Optional[str] = None) -> int:
        """Load golden test set from JSON file.

        Args:
            test_set_path: Path to test set file (overrides init path)

        Returns:
            Number of test cases loaded
        """
        path = test_set_path or self.test_set_path

        if not path:
            raise ValueError("No test set path provided")

        path_obj = Path(path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Test set file not found: {path}")

        with open(path_obj, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Support two formats: dict with "test_cases" key or list
        if isinstance(data, dict) and "test_cases" in data:
            self.test_data = data["test_cases"]
        elif isinstance(data, list):
            self.test_data = data
        else:
            raise ValueError("Invalid test set format. Expected list or dict with 'test_cases' key")

        return len(self.test_data)

    def create_test_set_template(self, output_path: str) -> None:
        """Create an empty test set template.

        Args:
            output_path: Where to save the template
        """
        template = {
            "name": "Golden Test Set",
            "description": "RAG evaluation test cases",
            "created_at": datetime.now().isoformat(),
            "test_cases": [
                {
                    "id": "test_001",
                    "question": "What is machine learning?",
                    "answer": "Machine learning is a subset of artificial intelligence...",
                    "contexts": [
                        "Machine learning is a branch of AI that focuses on...",
                        "ML algorithms learn from data to make predictions..."
                    ],
                    "ground_truth": "Machine learning is a subset of AI that enables systems to learn from data.",
                    "retrieved_docs": ["doc1", "doc2"],
                    "relevant_docs": ["doc1", "doc3"],
                    "metadata": {
                        "category": "definition",
                        "difficulty": "easy"
                    }
                }
            ]
        }

        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path_obj, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)

    def run_evaluation(
        self,
        test_set_path: Optional[str] = None,
        include_retrieval: bool = True,
        include_generation: bool = True
    ) -> Dict[str, Any]:
        """Run evaluation on loaded or specified test set.

        Args:
            test_set_path: Path to test set (optional if already loaded)
            include_retrieval: Whether to evaluate retrieval
            include_generation: Whether to evaluate generation

        Returns:
            Evaluation results summary
        """
        # Load test set if path provided
        if test_set_path:
            self.load_test_set(test_set_path)

        if not self.test_data:
            raise ValueError("No test data loaded. Call load_test_set() first.")

        self.results = []

        # Process each test case
        for i, test_case in enumerate(self.test_data):
            result = self._evaluate_test_case(
                test_case,
                include_retrieval,
                include_generation
            )
            result["test_id"] = test_case.get("id", f"test_{i:03d}")
            self.results.append(result)

        # Compute summary statistics
        summary = self._compute_summary()

        return {
            "summary": summary,
            "individual_results": self.results,
            "num_test_cases": len(self.test_data),
            "timestamp": datetime.now().isoformat()
        }

    def _evaluate_test_case(
        self,
        test_case: Dict[str, Any],
        include_retrieval: bool,
        include_generation: bool
    ) -> Dict[str, Any]:
        """Evaluate a single test case.

        Args:
            test_case: Test case data
            include_retrieval: Whether to evaluate retrieval
            include_generation: Whether to evaluate generation

        Returns:
            Evaluation result for this test case
        """
        result = {}

        question = test_case.get("question", "")
        answer = test_case.get("answer", "")
        contexts = test_case.get("contexts", [])
        ground_truth = test_case.get("ground_truth")
        retrieved_docs = test_case.get("retrieved_docs", [])
        relevant_docs = test_case.get("relevant_docs", [])

        # Retrieval evaluation
        if include_retrieval and retrieved_docs and relevant_docs:
            retrieval_result = self.composite_evaluator.evaluate_retrieval(
                question, retrieved_docs, relevant_docs
            )
            result["retrieval"] = retrieval_result

        # Generation evaluation
        if include_generation and answer and contexts:
            generation_result = self.composite_evaluator.evaluate_generation(
                question, answer, contexts, ground_truth
            )
            result["generation"] = generation_result

        # End-to-end if both available
        if (include_retrieval and include_generation and
            retrieved_docs and relevant_docs and answer and contexts):

            e2e_result = self.composite_evaluator.evaluate_end_to_end(
                question, answer, retrieved_docs, relevant_docs, contexts, ground_truth
            )
            result["end_to_end"] = e2e_result

        return result

    def _compute_summary(self) -> Dict[str, Any]:
        """Compute summary statistics from results.

        Returns:
            Summary statistics
        """
        if not self.results:
            return {}

        summary = {
            "num_cases": len(self.results),
            "retrieval": {},
            "generation": {},
            "overall": {}
        }

        # Aggregate retrieval metrics
        retrieval_scores = []
        for result in self.results:
            if "retrieval" in result and "aggregate" in result["retrieval"]:
                retrieval_scores.append(result["retrieval"]["aggregate"])

        if retrieval_scores:
            summary["retrieval"] = {
                "avg_precision": sum(s.get("avg_precision", 0) for s in retrieval_scores) / len(retrieval_scores),
                "avg_recall": sum(s.get("avg_recall", 0) for s in retrieval_scores) / len(retrieval_scores),
                "avg_f1": sum(s.get("avg_f1", 0) for s in retrieval_scores) / len(retrieval_scores),
            }

        # Aggregate generation metrics
        generation_scores = []
        for result in self.results:
            if "generation" in result and "ragas" in result["generation"]:
                ragas_scores = result["generation"]["ragas"]
                if ragas_scores:
                    generation_scores.append(ragas_scores)

        if generation_scores:
            # Average each metric
            all_metrics = set()
            for scores in generation_scores:
                all_metrics.update(scores.keys())

            summary["generation"] = {}
            for metric in all_metrics:
                values = [s.get(metric, 0) for s in generation_scores if metric in s]
                if values:
                    summary["generation"][f"avg_{metric}"] = sum(values) / len(values)

        # Overall scores
        overall_scores = []
        for result in self.results:
            if "end_to_end" in result and "overall" in result["end_to_end"]:
                overall_score = result["end_to_end"]["overall"].get("overall_score", 0)
                overall_scores.append(overall_score)

        if overall_scores:
            summary["overall"] = {
                "avg_score": sum(overall_scores) / len(overall_scores),
                "min_score": min(overall_scores),
                "max_score": max(overall_scores)
            }

        return summary

    def save_results(self, output_path: str) -> None:
        """Save evaluation results to JSON file.

        Args:
            output_path: Where to save results
        """
        if not self.results:
            raise ValueError("No results to save. Run evaluation first.")

        output_data = {
            "summary": self._compute_summary(),
            "individual_results": self.results,
            "num_test_cases": len(self.test_data),
            "timestamp": datetime.now().isoformat()
        }

        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path_obj, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

    def get_results(self) -> List[Dict[str, Any]]:
        """Get individual test case results.

        Returns:
            List of evaluation results
        """
        return self.results

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics.

        Returns:
            Summary statistics
        """
        return self._compute_summary()
