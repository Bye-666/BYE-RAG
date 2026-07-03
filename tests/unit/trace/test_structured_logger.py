"""Tests for StructuredLogger."""

import pytest
import json
from pathlib import Path

from src.trace.structured_logger import StructuredLogger


def test_structured_logger_instantiation(tmp_path):
    """StructuredLogger can be instantiated."""
    logger = StructuredLogger("test", log_dir=str(tmp_path))

    assert logger.name == "test"
    assert logger.log_dir == tmp_path


def test_log_creates_file(tmp_path):
    """Logging creates log file."""
    logger = StructuredLogger("test", log_dir=str(tmp_path))

    logger.info("test_event", key="value")

    log_file = tmp_path / "test.jsonl"
    assert log_file.exists()


def test_log_json_format(tmp_path):
    """Log entries are in JSON format."""
    logger = StructuredLogger("test", log_dir=str(tmp_path))

    logger.info("test_event", key="value", count=42)

    log_file = tmp_path / "test.jsonl"
    with open(log_file) as f:
        line = f.readline()
        entry = json.loads(line)

    assert entry["event"] == "test_event"
    assert entry["key"] == "value"
    assert entry["count"] == 42
    assert entry["level"] == "info"


def test_log_levels(tmp_path):
    """Different log levels work."""
    logger = StructuredLogger("test", log_dir=str(tmp_path))

    logger.info("info_event")
    logger.warning("warning_event")
    logger.error("error_event")

    log_file = tmp_path / "test.jsonl"
    with open(log_file) as f:
        lines = f.readlines()

    assert len(lines) == 3

    entries = [json.loads(line) for line in lines]
    assert entries[0]["level"] == "info"
    assert entries[1]["level"] == "warning"
    assert entries[2]["level"] == "error"


def test_log_includes_timestamp(tmp_path):
    """Log entries include timestamp."""
    logger = StructuredLogger("test", log_dir=str(tmp_path))

    logger.info("test_event")

    log_file = tmp_path / "test.jsonl"
    with open(log_file) as f:
        entry = json.loads(f.readline())

    assert "timestamp" in entry
    assert "T" in entry["timestamp"]  # ISO format


def test_multiple_events(tmp_path):
    """Multiple events are logged."""
    logger = StructuredLogger("test", log_dir=str(tmp_path))

    for i in range(5):
        logger.info(f"event_{i}", index=i)

    log_file = tmp_path / "test.jsonl"
    with open(log_file) as f:
        lines = f.readlines()

    assert len(lines) == 5
