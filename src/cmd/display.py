#!/usr/bin/env python3
"""Enhanced display functions for CLI output and help system"""
from typing import List, Optional
import click
from src.cmd.groups import COMMAND_GROUPS
from src.logging.config import get_logger
from src.cmd.examples.example_builder import ExampleBuilder

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

{commands_section}

{examples_section}

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


class HelpExampleProvider:
    """
    Duck typing system for getting help examples from command modules.

    Similar to the error provider system, this discovers help examples
    from command modules using duck typing pattern.
    """

    @staticmethod
    def get_examples_from_command_module(
        command_name: str, group_name: str, example_type: str = "detailed"
    ) -> Optional[str]:
        """
        Get examples from command module using duck typing.

        Args:
            command_name: Name of the command (e.g., "info")
            group_name: Group name (e.g., "device")
            example_type: Type of examples ("basic" or "detailed")

        Returns:
            Formatted example string or None if not found
        """
        try:
            module_path = f"src.cmd.commands.{group_name}.{command_name}"
            module = __import__(module_path, fromlist=[command_name])

            if example_type == "basic" and hasattr(module, "basic_usage"):
                basic_usage_func = getattr(module, "basic_usage")
                return basic_usage_func()
            elif example_type == "detailed" and hasattr(
                module, "detailed_examples"
            ):
                detailed_examples_func = getattr(module, "detailed_examples")
                return detailed_examples_func()

        except (ImportError, AttributeError) as e:
            logger.debug(
                "Could not get examples from %s.%s: %s",
                group_name,
                command_name,
                e,
            )

        return None

    @staticmethod
    def get_command_description_from_module(
        command_name: str, group_name: str
    ) -> Optional[str]:
        """
        Get command description from module using duck typing.

        Looks for a COMMAND_DESCRIPTION constant or get_description() function in the module.
        """
        try:
            module_path = f"src.cmd.commands.{group_name}.{command_name}"
            module = __import__(module_path, fromlist=[command_name])

            # Try to get description from module
            if hasattr(module, "COMMAND_DESCRIPTION"):
                return getattr(module, "COMMAND_DESCRIPTION")
            elif hasattr(module, "get_description"):
                desc_func = getattr(module, "get_description")
                return desc_func()

        except (ImportError, AttributeError) as e:
            logger.debug(
                "Could not get description from %s.%s: %s",
                group_name,
                command_name,
                e,
            )

        return None

    @staticmethod
    def get_fallback_examples(command_name: str, group_name: str) -> str:
        """
        Generate fallback examples using ExampleBuilder when no module examples exist.
        """
        try:
            if group_name == "device":
                if command_name == "list":
                    examples = ExampleBuilder.simple_command_examples(
                        f"{group_name} {command_name}"
                    )
                else:
                    examples = ExampleBuilder.standard_command_examples(
                        command=f"{group_name} {command_name}",
                        alias=f"d {command_name}",
                        detail_option=True,
                        batch_operations=True,
                    )
            elif group_name == "network":
                examples = ExampleBuilder.network_command_examples(
                    command=command_name,
                    detail_option=True,
                    batch_operations=True,
                )
            else:
                # Generic fallback
                examples = ExampleBuilder.standard_command_examples(
                    command=f"{group_name} {command_name}",
                    detail_option=True,
                    batch_operations=True,
                )

            return examples.for_help(max_examples=3)

        except Exception as e:
            logger.debug(
                "Error generating fallback examples for %s.%s: %s",
                group_name,
                command_name,
                e,
            )
            return f"\nExamples:\n  uv run gnmibuddy.py {group_name} {command_name} --device R1"

    @staticmethod
    def get_command_examples(command_name: str, group_name: str) -> str:
        """
        Get command examples using duck typing with fallbacks.

        1. Try to get from command module (duck typing)
        2. Fall back to ExampleBuilder
        3. Final fallback to basic example
        """
        # Try duck typing first
        examples = HelpExampleProvider.get_examples_from_command_module(
            command_name, group_name, "detailed"
        )

        if examples:
            return examples

        # Fall back to ExampleBuilder
        return HelpExampleProvider.get_fallback_examples(
            command_name, group_name
        )


