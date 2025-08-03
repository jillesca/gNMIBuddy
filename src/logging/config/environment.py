#!/usr/bin/env python3
"""
Environment variable configuration reader.

This module is responsible for reading and parsing logging configuration
from environment variables using the centralized GNMIBuddySettings class.
"""

from typing import Dict, Any, Optional

from ..core.enums import LogLevel, SuppressionMode
from ..core.models import EnvironmentConfiguration


class EnvironmentConfigReader:
    """
    Reads logging configuration from environment variables using centralized settings.

    This class now uses the GNMIBuddySettings class to access environment variables
    consistently across the codebase, eliminating direct os.environ.get() calls.
    """

    @classmethod
    def read_configuration(cls) -> EnvironmentConfiguration:
        """
        Read complete logging configuration from environment variables using centralized settings.

        Returns:
            EnvironmentConfiguration object with parsed environment variable values
        """
        # Import here to avoid circular dependency
        from ...config.environment import get_settings

        settings = get_settings()

        # Read and validate all configuration values
        global_level = cls._validate_log_level(settings.gnmibuddy_log_level)
        module_levels = cls._parse_module_levels(
            settings.gnmibuddy_module_levels
        )
        structured_flag = cls._parse_structured_logging(
            settings.gnmibuddy_structured_logging
        )
        log_file = cls._parse_log_file(settings.gnmibuddy_log_file)
        suppression_mode = cls._validate_suppression_mode(
            settings.gnmibuddy_external_suppression_mode
        )

        return EnvironmentConfiguration(
            global_level=global_level,
            module_levels=module_levels,
            enable_structured=structured_flag,
            log_file=log_file,
            external_suppression_mode=suppression_mode,
        )

    @classmethod
    def _validate_log_level(cls, level_str: Optional[str]) -> Optional[str]:
        """Validate log level from settings."""
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
    def _parse_module_levels(
        cls, module_levels_str: Optional[str]
    ) -> Optional[Dict[str, str]]:
        """Parse module-specific log levels from settings."""
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
    def _parse_structured_logging(
        cls, structured_value: Optional[bool]
    ) -> Optional[bool]:
        """Parse structured logging flag from settings."""
        return structured_value

    @classmethod
    def _parse_log_file(cls, log_file: Optional[str]) -> Optional[str]:
        """Parse log file path from settings."""
        return log_file.strip() if log_file else None

    @classmethod
    def _validate_suppression_mode(
        cls, mode_str: Optional[str]
    ) -> Optional[str]:
        """Validate suppression mode from settings."""
        if not mode_str:
            return None

        try:
            # Validate by attempting to parse
            SuppressionMode.from_string(mode_str)
            return mode_str.lower().strip()
        except ValueError:
            # Invalid mode, ignore silently
            return None
