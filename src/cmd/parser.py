#!/usr/bin/env python3
"""Main CLI parser and entry point with Click framework"""
import os
import sys
import click
from src.logging.config import get_logger
from src.cmd.cli_utils import display_program_banner
from src.cmd.context import CLIContext
from src.cmd.display import display_all_commands
from src.cmd.error_handler import handle_click_exception
from src.utils.version_utils import load_gnmibuddy_version, get_python_version
from src.cmd.templates.usage_templates import UsageTemplates
from src.cmd.registries.coordinator import coordinator

logger = get_logger(__name__)


def show_help_with_banner(ctx, param, value):
    """Show help with program banner"""
    if not value or ctx.resilient_parsing:
        return

    # Display banner first
    banner = display_program_banner()
    click.echo(banner)

    # Then display all commands grouped
    display_all_commands(detailed=False)

    ctx.exit()


def show_version_callback(ctx, param, value):
    """Show version information"""
    if not value or ctx.resilient_parsing:
        return

    version = load_gnmibuddy_version()
    python_version = get_python_version()
    click.echo(f"gNMIBuddy version: {version}")
    click.echo(f"Python version: {python_version}")
    ctx.exit()


def show_detailed_version_callback(ctx, param, value):
    """Show detailed version information"""
    if not value or ctx.resilient_parsing:
        return

    from src.cmd.version import get_version_info

    detailed_info = get_version_info(detailed=True)
    click.echo(detailed_info)
    ctx.exit()


@click.group(invoke_without_command=True)
@click.option(
    "-h",
    "--help",
    is_flag=True,
    expose_value=False,
    is_eager=True,
    callback=show_help_with_banner,
    help="Show this message and exit.",
)
@click.option(
    "-V",
    "--version",
    is_flag=True,
    expose_value=False,
    is_eager=True,
    callback=show_version_callback,
    help="Show version information and exit.",
)
@click.option(
    "--version-detailed",
    is_flag=True,
    expose_value=False,
    is_eager=True,
    callback=show_detailed_version_callback,
    help="Show detailed version information and exit.",
)
@click.option(
    "--log-level",
    type=click.Choice(
        ["debug", "info", "warning", "error"], case_sensitive=False
    ),
    default="info",
    help="Set the global logging level",
)
@click.option(
    "--module-log-levels",
    type=str,
    help="Set specific log levels for modules (format: module1=debug,module2=warning)",
)
@click.option(
    "--structured-logging", is_flag=True, help="Enable structured JSON logging"
)
@click.option(
    "--quiet-external",
    is_flag=True,
    default=True,
    help="Reduce noise from external libraries",
)
@click.option(
    "--all-devices",
    is_flag=True,
    help="Run command on all devices in inventory concurrently",
)
@click.option(
    "--max-workers",
    type=int,
    default=5,
    help="Maximum number of concurrent workers when using --all-devices",
)
@click.option("--inventory", type=str, help="Path to inventory JSON file")
@click.pass_context
def cli(
    ctx,
    log_level,
    module_log_levels,
    structured_logging,
    quiet_external,
    all_devices,
    max_workers,
    inventory,
):
    """gNMIBuddy - Essential network information using gNMI/OpenConfig

    \b
    A tool for retrieving essential network information from devices using gNMI and OpenConfig models.
    Designed primarily for LLMs with Model Context Protocol (MCP) integration, it also provides a full CLI.

    \b
    Examples:
      gnmibuddy device info --device R1
      gnmibuddy network routing --device R1
      gnmibuddy --all-devices ops logs
    """
    # Create and configure context
    ctx.ensure_object(CLIContext)
    ctx.obj = CLIContext(
        log_level=log_level,
        module_log_levels=module_log_levels,
        structured_logging=structured_logging,
        quiet_external=quiet_external,
        all_devices=all_devices,
        max_workers=max_workers,
        inventory=inventory,
    )

    # Set environment variable for inventory if provided
    if inventory:
        os.environ["NETWORK_INVENTORY"] = inventory

    # If no command provided, show help
    if ctx.invoked_subcommand is None:
        # Display banner and commands
        banner = display_program_banner()
        click.echo(banner)
        display_all_commands(detailed=False)


def register_commands():
    """Register all command groups and commands using the new registry system"""
    try:

        # Import all command modules to trigger auto-registration
        coordinator.import_all_command_modules()

        # Register all commands with their groups
        coordinator.register_all_commands_with_groups()

        # Register all groups with the main CLI
        coordinator.register_groups_with_cli(cli)

        # Log registration stats
        stats = coordinator.get_registration_stats()
        logger.info("Registration complete: %s", stats)

    except Exception as e:
        logger.error("Failed to register commands: %s", e)
        raise


