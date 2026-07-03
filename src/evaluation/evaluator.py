"""Simple evaluation system for RAG quality."""

from typing import List, Dict, Any


class Evaluator:
    """Basic RAG evaluation metrics.

    Provides simple quality metrics for RAG system.
    """

    def __init__(self):
        """Initialize Evaluator."""
        self.evaluations: List[Dict[str, Any]] = []

    def evaluate_retrieval(
        self,
        query: str,
        retrieved_docs: List[str],
        relevant_docs: List[str]
    ) -> Dict[str, float]:
        """Evaluate retrieval quality.

        Args:
            query: Query text
            retrieved_docs: Retrieved document IDs
            relevant_docs: Ground truth relevant document IDs

        Returns:
            Evaluation metrics
        """
        retrieved_set = set(retrieved_docs)
        relevant_set = set(relevant_docs)

        # Precision: relevant retrieved / total retrieved
        precision = 0.0
        if len(retrieved_set) > 0:
            precision = len(retrieved_set & relevant_set) / len(retrieved_set)

        # Recall: relevant retrieved / total relevant
        recall = 0.0
        if len(relevant_set) > 0:
            recall = len(retrieved_set & relevant_set) / len(relevant_set)

        # F1 Score
        f1 = 0.0
        if precision + recall > 0:
            f1 = 2 * (precision * recall) / (precision + recall)

        result = {
            "query": query,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "retrieved_count": len(retrieved_docs),
            "relevant_count": len(relevant_docs)
        }

        self.evaluations.append(result)
        return result

    def get_average_metrics(self) -> Dict[str, float]:
        """Get average metrics across all evaluations.

        Returns:
            Average metrics
        """
        if not self.evaluations:
            return {
                "avg_precision": 0.0,
                "avg_recall": 0.0,
                "avg_f1": 0.0
            }

        total = len(self.evaluations)
        return {
            "avg_precision": sum(e["precision"] for e in self.evaluations) / total,
            "avg_recall": sum(e["recall"] for e in self.evaluations) / total,
            "avg_f1": sum(e["f1"] for e in self.evaluations) / total,
            "total_evaluations": total
        }

    def get_evaluations(self) -> List[Dict[str, Any]]:
        """Get all evaluations.

        Returns:
            List of evaluation results
        """
        return self.evaluations

    def clear(self):
        """Clear all evaluations."""
        self.evaluations = []
