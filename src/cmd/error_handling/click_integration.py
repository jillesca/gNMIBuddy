#!/usr/bin/env python3
"""Click exception handling integration"""

import click
from typing import Optional
from src.cmd.schemas import CommandGroup
from src.cmd.templates.usage_templates import UsageTemplates
from src.cmd.error_handling.handlers import CLIErrorHandler
from src.logging.config import get_logger

logger = get_logger(__name__)


def handle_click_exception(
    exception: click.ClickException,
    command_name: str = "",
    group_name: str = "",
) -> None:
    """Handle Click exceptions with enhanced error messages

    Args:
        exception: The Click exception that was raised
        command_name: Name of the command (if known)
        group_name: Name of the group (if known)
    """
    error_handler = CLIErrorHandler()
    error_msg = str(exception.message)

    # Handle different types of Click exceptions
    if isinstance(exception, click.NoSuchOption):
        # Unknown option
        click.echo(f"Error: {error_msg}", err=True)

    elif isinstance(exception, click.MissingParameter):
        # Missing required parameter
        if "--device" in error_msg:
            _handle_missing_option_error("--device", command_name, group_name)
        else:
            _handle_missing_option_error(error_msg, command_name, group_name)

    elif isinstance(exception, click.BadParameter):
        # Bad parameter value
        if "Invalid value" in error_msg:
            _handle_invalid_value_error(error_msg)
        else:
            click.echo(f"Error: {error_msg}", err=True)

    elif isinstance(exception, click.UsageError):
        # Generic usage error
        if "Got unexpected extra argument" in error_msg:
            # Extract the unexpected argument
            parts = error_msg.split("(")
            if len(parts) > 1:
                unexpected_arg = parts[1].rstrip(")")
                _handle_unexpected_argument_error(
                    unexpected_arg, command_name, group_name
                )
            else:
                click.echo(f"Error: {error_msg}", err=True)
        elif "No such command" in error_msg:
            # Extract command name
            parts = error_msg.split("'")
            if len(parts) >= 2:
                unknown_command = parts[1]
                _handle_unknown_command_error(unknown_command, group_name)
            else:
                click.echo(f"Error: {error_msg}", err=True)
        elif error_msg.strip() == "":
            _handle_no_arguments_error(command_name, group_name)
        else:
            click.echo(f"Error: {error_msg}", err=True)
    else:
        # Generic Click exception
        click.echo(f"Error: {error_msg}", err=True)


def _handle_unexpected_argument_error(
    unexpected_arg: str, command_name: str, group_name: str
) -> None:
    """Handle unexpected argument errors"""
    error_handler = CLIErrorHandler()

    error_message = error_handler.handle_unexpected_argument(
        unexpected_arg=unexpected_arg,
        command_name=command_name,
        group_name=group_name,
    )

    click.echo(error_message, err=True)


def _handle_unknown_command_error(error_msg: str, group_name: str) -> None:
    """Handle unknown command errors with suggestions"""
    error_handler = CLIErrorHandler()

    # Extract command name from error message
    if "No such command" in error_msg and "'" in error_msg:
        parts = error_msg.split("'")
        if len(parts) >= 2:
            unknown_command = parts[1]
        else:
            unknown_command = ""
    else:
        unknown_command = error_msg

    if group_name:
        # Unknown command in a specific group
        context = group_name
    else:
        # Unknown command at root level
        context = "root"

    error_message = error_handler.handle_unknown_command(
        command=unknown_command, context=context
    )

    click.echo(error_message, err=True)


def _handle_missing_option_error(
    option: str, command_name: str, group_name: str
) -> None:
    """Handle missing required option errors"""
    error_handler = CLIErrorHandler()

    # Clean up the option name
    if "Missing option" in option:
        # Extract option from message like "Missing option '--device'"
        parts = option.split("'")
        if len(parts) >= 2:
            clean_option = parts[1]
        else:
            clean_option = option
    else:
        clean_option = option

    error_message = error_handler.handle_missing_option(
        command=command_name,
        option=clean_option,
        group_name=group_name,
    )

    click.echo(error_message, err=True)


def _handle_invalid_value_error(error_msg: str) -> None:
    """Handle invalid parameter value errors"""
    # Basic handling for now - could be enhanced
    click.echo(f"Error: {error_msg}", err=True)
    click.echo("Use --help to see valid options.", err=True)


def _handle_no_arguments_error(command_name: str, group_name: str) -> None:
    """Handle cases where no arguments are provided"""
    if group_name:
        help_command = f"uv run gnmibuddy.py {group_name} --help"
    else:
        help_command = "uv run gnmibuddy.py --help"

    click.echo("Error: No command specified.", err=True)
    click.echo(f"Run '{help_command}' to see available options.", err=True)


def suggest_command_from_typo(typo: str) -> Optional[str]:
    """Suggest a command based on a potential typo

    Args:
        typo: The potentially misspelled command

    Returns:
        Suggested command or None if no good match
    """
    error_handler = CLIErrorHandler()

    # Get all valid group names and aliases
    all_items = CommandGroup.get_all_names_and_aliases()

    # Find similar items
    suggestions = error_handler._find_similar_items(typo, all_items)

    return suggestions[0] if suggestions else None


def handle_inventory_error(error_msg: str, show_help: bool = False):
    """
    Handle inventory-related errors with clear user guidance

    Args:
        error_msg: The original error message
        show_help: Whether to show help after the error message
    """
    from src.cmd.templates.usage_templates import InventoryUsageData

    # Build example commands
    inventory_example = "uv run gnmibuddy.py --inventory path/to/your/devices.json device info --device R1"
    env_example = "uv run gnmibuddy.py device info --device R1"

    data = InventoryUsageData(
        inventory_example=inventory_example, env_example=env_example
    )

    formatted_message = UsageTemplates.format_inventory_error(data)
    click.echo(formatted_message, err=True)

    if show_help:
        click.echo("\n" + "═" * 50, err=True)
        click.echo("Command Help:", err=True)
        from click.testing import CliRunner
        from src.cmd.parser import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        click.echo(result.output, err=True)
