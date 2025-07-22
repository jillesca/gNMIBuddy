#!/usr/bin/env python3
"""Error providers for command-specific error handling"""

from typing import Dict, Any, Optional
from src.cmd.schemas import Command, CommandGroup

# Import the command registry to find command info
from src.cmd.schemas.commands import command_registry


class CommandErrorProvider:
    """Enhanced error provider with automatic Command enum integration"""

    def __init__(self, command: Command):
        self.command = command

    @property
    def group(self) -> Optional[CommandGroup]:
        """Get the CommandGroup for this command"""
        return self._resolve_group()

    def _resolve_group(self) -> Optional[CommandGroup]:
        """Resolve the group for this command"""
        # Find the command info from the registry
        cmd_info = None
        for info in command_registry.get_all_commands():
            if info.command == self.command:
                cmd_info = info
                break

        return cmd_info.group if cmd_info else None

    @property
    def command_name(self) -> str:
        """Get the command name"""
        return self.command.command_name

    @property
    def group_name(self) -> str:
        """Get the group name"""
        group = self.group
        return group.group_name if group else ""

    @property
    def full_command_name(self) -> str:
        """Get the full command name (group + command)"""
        return (
            f"{self.group_name} {self.command_name}"
            if self.group_name
            else self.command_name
        )

    def get_error_context(self) -> Dict[str, Any]:
        """Get context information for error handling"""
        return {
            "command": self.command_name,
            "group": self.group_name,
            "full_command": self.full_command_name,
            "supports_batch": self.supports_batch(),
            "supports_detail": self.supports_detail(),
            "requires_device": self.requires_device(),
        }

    def requires_device(self) -> bool:
        """Check if this command requires a device parameter"""
        cmd_info = command_registry.get_command_info(
            self.group_name, self.command_name
        )
        return cmd_info.requires_device if cmd_info else True

    def supports_batch(self) -> bool:
        """Check if this command supports batch operations"""
        cmd_info = command_registry.get_command_info(
            self.group_name, self.command_name
        )
        return cmd_info.supports_batch if cmd_info else True

    def supports_detail(self) -> bool:
        """Check if this command supports detail flag"""
        cmd_info = command_registry.get_command_info(
            self.group_name, self.command_name
        )
        return cmd_info.supports_detail if cmd_info else True