class GroupedHelpFormatter:
    """
    Custom help formatter that groups commands by category using duck typing.

    Uses duck typing to get command descriptions and examples from command modules,
    falling back to hardcoded defaults when modules don't provide them.
    """

    def __init__(self):
        # Fallback command descriptions - can be overridden by modules using duck typing
        self.fallback_command_descriptions = {
            # Device group
            "info": "Get system information from a network device",
            "profile": "Get device profile and role information",
            "list": "List all available devices in the inventory",
            # Network group
            "routing": "Get routing protocol information (BGP, ISIS, OSPF)",
            "interface": "Get interface status and configuration",
            "mpls": "Get MPLS forwarding and label information",
            "vpn": "Get VPN/VRF configuration and status",
            # Topology group
            "neighbors": "Get direct neighbor information via LLDP/CDP",
            "adjacency": "Get complete topology adjacency information",
            # Operations group
            "logs": "Retrieve and filter device logs",
            "test-all": "Test all gNMI operations on a device",
            # Management group
            "list-commands": "List all available CLI commands",
            "log-level": "Configure logging levels dynamically",
        }

        self.group_descriptions = {
            "device": (
                "Device Information",
                "Commands for device management and information",
            ),
            "network": (
                "Network Protocols",
                "Commands for network protocol analysis",
            ),
            "topology": (
                "Network Topology",
                "Commands for topology discovery and analysis",
            ),
            "ops": (
                "Operations",
                "Commands for operational tasks and testing",
            ),
        }

        self.group_aliases = {
            "device": "d",
            "network": "n",
            "topology": "t",
            "ops": "o",
            "manage": "m",
        }

    def get_command_description(
        self, command_name: str, group_name: str
    ) -> str:
        """
        Get command description using duck typing with fallback.

        1. Try to get from command module (duck typing)
        2. Fall back to hardcoded description
        """
        # Try duck typing first
        description = HelpExampleProvider.get_command_description_from_module(
            command_name, group_name
        )

        if description:
            return description

        # Fall back to hardcoded descriptions
        return self.fallback_command_descriptions.get(command_name, "")

    def _build_commands_section(self) -> str:
        """Build the commands section with grouped commands."""
        commands_lines = []

        for group_name, group in COMMAND_GROUPS.items():
            group_title, group_desc = self.group_descriptions.get(
                group_name, (group_name.title(), "")
            )
            alias = self.group_aliases.get(group_name, "")

            # Format group header
            if alias:
                group_header = f"  {group_title}:\n    {group_name} ({alias})    {group_desc}"
            else:
                group_header = (
                    f"  {group_title}:\n    {group_name}      {group_desc}"
                )

            commands_lines.append(group_header)

            # Add commands in this group
            commands = self._get_commands_in_group(group)
            for cmd_name in sorted(commands):
                cmd_desc = self.get_command_description(cmd_name, group_name)
                commands_lines.append(f"      {cmd_name:<12} {cmd_desc}")

            commands_lines.append("")  # Empty line between groups

        return "\n".join(commands_lines)

    def _build_examples_section(self) -> str:
        """Build the examples section using duck typing from command modules."""
        sample_commands = [
            ("device", "info"),
            ("network", "routing"),
            ("topology", "neighbors"),
            ("ops", "logs"),
        ]

        example_lines = []

        for group_name, command_name in sample_commands:
            try:
                # Try to get basic examples from command module
                basic_examples = (
                    HelpExampleProvider.get_examples_from_command_module(
                        command_name, group_name, "basic"
                    )
                )

                if basic_examples:
                    # Extract first example line
                    first_line = basic_examples.split("\n")[0].strip()
                    if first_line and not first_line.startswith("#"):
                        example_lines.append(f"  {first_line}")
                else:
                    # Fallback to basic example
                    example_lines.append(
                        f"  uv run gnmibuddy.py {group_name} {command_name} --device R1"
                    )

            except Exception as e:
                logger.debug(
                    "Error getting examples for %s.%s: %s",
                    group_name,
                    command_name,
                    e,
                )
                example_lines.append(
                    f"  uv run gnmibuddy.py {group_name} {command_name} --device R1"
                )

        # Add some group alias examples
        example_lines.extend(
            [
                "  uv run gnmibuddy.py d info --device R1  # Using alias",
                "  uv run gnmibuddy.py n routing --device R1  # Using alias",
            ]
        )

        return "\n".join(example_lines)

    def format_grouped_help(self, show_examples: bool = False) -> str:
        """Format help output with commands grouped by category."""
        commands_section = self._build_commands_section()

        if show_examples:
            examples_content = self._build_examples_section()
            examples_section = EXAMPLES_SECTION_TEMPLATE.format(
                example_lines=examples_content
            )
        else:
            examples_section = ""

        return MAIN_HELP_TEMPLATE.format(
            commands_section=commands_section,
            examples_section=examples_section,
        ).strip()

    def _get_commands_in_group(self, group) -> List[str]:
        """Get list of command names in a Click group."""
        if hasattr(group, "commands"):
            return list(group.commands.keys())
        return []


def display_all_commands(detailed=False):
    """
    Display all available commands organized by groups

    Args:
        detailed: Whether to show detailed information including examples
    """
    formatter = GroupedHelpFormatter()
    help_output = formatter.format_grouped_help(show_examples=detailed)
    click.echo(help_output)


def display_group_help(group_name: str, group_commands: List[str]) -> str:
    """
    Display help for a specific command group

    Args:
        group_name: Name of the command group
        group_commands: List of commands in the group

    Returns:
        Formatted group help text
    """
    formatter = GroupedHelpFormatter()
    group_title, group_desc = formatter.group_descriptions.get(
        group_name, (group_name.title(), "")
    )
    alias = formatter.group_aliases.get(group_name, "")

    # Build alias usage line
    alias_usage = ""
    if alias:
        alias_usage = f"\n       uv run gnmibuddy.py {alias} [OPTIONS] COMMAND [ARGS]...  # Short alias"

    # Build commands list
    commands_list_lines = []
    for cmd_name in sorted(group_commands):
        cmd_desc = formatter.get_command_description(cmd_name, group_name)
        commands_list_lines.append(f"  {cmd_name:<12} {cmd_desc}")

    commands_list = "\n".join(commands_list_lines)

    return GROUP_HELP_TEMPLATE.format(
        group_name=group_name,
        alias_usage=alias_usage,
        group_description=group_desc,
        commands_list=commands_list,
    ).strip()
