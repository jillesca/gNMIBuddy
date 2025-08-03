#!/usr/bin/env python3
"""
Logging enums for type safety and consistency.

This module defines enums that replace string constants throughout
the logging system, following the Zen of Python principle of
"Explicit is better than implicit."
"""

import logging
from enum import Enum, IntEnum
from typing import Dict


class LogLevel(IntEnum):
    """
    Logging levels with integer values compatible with Python's logging module.

    Uses IntEnum to maintain compatibility with logging.Logger.setLevel()
    while providing type safety and preventing typos.
    """

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR

    @classmethod
    def from_string(cls, level_str: str) -> "LogLevel":
        """
        Convert string representation to LogLevel enum.

        Args:
            level_str: String representation (case-insensitive)

        Returns:
            LogLevel enum value

        Raises:
            ValueError: If level_str is not a valid log level
        """
        level_map = {
            "debug": cls.DEBUG,
            "info": cls.INFO,
            "warning": cls.WARNING,
            "error": cls.ERROR,
        }

        normalized = level_str.lower().strip()
        if normalized not in level_map:
            valid_levels = ", ".join(level_map.keys())
            raise ValueError(
                f"Invalid log level '{level_str}'. Valid levels: {valid_levels}"
            )

        return level_map[normalized]

    def to_string(self) -> str:
        """Convert LogLevel to lowercase string representation."""
        return self.name.lower()


class SuppressionMode(Enum):
    """
    External library suppression modes.

    Each mode defines a different strategy for suppressing external
    library logging based on the runtime context.
    """

    CLI = "cli"  # Moderate suppression for CLI tools
    MCP = "mcp"  # Aggressive suppression for MCP servers
    DEVELOPMENT = "development"  # Minimal suppression for debugging

    @classmethod
    def from_string(cls, mode_str: str) -> "SuppressionMode":
        """
        Convert string representation to SuppressionMode enum.

        Args:
            mode_str: String representation (case-insensitive)

        Returns:
            SuppressionMode enum value

        Raises:
            ValueError: If mode_str is not a valid suppression mode
        """
        mode_map = {
            "cli": cls.CLI,
            "mcp": cls.MCP,
            "development": cls.DEVELOPMENT,
        }

        normalized = mode_str.lower().strip()
        if normalized not in mode_map:
            valid_modes = ", ".join(mode_map.keys())
            raise ValueError(
                f"Invalid suppression mode '{mode_str}'. Valid modes: {valid_modes}"
            )

        return mode_map[normalized]

    def to_string(self) -> str:
        """Convert SuppressionMode to string representation."""
        return self.value


class EnvironmentVariable(Enum):
    """
    Environment variables used by gNMIBuddy for centralized reference.

    This enum provides a single place to define all environment variable names,
    following DRY principles and preventing typos throughout the codebase.
    """

    # Network configuration
    NETWORK_INVENTORY = "NETWORK_INVENTORY"

    # Logging configuration
    LOG_LEVEL = "GNMIBUDDY_LOG_LEVEL"
    MODULE_LEVELS = "GNMIBUDDY_MODULE_LEVELS"
    STRUCTURED_LOGGING = "GNMIBUDDY_STRUCTURED_LOGGING"
    LOG_FILE = "GNMIBUDDY_LOG_FILE"
    EXTERNAL_SUPPRESSION_MODE = "GNMIBUDDY_EXTERNAL_SUPPRESSION_MODE"

    # MCP configuration
    MCP_TOOL_DEBUG = "GNMIBUDDY_MCP_TOOL_DEBUG"

    def __str__(self) -> str:
        """Return the environment variable name as string."""
        return self.value

    @classmethod
    def get_all_variables(cls) -> Dict[str, str]:
        """
        Get all environment variables with their descriptions.

        Returns:
            Dictionary mapping variable names to descriptions
        """
        descriptions = {
            cls.NETWORK_INVENTORY: "Path to network device inventory JSON file",
            cls.LOG_LEVEL: "Global log level (debug, info, warning, error)",
            cls.MODULE_LEVELS: "Module-specific levels (format: module1=debug,module2=warning)",
            cls.STRUCTURED_LOGGING: "Enable structured JSON logging (true/false)",
            cls.LOG_FILE: "Custom log file path",
            cls.EXTERNAL_SUPPRESSION_MODE: "External library suppression mode (cli, mcp, development)",
            cls.MCP_TOOL_DEBUG: "Enable debug logging for MCP tools (true/false)",
        }

        return {var.value: descriptions[var] for var in cls}
