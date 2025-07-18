#!/usr/bin/env python3
"""Base classes and utilities for Click-based CLI command handling"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable
import click
from src.logging.config import get_logger
from src.cmd.context import CLIContext, service_registry


logger = get_logger(__name__)


class ClickCommand(ABC):
    """Base class for all Click-based CLI commands"""

    name: str = ""
    help: str = ""
    description: str = ""

    def __init__(self):
        """Initialize the command"""
        self.click_command = None

    @abstractmethod
    def execute(self, ctx: CLIContext, **kwargs):
        """Execute the command with the given context and parameters"""
        pass

    def get_click_options(self) -> list:
        """Return list of Click options for this command"""
        return []

    def create_click_command(self) -> click.Command:
        """Create and return the Click command"""
        if self.click_command is not None:
            return self.click_command

        # Get command-specific options
        options = self.get_click_options()

        # Create the command function
        @click.pass_context
        def command_func(click_ctx, **kwargs):
            """Generated command function for Click"""
            # Get CLI context from Click context
            cli_ctx = click_ctx.obj

            # Validate device options if needed
            if not cli_ctx.validate_device_options(self.name):
                click.echo(
                    f"Error: Device validation failed for command '{self.name}'",
                    err=True,
                )
                raise click.Abort()

            try:
                # Execute the command
                result = self.execute(cli_ctx, **kwargs)

                # Store result in Click context for processing
                click_ctx.obj._last_result = result

                return result

            except Exception as e:
                logger.error("Error executing command %s: %s", self.name, e)
                click.echo(f"Error executing command: {e}", err=True)
                raise click.Abort()

        # Apply options to the command function
        for option in reversed(options):  # Reverse to apply in correct order
            command_func = option(command_func)

        # Create the Click command
        self.click_command = click.command(name=self.name, help=self.help)(
            command_func
        )

        return self.click_command


class CommandRegistry:
    """Registry for managing Click commands"""

    def __init__(self):
        self._commands: Dict[str, ClickCommand] = {}

    def register(self, command: ClickCommand):
        """Register a command"""
        if not command.name:
            raise ValueError(
                f"Command {command.__class__.__name__} must define a name"
            )

        self._commands[command.name] = command
        logger.debug("Registered command: %s", command.name)

    def get(self, name: str) -> Optional[ClickCommand]:
        """Get a registered command"""
        return self._commands.get(name)

    def get_all(self) -> Dict[str, ClickCommand]:
        """Get all registered commands"""
        return self._commands.copy()

    def get_names(self) -> list:
        """Get all command names"""
        return list(self._commands.keys())


# Global command registry
command_registry = CommandRegistry()


def command_option(*option_args, **option_kwargs):
    """Decorator to add Click options to commands"""

    def decorator(func):
        # Store options in function for later use
        if not hasattr(func, "_click_options"):
            func._click_options = []
        func._click_options.append(click.option(*option_args, **option_kwargs))
        return func

    return decorator


def create_backward_compatible_args(ctx: CLIContext, **kwargs) -> object:
    """Create an argparse-like namespace for backward compatibility"""

    class Args:
        def __init__(self, ctx: CLIContext, **kwargs):
            # Map CLI context to args attributes
            self.device = ctx.device
            self.all_devices = ctx.all_devices
            self.max_workers = ctx.max_workers
            self.inventory = ctx.inventory
            self.log_level = ctx.log_level
            self.module_log_levels = ctx.module_log_levels
            self.structured_logging = ctx.structured_logging

            # Set default values for common command arguments
            self.protocol = None
            self.detail = False
            self.name = None
            self.vrf = None
            self.minutes = 5
            self.show_all_logs = False
            self.test_query = False
            self.log_action = None
            self.module = None
            self.level = None

            # Add command-specific kwargs (these will override defaults)
            for key, value in kwargs.items():
                setattr(self, key, value)

    return Args(ctx, **kwargs)


# Legacy compatibility functions for existing commands
def get_legacy_commands_dict():
    """Get legacy commands dictionary for backward compatibility"""
    from src.cmd.commands import (
        RoutingCommand,
        InterfaceCommand,
        MPLSCommand,
        VPNCommand,
        SystemCommand,
        DeviceProfileCommand,
        ListDevicesCommand,
        ListCommandsCommand,
        LoggingCommand,
        TestAllCommand,
        TopologyIPAdjacencyCommand,
        TopologyNeighborsCommand,
        LogLevelCommand,
    )

    return {
        cmd.name: cmd()
        for cmd in [
            RoutingCommand,
            InterfaceCommand,
            MPLSCommand,
            VPNCommand,
            ListDevicesCommand,
            ListCommandsCommand,
            LoggingCommand,
            TestAllCommand,
            SystemCommand,
            DeviceProfileCommand,
            TopologyIPAdjacencyCommand,
            TopologyNeighborsCommand,
            LogLevelCommand,
        ]
    }
