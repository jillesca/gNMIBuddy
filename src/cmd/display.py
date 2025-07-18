#!/usr/bin/env python3
"""Enhanced display functions for CLI output and help system"""
from typing import Dict, List, Any, Optional
import click
from src.cmd.groups import COMMAND_GROUPS
from src.logging.config import get_logger

logger = get_logger(__name__)


class GroupedHelpFormatter:
    """Custom help formatter that groups commands by category"""

    def __init__(self):
        self.command_descriptions = {
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
            "manage": ("Management", "Commands for CLI and system management"),
        }

    def format_grouped_help(self, show_examples: bool = False) -> str:
        """Format help output with commands grouped by category"""
        help_text = []

        # Add usage section
        help_text.append("Usage: gnmibuddy [OPTIONS] COMMAND [ARGS]...")
        help_text.append("")
        help_text.append("Options:")
        help_text.append(
            "  -h, --help               Show this message and exit"
        )
        help_text.append("  --log-level [debug|info|warning|error]")
        help_text.append(
            "                           Set the global logging level"
        )
        help_text.append(
            "  --all-devices            Run command on all devices concurrently"
        )
        help_text.append(
            "  --inventory TEXT         Path to inventory JSON file"
        )
        help_text.append("")

        # Add grouped commands
        help_text.append("Commands:")
        help_text.append("")

        for group_name, group in COMMAND_GROUPS.items():
            group_title, group_desc = self.group_descriptions.get(
                group_name, (group_name.title(), "")
            )
            alias = self._get_group_alias(group_name)

            help_text.append(f"  {group_title}:")
            if alias:
                help_text.append(f"    {group_name} ({alias})    {group_desc}")
            else:
                help_text.append(f"    {group_name}      {group_desc}")

            # Add commands in this group
            commands = self._get_commands_in_group(group)
            for cmd_name in sorted(commands):
                cmd_desc = self.command_descriptions.get(cmd_name, "")
                help_text.append(f"      {cmd_name:<12} {cmd_desc}")

            help_text.append("")

        if show_examples:
            help_text.extend(self._get_usage_examples())

        help_text.append(
            "Run 'gnmibuddy COMMAND --help' for more information on a specific command."
        )
        help_text.append(
            "Run 'gnmibuddy GROUP --help' to see commands in a specific group."
        )
        help_text.append("")

        return "\n".join(help_text)

    def _get_group_alias(self, group_name: str) -> str:
        """Get the alias for a command group"""
        aliases = {
            "device": "d",
            "network": "n",
            "topology": "t",
            "ops": "o",
            "manage": "m",
        }
        return aliases.get(group_name, "")

    def _get_commands_in_group(self, group) -> List[str]:
        """Get list of command names in a Click group"""
        if hasattr(group, "commands"):
            return list(group.commands.keys())
        return []

    def _get_usage_examples(self) -> List[str]:
        """Get usage examples for the help system"""
        examples = [
            "",
            "Examples:",
            "  # Get system information from a device",
            "  gnmibuddy device info --device R1",
            "",
            "  # Get routing information with protocol filter",
            "  gnmibuddy network routing --device R1 --protocol bgp",
            "",
            "  # List all devices in inventory",
            "  gnmibuddy device list",
            "",
            "  # Get interface information for specific interface",
            "  gnmibuddy network interface --device R1 --name GigabitEthernet0/0/0/1",
            "",
            "  # Get topology neighbors",
            "  gnmibuddy topology neighbors --device R1",
            "",
            "  # Run on all devices concurrently",
            "  gnmibuddy --all-devices device info",
            "",
            "  # Use command aliases for shorter commands",
            "  gnmibuddy d info --device R1    # Same as 'device info'",
            "  gnmibuddy n routing --device R1 # Same as 'network routing'",
            "",
        ]
        return examples


def display_all_commands(detailed=False):
    """
    Display all available commands organized by groups

    Args:
        detailed: Whether to show detailed information including examples
    """
    formatter = GroupedHelpFormatter()
    help_output = formatter.format_grouped_help(show_examples=detailed)
    click.echo(help_output)


