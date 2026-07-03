"""Test TraceContext functionality."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.trace.trace_context import TraceContext, get_trace_recorder


def test_trace_context():
    """Test basic TraceContext usage."""
    # Clear any existing traces
    recorder = get_trace_recorder()
    recorder.clear()

    # Test basic trace
    with TraceContext("ingestion", "test_operation") as trace:
        trace.add_step("step1", {"data": "value1"})
        trace.add_step("step2", {"data": "value2"})
        trace.finish({"status": "success"})

    # Verify trace was recorded
    traces = recorder.get_traces()
    assert len(traces) == 1

    trace_dict = traces[0]
    assert trace_dict["trace_type"] == "ingestion"
    assert trace_dict["operation"] == "test_operation"
    assert len(trace_dict["steps"]) == 2
    assert trace_dict["duration_ms"] is not None
    assert trace_dict["result"]["status"] == "success"

    print("[OK] Basic trace test passed")

    # Test nested traces
    recorder.clear()

    with TraceContext("query", "parent_operation") as parent:
        parent.add_step("parent_step1", {})

        with parent.sub_trace("child_operation") as child:
            child.add_step("child_step1", {})
            child.finish({"child_result": "ok"})

        parent.finish({"parent_result": "ok"})

    traces = recorder.get_traces()
    assert len(traces) == 1

    trace_dict = traces[0]
    assert len(trace_dict["sub_traces"]) == 1
    assert trace_dict["sub_traces"][0]["operation"] == "child_operation"

    print("[OK] Nested trace test passed")

    # Test error handling
    recorder.clear()

    try:
        with TraceContext("query", "error_operation") as trace:
            trace.add_step("step1", {})
            raise ValueError("Test error")
    except ValueError:
        pass

    traces = recorder.get_traces()
    assert len(traces) == 1
    assert traces[0]["error"] is not None
    assert "ValueError" in traces[0]["error"]

    print("[OK] Error handling test passed")

    print("\n[SUCCESS] All TraceContext tests passed!")


if __name__ == "__main__":
    test_trace_context()
