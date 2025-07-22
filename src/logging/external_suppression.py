#!/usr/bin/env python3
"""
External library logging suppression for gNMIBuddy.

This module provides utilities to suppress verbose logging from external libraries
that tend to pollute application logs, especially in contexts where clean output
is required (like MCP servers, CLI tools, etc.).
"""
import os
import logging
from typing import Dict, List, Optional


class ExternalLibrarySuppressor:
    """
    Centralized suppression of external library logging.

    Handles both Python logging configuration and environment variable
    suppression for libraries that bypass Python's logging system.
    """

    # Default suppression configuration
    DEFAULT_SUPPRESSIONS = {
        "pygnmi": "error",  # Only show pygnmi errors
        "grpc": "error",  # Only show gRPC errors
        "urllib3": "warning",  # Reduce urllib3 noise
        "asyncio": "warning",  # Reduce asyncio noise
        "requests": "warning",  # Reduce requests library noise
        "paramiko": "warning",  # SSH library noise reduction
    }

    # gRPC-specific environment variables for deeper suppression
    GRPC_ENV_VARS = {
        "GRPC_VERBOSITY": "ERROR",
        "GRPC_TRACE": "",
        "GRPC_GO_LOG_VERBOSITY_LEVEL": "99",
        "GRPC_GO_LOG_SEVERITY_LEVEL": "ERROR",
    }

    @classmethod
    def setup_environment_suppression(cls) -> None:
        """
        Set environment variables to suppress external library output.

        This must be called before importing libraries that read these
        environment variables at import time (like gRPC).
        """
        for env_var, value in cls.GRPC_ENV_VARS.items():
            os.environ.setdefault(env_var, value)

    @classmethod
    def setup_python_logging_suppression(
        cls,
        custom_levels: Optional[Dict[str, str]] = None,
        include_defaults: bool = True,
    ) -> None:
        """
        Configure Python logging suppression for external libraries.

        Args:
            custom_levels: Additional or override suppression levels
            include_defaults: Whether to include default suppressions
        """
        suppressions = {}

        if include_defaults:
            suppressions.update(cls.DEFAULT_SUPPRESSIONS)

        if custom_levels:
            suppressions.update(custom_levels)

        # Apply logging level suppressions
        for logger_name, level_str in suppressions.items():
            level = getattr(logging, level_str.upper(), logging.WARNING)
            logger = logging.getLogger(logger_name)
            logger.setLevel(level)

    @classmethod
    def setup_grpc_deep_suppression(cls) -> None:
        """
        Apply deep gRPC suppression at the library level.

        This disables gRPC's internal logging mechanisms that can
        write directly to stdout/stderr bypassing Python logging.
        """
        try:
            import grpc

            # Disable main gRPC logger
            grpc_logger = logging.getLogger("grpc")
            grpc_logger.setLevel(logging.CRITICAL)
            grpc_logger.disabled = True

            # Disable gRPC internal module loggers
            grpc_modules = [
                "grpc._channel",
                "grpc._common",
                "grpc._server",
                "grpc._simple_stubs",
                "grpc.beta",
                "grpc.experimental",
                "grpc.health",
            ]

            for module_name in grpc_modules:
                try:
                    module_logger = logging.getLogger(module_name)
                    module_logger.setLevel(logging.CRITICAL)
                    module_logger.disabled = True
                except Exception:
                    # Silent fail for modules that don't exist
                    pass

        except ImportError:
            # gRPC not available, no suppression needed
            pass

    @classmethod
    def setup_pygnmi_suppression(cls) -> None:
        """
        Apply specific pygnmi suppression.

        pygnmi can be particularly verbose during connection establishment
        and capability negotiation.
        """
        try:
            # Suppress pygnmi main logger
            pygnmi_logger = logging.getLogger("pygnmi")
            pygnmi_logger.setLevel(logging.ERROR)

            # Suppress pygnmi submodules that tend to be verbose
            pygnmi_modules = [
                "pygnmi.client",
                "pygnmi.path",
                "pygnmi.subscribe",
            ]

            for module_name in pygnmi_modules:
                try:
                    module_logger = logging.getLogger(module_name)
                    module_logger.setLevel(logging.ERROR)
                except Exception:
                    pass

        except ImportError:
            # pygnmi not available
            pass

    @classmethod
    def setup_all_suppressions(
        cls,
        custom_levels: Optional[Dict[str, str]] = None,
        include_defaults: bool = True,
        deep_grpc_suppression: bool = True,
        pygnmi_suppression: bool = True,
    ) -> None:
        """
        Apply comprehensive external library suppression.

        Args:
            custom_levels: Additional suppression levels
            include_defaults: Include default suppressions
            deep_grpc_suppression: Enable deep gRPC suppression
            pygnmi_suppression: Enable specific pygnmi suppression
        """
        # Environment variable suppression (must be first)
        cls.setup_environment_suppression()

        # Python logging suppression
        cls.setup_python_logging_suppression(custom_levels, include_defaults)

        # Deep library-specific suppression
        if deep_grpc_suppression:
            cls.setup_grpc_deep_suppression()

        if pygnmi_suppression:
            cls.setup_pygnmi_suppression()

    @classmethod
    def get_default_suppressions(cls) -> Dict[str, str]:
        """Get the default suppression configuration."""
        return cls.DEFAULT_SUPPRESSIONS.copy()

    @classmethod
    def is_suppressed_library(cls, logger_name: str) -> bool:
        """Check if a logger name corresponds to a suppressed library."""
        return any(
            logger_name.startswith(lib_name)
            for lib_name in cls.DEFAULT_SUPPRESSIONS.keys()
        )


# Convenience functions for common use cases
def setup_mcp_suppression() -> None:
    """
    Setup suppression optimized for MCP servers.

    MCP servers need clean stdout for JSON protocol, so this applies
    the most aggressive suppression available.
    """
    ExternalLibrarySuppressor.setup_all_suppressions(
        custom_levels={
            "pygnmi": "error",  # Only errors
            "grpc": "error",  # Only errors
            "urllib3": "error",  # Only errors
            "asyncio": "error",  # Only errors
        },
        deep_grpc_suppression=True,
        pygnmi_suppression=True,
    )


def setup_cli_suppression() -> None:
    """
    Setup suppression optimized for CLI usage.

    CLI tools need readable output, so this uses moderate suppression
    that still allows important warnings through.
    """
    ExternalLibrarySuppressor.setup_all_suppressions(
        custom_levels={
            "pygnmi": "warning",  # Allow warnings
            "grpc": "warning",  # Allow warnings
            "urllib3": "warning",  # Standard
            "asyncio": "warning",  # Standard
        },
        deep_grpc_suppression=False,  # Less aggressive for CLI
        pygnmi_suppression=True,
    )


def setup_development_suppression() -> None:
    """
    Setup suppression for development/debugging.

    Allows more verbose logging from external libraries for debugging.
    """
    ExternalLibrarySuppressor.setup_all_suppressions(
        custom_levels={
            "pygnmi": "info",  # More verbose for debugging
            "grpc": "warning",  # Some gRPC info might be useful
            "urllib3": "warning",  # Standard
            "asyncio": "warning",  # Standard
        },
        deep_grpc_suppression=False,
        pygnmi_suppression=False,
    )
