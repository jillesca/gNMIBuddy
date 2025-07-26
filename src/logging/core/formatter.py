#!/usr/bin/env python3
"""
OpenTelemetry-compatible logging formatter.

This module provides structured logging formatters that follow OpenTelemetry
conventions for observability and log aggregation systems.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any


class OTelFormatter(logging.Formatter):
    """
    Custom formatter that follows OpenTelemetry logging conventions.

    Includes structured fields that can be easily parsed by observability tools
    like Grafana Loki, ELK Stack, Splunk, and cloud logging services.

    The formatter produces JSON output with standard OTel fields plus
    application-specific context fields for network operations.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as OpenTelemetry-compatible JSON.

        Args:
            record: Python logging record to format

        Returns:
            JSON string with OTel-compatible structured data
        """
        # Build OTel standard fields
        log_data = self._build_otel_fields(record)

        # Add trace context if available (for future OTel integration)
        self._add_trace_context(log_data, record)

        # Add application-specific context fields
        self._add_application_context(log_data, record)

        # Add exception info if present
        self._add_exception_info(log_data, record)

        return json.dumps(log_data, default=str)

    def _build_otel_fields(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Build the core OpenTelemetry standard fields."""
        return {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": getattr(record, "module", record.name.split(".")[-1]),
            "function": record.funcName,
            "line": record.lineno,
        }

    def _add_trace_context(
        self, log_data: Dict[str, Any], record: logging.LogRecord
    ) -> None:
        """Add OpenTelemetry trace context if available."""
        if hasattr(record, "trace_id"):
            log_data["trace_id"] = getattr(record, "trace_id")
        if hasattr(record, "span_id"):
            log_data["span_id"] = getattr(record, "span_id")

    def _add_application_context(
        self, log_data: Dict[str, Any], record: logging.LogRecord
    ) -> None:
        """Add application-specific context fields."""
        # Network device context
        if hasattr(record, "device_name"):
            log_data["device_name"] = getattr(record, "device_name")

        # Operation tracking
        if hasattr(record, "operation"):
            log_data["operation"] = getattr(record, "operation")

        # Performance metrics
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = getattr(record, "duration_ms")

        # Network interface context
        if hasattr(record, "interface"):
            log_data["interface"] = getattr(record, "interface")

        # Protocol context
        if hasattr(record, "protocol"):
            log_data["protocol"] = getattr(record, "protocol")

    def _add_exception_info(
        self, log_data: Dict[str, Any], record: logging.LogRecord
    ) -> None:
        """Add exception information if present."""
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)


class HumanReadableFormatter(logging.Formatter):
    """
    Human-readable formatter for console output.

    Provides a clean, structured format that's easy to read during
    development and CLI usage while maintaining OTel-friendly structure.
    """

    def __init__(self):
        """Initialize with a comprehensive format string."""
        super().__init__(
            fmt="%(asctime)s | %(levelname)-8s | %(name)-30s | %(funcName)-20s:%(lineno)-4d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def format(self, record: logging.LogRecord) -> str:
        """
        Format record with additional context if available.

        Extends the base format with application-specific context
        when present in the log record.
        """
        # Format the base message
        formatted = super().format(record)

        # Add context information if available
        context_parts = []

        if hasattr(record, "device_name"):
            context_parts.append(f"device={getattr(record, 'device_name')}")

        if hasattr(record, "operation"):
            context_parts.append(f"op={getattr(record, 'operation')}")

        if hasattr(record, "duration_ms"):
            context_parts.append(
                f"duration={getattr(record, 'duration_ms')}ms"
            )

        if hasattr(record, "interface"):
            context_parts.append(f"if={getattr(record, 'interface')}")

        if hasattr(record, "protocol"):
            context_parts.append(f"proto={getattr(record, 'protocol')}")

        # Append context if any
        if context_parts:
            formatted += f" | {' '.join(context_parts)}"

        return formatted
