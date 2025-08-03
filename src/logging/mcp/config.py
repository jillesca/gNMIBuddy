#!/usr/bin/env python3
"""
MCP-specific logging configuration.

This module provides simplified logging setup specifically for MCP servers,
ensuring logs go to stderr and integrating with the new logging architecture.
"""

import os
from typing import Optional, Dict, Any

from ..config.configurator import LoggingConfigurator
from ..utils.dynamic import set_module_level
from ..core.logger_names import LoggerNames
from ..suppression.external import ExternalLibrarySuppressor


def setup_mcp_logging(
    log_level: Optional[str] = None,
    tool_debug_mode: bool = False,
    custom_module_levels: Optional[Dict[str, str]] = None,
) -> None:
    """
    Configure logging specifically for MCP server operation.

    This ensures logs go to stderr (not stdout which is used for MCP protocol),
    applies appropriate external library suppression, and sets up tool-specific
    debug logging if requested.

    Args:
        log_level: Global log level (defaults to environment or "info")
        tool_debug_mode: Enable debug logging for all MCP tools
        custom_module_levels: Additional module-specific log levels
    """
    # Early environment suppression (before any gRPC imports)
    ExternalLibrarySuppressor._setup_environment_suppression(
        {
            "GRPC_VERBOSITY": "ERROR",
            "GRPC_TRACE": "",
            "GRPC_GO_LOG_VERBOSITY_LEVEL": "99",
            "GRPC_GO_LOG_SEVERITY_LEVEL": "ERROR",
        }
    )

    # Default module levels for MCP operation
    default_module_levels = {
        # Suppress external library noise aggressively for MCP
        "pygnmi": "error",
        "grpc": "error",
        "urllib3": "error",
        "asyncio": "error",
        "requests": "error",
        # Keep our core modules at info by default
        "gnmibuddy.services": "info",
        "gnmibuddy.collectors": "info",
        "gnmibuddy.processors": "info",
    }

    # Add tool debug levels if requested
    if tool_debug_mode:
        mcp_tools = [
            "get_vpn_info",
            "get_devices",
            "get_interface_info",
            "get_routing_info",
            "get_mpls_info",
            "get_logs",
            "get_device_profile_api",
            "get_system_info",
            "get_network_topology_api",
            "get_topology_neighbors",
        ]
        for tool in mcp_tools:
            default_module_levels[f"{LoggerNames.MCP}.tools.{tool}"] = "debug"

    # Merge with custom levels (custom levels take precedence)
    module_levels = default_module_levels.copy()
    if custom_module_levels:
        module_levels.update(custom_module_levels)

    # Configure logging with MCP-specific settings
    LoggingConfigurator.configure(
        global_level=log_level or "info",
        module_levels=module_levels,
        enable_structured=False,  # Keep human-readable for MCP server logs
        enable_file_output=True,
        log_file=None,
        enable_external_suppression=True,
        external_suppression_mode="mcp",  # Uses stderr and aggressive suppression
    )


def read_mcp_environment_config() -> Dict[str, Any]:
    """
    Read MCP-specific configuration from environment variables.

    Returns:
        Configuration dictionary with MCP-specific settings
    """
    config = {}

    # Check for tool debug mode using centralized environment management
    # Note: We use lazy import to avoid circular dependency issues
    try:
        from ...config.environment import get_settings

        settings = get_settings()
        if settings.get_mcp_tool_debug():
            config["tool_debug_mode"] = True
    except ImportError:
        # Fallback to direct environment variable access if import fails
        if os.getenv("GNMIBUDDY_MCP_TOOL_DEBUG", "").lower() in [
            "true",
            "1",
            "yes",
            "on",
        ]:
            config["tool_debug_mode"] = True

    return config


def enable_tool_debug(tool_name: str) -> None:
    """
    Dynamically enable debug logging for a specific MCP tool.

    Args:
        tool_name: The tool name (e.g., 'get_vpn_info', 'get_devices')
    """
    module_name = f"{LoggerNames.MCP}.tools.{tool_name}"
    set_module_level(module_name, "debug")


def disable_tool_debug(tool_name: str) -> None:
    """
    Dynamically disable debug logging for a specific MCP tool.

    Args:
        tool_name: The tool name (e.g., 'get_vpn_info', 'get_devices')
    """
    module_name = f"{LoggerNames.MCP}.tools.{tool_name}"
    set_module_level(module_name, "info")
