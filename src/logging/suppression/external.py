#!/usr/bin/env python3
"""
External library logging suppression.

This module provides the ExternalLibrarySuppressor class for controlling
verbose logging from external libraries like pygnmi, grpc, etc.
"""

import os
import logging
from typing import Dict, Optional
from dataclasses import dataclass, field

from ..core.enums import LogLevel


@dataclass(frozen=True)
class SuppressionConfiguration:
    """
    Configuration for external library suppression.

    Encapsulates suppression settings in a proper data structure
    rather than using plain dictionaries.
    """

    library_levels: Dict[str, LogLevel] = field(default_factory=dict)
    environment_variables: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def create_default(cls) -> "SuppressionConfiguration":
        """Create default suppression configuration."""
        default_levels = {
            "pygnmi": LogLevel.ERROR,
            "grpc": LogLevel.ERROR,
            "urllib3": LogLevel.WARNING,
            "asyncio": LogLevel.WARNING,
            "requests": LogLevel.WARNING,
            "paramiko": LogLevel.WARNING,
        }

        default_env_vars = {
            "GRPC_VERBOSITY": "ERROR",
            "GRPC_TRACE": "",
            "GRPC_GO_LOG_VERBOSITY_LEVEL": "99",
            "GRPC_GO_LOG_SEVERITY_LEVEL": "ERROR",
        }

        return cls(
            library_levels=default_levels,
            environment_variables=default_env_vars,
        )


class ExternalLibrarySuppressor:
    """
    Centralized suppression of external library logging.

    Handles both Python logging configuration and environment variable
    suppression for libraries that bypass Python's logging system.

    Refactored to use proper data structures and follow SRP.
    """

    @classmethod
    def apply_suppression(
        cls,
        config: SuppressionConfiguration,
        additional_levels: Optional[Dict[str, LogLevel]] = None,
    ) -> None:
        """
        Apply comprehensive external library suppression.

        Args:
            config: Suppression configuration to apply
            additional_levels: Additional library-specific levels
        """
        # Apply environment variable suppression first
        cls._setup_environment_suppression(config.environment_variables)

        # Prepare combined library levels
        combined_levels = config.library_levels.copy()
        if additional_levels:
            combined_levels.update(additional_levels)

        # Apply Python logging suppression
        cls._setup_python_logging_suppression(combined_levels)

        # Apply deep library-specific suppression
        cls._setup_grpc_deep_suppression()
        cls._setup_pygnmi_suppression()

    @classmethod
    def _setup_environment_suppression(cls, env_vars: Dict[str, str]) -> None:
        """Set environment variables to suppress external library output."""
        for env_var, value in env_vars.items():
            os.environ.setdefault(env_var, value)

    @classmethod
    def _setup_python_logging_suppression(
        cls, library_levels: Dict[str, LogLevel]
    ) -> None:
        """Configure Python logging suppression for external libraries."""
        for logger_name, level in library_levels.items():
            logger = logging.getLogger(logger_name)
            logger.setLevel(level)

    @classmethod
    def _setup_grpc_deep_suppression(cls) -> None:
        """Apply deep gRPC suppression at the library level."""
        try:
            import grpc

            # Disable main gRPC logger
            grpc_logger = logging.getLogger("grpc")
            grpc_logger.setLevel(LogLevel.ERROR)
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
                    module_logger.setLevel(LogLevel.ERROR)
                    module_logger.disabled = True
                except Exception:
                    # Silent fail for modules that don't exist
                    pass

        except ImportError:
            # gRPC not available, no suppression needed
            pass

    @classmethod
    def _setup_pygnmi_suppression(cls) -> None:
        """Apply specific pygnmi suppression."""
        try:
            # Suppress pygnmi main logger
            pygnmi_logger = logging.getLogger("pygnmi")
            pygnmi_logger.setLevel(LogLevel.ERROR)

            # Suppress pygnmi submodules that tend to be verbose
            pygnmi_modules = [
                "pygnmi.client",
                "pygnmi.path",
                "pygnmi.subscribe",
            ]

            for module_name in pygnmi_modules:
                try:
                    module_logger = logging.getLogger(module_name)
                    module_logger.setLevel(LogLevel.ERROR)
                except Exception:
                    pass

        except ImportError:
            # pygnmi not available
            pass

    @classmethod
    def get_default_configuration(cls) -> SuppressionConfiguration:
        """Get the default suppression configuration."""
        return SuppressionConfiguration.create_default()

    @classmethod
    def is_suppressed_library(cls, logger_name: str) -> bool:
        """Check if a logger name corresponds to a suppressed library."""
        default_config = cls.get_default_configuration()
        return any(
            logger_name.startswith(lib_name)
            for lib_name in default_config.library_levels.keys()
        )
