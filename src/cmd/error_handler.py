#!/usr/bin/env python3
"""Enhanced error handling system for CLI with suggestions and context-aware messages"""
import difflib
from typing import List, Optional, Tuple
import click
from src.cmd.groups import COMMAND_GROUPS
from src.logging.config import get_logger

logger = get_logger(__name__)


class CLIErrorHandler:
    """Enhanced error handling with suggestions and context-aware messages"""

    def __init__(self):
        # All available command names and aliases
        self.all_groups = list(COMMAND_GROUPS.keys()) + [
            "d",
            "n",
            "t",
            "o",
            "m",
        ]
        self.all_commands = self._get_all_commands()
        self.group_aliases = {
            "d": "device",
            "n": "network",
            "t": "topology",
            "o": "ops",
            "m": "manage",
        }

    def _get_all_commands(self) -> List[str]:
        """Get all available command names from all groups"""
        commands = []
        for group in COMMAND_GROUPS.values():
            if hasattr(group, "commands"):
                commands.extend(group.commands.keys())
        return commands

    def handle_unknown_command(
        self, command: str, context: str = "root"
    ) -> str:
        """
        Handle unknown command with suggestions

        Args:
            command: The unknown command that was entered
            context: Context where the error occurred (root, group name, etc.)

        Returns:
            Formatted error message with suggestions
        """
        error_msg = [f"Error: Unknown command '{command}'"]

        if context == "root":
            # Check if it's a group command
            suggestions = self._find_similar_items(command, self.all_groups)
            if suggestions:
                error_msg.append(f"Did you mean one of these groups?")
                for suggestion in suggestions[:3]:  # Show top 3 suggestions
                    error_msg.append(f"  {suggestion}")

            # Provide helpful context
            error_msg.extend(
                [
                    "",
                    "Available command groups:",
                    "  device (d)    Device management commands",
                    "  network (n)   Network protocol commands",
                    "  topology (t)  Network topology commands",
                    "  ops (o)       Operational commands",
                    "  manage (m)    Management commands",
                    "",
                    "Run 'gnmibuddy --help' to see all available commands.",
                ]
            )
        else:
            # Context is a specific group - suggest commands in that group
            group_commands = self._get_group_commands(context)
            suggestions = self._find_similar_items(command, group_commands)

            if suggestions:
                error_msg.append(
                    f"Did you mean one of these commands in '{context}'?"
                )
                for suggestion in suggestions[:3]:
                    error_msg.append(f"  {suggestion}")

            # Always show available commands in the group
            if group_commands:
                error_msg.extend(
                    [
                        "",
                        f"Available commands in '{context}':",
                        *[f"  {cmd}" for cmd in sorted(group_commands)],
                    ]
                )

            error_msg.extend(
                [
                    "",
                    f"Run 'gnmibuddy {context} --help' to see available commands in this group.",
                ]
            )

        return "\n".join(error_msg)

    def handle_missing_option(self, command: str, option: str) -> str:
        """
        Handle missing required option with helpful suggestions

        Args:
            command: The command being executed
            option: The missing option

        Returns:
            Formatted error message with suggestions
        """
        error_msg = [
            f"Error: Missing required option '{option}' for command '{command}'"
        ]

        # Provide context-specific help
        if option == "--device":
            error_msg.extend(
                [
                    "",
                    "The --device option specifies which device to query.",
                    "Examples:",
                    f"  uv run gnmibuddy.py ... {command} --device R1",
                    f"  uv run gnmibuddy.py ... {command} --device PE1",
                    "",
                    "To see available devices, run:",
                    "  uv run gnmibuddy.py device list",
                ]
            )
        elif option == "--name":
            error_msg.extend(
                [
                    "",
                    "The --name option specifies the interface name.",
                    "Examples:",
                    f"  uv run gnmibuddy.py ... {command} --name GigabitEthernet0/0/0/1",
                    f"  uv run gnmibuddy.py ... {command} --name Loopback0",
                ]
            )
        else:
            error_msg.extend(
                [
                    "",
                    f"Run 'gnmibuddy ... {command} --help' for usage information.",
                ]
            )

        return "\n".join(error_msg)

    def handle_invalid_choice(
        self, option: str, value: str, choices: List[str]
    ) -> str:
        """
        Handle invalid option choice with suggestions

        Args:
            option: The option name
            value: The invalid value provided
            choices: List of valid choices

        Returns:
            Formatted error message with suggestions
        """
        error_msg = [f"Error: Invalid value '{value}' for option '{option}'"]

        # Find similar choices
        suggestions = self._find_similar_items(value, choices)
        if suggestions:
            error_msg.append("Did you mean one of these?")
            for suggestion in suggestions[:3]:
                error_msg.append(f"  {suggestion}")

        error_msg.extend(
            ["", f"Valid choices for {option}:", f"  {', '.join(choices)}"]
        )

        return "\n".join(error_msg)

    def handle_device_not_found(self, device: str) -> str:
        """
        Handle device not found error with suggestions

        Args:
            device: The device name that was not found

        Returns:
            Formatted error message with suggestions
        """
        error_msg = [f"Error: Device '{device}' not found in inventory"]

        # Try to get available devices and suggest similar ones
        try:
            from src.inventory.manager import InventoryManager

            inventory = InventoryManager.get_instance()
            devices = list(inventory.get_devices().keys())

            if devices:
                suggestions = self._find_similar_items(device, devices)
                if suggestions:
                    error_msg.append("Did you mean one of these devices?")
                    for suggestion in suggestions[:3]:
                        error_msg.append(f"  {suggestion}")

                error_msg.extend(
                    [
                        "",
                        "Available devices:",
                        *[
                            f"  {dev}" for dev in sorted(devices)[:10]
                        ],  # Show first 10
                    ]
                )

                if len(devices) > 10:
                    error_msg.append(f"  ... and {len(devices) - 10} more")
            else:
                error_msg.extend(
                    [
                        "",
                        "No devices found in inventory.",
                        "Check your inventory file or use --inventory to specify the path.",
                    ]
                )
        except Exception as e:
            logger.debug("Could not access inventory for suggestions: %s", e)
            error_msg.extend(
                ["", "Run 'gnmibuddy device list' to see available devices."]
            )

        return "\n".join(error_msg)

    def _find_similar_items(
        self, target: str, candidates: List[str], cutoff: float = 0.6
    ) -> List[str]:
        """
        Find similar items using fuzzy string matching

        Args:
            target: The string to find matches for
            candidates: List of candidate strings
            cutoff: Similarity threshold (0.0 to 1.0)

        Returns:
            List of similar strings, sorted by similarity
        """
        if not candidates:
            return []

        # Use difflib to find close matches
        matches = difflib.get_close_matches(
            target, candidates, n=5, cutoff=cutoff  # Return top 5 matches
        )

        return matches

    def _get_group_commands(self, group_name: str) -> List[str]:
        """
        Get commands available in a specific group

        Args:
            group_name: Name of the command group

        Returns:
            List of command names in the group
        """
        # Resolve alias to full name if needed
        group_name = self.group_aliases.get(group_name, group_name)

        # Hard-coded mapping for known groups (more reliable)
        group_commands = {
            "device": ["info", "profile", "list"],
            "network": ["routing", "interface", "mpls", "vpn"],
            "topology": ["neighbors", "adjacency"],
            "ops": ["logs", "test-all"],
            "manage": ["list-commands", "log-level"],
        }

        return group_commands.get(group_name, [])

    def get_common_mistake_suggestions(self) -> List[str]:
        """Get suggestions for common CLI mistakes"""
        return [
            "Common mistakes and solutions:",
            "",
            "1. Forgot to specify device:",
            "   uv run gnmibuddy.py network routing --device R1",
            "",
            "2. Using old flat command structure:",
            "   Old: gnmibuddy routing --device R1",
            "   New: gnmibuddy network routing --device R1",
            "",
            "3. Trying to use a command that doesn't exist:",
            "   Run 'gnmibuddy --help' to see all available commands",
            "",
            "4. Device not found:",
            "   Run 'gnmibuddy device list' to see available devices",
            "",
            "5. Want to see what's available:",
            "   uv run gnmibuddy.py --help              # All commands",
            "   uv run gnmibuddy.py device --help       # Device commands",
            "   uv run gnmibuddy.py network --help      # Network commands",
        ]


