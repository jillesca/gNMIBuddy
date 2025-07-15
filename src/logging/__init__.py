#!/usr/bin/env python3
"""
gNMIBuddy logging module.

This module provides comprehensive logging functionality with OpenTelemetry compatibility,
structured logging, and module-specific log level control.

Key Components:
- LoggingConfig: Centralized logging configuration
- OTelFormatter: OpenTelemetry-compatible structured logging
- LoggerNames: Standardized logger naming hierarchy
- Operation tracking with decorators
- Dynamic log level management

Usage:
    from src.logging import configure_logging, get_logger

    logger = configure_logging(log_level="info")
    module_logger = get_logger(__name__)
"""

# Re-export main logging utilities for convenience
from src.logging.config import (
    LoggingConfig,
    LoggerNames,
    OTelFormatter,
    configure_logging,
    get_logger,
    log_operation,
)

__all__ = [
    "LoggingConfig",
    "LoggerNames",
    "OTelFormatter",
    "configure_logging",
    "get_logger",
    "log_operation",
]
