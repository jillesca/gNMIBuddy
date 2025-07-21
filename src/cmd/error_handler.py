#!/usr/bin/env python3
"""Enhanced error handling system for CLI with suggestions and context-aware messages"""
import difflib
import re
from typing import List, Optional
import click
from src.cmd.groups import COMMAND_GROUPS, get_error_provider
from src.logging.config import get_logger
from src.cmd.examples.example_builder import ExampleBuilder, ExampleSet

logger = get_logger(__name__)


# Error message templates - separated from logic for better readability
UNKNOWN_COMMAND_ROOT_TEMPLATE = """Error: Unknown command '{command}'

Did you mean one of these groups?
{suggestions}

Available command groups:
  device (d)    Device management commands
  network (n)   Network protocol commands
  topology (t)  Network topology commands
  ops (o)       Operational commands

Run 'gnmibuddy --help' to see all available commands."""

UNKNOWN_COMMAND_GROUP_TEMPLATE = """Error: Unknown command '{command}'

Did you mean one of these commands in '{context}'?
{suggestions}

Available commands in '{context}':
{group_commands}

Run 'gnmibuddy {context} --help' to see available commands in this group."""

MISSING_DEVICE_OPTION_TEMPLATE = """Error: Missing required option '{option}' for command '{command}'

The --device option specifies which device to query.
{examples}

To see available devices, run:
  uv run gnmibuddy.py device list"""

MISSING_INTERFACE_OPTION_TEMPLATE = """Error: Missing required option '{option}' for command '{command}'

The --name option specifies the interface name.
{examples}"""

MISSING_OPTION_GENERIC_TEMPLATE = """Error: Missing required option '{option}' for command '{command}'

Run 'uv run gnmibuddy.py ... {command} --help' for usage information."""

INVALID_CHOICE_TEMPLATE = """Error: Invalid value '{value}' for option '{option}'

Did you mean one of these?
{suggestions}

Valid choices for {option}:
  {choices}"""

DEVICE_NOT_FOUND_TEMPLATE = """Error: Device '{device}' not found in inventory

Did you mean one of these devices?
{suggestions}

Available devices:
{available_devices}"""

DEVICE_NOT_FOUND_NO_DEVICES_TEMPLATE = """Error: Device '{device}' not found in inventory

No devices found in inventory.
Check your inventory file or use --inventory to specify the path."""

UNEXPECTED_ARGUMENT_TEMPLATE = """❌ Command Error
═══════════════════════════════════════════════════════════

Unexpected argument: '{unexpected_arg}'

💡 How to fix this:
{fix_instructions}

📝 The device name must be specified with the --device flag.

📖 Examples:
{examples}"""

UNEXPECTED_ARGUMENT_DEVICE_INFO_FIX = """  Use: gnmibuddy device info --device {arg}
  Not: gnmibuddy device info {arg}"""

UNEXPECTED_ARGUMENT_NETWORK_ROUTING_FIX = """  Use: gnmibuddy network routing --device {arg}
  Not: gnmibuddy network routing {arg}"""

UNEXPECTED_ARGUMENT_NETWORK_INTERFACE_FIX = """  Use: gnmibuddy network interface --device {arg}
  Not: gnmibuddy network interface {arg}"""

UNEXPECTED_ARGUMENT_GENERIC_FIX = """  The command '{command}' doesn't accept positional arguments.
  Try using an option like --device {arg}"""

INVALID_OPTION_VALUE_TEMPLATE = """❌ Invalid Option Value
═══════════════════════════════════════════════════════════

Invalid value '{invalid_value}' for option '{option_name}'

💡 Run the command with --help to see valid options."""

COMMAND_NO_ARGUMENTS_TEMPLATE = """❌ Command Error
═══════════════════════════════════════════════════════════

The command '{command_name}' doesn't accept arguments.

💡 How to fix this:
  Use: gnmibuddy {full_command}

📖 If you need to specify options, use flags like --device, --output, etc."""


