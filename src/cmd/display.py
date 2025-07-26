#!/usr/bin/env python3
"""Display and formatting utilities for CLI help and output"""

from typing import List, Optional
from src.cmd.schemas import Command, CommandGroup
from src.cmd.schemas.commands import command_registry
from src.logging import get_logger

logger = get_logger(__name__)


# Help text templates - separated from logic for better readability
MAIN_HELP_TEMPLATE = """Usage: gnmibuddy [OPTIONS] COMMAND [ARGS]...

📋 INVENTORY REQUIREMENT:
  You must provide device inventory via either:
  • --inventory PATH_TO_FILE.json
  • Set NETWORK_INVENTORY environment variable

Options:
  -h, --help               Show this message and exit
  --log-level [debug|info|warning|error]
                           Set the global logging level
  --all-devices            Run command on all devices concurrently
  --inventory TEXT         Path to inventory JSON file (REQUIRED)

Commands:

{commands_section}{examples_section}

Run 'uv run gnmibuddy.py COMMAND --help' for more information on a specific command.
Run 'uv run gnmibuddy.py GROUP --help' to see commands in a specific group.
"""

GROUP_HELP_TEMPLATE = """Usage: gnmibuddy {group_name} [OPTIONS] COMMAND [ARGS]...{alias_usage}

{group_description}

Commands:
{commands_list}

Run 'uv run gnmibuddy.py {group_name} COMMAND --help' for more information on a specific command."""

EXAMPLES_SECTION_TEMPLATE = """Examples:
{example_lines}"""


# Helper function for external components that need basic command info
def get_command_names() -> List[str]:
    """Get all available command names (for backward compatibility)"""
    return Command.get_all_command_names()


def get_group_names() -> List[str]:
    """Get all available group names (for backward compatibility)"""
    return CommandGroup.get_all_names()


def get_all_valid_names() -> List[str]:
    """Get all valid command and group names including aliases"""
    names = CommandGroup.get_all_names_and_aliases()
    names.extend(Command.get_all_command_names())
    return names


def validate_command_group(group_name: str) -> bool:
    """Validate if a group name or alias is valid"""
    return CommandGroup.is_valid_name_or_alias(group_name)


def resolve_group_alias(name_or_alias: str) -> Optional[str]:
    """Resolve group alias to full name"""
    group = CommandGroup.resolve_name_or_alias(name_or_alias)
    return group.group_name if group else None


class HelpExampleProvider:
    """Provides command examples for help text by inspecting command modules"""

    @staticmethod
    def get_examples_from_command_module(
        command_name: str, group_name: str, example_type: str = "detailed"
    ) -> Optional[str]:
        """Get examples from a command module

        Args:
            command_name: Name of the command
            group_name: Name of the command group
            example_type: Type of examples to retrieve ("basic" or "detailed")

        Returns:
            Example text or None if not found
        """
        # Resolve group alias to full name if needed
        resolved_group = CommandGroup.resolve_name_or_alias(group_name)
        if not resolved_group:
            return None

        actual_group_name = resolved_group.group_name

        try:
            # Try to import the command module
            import importlib

            module_name = f"src.cmd.commands.{actual_group_name}.{command_name.replace('-', '_')}"
            command_module = importlib.import_module(module_name)

            # Look for example functions
            if example_type == "basic" and hasattr(
                command_module, "basic_usage"
            ):
                basic_usage_func = getattr(command_module, "basic_usage")
                return basic_usage_func()
            elif example_type == "detailed" and hasattr(
                command_module, "detailed_examples"
            ):
                detailed_examples_func = getattr(
                    command_module, "detailed_examples"
                )
                return detailed_examples_func()
            elif hasattr(command_module, "_get_command_help"):
                get_command_help_func = getattr(
                    command_module, "_get_command_help"
                )
                return get_command_help_func()

        except ImportError:
            logger.debug(
                "Could not import command module for %s.%s",
                actual_group_name,
                command_name,
            )
        except Exception as e:
            logger.debug(
                "Error getting examples from %s.%s: %s",
                actual_group_name,
                command_name,
                e,
            )

        return None

    @staticmethod
    def get_command_description_from_module(
        command_name: str, group_name: str
    ) -> Optional[str]:
        """Get command description from command enum or module"""
        # First try to get from Command enum
        command_enum = Command.get_by_name(command_name)
        if command_enum:
            return command_enum.description

        return None

    @staticmethod
    def get_fallback_examples(command_name: str, group_name: str) -> str:
        """Generate fallback examples when module examples aren't available"""
        # Resolve group alias to full name
        resolved_group = CommandGroup.resolve_name_or_alias(group_name)
        if not resolved_group:
            return f"uv run gnmibuddy.py {group_name} {command_name} --help"

        actual_group_name = resolved_group.group_name
        alias = resolved_group.alias

        examples = [
            f"# Basic usage",
            f"uv run gnmibuddy.py {actual_group_name} {command_name} --device R1",
            f"",
            f"# Using alias",
            f"uv run gnmibuddy.py {alias} {command_name} --device R1",
            f"",
            f"# Get help",
            f"uv run gnmibuddy.py {actual_group_name} {command_name} --help",
        ]

        return "\n".join(examples)

    @staticmethod
    def get_command_examples(command_name: str, group_name: str) -> str:
        """Get examples for a command, trying multiple sources"""
        # First try detailed examples from module
        examples = HelpExampleProvider.get_examples_from_command_module(
            command_name, group_name, "detailed"
        )
        if examples:
            return examples

        # Then try basic examples
        examples = HelpExampleProvider.get_examples_from_command_module(
            command_name, group_name, "basic"
        )
        if examples:
            return examples

        # Finally, generate fallback
        return HelpExampleProvider.get_fallback_examples(
            command_name, group_name
        )


