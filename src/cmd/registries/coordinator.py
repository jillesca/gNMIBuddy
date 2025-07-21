#!/usr/bin/env python3
"""Coordination between command registration and group management"""

import importlib
from typing import Dict, List
import click
from src.cmd.schemas import Command, CommandGroup
from src.cmd.registries.group_registry import group_registry
from src.logging.config import get_logger

logger = get_logger(__name__)


class RegistrationCoordinator:
    """Coordinates the registration of commands with their groups"""

    def __init__(self):
        self.group_registry = group_registry

    def register_all_commands_with_groups(self) -> None:
        """Register all commands with their appropriate Click groups"""
        self.import_all_command_modules()
        for group_enum in CommandGroup:
            self._register_commands_for_group(group_enum)

    def _register_commands_for_group(self, group_enum: CommandGroup) -> None:
        """Register all commands for a specific group

        Args:
            group_enum: The CommandGroup to register commands for
        """
        click_group = self.group_registry.get_group(group_enum)
        if not click_group:
            logger.error("No Click group found for %s", group_enum.group_name)
            return

        # Get all commands for this group
        commands_for_group = Command.get_commands_for_group_name(
            group_enum.group_name
        )

        for command_enum in commands_for_group:
            # Import the command module dynamically
            module_path = self._get_module_path_for_command(
                group_enum, command_enum
            )
            try:
                command_module = importlib.import_module(module_path)
                # Get the command function
                command_func_name = self._get_command_function_name(
                    group_enum, command_enum
                )
                if hasattr(command_module, command_func_name):
                    command_func = getattr(command_module, command_func_name)
                    click_group.add_command(
                        command_func, name=command_enum.command_name
                    )
                    logger.debug(
                        "Registered %s.%s",
                        group_enum.group_name,
                        command_enum.command_name,
                    )
                else:
                    logger.warning(
                        "Command function %s not found in module %s",
                        command_func_name,
                        module_path,
                    )
            except ImportError as e:
                logger.warning(
                    "Could not import command module %s: %s", module_path, e
                )

    def register_groups_with_cli(self, cli: click.Group) -> None:
        """Register all groups with the main CLI group

        Args:
            cli: The main Click CLI group
        """
        for group_enum in CommandGroup:
            click_group = self.group_registry.get_group(group_enum)
            if click_group:
                # Add group with both name and alias
                cli.add_command(click_group, name=group_enum.group_name)
                cli.add_command(click_group, name=group_enum.alias)
                logger.debug(
                    "Registered group %s with alias %s",
                    group_enum.group_name,
                    group_enum.alias,
                )

    def get_valid_group_names_and_aliases(self) -> List[str]:
        """Get all valid group names and aliases"""
        return CommandGroup.get_all_names_and_aliases()

    def is_valid_group_name_or_alias(self, name: str) -> bool:
        """Check if name is a valid group name or alias"""
        return CommandGroup.is_valid_name_or_alias(name)

    def get_registration_stats(self) -> Dict[str, int]:
        """Get statistics about command registration

        Returns:
            Dictionary with registration statistics
        """
        stats = {
            "total_groups": len(CommandGroup),
            "total_commands": len(list(Command)),
        }

        # Count commands per group
        for group_enum in CommandGroup:
            commands_for_group = Command.get_commands_for_group_name(
                group_enum.group_name
            )
            stats[f"{group_enum.group_name}_commands"] = len(
                commands_for_group
            )

        return stats

    def import_all_command_modules(self) -> None:
        """Import all command modules to ensure they are registered"""
        command_modules = [
            # Device commands
            "src.cmd.commands.device.info",
            "src.cmd.commands.device.profile",
            "src.cmd.commands.device.list",
            # Network commands
            "src.cmd.commands.network.routing",
            "src.cmd.commands.network.interface",
            "src.cmd.commands.network.mpls",
            "src.cmd.commands.network.vpn",
            # Topology commands
            "src.cmd.commands.topology.neighbors",
            "src.cmd.commands.topology.adjacency",
            # Operations commands
            "src.cmd.commands.ops.logs",
            "src.cmd.commands.ops.test_all",
        ]

        for module_path in command_modules:
            try:
                importlib.import_module(module_path)
                logger.debug("Imported command module: %s", module_path)
            except ImportError as e:
                logger.warning(
                    "Could not import command module %s: %s", module_path, e
                )

    def _get_module_path_for_command(
        self, group_enum: CommandGroup, command_enum: Command
    ) -> str:
        """Get the module path for a command"""
        return f"src.cmd.commands.{group_enum.group_name}.{command_enum.command_name.replace('-', '_')}"

    def _get_command_function_name(
        self, group_enum: CommandGroup, command_enum: Command
    ) -> str:
        """Get the expected function name for a command"""
        return f"{group_enum.group_name}_{command_enum.command_name.replace('-', '_')}"


# Global coordinator instance
coordinator = RegistrationCoordinator()
