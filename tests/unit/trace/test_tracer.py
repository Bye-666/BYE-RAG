"""Tests for Tracer."""

import pytest
import json
from pathlib import Path

from src.trace.tracer import Tracer


def test_tracer_instantiation():
    """Tracer can be instantiated."""
    tracer = Tracer()
    assert tracer.traces == []
    assert tracer.current_trace is None


def test_start_trace():
    """Start a new trace."""
    tracer = Tracer()
    tracer.start_trace("trace-1", "query")

    assert tracer.current_trace is not None
    assert tracer.current_trace["trace_id"] == "trace-1"
    assert tracer.current_trace["operation"] == "query"
    assert "start_time" in tracer.current_trace


def test_add_step():
    """Add step to trace."""
    tracer = Tracer()
    tracer.start_trace("trace-1", "query")
    tracer.add_step("retrieval", {"results": 5})

    assert len(tracer.current_trace["steps"]) == 1
    assert tracer.current_trace["steps"][0]["name"] == "retrieval"
    assert tracer.current_trace["steps"][0]["data"] == {"results": 5}


def test_end_trace():
    """End trace and save it."""
    tracer = Tracer()
    tracer.start_trace("trace-1", "query")
    tracer.add_step("step1", {})
    tracer.end_trace(result="success")

    assert tracer.current_trace is None
    assert len(tracer.traces) == 1
    assert tracer.traces[0]["trace_id"] == "trace-1"
    assert tracer.traces[0]["result"] == "success"


def test_get_traces():
    """Get all traces."""
    tracer = Tracer()
    tracer.start_trace("trace-1", "op1")
    tracer.end_trace()
    tracer.start_trace("trace-2", "op2")
    tracer.end_trace()

    traces = tracer.get_traces()
    assert len(traces) == 2


def test_get_trace_by_id():
    """Get specific trace by ID."""
    tracer = Tracer()
    tracer.start_trace("trace-1", "op1")
    tracer.end_trace()

    trace = tracer.get_trace("trace-1")
    assert trace is not None
    assert trace["trace_id"] == "trace-1"


def test_get_nonexistent_trace():
    """Get nonexistent trace returns None."""
    tracer = Tracer()
    trace = tracer.get_trace("nonexistent")
    assert trace is None


def test_clear_traces():
    """Clear all traces."""
    tracer = Tracer()
    tracer.start_trace("trace-1", "op1")
    tracer.end_trace()

    tracer.clear()
    assert tracer.traces == []
    assert tracer.current_trace is None


def test_export_json(tmp_path):
    """Export traces to JSON."""
    tracer = Tracer()
    tracer.start_trace("trace-1", "query")
    tracer.add_step("step1", {"key": "value"})
    tracer.end_trace()

    output_file = tmp_path / "traces.json"
    tracer.export_json(str(output_file))

    assert output_file.exists()

    with open(output_file) as f:
        data = json.load(f)

    assert len(data) == 1
    assert data[0]["trace_id"] == "trace-1"


def test_multiple_steps():
    """Add multiple steps to trace."""
    tracer = Tracer()
    tracer.start_trace("trace-1", "query")
    tracer.add_step("step1", {"data": 1})
    tracer.add_step("step2", {"data": 2})
    tracer.add_step("step3", {"data": 3})
    tracer.end_trace()

    trace = tracer.get_trace("trace-1")
    assert len(trace["steps"]) == 3
