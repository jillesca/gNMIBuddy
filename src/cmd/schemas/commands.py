#!/usr/bin/env python3
"""Command schema definitions for CLI organization"""

from typing import Dict, List, Optional
from dataclasses import dataclass

from .command import Command
from .command_group import CommandGroup


@dataclass
class CommandInfo:
    """Information about a specific command"""

    command: Command
    group: CommandGroup
    supports_batch: bool = True
    supports_detail: bool = True
    requires_device: bool = True

    @property
    def name(self) -> str:
        """Get command name (for backward compatibility)"""
        return self.command.command_name

    @property
    def description(self) -> str:
        """Get command description"""
        return self.command.description

    @property
    def full_command(self) -> str:
        """Get full command string"""
        return f"{self.group.group_name} {self.command.command_name}"


class CommandRegistry:
    """Registry for command information and validation"""

    def __init__(self):
        self._commands: Dict[str, CommandInfo] = {}
        self._initialize_commands()

    def _initialize_commands(self):
        """Initialize with known commands using Command enum"""
        commands = [
            # Device commands
            CommandInfo(
                command=Command.DEVICE_INFO,
                group=CommandGroup.DEVICE,
            ),
            CommandInfo(
                command=Command.DEVICE_PROFILE,
                group=CommandGroup.DEVICE,
            ),
            CommandInfo(
                command=Command.DEVICE_LIST,
                group=CommandGroup.DEVICE,
                requires_device=False,
            ),
            CommandInfo(
                command=Command.DEVICE_CAPABILITIES,
                group=CommandGroup.DEVICE,
            ),
            # Network commands
            CommandInfo(
                command=Command.NETWORK_ROUTING,
                group=CommandGroup.NETWORK,
            ),
            CommandInfo(
                command=Command.NETWORK_INTERFACE,
                group=CommandGroup.NETWORK,
            ),
            CommandInfo(
                command=Command.NETWORK_MPLS,
                group=CommandGroup.NETWORK,
            ),
            CommandInfo(
                command=Command.NETWORK_VPN,
                group=CommandGroup.NETWORK,
            ),
            # Topology commands
            CommandInfo(
                command=Command.TOPOLOGY_NEIGHBORS,
                group=CommandGroup.TOPOLOGY,
            ),
            CommandInfo(
                command=Command.TOPOLOGY_NETWORK,
                group=CommandGroup.TOPOLOGY,
                requires_device=False,
            ),
            # Operations commands
            CommandInfo(
                command=Command.OPS_LOGS,
                group=CommandGroup.OPS,
            ),
            CommandInfo(
                command=Command.OPS_VALIDATE,
                group=CommandGroup.OPS,
            ),
            # Inventory commands
            CommandInfo(
                command=Command.INVENTORY_VALIDATE,
                group=CommandGroup.INVENTORY,
                supports_batch=False,  # File-level operation
                supports_detail=False,  # Not applicable
                requires_device=False,  # No device needed
            ),
        ]

        for cmd in commands:
            key = f"{cmd.group.group_name}.{cmd.name}"
            self._commands[key] = cmd

    def get_command_info(
        self, group_name: str, command_name: str
    ) -> Optional[CommandInfo]:
        """Get command information"""
        key = f"{group_name}.{command_name}"
        return self._commands.get(key)

    def get_commands_for_group(self, group_name: str) -> List[CommandInfo]:
        """Get all commands for a specific group"""
        group = CommandGroup.get_by_name(group_name)
        if not group:
            return []

        return [cmd for cmd in self._commands.values() if cmd.group == group]

    def get_all_commands(self) -> List[CommandInfo]:
        """Get all registered commands"""
        return list(self._commands.values())

    def command_requires_device(
        self, group_name: str, command_name: str
    ) -> bool:
        """Check if command requires device parameter"""
        cmd_info = self.get_command_info(group_name, command_name)
        return cmd_info.requires_device if cmd_info else True

    def command_supports_batch(
        self, group_name: str, command_name: str
    ) -> bool:
        """Check if command supports batch operations"""
        cmd_info = self.get_command_info(group_name, command_name)
        return cmd_info.supports_batch if cmd_info else True

    def command_supports_detail(
        self, group_name: str, command_name: str
    ) -> bool:
        """Check if command supports detail flag"""
        cmd_info = self.get_command_info(group_name, command_name)
        return cmd_info.supports_detail if cmd_info else True


# Global command registry instance
command_registry = CommandRegistry()
