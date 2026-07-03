"""Composite evaluator combining multiple evaluation metrics."""

from typing import List, Dict, Any, Optional
from .evaluator import Evaluator
from .ragas_evaluator import RagasEvaluator


class CompositeEvaluator:
    """Combine multiple evaluators for comprehensive assessment.

    Supports both retrieval metrics and RAG generation metrics.
    Aggregates results from multiple evaluation methods.
    """

    def __init__(
        self,
        evaluators: Optional[List[Evaluator]] = None,
        ragas_evaluator: Optional[RagasEvaluator] = None
    ):
        """Initialize CompositeEvaluator.

        Args:
            evaluators: List of basic evaluator instances
            ragas_evaluator: RagasEvaluator instance for generation metrics
        """
        self.evaluators = evaluators or []
        self.base_evaluator = Evaluator()
        self.ragas_evaluator = ragas_evaluator

    def add_evaluator(self, evaluator: Evaluator):
        """Add a basic evaluator.

        Args:
            evaluator: Evaluator instance
        """
        self.evaluators.append(evaluator)

    def set_ragas_evaluator(self, ragas_evaluator: RagasEvaluator):
        """Set RagasEvaluator for generation metrics.

        Args:
            ragas_evaluator: RagasEvaluator instance
        """
        self.ragas_evaluator = ragas_evaluator

    def evaluate_retrieval(
        self,
        query: str,
        retrieved_docs: List[str],
        relevant_docs: List[str]
    ) -> Dict[str, Any]:
        """Evaluate retrieval quality using all evaluators.

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
        all_results["aggregate"] = self._aggregate_retrieval_metrics(all_results)

        return all_results

    def evaluate_generation(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: Optional[str] = None
    ) -> Dict[str, Any]:
        """Evaluate RAG generation quality.

        Args:
            question: User's question
            answer: Generated answer
            contexts: Retrieved contexts
            ground_truth: Ground truth answer (optional)

        Returns:
            Evaluation results including ragas metrics
        """
        results = {}

        # Ragas evaluation
        if self.ragas_evaluator:
            ragas_scores = self.ragas_evaluator.evaluate(
                question, answer, contexts, ground_truth
            )
            results["ragas"] = ragas_scores
            results["ragas_available"] = self.ragas_evaluator.is_available()
        else:
            results["ragas"] = {}
            results["ragas_available"] = False

        return results

    def evaluate_end_to_end(
        self,
        query: str,
        answer: str,
        retrieved_docs: List[str],
        relevant_docs: List[str],
        contexts: List[str],
        ground_truth: Optional[str] = None
    ) -> Dict[str, Any]:
        """Comprehensive end-to-end evaluation.

        Evaluates both retrieval and generation quality.

        Args:
            query: User's query
            answer: Generated answer
            retrieved_docs: Retrieved document IDs
            relevant_docs: Ground truth relevant document IDs
            contexts: Retrieved context texts
            ground_truth: Ground truth answer (optional)

        Returns:
            Combined retrieval and generation metrics
        """
        results = {}

        # Retrieval evaluation
        results["retrieval"] = self.evaluate_retrieval(
            query, retrieved_docs, relevant_docs
        )

        # Generation evaluation
        results["generation"] = self.evaluate_generation(
            query, answer, contexts, ground_truth
        )

        # Overall score (weighted average)
        results["overall"] = self._compute_overall_score(results)

        return results

    def evaluate_batch(
        self,
        questions: List[str],
        answers: List[str],
        contexts_list: List[List[str]],
        ground_truths: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Batch evaluation for multiple samples.

        Args:
            questions: List of questions
            answers: List of generated answers
            contexts_list: List of context lists
            ground_truths: List of ground truth answers (optional)

        Returns:
            Aggregated evaluation results
        """
        results = {}

        # Ragas batch evaluation
        if self.ragas_evaluator:
            ragas_results = self.ragas_evaluator.evaluate_batch(
                questions, answers, contexts_list, ground_truths
            )
            results["ragas"] = ragas_results
        else:
            results["ragas"] = {"average_scores": {}, "num_samples": 0}

        results["num_samples"] = len(questions)

        return results

    def _aggregate_retrieval_metrics(self, results: Dict[str, Any]) -> Dict[str, float]:
        """Aggregate retrieval metrics from all evaluators.

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

    def _compute_overall_score(self, results: Dict[str, Any]) -> Dict[str, float]:
        """Compute overall score from retrieval and generation metrics.

        Args:
            results: Combined results

        Returns:
            Overall weighted score
        """
        scores = []

        # Retrieval score (F1)
        if "retrieval" in results and "aggregate" in results["retrieval"]:
            retrieval_f1 = results["retrieval"]["aggregate"].get("avg_f1", 0)
            scores.append(("retrieval", retrieval_f1, 0.3))  # 30% weight

        # Generation scores
        if "generation" in results and "ragas" in results["generation"]:
            ragas_scores = results["generation"]["ragas"]

            # Extract individual ragas metrics
            for metric, score in ragas_scores.items():
                if isinstance(score, (int, float)):
                    # Equal weight for generation metrics, 70% total
                    weight = 0.7 / max(len(ragas_scores), 1)
                    scores.append((f"generation_{metric}", score, weight))

        # Weighted average
        if scores:
            total_score = sum(score * weight for _, score, weight in scores)
            total_weight = sum(weight for _, _, weight in scores)

            if total_weight > 0:
                return {
                    "overall_score": total_score / total_weight,
                    "components": {name: score for name, score, _ in scores}
                }

        return {"overall_score": 0.0, "components": {}}
