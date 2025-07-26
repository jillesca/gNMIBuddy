#!/usr/bin/env python3
"""
Environment variable configuration reader.

This module is responsible for reading and parsing logging configuration
from environment variables, following the Single Responsibility Principle.
"""

import os
from typing import Dict, Any, Optional

from ..core.enums import LogLevel, SuppressionMode


class EnvironmentConfigReader:
    """
    Reads logging configuration from environment variables.

    Encapsulates all environment variable reading logic in one place,
    providing validation and type conversion for environment values.
    """

    # Environment variable names
    LOG_LEVEL_VAR = "GNMIBUDDY_LOG_LEVEL"
    MODULE_LEVELS_VAR = "GNMIBUDDY_MODULE_LEVELS"
    STRUCTURED_LOGGING_VAR = "GNMIBUDDY_STRUCTURED_LOGGING"
    LOG_FILE_VAR = "GNMIBUDDY_LOG_FILE"
    EXTERNAL_SUPPRESSION_MODE_VAR = "GNMIBUDDY_EXTERNAL_SUPPRESSION_MODE"

    @classmethod
    def read_configuration(cls) -> Dict[str, Any]:
        """
        Read complete logging configuration from environment variables.

        Returns:
            Dictionary with parsed environment variable values
        """
        config = {}

        # Read global log level
        if global_level := cls._read_log_level():
            config["global_level"] = global_level

        # Read module-specific levels
        if module_levels := cls._read_module_levels():
            config["module_levels"] = module_levels

        # Read structured logging flag
        if structured_flag := cls._read_structured_logging():
            config["enable_structured"] = structured_flag

        # Read custom log file
        if log_file := cls._read_log_file():
            config["log_file"] = log_file

        # Read suppression mode
        if suppression_mode := cls._read_suppression_mode():
            config["external_suppression_mode"] = suppression_mode

        return config

    @classmethod
    def _read_log_level(cls) -> Optional[str]:
        """Read and validate global log level."""
        level_str = os.getenv(cls.LOG_LEVEL_VAR)
        if not level_str:
            return None

        try:
            # Validate by attempting to parse
            LogLevel.from_string(level_str)
            return level_str.lower().strip()
        except ValueError:
            # Invalid level, ignore silently
            return None

    @classmethod
    def _read_module_levels(cls) -> Optional[Dict[str, str]]:
        """Read and parse module-specific log levels."""
        module_levels_str = os.getenv(cls.MODULE_LEVELS_VAR)
        if not module_levels_str:
            return None

        module_levels = {}
        try:
            for pair in module_levels_str.split(","):
                if "=" not in pair:
                    continue

                module, level = pair.strip().split("=", 1)
                module = module.strip()
                level = level.strip().lower()

                # Validate level
                try:
                    LogLevel.from_string(level)
                    module_levels[module] = level
                except ValueError:
                    # Invalid level for this module, skip it
                    continue

        except Exception:
            # Malformed module levels, return empty dict
            return {}

        return module_levels if module_levels else None

    @classmethod
    def _read_structured_logging(cls) -> Optional[bool]:
        """Read structured logging flag."""
        structured_str = os.getenv(cls.STRUCTURED_LOGGING_VAR)
        if not structured_str:
            return None

        return structured_str.lower().strip() in ["true", "1", "yes", "on"]

    @classmethod
    def _read_log_file(cls) -> Optional[str]:
        """Read custom log file path."""
        log_file = os.getenv(cls.LOG_FILE_VAR)
        return log_file.strip() if log_file else None

    @classmethod
    def _read_suppression_mode(cls) -> Optional[str]:
        """Read and validate suppression mode."""
        mode_str = os.getenv(cls.EXTERNAL_SUPPRESSION_MODE_VAR)
        if not mode_str:
            return None

        try:
            # Validate by attempting to parse
            SuppressionMode.from_string(mode_str)
            return mode_str.lower().strip()
        except ValueError:
            # Invalid mode, ignore silently
            return None

    @classmethod
    def get_supported_variables(cls) -> Dict[str, str]:
        """
        Get documentation for supported environment variables.

        Returns:
            Dictionary mapping variable names to descriptions
        """
        return {
            cls.LOG_LEVEL_VAR: "Global log level (debug, info, warning, error)",
            cls.MODULE_LEVELS_VAR: "Module-specific levels (format: module1=debug,module2=warning)",
            cls.STRUCTURED_LOGGING_VAR: "Enable structured JSON logging (true/false)",
            cls.LOG_FILE_VAR: "Custom log file path",
            cls.EXTERNAL_SUPPRESSION_MODE_VAR: "External library suppression mode (cli, mcp, development)",
        }
