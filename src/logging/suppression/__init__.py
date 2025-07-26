#!/usr/bin/env python3
"""
External library suppression components.

This module provides utilities to suppress verbose logging from external
libraries that tend to pollute application logs.
"""

from .external import ExternalLibrarySuppressor
from .strategies import (
    get_suppression_strategy,
    setup_cli_suppression,
    setup_mcp_suppression,
    setup_development_suppression,
)

__all__ = [
    "ExternalLibrarySuppressor",
    "get_suppression_strategy",
    "setup_cli_suppression",
    "setup_mcp_suppression",
    "setup_development_suppression",
]
