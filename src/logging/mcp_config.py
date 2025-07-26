#!/usr/bin/env python3
"""
MCP-specific logging configuration for gNMIBuddy.

This module provides simplified logging setup specifically for MCP servers,
ensuring logs go to stderr and integrating with FastMCP's context logging.
"""
import os
import sys
from typing import Optional, Dict, Any
from mcp.server.fastmcp import Context

from .config import configure_logging, get_logger, LoggerNames, LoggingConfig
from .external_suppression import ExternalLibrarySuppressor


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
    ExternalLibrarySuppressor.setup_environment_suppression()

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
    configure_logging(
        log_level=log_level or "info",
        module_levels=module_levels,
        external_suppression_mode="mcp",  # Uses stderr and aggressive suppression
        structured=False,  # Keep human-readable for MCP server logs
    )


def get_mcp_logger(
    name: str, context: Optional[Context] = None
) -> "MCPContextLogger":
    """
    Get an MCP-aware logger that can use FastMCP context if available.

    Args:
        name: Logger name (typically module name)
        context: Optional MCP context for enhanced logging

    Returns:
        Logger that can use MCP context when available
    """
    return MCPContextLogger(name, context)


class MCPContextLogger:
    """
    Simple MCP context logger that uses FastMCP context when available,
    falls back to standard logging otherwise.
    """

    def __init__(self, name: str, context: Optional[Context] = None):
        self.name = name
        self.std_logger = get_logger(name)
        self.context = context

    def set_context(self, context: Optional[Context]):
        """Update the MCP context."""
        self.context = context

    async def debug(self, message: str, *args, **extra):
        """Log debug message."""
        if self.context:
            try:
                # Format the message for MCP context (which expects a string)
                formatted_message = message % args if args else message
                await self.context.debug(formatted_message, **extra)
                return
            except Exception:
                pass
        # Standard logger supports lazy evaluation natively
        self.std_logger.debug(message, *args, extra=extra)

    async def info(self, message: str, *args, **extra):
        """Log info message."""
        if self.context:
            try:
                # Format the message for MCP context (which expects a string)
                formatted_message = message % args if args else message
                await self.context.info(formatted_message, **extra)
                return
            except Exception:
                pass
        # Standard logger supports lazy evaluation natively
        self.std_logger.info(message, *args, extra=extra)

    async def warning(self, message: str, *args, **extra):
        """Log warning message."""
        if self.context:
            try:
                # Format the message for MCP context (which expects a string)
                formatted_message = message % args if args else message
                await self.context.warning(formatted_message, **extra)
                return
            except Exception:
                pass
        # Standard logger supports lazy evaluation natively
        self.std_logger.warning(message, *args, extra=extra)

    async def error(self, message: str, *args, **extra):
        """Log error message."""
        if self.context:
            try:
                # Format the message for MCP context (which expects a string)
                formatted_message = message % args if args else message
                await self.context.error(formatted_message, **extra)
                return
            except Exception:
                pass
        # Standard logger supports lazy evaluation natively
        self.std_logger.error(message, *args, extra=extra)


def read_mcp_environment_config() -> Dict[str, Any]:
    """
    Read MCP-specific configuration from environment variables.

    Returns:
        Configuration dictionary with MCP-specific settings
    """
    config = {}

    # Check for tool debug mode
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
    LoggingConfig.set_module_level(module_name, "debug")


def disable_tool_debug(tool_name: str) -> None:
    """
    Dynamically disable debug logging for a specific MCP tool.

    Args:
        tool_name: The tool name (e.g., 'get_vpn_info', 'get_devices')
    """
    module_name = f"{LoggerNames.MCP}.tools.{tool_name}"
    LoggingConfig.set_module_level(module_name, "info")
