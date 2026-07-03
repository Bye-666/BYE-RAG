"""Composite evaluator combining multiple evaluation metrics."""

from typing import List, Dict, Any
from .evaluator import Evaluator


class CompositeEvaluator:
    """Combine multiple evaluators for comprehensive assessment.

    Aggregates results from multiple evaluation methods.
    """

    def __init__(self, evaluators: List[Evaluator] = None):
        """Initialize CompositeEvaluator.

        Args:
            evaluators: List of evaluator instances
        """
        self.evaluators = evaluators or []
        self.base_evaluator = Evaluator()

    def add_evaluator(self, evaluator: Evaluator):
        """Add an evaluator.

        Args:
            evaluator: Evaluator instance
        """
        self.evaluators.append(evaluator)

    def evaluate_retrieval(
        self,
        query: str,
        retrieved_docs: List[str],
        relevant_docs: List[str]
    ) -> Dict[str, Any]:
        """Evaluate using all evaluators.

        Args:
            query: Query text
            retrieved_docs: Retrieved document IDs
            relevant_docs: Ground truth relevant document IDs

        Returns:
            Combined evaluation results
        """
        # Base metrics
        base_result = self.base_evaluator.evaluate_retrieval(
            query, retrieved_docs, relevant_docs
        )

        # Collect from all evaluators
        all_results = {"base": base_result}

        for i, evaluator in enumerate(self.evaluators):
            result = evaluator.evaluate_retrieval(query, retrieved_docs, relevant_docs)
            all_results[f"evaluator_{i}"] = result

        # Aggregate metrics
        all_results["aggregate"] = self._aggregate_metrics(all_results)

        return all_results

    def _aggregate_metrics(self, results: Dict[str, Any]) -> Dict[str, float]:
        """Aggregate metrics from all evaluators.

        Args:
            results: Results from all evaluators

        Returns:
            Aggregated metrics
        """
        precisions = []
        recalls = []
        f1s = []

        for key, result in results.items():
            if key != "aggregate" and isinstance(result, dict):
                if "precision" in result:
                    precisions.append(result["precision"])
                if "recall" in result:
                    recalls.append(result["recall"])
                if "f1" in result:
                    f1s.append(result["f1"])

        return {
            "avg_precision": sum(precisions) / len(precisions) if precisions else 0,
            "avg_recall": sum(recalls) / len(recalls) if recalls else 0,
            "avg_f1": sum(f1s) / len(f1s) if f1s else 0
        }
