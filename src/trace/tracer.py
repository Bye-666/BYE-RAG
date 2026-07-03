"""Simple trace system for RAG pipeline."""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json


class Tracer:
    """Lightweight trace system for debugging RAG pipeline.
    
    Tracks execution flow, timing, and intermediate results.
    """

    def __init__(self):
        """Initialize Tracer."""
        self.traces: List[Dict[str, Any]] = []
        self.current_trace: Optional[Dict[str, Any]] = None

    def start_trace(self, trace_id: str, operation: str):
        """Start a new trace.
        
        Args:
            trace_id: Unique trace identifier
            operation: Operation name
        """
        self.current_trace = {
            "trace_id": trace_id,
            "operation": operation,
            "start_time": datetime.now().isoformat(),
            "steps": []
        }

    def add_step(self, step_name: str, data: Dict[str, Any]):
        """Add a step to current trace.
        
        Args:
            step_name: Step name
            data: Step data
        """
        if self.current_trace:
            self.current_trace["steps"].append({
                "name": step_name,
                "timestamp": datetime.now().isoformat(),
                "data": data
            })

    def end_trace(self, result: Any = None):
        """End current trace.
        
        Args:
            result: Optional result data
        """
        if self.current_trace:
            self.current_trace["end_time"] = datetime.now().isoformat()
            self.current_trace["result"] = result
            self.traces.append(self.current_trace)
            self.current_trace = None

    def get_traces(self) -> List[Dict[str, Any]]:
        """Get all traces.
        
        Returns:
            List of trace dictionaries
        """
        return self.traces

    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Get specific trace by ID.
        
        Args:
            trace_id: Trace identifier
            
        Returns:
            Trace dictionary or None
        """
        for trace in self.traces:
            if trace.get("trace_id") == trace_id:
                return trace
        return None

    def clear(self):
        """Clear all traces."""
        self.traces = []
        self.current_trace = None

    def export_json(self, file_path: str):
        """Export traces to JSON file.
        
        Args:
            file_path: Output file path
        """
        with open(file_path, 'w') as f:
            json.dump(self.traces, f, indent=2)
