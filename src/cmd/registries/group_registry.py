#!/usr/bin/env python3
"""Group registry for managing Click command groups"""

from typing import Dict, Optional, List
import click
from src.cmd.schemas import CommandGroup
from src.logging.config import get_logger

logger = get_logger(__name__)

# Context settings for all groups
CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


class GroupRegistry:
    """Registry for managing Click command groups"""

    def __init__(self):
        self._groups: Dict[CommandGroup, click.Group] = {}
        self._initialize_groups()

    def _initialize_groups(self) -> None:
        """Initialize all command groups from the CommandGroup enum"""
        for group_enum in CommandGroup:
            self._groups[group_enum] = self._create_group(group_enum)

    def _create_group(self, group_enum: CommandGroup) -> click.Group:
        """Create a Click group from CommandGroup enum"""

        @click.group(context_settings=CONTEXT_SETTINGS)
        @click.pass_context
        def group_func(ctx):
            """Dynamic group function"""
            pass

        # Set the group properties
        group_func.name = group_enum.group_name
        group_func.help = self._get_group_help(group_enum)
        group_func.short_help = group_enum.title

        return group_func

    def _get_group_help(self, group_enum: CommandGroup) -> str:
        """Generate help text for a group including alias information"""
        help_text = f"{group_enum.description}\n\n"
        help_text += f"Alias: {group_enum.alias}\n\n"
        help_text += f"Usage: gnmibuddy {group_enum.group_name} [OPTIONS] COMMAND [ARGS]...\n"
        help_text += (
            f"   or: gnmibuddy {group_enum.alias} [OPTIONS] COMMAND [ARGS]..."
        )
        return help_text

    def get_group(self, group_enum: CommandGroup) -> Optional[click.Group]:
        """Get Click group by CommandGroup enum"""
        return self._groups.get(group_enum)

    def get_group_by_name(self, name: str) -> Optional[click.Group]:
        """Get Click group by name or alias

        Args:
            name: Group name or alias to look up

        Returns:
            Click group if found, None otherwise
        """
        # Try to resolve the name or alias to a CommandGroup
        group_enum = CommandGroup.resolve_name_or_alias(name)
        if group_enum:
            return self._groups.get(group_enum)
        return None

    def get_all_groups(self) -> Dict[CommandGroup, click.Group]:
        """Get all registered groups"""
        return self._groups.copy()

    def get_valid_group_names_and_aliases(self) -> List[str]:
        """Get all valid group names and aliases

        Returns:
            List of all valid group names and aliases
        """
        return CommandGroup.get_all_names_and_aliases()

    def is_valid_group_name_or_alias(self, name: str) -> bool:
        """Check if name is a valid group name or alias"""
        return CommandGroup.is_valid_name_or_alias(name)


# Global group registry instance
group_registry = GroupRegistry()
