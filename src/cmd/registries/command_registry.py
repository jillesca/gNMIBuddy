#!/usr/bin/env python3
"""Command registration system for CLI commands"""

from typing import Dict, Optional, List, Callable, TYPE_CHECKING
from src.cmd.schemas import Command, CommandGroup
from src.cmd.schemas.commands import command_registry
from src.logging.config import get_logger

if TYPE_CHECKING:
    from src.cmd.error_providers import CommandErrorProvider

logger = get_logger(__name__)


class CommandRegistry:
    """Registry for command functions and their metadata"""

    def __init__(self):
        self._command_functions: Dict[Command, Callable] = {}
        self._error_providers: Dict[Command, "CommandErrorProvider"] = {}

    def register_command(
        self, command: Command, command_function: Callable
    ) -> None:
        """Register a command function

        Args:
            command: Command enum value
            command_function: The Click command function to register
        """
        self._command_functions[command] = command_function
        logger.debug(
            "Registered command function: %s -> %s",
            command.command_name,
            getattr(command_function, "__name__", str(command_function)),
        )

    def register_error_provider(
        self, command: Command, error_provider: "CommandErrorProvider"
    ) -> None:
        """Register an error provider for a command"""
        self._error_providers[command] = error_provider

    def get_command_function(self, command: Command) -> Optional[Callable]:
        """Get the registered function for a command"""
        return self._command_functions.get(command)

    def get_error_provider(
        self, command: Command
    ) -> Optional["CommandErrorProvider"]:
        """Get the error provider for a command"""
        return self._error_providers.get(command)

    def get_group_for_command(
        self, command: Command
    ) -> Optional[CommandGroup]:
        """Get the command group for a command"""
        cmd_info = command_registry.get_command_info(
            command.name.split("_")[0].lower(), command.command_name
        )
        return cmd_info.group if cmd_info else None

    def get_registered_commands_for_group(
        self, group: CommandGroup
    ) -> List[Command]:
        """Get all registered commands for a group"""
        return [
            cmd
            for cmd in self._command_functions.keys()
            if self.get_group_for_command(cmd) == group
        ]

    def is_command_registered(self, command: Command) -> bool:
        """Check if a command is registered"""
        return command in self._command_functions


# Global registry instance
_command_registry = CommandRegistry()


def register_command(command: Command):
    """Decorator to register a command function"""

    def decorator(func: Callable):
        _command_registry.register_command(command, func)
        return func

    return decorator


def register_error_provider(
    command: Command, error_provider: "CommandErrorProvider"
) -> None:
    """Register an error provider for a command"""
    _command_registry.register_error_provider(command, error_provider)
