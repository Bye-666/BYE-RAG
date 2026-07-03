"""Structured logger for RAG system."""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class StructuredLogger:
    """Structured logging with JSON output.

    Provides consistent logging format across the system.
    """

    def __init__(self, name: str, log_dir: str = "logs"):
        """Initialize StructuredLogger.

        Args:
            name: Logger name
            log_dir: Log directory path
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Setup logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # JSON file handler
        log_file = self.log_dir / f"{name}.jsonl"
        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)

        # Console handler
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(console)

    def log(self, level: str, event: str, **kwargs):
        """Log structured event.

        Args:
            level: Log level (info/warning/error)
            event: Event name
            **kwargs: Additional context
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "logger": self.name,
            "level": level,
            "event": event,
            **kwargs
        }

        log_line = json.dumps(log_entry, ensure_ascii=False)

        if level == "info":
            self.logger.info(log_line)
        elif level == "warning":
            self.logger.warning(log_line)
        elif level == "error":
            self.logger.error(log_line)

    def info(self, event: str, **kwargs):
        """Log info event."""
        self.log("info", event, **kwargs)

    def warning(self, event: str, **kwargs):
        """Log warning event."""
        self.log("warning", event, **kwargs)

    def error(self, event: str, **kwargs):
        """Log error event."""
        self.log("error", event, **kwargs)
