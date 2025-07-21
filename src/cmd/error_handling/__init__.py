#!/usr/bin/env python3
"""Error handling package for CLI with clear separation of concerns"""

from .handlers import CLIErrorHandler
from .templates import ErrorTemplates
from .click_integration import handle_click_exception

__all__ = [
    "CLIErrorHandler",
    "handle_click_exception",
    "ErrorTemplates",
]
