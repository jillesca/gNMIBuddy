#!/usr/bin/env python3
"""
gNMIBuddy logging module.

This module provides comprehensive logging functionality with OpenTelemetry compatibility,
structured logging, and module-specific log level control.

Modular architecture:
- Core components: enums, models, logger names, formatters
- Configuration: environment reading, file utils, main configurator
- Suppression: external library noise reduction with strategies
- MCP: specialized MCP server logging
- Decorators: operation tracking
- Utils: dynamic logger creation and level management

Key Components:
- LoggingConfigurator: Centralized logging configuration
- OTelFormatter: OpenTelemetry-compatible structured logging
- LoggerNames: Standardized logger naming hierarchy
- ExternalLibrarySuppressor: External library noise suppression
- Operation tracking with decorators
- Dynamic log level management

Usage:
    from src.logging import LoggingConfigurator, get_logger

    LoggingConfigurator.configure(global_level="info")
    module_logger = get_logger(__name__)
"""

# Core components
from .core import (
    LogLevel,
    SuppressionMode,
    LoggingConfiguration,
    ModuleLevelConfiguration,
    LoggerNames,
    OTelFormatter,
)

# Configuration components
from .config import (
    LoggingConfigurator,
    EnvironmentConfigReader,
    LogFilePathGenerator,
)

# Suppression components
from .suppression import (
    ExternalLibrarySuppressor,
    setup_cli_suppression,
    setup_mcp_suppression,
    setup_development_suppression,
)

# Decorators
from .decorators import log_operation

# Utilities
from .utils.dynamic import get_logger, set_module_level, get_module_levels

# MCP-specific utilities
from .mcp import (
    setup_mcp_logging,
    get_mcp_logger,
    MCPContextLogger,
    enable_tool_debug,
    disable_tool_debug,
    read_mcp_environment_config,
)

__all__ = [
    # Core components
    "LogLevel",
    "SuppressionMode",
    "LoggingConfiguration",
    "ModuleLevelConfiguration",
    "LoggerNames",
    "OTelFormatter",
    # Configuration
    "LoggingConfigurator",
    "EnvironmentConfigReader",
    "LogFilePathGenerator",
    # Main API functions
    "get_logger",
    "log_operation",
    # Dynamic level management
    "set_module_level",
    "get_module_levels",
    # External suppression
    "ExternalLibrarySuppressor",
    "setup_cli_suppression",
    "setup_mcp_suppression",
    "setup_development_suppression",
    # MCP-specific exports
    "setup_mcp_logging",
    "get_mcp_logger",
    "MCPContextLogger",
    "enable_tool_debug",
    "disable_tool_debug",
    "read_mcp_environment_config",
]
