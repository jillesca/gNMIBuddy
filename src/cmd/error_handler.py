#!/usr/bin/env python3
"""Enhanced error handling system for CLI - main interface (delegating to new architecture)"""

# Re-export from the new organized error handling system
from src.cmd.error_handling import CLIErrorHandler, handle_click_exception
from src.cmd.error_handling.click_integration import (
    suggest_command_from_typo,
    handle_inventory_error,
)

# Maintain backward compatibility by exporting the main handler instance
from src.cmd.error_handling.handlers import error_handler

# Export all the main interfaces for backward compatibility
__all__ = [
    "CLIErrorHandler",
    "handle_click_exception",
    "error_handler",
    "suggest_command_from_typo",
    "handle_inventory_error",
]
