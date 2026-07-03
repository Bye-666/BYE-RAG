"""Tests for Dashboard smoke testing."""

import pytest
from src.dashboard.app import Dashboard


class TestDashboardSmoke:
    """Smoke tests for Dashboard functionality."""

    def test_dashboard_can_instantiate(self):
        """Dashboard can be created."""
        dashboard = Dashboard()
        assert dashboard is not None


    def test_dashboard_log_query(self):
        """Dashboard can log queries."""
        dashboard = Dashboard()

        dashboard.log_query("test query", 5, 0.5)

        stats = dashboard.get_stats()
        assert stats["total_queries"] == 1


    def test_dashboard_log_ingestion(self):
        """Dashboard can log ingestion."""
        dashboard = Dashboard()

        dashboard.log_ingestion("test.pdf", 10, True)

        stats = dashboard.get_stats()
        assert stats["total_ingestions"] == 1


    def test_dashboard_get_recent_queries(self):
        """Dashboard can get recent queries."""
        dashboard = Dashboard()

        dashboard.log_query("q1", 5, 0.5)
        dashboard.log_query("q2", 3, 0.3)

        recent = dashboard.get_recent_queries(limit=10)
        assert len(recent) == 2


    def test_dashboard_get_recent_ingestions(self):
        """Dashboard can get recent ingestions."""
        dashboard = Dashboard()

        dashboard.log_ingestion("file1.pdf", 10, True)
        dashboard.log_ingestion("file2.pdf", 5, False)

        recent = dashboard.get_recent_ingestions(limit=10)
        assert len(recent) == 2


    def test_dashboard_clear(self):
        """Dashboard can clear metrics."""
        dashboard = Dashboard()

        dashboard.log_query("test", 5, 0.5)
        dashboard.clear()

        stats = dashboard.get_stats()
        assert stats["total_queries"] == 0