class GroupedHelpFormatter:
    """Formats help text with grouped commands and intelligent alias handling"""

    def __init__(self):
        # Use the centralized command registry and CommandGroup enum
        self.command_registry = command_registry

    def _get_fallback_command_description(self, command_name: str) -> str:
        """Generate a fallback description for commands without descriptions"""
        return f"Execute {command_name} operation"

    def get_command_description(
        self, command_name: str, group_name: str
    ) -> str:
        """Get description for a command

        Args:
            command_name: Name of the command
            group_name: Name of the command group

        Returns:
            Command description
        """
        # Try to get from module first
        description = HelpExampleProvider.get_command_description_from_module(
            command_name, group_name
        )
        if description:
            return description

        # Fallback to a generic description
        return self._get_fallback_command_description(command_name)

    def _build_commands_section(self) -> str:
        """Build the commands section of help text"""
        lines = []
        groups = list(CommandGroup)

        for i, group_enum in enumerate(groups):
            # Group header with alias
            group_line = f"  {group_enum.group_name} ({group_enum.alias})"
            lines.append(f"{group_line:<25} {group_enum.title}")

            # Get commands for this group
            commands = self.command_registry.get_commands_for_group(
                group_enum.group_name
            )

            # Sort commands for consistent display
            commands.sort(key=lambda cmd: cmd.name)

            # Add each command with indentation
            for cmd_info in commands:
                cmd_line = f"    {cmd_info.name}"
                lines.append(f"{cmd_line:<23} {cmd_info.description}")

            # Only add empty line between groups, not after the last one
            if i < len(groups) - 1:
                lines.append("")

        return "\n".join(lines)

    def _build_enhanced_commands_section(self) -> str:
        """Build an enhanced commands section with emojis and better visual formatting"""
        lines = []
        groups = list(CommandGroup)

        # Emoji mapping for different command groups
        group_emojis = {
            "device": "🔧",
            "network": "🌐",
            "topology": "🗺️",
            "ops": "⚙️",
            "manage": "📋",
        }

        for i, group_enum in enumerate(groups):
            # Get emoji for group
            emoji = group_emojis.get(group_enum.group_name, "📁")

            # Enhanced group header with emoji and alias
            group_line = (
                f"  {emoji} {group_enum.group_name} ({group_enum.alias})"
            )
            lines.append(f"{group_line:<35} {group_enum.title}")

            # Get commands for this group
            commands = self.command_registry.get_commands_for_group(
                group_enum.group_name
            )

            # Sort commands for consistent display
            commands.sort(key=lambda cmd: cmd.name)

            # Add each command with better indentation and formatting
            for cmd_info in commands:
                cmd_line = f"    {cmd_info.name}"
                lines.append(f"{cmd_line:<33} {cmd_info.description}")

            # Only add empty line between groups, not after the last one
            if i < len(groups) - 1:
                lines.append("")

        return "\n".join(lines)

    def _build_simple_commands_section(self) -> str:
        """Build a simple, clean commands section following Docker/kubectl style"""
        lines = []
        groups = list(CommandGroup)

        for i, group_enum in enumerate(groups):
            # Simple group header with alias - Docker style
            group_line = f"  {group_enum.group_name} ({group_enum.alias})"
            lines.append(f"{group_line:<20} {group_enum.title}")

            # Get commands for this group
            commands = self.command_registry.get_commands_for_group(
                group_enum.group_name
            )

            # Sort commands for consistent display
            commands.sort(key=lambda cmd: cmd.name)

            # Add each command with simple indentation
            for cmd_info in commands:
                cmd_line = f"    {cmd_info.name}"
                lines.append(f"{cmd_line:<16} {cmd_info.description}")

            # Only add empty line between groups, not after the last one
            if i < len(groups) - 1:
                lines.append("")

        return "\n".join(lines)

    def _build_examples_section(self) -> str:
        """Build the examples section content for template"""
        example_lines = [
            "  # List all devices",
            "  uv run gnmibuddy.py device list",
            "",
            "  # Get device information",
            "  uv run gnmibuddy.py device info --device R1",
            "  uv run gnmibuddy.py d info --device R1  # Using alias",
            "",
            "  # Get interface information",
            "  uv run gnmibuddy.py network interface --device R1",
            "  uv run gnmibuddy.py n interface --device R1  # Using alias",
            "",
            "  # Batch operations",
            "  uv run gnmibuddy.py device info --all-devices",
            "  uv run gnmibuddy.py device info --devices R1,R2,R3",
            "",
            "  # Different output formats",
            "  uv run gnmibuddy.py device info --device R1 --output yaml",
            "",
            "  # Get detailed help for any command",
            "  uv run gnmibuddy.py device info --help",
            "  uv run gnmibuddy.py network interface --help",
        ]

        return "\n".join(example_lines)

    def format_grouped_help(self, show_examples: bool = False) -> str:
        """Format the complete help text with grouped commands

        Args:
            show_examples: Whether to include examples section

        Returns:
            Formatted help text
        """
        commands_section = self._build_commands_section()

        if show_examples:
            examples_content = self._build_examples_section()
            examples_section = "\n\n" + EXAMPLES_SECTION_TEMPLATE.format(
                example_lines=examples_content
            )
        else:
            examples_section = ""

        # Format the template and clean up extra whitespace
        result = MAIN_HELP_TEMPLATE.format(
            commands_section=commands_section,
            examples_section=examples_section,
        )

        # Remove any multiple consecutive blank lines and trailing whitespace
        import re

        result = re.sub(r"\n{3,}", "\n\n", result)
        return result.strip()

    def _get_commands_in_group(self, group) -> List[str]:
        """Get command names for a group (for backward compatibility)"""
        commands = self.command_registry.get_commands_for_group(
            group.group_name
        )
        return [cmd.name for cmd in commands]


