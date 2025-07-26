#!/usr/bin/env python3
"""
gNMIBuddy logging module.

This module provides comprehensive logging functionality with OpenTelemetry compatibility,
structured logging, and module-specific log level control.

Key Components:
- LoggingConfig: Centralized logging configuration
- OTelFormatter: OpenTelemetry-compatible structured logging
- LoggerNames: Standardized logger naming hierarchy
- ExternalLibrarySuppressor: External library noise suppression
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

# Re-export external suppression utilities
from src.logging.external_suppression import (
    ExternalLibrarySuppressor,
    setup_mcp_suppression,
    setup_cli_suppression,
    setup_development_suppression,
)

# Re-export MCP-specific utilities
from src.logging.mcp_config import (
    setup_mcp_logging,
    get_mcp_logger,
    MCPContextLogger,
    enable_tool_debug,
    disable_tool_debug,
    read_mcp_environment_config,
)

__all__ = [
    "LoggingConfig",
    "LoggerNames",
    "OTelFormatter",
    "configure_logging",
    "get_logger",
    "log_operation",
    "ExternalLibrarySuppressor",
    "setup_mcp_suppression",
    "setup_cli_suppression",
    "setup_development_suppression",
    # MCP-specific exports
    "setup_mcp_logging",
    "get_mcp_logger",
    "MCPContextLogger",
    "enable_tool_debug",
    "disable_tool_debug",
    "read_mcp_environment_config",
]