class CLIErrorHandler:
    """Enhanced error handling with suggestions and context-aware messages"""

    def __init__(self):
        # All available command names and aliases
        self.all_groups = list(COMMAND_GROUPS.keys()) + [
            "d",
            "n",
            "t",
            "o",
        ]
        self.all_commands = self._get_all_commands()
        self.group_aliases = {
            "d": "device",
            "n": "network",
            "t": "topology",
            "o": "ops",
        }

    def _get_all_commands(self) -> List[str]:
        """Get all available command names from all groups"""
        commands = []
        for group in COMMAND_GROUPS.values():
            if hasattr(group, "commands"):
                commands.extend(group.commands.keys())
        return commands

    def _get_examples_from_command_provider(
        self, command_name: str, group_name: str, error_type: str, **kwargs
    ) -> Optional[ExampleSet]:
        """
        Get examples from command-specific error provider using duck typing.

        This is the core of the duck typing pattern - we try to get an error
        provider for the specific command and ask it for examples.
        """
        provider = get_error_provider(group_name, command_name)

        if provider and hasattr(provider, "get_examples_for_error_type"):
            try:
                examples = provider.get_examples_for_error_type(
                    error_type, **kwargs
                )
                if examples and len(examples) > 0:
                    return examples
            except Exception as e:
                logger.debug(
                    "Error getting examples from provider %s.%s: %s",
                    group_name,
                    command_name,
                    e,
                )

        return None

    def _get_fallback_examples(self, error_type: str, **kwargs) -> ExampleSet:
        """
        Get fallback examples using ExampleBuilder when no command-specific provider exists.
        """
        if error_type == "missing_device":
            command = kwargs.get("command", "command")
            group = kwargs.get("group", "")
            return ExampleBuilder.missing_device_error_examples(command, group)

        elif error_type == "unexpected_argument":
            command = kwargs.get("command", "command")
            group = kwargs.get("group", "")
            return ExampleBuilder.unexpected_argument_error_examples(
                command, group
            )

        elif error_type == "device_not_found":
            device = kwargs.get("device", "R1")
            return ExampleBuilder.device_not_found_error_examples(device)

        elif error_type == "inventory_missing":
            return ExampleBuilder.inventory_missing_error_examples()

        elif error_type == "invalid_choice":
            option = kwargs.get("option", "--option")
            valid_choices = kwargs.get("valid_choices", [])
            command = kwargs.get("command", "command")
            return ExampleBuilder.invalid_choice_error_examples(
                option, valid_choices, command
            )

        # Return empty set for unknown error types
        return ExampleSet(f"unknown_{error_type}")

    def get_examples_for_error(
        self,
        error_type: str,
        command_name: str = "",
        group_name: str = "",
        **kwargs,
    ) -> str:
        """
        Get formatted examples for an error, trying command-specific providers first.

        This method implements the duck typing pattern:
        1. Try to get examples from command-specific error provider
        2. Fallback to generic examples using ExampleBuilder
        3. Final fallback to legacy system
        """
        examples = None

        # Try command-specific provider first (duck typing)
        if command_name and group_name:
            examples = self._get_examples_from_command_provider(
                command_name, group_name, error_type, **kwargs
            )

        # Fallback to generic ExampleBuilder
        if not examples:
            examples = self._get_fallback_examples(error_type, **kwargs)

        # Format examples for error display
        if examples and len(examples) > 0:
            return examples.for_error(prefix="  ")

        # Final fallback to empty string
        return ""

    def _format_suggestions_list(self, suggestions: List[str]) -> str:
        """Format a list of suggestions with proper indentation."""
        if not suggestions:
            return ""
        return "\n".join(f"  {suggestion}" for suggestion in suggestions[:3])

    def _format_commands_list(self, commands: List[str]) -> str:
        """Format a list of commands with proper indentation."""
        if not commands:
            return ""
        return "\n".join(f"  {cmd}" for cmd in sorted(commands))

    def _format_device_list(
        self, devices: List[str], max_devices: int = 10
    ) -> str:
        """Format a list of devices with proper indentation and truncation."""
        if not devices:
            return ""

        result_lines = []
        sorted_devices = sorted(devices)

        for device in sorted_devices[:max_devices]:
            result_lines.append(f"  {device}")

        if len(devices) > max_devices:
            result_lines.append(f"  ... and {len(devices) - max_devices} more")

        return "\n".join(result_lines)

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
        if context == "root":
            # Check if it's a group command
            suggestions = self._find_similar_items(command, self.all_groups)
            suggestions_text = self._format_suggestions_list(suggestions)

            return UNKNOWN_COMMAND_ROOT_TEMPLATE.format(
                command=command, suggestions=suggestions_text
            ).strip()
        else:
            # Context is a specific group - suggest commands in that group
            group_commands = self._get_group_commands(context)
            suggestions = self._find_similar_items(command, group_commands)

            suggestions_text = self._format_suggestions_list(suggestions)
            group_commands_text = self._format_commands_list(group_commands)

            return UNKNOWN_COMMAND_GROUP_TEMPLATE.format(
                command=command,
                context=context,
                suggestions=suggestions_text,
                group_commands=group_commands_text,
            ).strip()

    def handle_missing_option(self, command: str, option: str) -> str:
        """
        Handle missing required option with helpful suggestions

        Args:
            command: The command being executed
            option: The missing option

        Returns:
            Formatted error message with suggestions
        """
        if option == "--device":
            # Try to get examples from command-specific provider first
            examples_text = self.get_examples_for_error(
                error_type="missing_device",
                command_name=command.split()[-1] if command else "",
                group_name=(
                    command.split()[0] if len(command.split()) > 1 else ""
                ),
                command=command,
            )

            if not examples_text:
                examples_text = (
                    "Use: gnmibuddy <group> <command> --device <device_name>"
                )

            return MISSING_DEVICE_OPTION_TEMPLATE.format(
                option=option, command=command, examples=examples_text
            ).strip()

        elif option == "--name":
            # Try to get examples from command-specific provider
            examples_text = self.get_examples_for_error(
                error_type="missing_interface_name",
                command_name="interface",
                group_name="network",
            )

            # Fallback to static example if no provider examples
            if not examples_text:
                interface_examples = (
                    ExampleBuilder.missing_device_error_examples(
                        "interface", "network"
                    )
                )
                examples_text = interface_examples.for_error(prefix="  ")

            return MISSING_INTERFACE_OPTION_TEMPLATE.format(
                option=option, command=command, examples=examples_text
            ).strip()

        else:
            return MISSING_OPTION_GENERIC_TEMPLATE.format(
                option=option, command=command
            ).strip()

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
        # Find similar choices
        suggestions = self._find_similar_items(value, choices)
        suggestions_text = self._format_suggestions_list(suggestions)
        choices_text = ", ".join(choices)

        return INVALID_CHOICE_TEMPLATE.format(
            value=value,
            option=option,
            suggestions=suggestions_text,
            choices=choices_text,
        ).strip()

    def handle_device_not_found(self, device: str) -> str:
        """
        Handle device not found error with suggestions

        Args:
            device: The device name that was not found

        Returns:
            Formatted error message with suggestions
        """
        # Try to get available devices and suggest similar ones
        try:
            from src.inventory.manager import InventoryManager

            inventory = InventoryManager.get_instance()
            devices = list(inventory.get_devices().keys())

            if devices:
                suggestions = self._find_similar_items(device, devices)
                suggestions_text = self._format_suggestions_list(suggestions)
                available_devices_text = self._format_device_list(devices)

                return DEVICE_NOT_FOUND_TEMPLATE.format(
                    device=device,
                    suggestions=suggestions_text,
                    available_devices=available_devices_text,
                ).strip()
            else:
                return DEVICE_NOT_FOUND_NO_DEVICES_TEMPLATE.format(
                    device=device
                ).strip()

        except Exception as e:
            logger.debug("Could not access inventory for suggestions: %s", e)
            return f"Error: Device '{device}' not found in inventory\n\nRun 'gnmibuddy device list' to see available devices."

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
        # Get common mistake examples using ExampleBuilder
        common_examples = ExampleBuilder.missing_device_error_examples(
            "command", "group"
        )

        return [
            "Common mistakes and solutions:",
            "",
        ] + common_examples.to_list()


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
            match = re.search(
                r"Got unexpected extra argument \(([^)]+)\)", error_msg
            )
            if match:
                unexpected_arg = match.group(1)

                # Determine fix instructions based on command
                if command_name == "info" and group_name == "device":
                    fix_instructions = (
                        UNEXPECTED_ARGUMENT_DEVICE_INFO_FIX.format(
                            arg=unexpected_arg
                        )
                    )
                elif command_name == "routing" and group_name == "network":
                    fix_instructions = (
                        UNEXPECTED_ARGUMENT_NETWORK_ROUTING_FIX.format(
                            arg=unexpected_arg
                        )
                    )
                elif command_name == "interface" and group_name == "network":
                    fix_instructions = (
                        UNEXPECTED_ARGUMENT_NETWORK_INTERFACE_FIX.format(
                            arg=unexpected_arg
                        )
                    )
                else:
                    fix_instructions = UNEXPECTED_ARGUMENT_GENERIC_FIX.format(
                        command=command_name, arg=unexpected_arg
                    )

                # Get examples using the error handler
                if command_name == "info" and group_name == "device":
                    # Use new ExampleBuilder system
                    examples_text = error_handler.get_examples_for_error(
                        error_type="unexpected_argument",
                        command_name=command_name,
                        group_name=group_name,
                        command=command_name,
                    )

                    if not examples_text:
                        # Fallback to hardcoded examples
                        examples_text = """  uv run gnmibuddy.py device info --device R1
  uv run gnmibuddy.py device info --device PE1 --detail
  uv run gnmibuddy.py device info --all-devices"""

                elif command_name and group_name:
                    # Use new ExampleBuilder system for any command
                    examples_text = error_handler.get_examples_for_error(
                        error_type="unexpected_argument",
                        command_name=command_name,
                        group_name=group_name,
                        command=f"{group_name} {command_name}",
                    )

                    if not examples_text:
                        # Fallback to generic examples
                        examples_text = f"""  uv run gnmibuddy.py {group_name} {command_name} --device R1
  uv run gnmibuddy.py {group_name} {command_name} --all-devices"""
                else:
                    examples_text = (
                        "  uv run gnmibuddy.py <group> <command> --device R1"
                    )

                formatted_message = UNEXPECTED_ARGUMENT_TEMPLATE.format(
                    unexpected_arg=unexpected_arg,
                    fix_instructions=fix_instructions,
                    examples=examples_text,
                )

                click.echo(formatted_message, err=True)
                return

        elif "No such command" in error_msg or "Unknown command" in error_msg:
            # Extract the command name from the error
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

                formatted_message = INVALID_OPTION_VALUE_TEMPLATE.format(
                    invalid_value=invalid_value, option_name=option_name
                )

                click.echo(formatted_message, err=True)
                return

        elif "takes no arguments" in error_msg:
            full_command = (
                f"{group_name + ' ' if group_name else ''}{command_name}"
            )

            formatted_message = COMMAND_NO_ARGUMENTS_TEMPLATE.format(
                command_name=command_name, full_command=full_command
            )

            click.echo(formatted_message, err=True)
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
