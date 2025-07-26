#!/usr/bin/env python3
"""
Convenience functions for logging configuration.

This module provides the main configure_logging function and other
convenience functions for backward compatibility with the existing API.
"""

import logging
from typing import Dict, Optional

from ..config.configurator import LoggingConfigurator


def configure_logging(
    log_level: Optional[str] = None,
    module_levels: Optional[Dict[str, str]] = None,
    structured: bool = False,
    external_suppression_mode: str = "cli",
) -> logging.Logger:
    """
    Configure the application's logging with OTel best practices.

    This is the main entry point for logging configuration, providing
    backward compatibility with the original API.

    Args:
        log_level: Global logging level (debug, info, warning, error)
        module_levels: Dict mapping module names to specific log levels
        structured: Whether to use structured JSON logging
        external_suppression_mode: Type of external library suppression

    Returns:
        Configured root application logger

    Raises:
        ValueError: If configuration parameters are invalid
    """
    return LoggingConfigurator.configure(
        global_level=log_level,
        module_levels=module_levels,
        enable_structured=structured,
        enable_file_output=True,  # Default to file output
        log_file=None,  # Use default file naming
        enable_external_suppression=True,  # Default to suppression
        external_suppression_mode=external_suppression_mode,
    )