def run_cli_mode():
    """
    Run the CLI mode with enhanced error handling

    Returns:
        Tuple of (result, ctx) or (None, None) if error occurred
    """
    # Register all commands
    register_commands()

    # Track execution context for better error reporting
    command_name = ""
    group_name = ""

    try:
        # Parse arguments to extract command context using registry
        if len(sys.argv) > 1:

            # Check if first argument is a group using the registry
            potential_group = sys.argv[1]
            if coordinator.is_valid_group_name_or_alias(potential_group):
                group_name = potential_group
                if len(sys.argv) > 2:
                    command_name = sys.argv[2]
            else:
                command_name = potential_group

        # Execute CLI
        result = cli.main(sys.argv[1:], standalone_mode=False)
        return result, cli

    except click.ClickException as e:
        # Enhanced error handling with context
        handle_click_exception(e, command_name, group_name)

        # Show help for the failing command if we have context
        if hasattr(e, "ctx") and getattr(e, "ctx", None):
            click.echo("\n" + "─" * 50, err=True)
            click.echo("Command Help:", err=True)
            click.echo("─" * 50, err=True)
            try:
                help_text = getattr(e, "ctx").get_help()
                click.echo(help_text, err=True)
            except Exception:
                # Fallback if we can't get help
                group_command = (
                    f"{group_name + ' ' if group_name else ''}{command_name}"
                )
                fallback_message = UsageTemplates.format_command_help_fallback(
                    group_command
                )
                click.echo(fallback_message, err=True)

        return None, None
    except click.Abort:
        # click.Abort() is used intentionally for user-facing errors, don't treat as unexpected
        return None, None
    except SystemExit as e:
        if e.code != 0:
            # For usage errors (exit code 2), try to show more helpful information
            if e.code == 2:
                click.echo(UsageTemplates.get_usage_error(), err=True)
            else:
                click.echo(UsageTemplates.get_cli_argument_error(), err=True)
        return None, None
    except FileNotFoundError as e:
        # Handle inventory-related errors gracefully
        error_msg = str(e)
        if "inventory file" in error_msg.lower():
            handle_inventory_error(error_msg)
        else:
            click.echo(f"File not found: {error_msg}", err=True)
        return None, None
    except Exception as e:
        # Provide more helpful error messages based on the exception type
        error_msg = str(e)

        # Handle common error patterns with user-friendly messages
        if "device" in error_msg.lower() and "not found" in error_msg.lower():
            logger.error("Device not found error: %s", e)
            click.echo(f"❌ Device Error: {error_msg}", err=True)
            click.echo(
                "\n💡 To see available devices, run: uv run gnmibuddy.py device list",
                err=True,
            )
        elif "inventory" in error_msg.lower():
            logger.error("Inventory error: %s", e)
            handle_inventory_error(error_msg)
        elif (
            "connection" in error_msg.lower() or "timeout" in error_msg.lower()
        ):
            logger.error("Connection error: %s", e)
            click.echo(f"❌ Connection Error: {error_msg}", err=True)
            click.echo(
                "\n💡 Check device connectivity and gNMI configuration",
                err=True,
            )
        elif (
            "permission" in error_msg.lower()
            or "unauthorized" in error_msg.lower()
        ):
            logger.error("Permission error: %s", e)
            click.echo(f"❌ Permission Error: {error_msg}", err=True)
            click.echo(
                "\n💡 Check device credentials and user permissions", err=True
            )
        else:
            # For truly unexpected errors, still log but provide better user message
            logger.error("Unexpected error in CLI: %s", e, exc_info=True)
            click.echo(f"❌ An unexpected error occurred.", err=True)
            click.echo(f"Details: {error_msg}", err=True)
            click.echo(
                "\n💡 For help, run: uv run gnmibuddy.py --help", err=True
            )
            click.echo("💡 Or check the logs for more details", err=True)
        return None, None


def handle_inventory_error(error_msg: str, show_help: bool = False):
    """
    Handle inventory-related errors with clear user guidance

    Args:
        error_msg: The original error message
        show_help: Whether to show help after the error message
    """
    # Use the centralized error handling
    from src.cmd.error_handling.click_integration import (
        handle_inventory_error as centralized_handler,
    )

    centralized_handler(error_msg, show_help)


if __name__ == "__main__":
    run_cli_mode()
