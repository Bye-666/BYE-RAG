"""Trace context for tracking execution flow and timing."""

from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import contextmanager
import time
import uuid


class TraceContext:
    """Context manager for tracing execution flow.

    Tracks:
    - Execution timing (start, end, duration)
    - Operation type (ingestion, query)
    - Steps and intermediate states
    - Nested sub-traces

    Usage:
        with TraceContext("ingestion", operation="pdf_ingestion") as trace:
            trace.add_step("load", {"file": "doc.pdf"})
            trace.add_step("split", {"chunks": 10})
            trace.finish({"status": "success"})
    """

    def __init__(
        self,
        trace_type: str,
        operation: str,
        trace_id: Optional[str] = None,
        parent_trace: Optional['TraceContext'] = None
    ):
        """Initialize TraceContext.

        Args:
            trace_type: Type of trace ("ingestion" or "query")
            operation: Operation name (e.g., "pdf_ingestion", "hybrid_search")
            trace_id: Optional trace ID (auto-generated if not provided)
            parent_trace: Optional parent trace for nested tracing
        """
        self.trace_id = trace_id or str(uuid.uuid4())
        self.trace_type = trace_type
        self.operation = operation
        self.parent_trace = parent_trace

        # Timing
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.duration_ms: Optional[float] = None

        # Steps tracking
        self.steps: List[Dict[str, Any]] = []

        # Result
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None

        # Sub-traces
        self.sub_traces: List['TraceContext'] = []

    def __enter__(self) -> 'TraceContext':
        """Enter context manager."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if exc_type is not None:
            self.error = f"{exc_type.__name__}: {exc_val}"

        self.finish()

        # Auto-record trace if it's a top-level trace (no parent)
        if self.parent_trace is None:
            get_trace_recorder().record(self)

        return False  # Don't suppress exceptions

    def start(self):
        """Start the trace."""
        self.start_time = datetime.now()

    def add_step(self, step_name: str, data: Optional[Dict[str, Any]] = None):
        """Add a step to the trace.

        Args:
            step_name: Name of the step
            data: Optional step data
        """
        step = {
            "name": step_name,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }
        self.steps.append(step)

    def finish(self, result: Optional[Dict[str, Any]] = None):
        """Finish the trace.

        Args:
            result: Optional result data
        """
        self.end_time = datetime.now()

        if self.start_time and self.end_time:
            self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000

        if result is not None:
            self.result = result

    def add_sub_trace(self, sub_trace: 'TraceContext'):
        """Add a nested sub-trace.

        Args:
            sub_trace: Child trace context
        """
        self.sub_traces.append(sub_trace)

    def to_dict(self) -> Dict[str, Any]:
        """Export trace as dictionary.

        Returns:
            Trace data dictionary
        """
        return {
            "trace_id": self.trace_id,
            "trace_type": self.trace_type,
            "operation": self.operation,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "steps": self.steps,
            "result": self.result,
            "error": self.error,
            "sub_traces": [st.to_dict() for st in self.sub_traces],
            "parent_id": self.parent_trace.trace_id if self.parent_trace else None
        }

    @contextmanager
    def sub_trace(self, operation: str):
        """Create a nested sub-trace.

        Args:
            operation: Sub-operation name

        Yields:
            Sub-trace context
        """
        sub = TraceContext(
            trace_type=self.trace_type,
            operation=operation,
            parent_trace=self
        )

        with sub:
            yield sub

        self.add_sub_trace(sub)


class TraceRecorder:
    """Global trace recorder for collecting traces."""

    def __init__(self):
        """Initialize TraceRecorder."""
        self.traces: List[TraceContext] = []

    def record(self, trace: TraceContext):
        """Record a completed trace.

        Args:
            trace: Trace to record
        """
        self.traces.append(trace)

    def get_traces(
        self,
        trace_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get recorded traces.

        Args:
            trace_type: Optional filter by trace type
            limit: Optional limit number of results

        Returns:
            List of trace dictionaries
        """
        filtered = self.traces

        if trace_type:
            filtered = [t for t in filtered if t.trace_type == trace_type]

        if limit:
            filtered = filtered[-limit:]

        return [t.to_dict() for t in filtered]

    def clear(self):
        """Clear all recorded traces."""
        self.traces = []


# Global trace recorder instance
_global_recorder = TraceRecorder()


def get_trace_recorder() -> TraceRecorder:
    """Get the global trace recorder instance.

    Returns:
        Global TraceRecorder instance
    """
    return _global_recorder
