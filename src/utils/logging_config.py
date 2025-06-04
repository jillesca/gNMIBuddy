#!/usr/bin/env python3
"""
Logging configuration module for network tools application.
Provides centralized logging configuration for the application.
"""
import os
import sys
import logging


def configure_logging(log_level=None):
    """
    Configure the application's logging.

    Args:
        log_level: Optional logging level from command line (debug, info, warning, error)
    """
    level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
    }

    # Default to INFO if not specified
    level = (
        level_map.get(log_level.lower(), logging.INFO)
        if log_level
        else logging.INFO
    )

    # Ensure log directory exists
    log_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
    )
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "network_tools.log")

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file),
        ],
    )

    logger = logging.getLogger(__name__)
    # logger.info(
    #     f"Logging initialized with level: {logging.getLevelName(level)}"
    # )
    # logger.info(f"Log file: {log_file}")

    return logger


def get_logger(name):
    """
    Get a logger for a specific module.

    Args:
        name: The name of the module requesting the logger

    Returns:
        A configured logger instance
    """
    return logging.getLogger(name)
