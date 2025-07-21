#!/usr/bin/env python3
"""Main CLI parser and entry point with Click framework"""
import click
import os
import sys
from src.logging.config import get_logger, LoggingConfig
from src.cmd.cli_utils import display_program_banner
from src.cmd.context import CLIContext
from src.cmd.display import display_all_commands
from src.cmd.error_handler import handle_click_exception
from src.utils.version_utils import load_gnmibuddy_version, get_python_version
from click.testing import CliRunner

logger = get_logger(__name__)


# Help and error message templates - separated from logic for better readability
INVENTORY_ERROR_TEMPLATE = """❌ Inventory Error
═══════════════════════════════════════════════════════════

The inventory file is required but not found.

💡 How to fix this:
  1. Use --inventory option:
     {inventory_example}

  2. Or set environment variable:
     export NETWORK_INVENTORY=path/to/your/devices.json
     {env_example}

📁 Example inventory files:
  • xrd_sandbox.json (in project root)
  • Any JSON file with device definitions"""

COMMAND_HELP_FALLBACK_TEMPLATE = """Run 'uv run gnmibuddy.py {group_command} --help' for usage information."""

USAGE_ERROR_TEMPLATE = """Error: Invalid option or argument.
Use --help for detailed usage information."""

CLI_ARGUMENT_ERROR_TEMPLATE = (
    """Command line argument error. Use --help for usage information."""
)


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
    """Register all command groups and commands"""
    try:
        # Import all command groups
        from src.cmd.groups import (
            device,
            network,
            topology,
            ops,
        )

        # Add command groups to main CLI
        cli.add_command(device, "device")
        cli.add_command(device, "d")  # Alias

        cli.add_command(network, "network")
        cli.add_command(network, "n")  # Alias

        cli.add_command(topology, "topology")
        cli.add_command(topology, "t")  # Alias

        cli.add_command(ops, "ops")
        cli.add_command(ops, "o")  # Alias

        # Import and call the actual register_commands function from groups
        from src.cmd.groups import register_commands as register_group_commands

        register_group_commands()

        logger.debug("Successfully registered all commands and groups")

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
        # Parse arguments to extract command context
        if len(sys.argv) > 1:
            # Check if first argument is a group
            potential_group = sys.argv[1]
            if potential_group in [
                "device",
                "d",
                "network",
                "n",
                "topology",
                "t",
                "ops",
                "o",
            ]:
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
                fallback_message = COMMAND_HELP_FALLBACK_TEMPLATE.format(
                    group_command=group_command
                )
                click.echo(fallback_message, err=True)

        return None, None
    except SystemExit as e:
        if e.code != 0:
            # For usage errors (exit code 2), try to show more helpful information
            if e.code == 2:
                click.echo(USAGE_ERROR_TEMPLATE, err=True)
            else:
                click.echo(CLI_ARGUMENT_ERROR_TEMPLATE, err=True)
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
        logger.error("Unexpected error in CLI: %s", e)
        click.echo(f"Unexpected error: {e}", err=True)
        return None, None


def handle_inventory_error(error_msg: str, show_help: bool = False):
    """
    Handle inventory-related errors with clear user guidance

    Args:
        error_msg: The original error message
        show_help: Whether to show help after the error message
    """
    # Build example commands
    inventory_example = "uv run gnmibuddy.py --inventory path/to/your/devices.json device info --device R1"
    env_example = "uv run gnmibuddy.py device info --device R1"

    formatted_message = INVENTORY_ERROR_TEMPLATE.format(
        inventory_example=inventory_example, env_example=env_example
    )

    click.echo(formatted_message, err=True)

    if show_help:
        click.echo("\n" + "═" * 50, err=True)
        click.echo("Command Help:", err=True)
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        click.echo(result.output, err=True)


if __name__ == "__main__":
    run_cli_mode()
