#!/usr/bin/env python3
"""Clean Click-based CLI parser for gNMIBuddy"""
import sys
from src.logging.config import get_logger
from src.cmd.context import CLIContext
from src.cmd.groups import COMMAND_GROUPS
from src.inventory import initialize_inventory
from src.utils.version_utils import load_gnmibuddy_version
from src.cmd.cli_utils import display_program_banner, get_python_version
import click

logger = get_logger(__name__)


def show_help_with_banner(ctx, param, value):
    """Custom help callback that shows banner only for main command"""
    if not value or ctx.resilient_parsing:
        return

    # Show banner only for main command help
    from src.cmd.display import GroupedHelpFormatter

    banner = display_program_banner()
    click.echo(banner)

    # Use our custom grouped help formatter
    formatter = GroupedHelpFormatter()
    grouped_help = formatter.format_grouped_help(show_examples=True)
    click.echo(grouped_help)
    ctx.exit()


def show_version_callback(ctx, param, value):
    """Custom version callback that shows simple version information"""
    if not value or ctx.resilient_parsing:
        return

    from src.cmd.version import get_version_info

    version_info = get_version_info(detailed=False)
    click.echo(version_info)
    ctx.exit()


def show_detailed_version_callback(ctx, param, value):
    """Custom version callback that shows detailed version information"""
    if not value or ctx.resilient_parsing:
        return

    from src.cmd.version import get_version_info

    version_info = get_version_info(detailed=True)
    click.echo(version_info)
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
    """gNMIBuddy CLI tool for network device management

    \b
    INVENTORY REQUIREMENT:
    You must provide device inventory via either:
    • --inventory PATH_TO_FILE.json
    • Set NETWORK_INVENTORY environment variable

    \b
    Examples:
      gnmibuddy --inventory devices.json device info --device R1
      export NETWORK_INVENTORY=./xrd_sandbox.json
      gnmibuddy device info --device xrd-1
    """

    # If no command provided, show banner and help
    if ctx.invoked_subcommand is None:
        from src.cmd.display import GroupedHelpFormatter

        banner = display_program_banner()
        click.echo(banner)

        # Use our custom grouped help formatter
        formatter = GroupedHelpFormatter()
        grouped_help = formatter.format_grouped_help(show_examples=True)
        click.echo(grouped_help)
        return

    # Create CLI context for dependency injection
    cli_ctx = CLIContext(
        log_level=log_level,
        module_log_levels=module_log_levels,
        structured_logging=structured_logging,
        quiet_external=quiet_external,
        device=None,  # Device is now handled at command level
        all_devices=all_devices,
        max_workers=max_workers,
        inventory=inventory,
    )

    # Store context in Click context object
    ctx.ensure_object(dict)
    ctx.obj = cli_ctx

    # Initialize inventory if specified
    if inventory:
        initialize_inventory(inventory)

    # Log version information
    gnmibuddy_version = load_gnmibuddy_version()
    logger.info("Python version: %s", get_python_version())
    logger.info("gNMIBuddy version: %s", gnmibuddy_version)


# Register command groups and commands
def register_commands():
    """Register all commands with their respective groups"""
    # Import commands
    from src.cmd.commands import (
        device_info,
        device_profile,
        device_list,
        network_routing,
        network_interface,
        network_mpls,
        network_vpn,
        topology_adjacency,
        topology_neighbors,
        ops_logs,
        ops_test_all,
        manage_list_commands,
        manage_log_level,
    )

    # Get command groups
    device_group = COMMAND_GROUPS["device"]
    network_group = COMMAND_GROUPS["network"]
    topology_group = COMMAND_GROUPS["topology"]
    ops_group = COMMAND_GROUPS["ops"]
    manage_group = COMMAND_GROUPS["manage"]

    # Register device commands
    device_group.add_command(device_info, name="info")
    device_group.add_command(device_profile, name="profile")
    device_group.add_command(device_list, name="list")

    # Register network commands
    network_group.add_command(network_routing, name="routing")
    network_group.add_command(network_interface, name="interface")
    network_group.add_command(network_mpls, name="mpls")
    network_group.add_command(network_vpn, name="vpn")

    # Register topology commands
    topology_group.add_command(topology_adjacency, name="adjacency")
    topology_group.add_command(topology_neighbors, name="neighbors")

    # Register ops commands
    ops_group.add_command(ops_logs, name="logs")
    ops_group.add_command(ops_test_all, name="test-all")

    # Register manage commands
    manage_group.add_command(manage_list_commands, name="list-commands")
    manage_group.add_command(manage_log_level, name="log-level")


# Add command groups to main CLI with aliases
group_aliases = {
    "device": "d",
    "network": "n",
    "topology": "t",
    "ops": "o",
    "manage": "m",
}

