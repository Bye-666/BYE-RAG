"""Simple dashboard for monitoring RAG system."""

from typing import Dict, Any, List
import json
from datetime import datetime


class Dashboard:
    """Lightweight dashboard for RAG system metrics.

    Provides basic monitoring and statistics.
    """

    def __init__(self):
        """Initialize Dashboard."""
        self.metrics: Dict[str, Any] = {
            "queries": [],
            "ingestions": [],
            "system_stats": {}
        }

    def log_query(self, query: str, results_count: int, latency: float):
        """Log a query event.

        Args:
            query: Query text
            results_count: Number of results
            latency: Query latency in seconds
        """
        self.metrics["queries"].append({
            "query": query,
            "results_count": results_count,
            "latency": latency,
            "timestamp": datetime.now().isoformat()
        })

    def log_ingestion(self, file_path: str, chunks: int, success: bool):
        """Log an ingestion event.

        Args:
            file_path: Ingested file path
            chunks: Number of chunks
            success: Whether ingestion succeeded
        """
        self.metrics["ingestions"].append({
            "file_path": file_path,
            "chunks": chunks,
            "success": success,
            "timestamp": datetime.now().isoformat()
        })

    def get_stats(self) -> Dict[str, Any]:
        """Get overall statistics.

        Returns:
            Statistics dictionary
        """
        total_queries = len(self.metrics["queries"])
        total_ingestions = len(self.metrics["ingestions"])

        avg_latency = 0
        if total_queries > 0:
            avg_latency = sum(q["latency"] for q in self.metrics["queries"]) / total_queries

        successful_ingestions = sum(1 for i in self.metrics["ingestions"] if i["success"])

        return {
            "total_queries": total_queries,
            "total_ingestions": total_ingestions,
            "successful_ingestions": successful_ingestions,
            "avg_query_latency": avg_latency,
            "last_updated": datetime.now().isoformat()
        }

    def get_recent_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent queries.

        Args:
            limit: Number of queries to return

        Returns:
            List of recent queries
        """
        return self.metrics["queries"][-limit:]

    def get_recent_ingestions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent ingestions.

        Args:
            limit: Number of ingestions to return

        Returns:
            List of recent ingestions
        """
        return self.metrics["ingestions"][-limit:]

    def export_metrics(self, file_path: str):
        """Export metrics to JSON file.

        Args:
            file_path: Output file path
        """
        with open(file_path, 'w') as f:
            json.dump(self.metrics, f, indent=2)

    def clear(self):
        """Clear all metrics."""
        self.metrics = {
            "queries": [],
            "ingestions": [],
            "system_stats": {}
        }
