#!/usr/bin/env python3
"""
Dynamic logging utilities.

This module provides utilities for dynamic logger creation and
runtime log level management.
"""

import logging
from typing import Union

from ..core.logger_names import LoggerNames
from ..core.enums import LogLevel


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module with proper naming convention.

    Converts Python module names to the application's logger naming convention
    and returns a configured logger instance.

    Args:
        name: The module name (typically __name__)

    Returns:
        A configured logger instance

    Example:
        # In a module file
        from src.logging.utils import get_logger
        logger = get_logger(__name__)
    """
    # Convert Python module names to our logger naming convention
    normalized_name = _normalize_logger_name(name)
    return logging.getLogger(normalized_name)


def _normalize_logger_name(name: str) -> str:
    """
    Normalize a module name to follow the application's logger naming convention.

    Args:
        name: Raw module name (e.g., from __name__)

    Returns:
        Normalized logger name following the gnmibuddy.* hierarchy
    """
    if name.startswith("src."):
        # Convert src.collectors.interfaces -> gnmibuddy.collectors.interfaces
        return name.replace("src.", LoggerNames.APP_ROOT + ".", 1)
    elif name.startswith("__main__"):
        return LoggerNames.APP_ROOT
    elif name.startswith(LoggerNames.APP_ROOT):
        # Already follows our convention
        return name
    else:
        # For modules outside our app hierarchy, keep their original name
        return name


def set_module_level(
    module_name: str, level: Union[str, LogLevel, int]
) -> None:
    """
    Dynamically change the log level for a specific module.

    This is a convenience function that delegates to the configurator
    for backward compatibility.

    Args:
        module_name: Name of the module logger
        level: New log level (string, LogLevel enum, or int)
    """
    from ..config.configurator import LoggingConfigurator

    LoggingConfigurator.set_module_level(module_name, level)


def get_module_levels() -> dict[str, str]:
    """
    Get current module-specific log levels.

    Returns:
        Dictionary mapping module names to level strings
    """
    from ..config.configurator import LoggingConfigurator

    return LoggingConfigurator.get_module_levels()
