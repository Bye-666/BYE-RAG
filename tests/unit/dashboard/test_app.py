"""Tests for Dashboard."""

import pytest
import json
from pathlib import Path

from src.dashboard.app import Dashboard


def test_dashboard_instantiation():
    """Dashboard can be instantiated."""
    dashboard = Dashboard()
    assert dashboard.metrics["queries"] == []
    assert dashboard.metrics["ingestions"] == []


def test_log_query():
    """Log a query event."""
    dashboard = Dashboard()
    dashboard.log_query("test query", 5, 0.5)

    assert len(dashboard.metrics["queries"]) == 1
    assert dashboard.metrics["queries"][0]["query"] == "test query"
    assert dashboard.metrics["queries"][0]["results_count"] == 5
    assert dashboard.metrics["queries"][0]["latency"] == 0.5


def test_log_ingestion():
    """Log an ingestion event."""
    dashboard = Dashboard()
    dashboard.log_ingestion("/path/to/file.pdf", 10, True)

    assert len(dashboard.metrics["ingestions"]) == 1
    assert dashboard.metrics["ingestions"][0]["file_path"] == "/path/to/file.pdf"
    assert dashboard.metrics["ingestions"][0]["chunks"] == 10
    assert dashboard.metrics["ingestions"][0]["success"] is True


def test_get_stats_empty():
    """Get stats with no events."""
    dashboard = Dashboard()
    stats = dashboard.get_stats()

    assert stats["total_queries"] == 0
    assert stats["total_ingestions"] == 0
    assert stats["avg_query_latency"] == 0


def test_get_stats_with_data():
    """Get stats with events."""
    dashboard = Dashboard()
    dashboard.log_query("q1", 5, 0.3)
    dashboard.log_query("q2", 3, 0.5)
    dashboard.log_ingestion("file1.pdf", 10, True)
    dashboard.log_ingestion("file2.pdf", 5, False)

    stats = dashboard.get_stats()

    assert stats["total_queries"] == 2
    assert stats["total_ingestions"] == 2
    assert stats["successful_ingestions"] == 1
    assert stats["avg_query_latency"] == 0.4  # (0.3 + 0.5) / 2


def test_get_recent_queries():
    """Get recent queries."""
    dashboard = Dashboard()
    for i in range(15):
        dashboard.log_query(f"query{i}", i, 0.1)

    recent = dashboard.get_recent_queries(limit=5)

    assert len(recent) == 5
    assert recent[0]["query"] == "query10"
    assert recent[-1]["query"] == "query14"


def test_get_recent_ingestions():
    """Get recent ingestions."""
    dashboard = Dashboard()
    for i in range(15):
        dashboard.log_ingestion(f"file{i}.pdf", i, True)

    recent = dashboard.get_recent_ingestions(limit=3)

    assert len(recent) == 3
    assert recent[0]["file_path"] == "file12.pdf"


def test_export_metrics(tmp_path):
    """Export metrics to JSON."""
    dashboard = Dashboard()
    dashboard.log_query("query1", 5, 0.5)
    dashboard.log_ingestion("file.pdf", 10, True)

    output_file = tmp_path / "metrics.json"
    dashboard.export_metrics(str(output_file))

    assert output_file.exists()

    with open(output_file) as f:
        data = json.load(f)

    assert len(data["queries"]) == 1
    assert len(data["ingestions"]) == 1


def test_clear():
    """Clear all metrics."""
    dashboard = Dashboard()
    dashboard.log_query("query", 5, 0.5)
    dashboard.log_ingestion("file.pdf", 10, True)

    dashboard.clear()

    assert dashboard.metrics["queries"] == []
    assert dashboard.metrics["ingestions"] == []
