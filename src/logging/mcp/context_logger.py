#!/usr/bin/env python3
"""
MCP context-aware logger.

This module provides the MCPContextLogger class that integrates with
FastMCP's context logging capabilities while falling back to standard logging.
"""

from typing import Optional


try:
    from mcp.server.fastmcp import Context as MCPContext
except ImportError:
    MCPContext = None

from ..utils.dynamic import get_logger


def get_mcp_logger(
    name: str, context: Optional["MCPContext"] = None
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
    MCP context logger that uses FastMCP context when available.

    Falls back to standard logging when MCP context is not available,
    providing seamless operation in both MCP and non-MCP environments.
    """

    def __init__(self, name: str, context: Optional["MCPContext"] = None):
        """
        Initialize MCP context logger.

        Args:
            name: Logger name
            context: Optional MCP context
        """
        self.name = name
        self.std_logger = get_logger(name)
        self.context = context

    def set_context(self, context: Optional["MCPContext"]) -> None:
        """Update the MCP context."""
        self.context = context

    async def debug(self, message: str, *args, **extra) -> None:
        """Log debug message."""
        if self.context and MCPContext is not None:
            try:
                # Format the message for MCP context (which expects a string)
                formatted_message = message % args if args else message
                await self.context.debug(formatted_message, **extra)
                return
            except Exception:
                # Fall through to standard logging on any error
                pass

        # Standard logger supports lazy evaluation natively
        self.std_logger.debug(message, *args, extra=extra)

    async def info(self, message: str, *args, **extra) -> None:
        """Log info message."""
        if self.context and MCPContext is not None:
            try:
                # Format the message for MCP context (which expects a string)
                formatted_message = message % args if args else message
                await self.context.info(formatted_message, **extra)
                return
            except Exception:
                # Fall through to standard logging on any error
                pass

        # Standard logger supports lazy evaluation natively
        self.std_logger.info(message, *args, extra=extra)

    async def warning(self, message: str, *args, **extra) -> None:
        """Log warning message."""
        if self.context and MCPContext is not None:
            try:
                # Format the message for MCP context (which expects a string)
                formatted_message = message % args if args else message
                await self.context.warning(formatted_message, **extra)
                return
            except Exception:
                # Fall through to standard logging on any error
                pass

        # Standard logger supports lazy evaluation natively
        self.std_logger.warning(message, *args, extra=extra)

    async def error(self, message: str, *args, **extra) -> None:
        """Log error message."""
        if self.context and MCPContext is not None:
            try:
                # Format the message for MCP context (which expects a string)
                formatted_message = message % args if args else message
                await self.context.error(formatted_message, **extra)
                return
            except Exception:
                # Fall through to standard logging on any error
                pass

        # Standard logger supports lazy evaluation natively
        self.std_logger.error(message, *args, extra=extra)

    # Synchronous versions for compatibility
    def debug_sync(self, message: str, *args, **extra) -> None:
        """Synchronous debug logging."""
        self.std_logger.debug(message, *args, extra=extra)

    def info_sync(self, message: str, *args, **extra) -> None:
        """Synchronous info logging."""
        self.std_logger.info(message, *args, extra=extra)

    def warning_sync(self, message: str, *args, **extra) -> None:
        """Synchronous warning logging."""
        self.std_logger.warning(message, *args, extra=extra)

    def error_sync(self, message: str, *args, **extra) -> None:
        """Synchronous error logging."""
        self.std_logger.error(message, *args, extra=extra)
