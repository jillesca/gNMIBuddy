#!/usr/bin/env python3
"""Base classes and utilities for Click-based CLI command handling"""
from typing import Any, Dict, Optional
from src.logging.config import get_logger
from src.cmd.context import CLIContext

logger = get_logger(__name__)


class ClickCommand:
    """Base class for Click-based CLI commands (if needed for future extensibility)"""

    name: str = ""
    help: str = ""
    description: str = ""

    def __init__(self):
        """Initialize the command"""
        self.click_command = None

    def execute(self, ctx: CLIContext, **kwargs):
        """Execute the command with the given context and parameters"""
        raise NotImplementedError("Subclasses must implement execute method")

    def get_click_options(self) -> list:
        """Return list of Click options for this command"""
        return []


# Minimal registry for any future command management needs
class CommandRegistry:
    """Registry for managing Click commands (minimal implementation)"""

    def __init__(self):
        self._commands: Dict[str, Any] = {}

    def register(self, name: str, command: Any):
        """Register a command"""
        self._commands[name] = command
        logger.debug("Registered command: %s", name)

    def get(self, name: str) -> Optional[Any]:
        """Get a registered command"""
        return self._commands.get(name)

    def get_all(self) -> Dict[str, Any]:
        """Get all registered commands"""
        return self._commands.copy()

    def get_names(self) -> list:
        """Get all command names"""
        return list(self._commands.keys())


# Global command registry (for any future use)
command_registry = CommandRegistry()