def format_command_help_with_examples(
    command_name: str, group_name: str, base_help: str
) -> str:
    """
    Format command help with usage examples

    Args:
        command_name: Name of the command
        group_name: Group the command belongs to
        base_help: Base help text from Click

    Returns:
        Enhanced help text with examples
    """
    examples_map = {
        # Device commands
        "info": [
            "Examples:",
            "  gnmibuddy device info --device R1",
            "  gnmibuddy device info --device PE1 --detail",
            "  gnmibuddy d info --device R1  # Using alias",
        ],
        "profile": [
            "Examples:",
            "  gnmibuddy device profile --device R1",
            "  gnmibuddy device profile --device PE1 --detail",
            "  gnmibuddy d profile --device R1  # Using alias",
        ],
        "list": [
            "Examples:",
            "  gnmibuddy device list",
            "  gnmibuddy device list --detail",
            "  gnmibuddy d list  # Using alias",
        ],
        # Network commands
        "routing": [
            "Examples:",
            "  gnmibuddy network routing --device R1",
            "  gnmibuddy network routing --device R1 --protocol bgp",
            "  gnmibuddy network routing --device R1 --detail",
            "  gnmibuddy n routing --device R1  # Using alias",
        ],
        "interface": [
            "Examples:",
            "  gnmibuddy network interface --device R1",
            "  gnmibuddy network interface --device R1 --name GigabitEthernet0/0/0/1",
            "  gnmibuddy network interface --device R1 --detail",
            "  gnmibuddy n interface --device R1  # Using alias",
        ],
        "mpls": [
            "Examples:",
            "  gnmibuddy network mpls --device R1",
            "  gnmibuddy network mpls --device R1 --detail",
            "  gnmibuddy n mpls --device R1  # Using alias",
        ],
        "vpn": [
            "Examples:",
            "  gnmibuddy network vpn --device R1",
            "  gnmibuddy network vpn --device R1 --detail",
            "  gnmibuddy n vpn --device R1  # Using alias",
        ],
        # Topology commands
        "neighbors": [
            "Examples:",
            "  gnmibuddy topology neighbors --device R1",
            "  gnmibuddy topology neighbors --device R1 --detail",
            "  gnmibuddy t neighbors --device R1  # Using alias",
        ],
        "adjacency": [
            "Examples:",
            "  gnmibuddy topology adjacency --device R1",
            "  gnmibuddy topology adjacency --device R1 --detail",
            "  gnmibuddy t adjacency --device R1  # Using alias",
        ],
        # Operations commands
        "logs": [
            "Examples:",
            "  gnmibuddy ops logs --device R1",
            "  gnmibuddy ops logs --device R1 --detail",
            "  gnmibuddy o logs --device R1  # Using alias",
        ],
        "test-all": [
            "Examples:",
            "  gnmibuddy ops test-all --device R1",
            "  gnmibuddy o test-all --device R1  # Using alias",
        ],
        # Management commands
        "list-commands": [
            "Examples:",
            "  gnmibuddy manage list-commands",
            "  gnmibuddy manage list-commands --detail",
            "  gnmibuddy m list-commands  # Using alias",
        ],
        "log-level": [
            "Examples:",
            "  gnmibuddy manage log-level",
            "  gnmibuddy m log-level  # Using alias",
        ],
    }

    examples = examples_map.get(command_name, [])
    if examples:
        return f"{base_help}\n\n" + "\n".join(examples) + "\n"
    return base_help


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
    alias = formatter._get_group_alias(group_name)

    help_text = []
    help_text.append(
        f"Usage: gnmibuddy {group_name} [OPTIONS] COMMAND [ARGS]..."
    )
    if alias:
        help_text.append(
            f"       gnmibuddy {alias} [OPTIONS] COMMAND [ARGS]...  # Short alias"
        )
    help_text.append("")
    help_text.append(f"{group_desc}")
    help_text.append("")
    help_text.append("Commands:")

    for cmd_name in sorted(group_commands):
        cmd_desc = formatter.command_descriptions.get(cmd_name, "")
        help_text.append(f"  {cmd_name:<12} {cmd_desc}")

    help_text.append("")
    help_text.append(
        f"Run 'gnmibuddy {group_name} COMMAND --help' for more information on a specific command."
    )

    return "\n".join(help_text)