for group_name, group in COMMAND_GROUPS.items():
    # Add the main group name
    cli.add_command(group, name=group_name)

    # Add alias if available
    alias = group_aliases.get(group_name)
    if alias:
        cli.add_command(group, name=alias)

# Register all commands
register_commands()


def run_cli_mode():
    """
    Run the CLI in Click mode

    Returns:
        Tuple of (result, parser_equivalent)
    """
    try:
        # Invoke the CLI
        ctx = cli.make_context("gnmibuddy", sys.argv[1:])
        result = cli.invoke(ctx)

        # In Click, the result is returned directly from cli.invoke()
        # No need to get it from context._last_result
        return result, ctx

    except click.Abort:
        return None, None
    except click.exceptions.Exit as e:
        # Click uses Exit exceptions for normal exits (like --help)
        # Exit code 0 is success, anything else is an error
        if e.exit_code == 0:
            return None, None
        else:
            click.echo(
                f"Command failed with exit code: {e.exit_code}", err=True
            )
            return None, None
    except click.exceptions.UsageError as e:
        # Handle Click usage errors with enhanced error handling
        from src.cmd.error_handler import handle_click_exception

        # Extract command context information
        command_name = ""
        group_name = ""

        if hasattr(e, "ctx") and e.ctx:
            ctx = e.ctx
            # The command that failed is the current context
            command_name = ctx.info_name or ""
            # The group is the parent context
            if ctx.parent and ctx.parent.info_name != "gnmibuddy":
                group_name = ctx.parent.info_name or ""

        # For "No such command" errors, the command_name is actually the failing command,
        # and we need to extract the unknown command from the error message
        error_msg = str(e)
        if "No such command" in error_msg:
            import re

            match = re.search(r"No such command '([^']+)'", error_msg)
            if match:
                unknown_command = match.group(1)
                # In this case, group_name is actually the command_name from context
                actual_group = command_name
                actual_command = unknown_command
                command_name = actual_command
                group_name = actual_group

        # Use enhanced error handler
        handle_click_exception(e, command_name, group_name)

        # Show help for the failing command if we have context
        if hasattr(e, "ctx") and e.ctx:
            click.echo("\n" + "─" * 50, err=True)
            click.echo("Command Help:", err=True)
            click.echo("─" * 50, err=True)
            try:
                help_text = e.ctx.get_help()
                click.echo(help_text, err=True)
            except Exception:
                # Fallback if we can't get help
                click.echo(
                    f"Run 'gnmibuddy {group_name + ' ' if group_name else ''}{command_name} --help' for usage information.",
                    err=True,
                )

        return None, None
    except SystemExit as e:
        if e.code != 0:
            click.echo(
                "Command line argument error. Use --help for usage information.",
                err=True,
            )
        return None, None
    except FileNotFoundError as e:
        # Handle inventory-related errors gracefully
        error_msg = str(e)
        if "inventory file" in error_msg.lower():
            _handle_inventory_error(error_msg)
        else:
            click.echo(f"File not found: {error_msg}", err=True)
        return None, None
    except Exception as e:
        # Handle other exceptions but check for inventory-related issues first
        error_msg = str(e)
        if "inventory" in error_msg.lower() and (
            "not found" in error_msg.lower()
            or "not specified" in error_msg.lower()
        ):
            _handle_inventory_error(error_msg)
        else:
            import traceback

            logger.error("Error in CLI mode: %s", e)
            logger.error("Traceback: %s", traceback.format_exc())
            click.echo(f"Unexpected error: {e}", err=True)
        return None, None


def _handle_inventory_error(error_msg: str, show_help: bool = False):
    """
    Handle inventory-related errors with clear user guidance

    Args:
        error_msg: The original error message
        show_help: Whether to show help after the error message
    """
    click.echo("\n❌ Inventory Error", err=True)
    click.echo("═" * 50, err=True)

    click.echo("\nThe inventory file is required but not found.", err=True)
    click.echo("\n💡 How to fix this:", err=True)
    click.echo("  1. Use --inventory option:", err=True)
    click.echo(
        "     gnmibuddy --inventory path/to/your/devices.json device info --device R1",
        err=True,
    )
    click.echo("\n  2. Or set environment variable:", err=True)
    click.echo(
        "     export NETWORK_INVENTORY=path/to/your/devices.json", err=True
    )
    click.echo("     gnmibuddy device info --device R1", err=True)

    click.echo("\n📁 Example inventory files:", err=True)
    click.echo("  • xrd_sandbox.json (in project root)", err=True)
    click.echo("  • Any JSON file with device definitions", err=True)

    if show_help:
        click.echo("\n" + "═" * 50, err=True)
        click.echo("Command Help:", err=True)
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        click.echo(result.output, err=True)


if __name__ == "__main__":
    # For testing purposes
    cli.main(standalone_mode=True)
