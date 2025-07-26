#!/usr/bin/env python3
"""
Logging utility functions.

This module provides utility functions for dynamic log level management
and logger creation.
"""

from .dynamic import get_logger

__all__ = [
    "get_logger",
]