def display_all_commands(detailed=False):
    """Display all commands organized by groups"""
    import click

    formatter = GroupedHelpFormatter()
    help_text = formatter.format_grouped_help(show_examples=detailed)
    click.echo(help_text)


def display_group_help(group_name: str, group_commands: List[str]) -> str:
    """Display help for a specific group

    Args:
        group_name: Name of the group
        group_commands: List of command names in the group

    Returns:
        Formatted help text for the group
    """
    # Resolve the group name/alias
    group_enum = CommandGroup.resolve_name_or_alias(group_name)
    if not group_enum:
        return f"Unknown group: {group_name}"

    # Build alias usage line
    alias_usage = ""
    if group_enum.alias:
        alias_usage = f"\n       uv run gnmibuddy.py {group_enum.alias} [OPTIONS] COMMAND [ARGS]...  # Short alias"

    # Build commands list
    commands_list_lines = []
    for cmd_name in sorted(group_commands):
        description = (
            HelpExampleProvider.get_command_description_from_module(
                cmd_name, group_name
            )
            or f"Execute {cmd_name} operation"
        )
        commands_list_lines.append(f"  {cmd_name:<12} {description}")

    commands_list = "\n".join(commands_list_lines)

    return GROUP_HELP_TEMPLATE.format(
        group_name=group_enum.group_name,
        alias_usage=alias_usage,
        group_description=group_enum.description,
        commands_list=commands_list,
    ).strip()