# Global error handler instance
error_handler = CLIErrorHandler()


def handle_click_exception(
    exception: click.ClickException,
    command_name: str = "",
    group_name: str = "",
) -> None:
    """
    Enhanced Click exception handler with context-aware suggestions

    Args:
        exception: The Click exception that was raised
        command_name: Name of the command that failed (if known)
        group_name: Name of the group context (if known)
    """
    if isinstance(exception, click.UsageError):
        # Handle usage errors with better messaging
        error_msg = str(exception)

        # Debug: Print what we're actually getting
        logger.debug(f"Handling Click error: {error_msg}")
        logger.debug(f"Command: {command_name}, Group: {group_name}")

        # Check for common patterns and enhance the message
        if "Got unexpected extra argument" in error_msg:
            # Extract the unexpected argument
            import re

            match = re.search(
                r"Got unexpected extra argument \(([^)]+)\)", error_msg
            )
            if match:
                unexpected_arg = match.group(1)
                click.echo("\n❌ Command Error", err=True)
                click.echo("═" * 50, err=True)
                click.echo(
                    f"\nUnexpected argument: '{unexpected_arg}'", err=True
                )

                # Provide specific guidance
                if command_name == "info" and group_name == "device":
                    click.echo("\n💡 How to fix this:", err=True)
                    click.echo(
                        f"  Use: gnmibuddy device info --device {unexpected_arg}",
                        err=True,
                    )
                    click.echo(
                        f"  Not: gnmibuddy device info {unexpected_arg}",
                        err=True,
                    )
                    click.echo(
                        "\n📝 The device name must be specified with the --device flag.",
                        err=True,
                    )

                elif command_name == "routing" and group_name == "network":
                    click.echo("\n💡 How to fix this:", err=True)
                    click.echo(
                        f"  Use: gnmibuddy network routing --device {unexpected_arg}",
                        err=True,
                    )
                    click.echo(
                        f"  Not: gnmibuddy network routing {unexpected_arg}",
                        err=True,
                    )

                elif command_name == "interface" and group_name == "network":
                    click.echo("\n💡 How to fix this:", err=True)
                    click.echo(
                        f"  Use: gnmibuddy network interface --device {unexpected_arg}",
                        err=True,
                    )
                    click.echo(
                        f"  Not: gnmibuddy network interface {unexpected_arg}",
                        err=True,
                    )

                else:
                    click.echo("\n💡 How to fix this:", err=True)
                    click.echo(
                        f"  The command '{command_name}' doesn't accept positional arguments.",
                        err=True,
                    )
                    click.echo(
                        f"  Try using an option like --device {unexpected_arg}",
                        err=True,
                    )

                click.echo("\n📖 Examples:", err=True)
                if command_name == "info" and group_name == "device":
                    click.echo(
                        "  uv run gnmibuddy.py device info --device R1",
                        err=True,
                    )
                    click.echo(
                        "  uv run gnmibuddy.py device info --device PE1 --detail",
                        err=True,
                    )
                    click.echo(
                        "  uv run gnmibuddy.py device info --all-devices",
                        err=True,
                    )
                elif command_name and group_name:
                    click.echo(
                        f"  uv run gnmibuddy.py {group_name} {command_name} --device R1",
                        err=True,
                    )
                    click.echo(
                        f"  uv run gnmibuddy.py {group_name} {command_name} --all-devices",
                        err=True,
                    )

                return

        elif "No such command" in error_msg or "Unknown command" in error_msg:
            # Extract the command name from the error
            import re

            # Try multiple patterns
            patterns = [
                r"No such command '([^']+)'",
                r"Unknown command '([^']+)'",
                r"No such command \"([^\"]+)\"",
                r"Unknown command \"([^\"]+)\"",
            ]

            bad_command = None
            for pattern in patterns:
                match = re.search(pattern, error_msg)
                if match:
                    bad_command = match.group(1)
                    break

            if bad_command:
                # Use the group_name from parameters, not from error message
                enhanced_msg = error_handler.handle_unknown_command(
                    bad_command, group_name or "root"
                )
                click.echo(enhanced_msg, err=True)
                return
            else:
                # Fallback - try to parse group from context
                click.echo(f"\n❌ Unknown Command", err=True)
                click.echo("═" * 50, err=True)
                click.echo(f"\n{error_msg}", err=True)

                if group_name:
                    click.echo(
                        f"\n💡 Run 'gnmibuddy {group_name} --help' to see available commands.",
                        err=True,
                    )
                else:
                    click.echo(
                        f"\n💡 Run 'gnmibuddy --help' to see available commands.",
                        err=True,
                    )
                return

        elif "Missing option" in error_msg:
            # Handle missing required options
            match = re.search(r"Missing option '([^']+)'", error_msg)
            if match:
                missing_option = match.group(1)
                enhanced_msg = error_handler.handle_missing_option(
                    command_name, missing_option
                )
                click.echo(enhanced_msg, err=True)
                return

        elif "Invalid value" in error_msg:
            # Handle invalid choices
            match = re.search(
                r"Invalid value for '([^']+)': invalid choice: ([^.]+)",
                error_msg,
            )
            if match:
                option_name = match.group(1)
                invalid_value = match.group(2).strip()
                click.echo(f"\n❌ Invalid Option Value", err=True)
                click.echo("═" * 50, err=True)
                click.echo(
                    f"\nInvalid value '{invalid_value}' for option '{option_name}'",
                    err=True,
                )
                click.echo(
                    "\n💡 Run the command with --help to see valid options.",
                    err=True,
                )
                return

        elif "takes no arguments" in error_msg:
            click.echo("\n❌ Command Error", err=True)
            click.echo("═" * 50, err=True)
            click.echo(
                f"\nThe command '{command_name}' doesn't accept arguments.",
                err=True,
            )
            click.echo("\n💡 How to fix this:", err=True)
            click.echo(
                f"  Use: gnmibuddy {group_name + ' ' if group_name else ''}{command_name}",
                err=True,
            )
            click.echo(
                "\n📖 If you need to specify options, use flags like --device, --output, etc.",
                err=True,
            )
            return

    # Fallback to original error message but make it cleaner
    click.echo(f"\n❌ Error: {exception}", err=True)


def suggest_command_from_typo(typo: str) -> Optional[str]:
    """
    Suggest a command based on a typo

    Args:
        typo: The mistyped command

    Returns:
        Suggested command or None if no good match found
    """
    all_items = error_handler.all_groups + error_handler.all_commands
    suggestions = error_handler._find_similar_items(
        typo, all_items, cutoff=0.7
    )
    return suggestions[0] if suggestions else None
