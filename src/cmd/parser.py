#!/usr/bin/env python3
"""Main CLI parser and entry point with Click framework"""
import os
import sys
from typing import Optional
import click
from src.logging.config import get_logger, LoggingConfig
from src.cmd.cli_utils import display_program_banner
from src.cmd.context import CLIContext
from src.cmd.display import display_all_commands
from src.cmd.error_handler import handle_click_exception
from src.utils.version_utils import load_gnmibuddy_version, get_python_version
from src.cmd.templates.usage_templates import UsageTemplates
from src.cmd.registries.coordinator import coordinator
from src.cmd.module_log_help import (
    show_module_log_help_callback,
    validate_module_log_levels,
)

logger = get_logger(__name__)


def build_complete_help_output(ctx):
    """Build the complete unified help output with enhanced formatting"""
    from src.cmd.display import GroupedHelpFormatter

    # Get the banner
    banner = display_program_banner()

    # Clean, concise help template following Docker/kubectl style
    ENHANCED_HELP_TEMPLATE = """
Usage: 
  gnmibuddy.py [OPTIONS] COMMAND [ARGS]...

📋 Inventory Requirement:
  Provide device inventory via --inventory PATH or set NETWORK_INVENTORY env var

Options:
{options_section}

Commands:
{commands_section}

Examples:
{examples_section}

Run 'gnmibuddy.py COMMAND --help' for more information on a command.
"""

    # Simplified options section
    options_lines = []
    options_lines.append(
        "  -h, --help                      Show this message and exit"
    )
    options_lines.append(
        "  -V, --version                   Show version information"
    )
    options_lines.append(
        "  --log-level LEVEL               Set logging level (debug, info, warning, error)"
    )
    options_lines.append(
        "  --module-log-help               Show detailed module logging help"
    )
    options_lines.append(
        "  --all-devices                   Run on all devices concurrently"
    )
    options_lines.append(
        "  --inventory PATH                Path to inventory JSON file"
    )
    options_section = "\n".join(options_lines)

    # Get simplified commands section from formatter
    formatter = GroupedHelpFormatter()
    commands_section_content = formatter._build_simple_commands_section()
    commands_section = commands_section_content

    # Minimal essential examples
    examples_lines = []
    examples_lines.append("  gnmibuddy.py device info --device R1")
    examples_lines.append("  gnmibuddy.py network routing --device R1")
    examples_lines.append("  gnmibuddy.py --all-devices device list")
    examples_section = "\n".join(examples_lines)

    # Apply to template
    complete_output = ENHANCED_HELP_TEMPLATE.format(
        options_section=options_section,
        commands_section=commands_section,
        examples_section=examples_section,
    ).strip()

    return f"{banner}\n{complete_output}"


def show_help_with_banner(ctx, param, value):
    """Show help with program banner and complete unified output"""
    if not value or ctx.resilient_parsing:
        return

    # Build the complete unified help output
    help_output = build_complete_help_output(ctx)
    click.echo(help_output)

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
    "--module-log-help",
    is_flag=True,
    expose_value=False,
    is_eager=True,
    callback=lambda ctx, param, value: show_module_log_help_callback(
        ctx, param, value
    ),
    help="Show detailed help for module-specific logging options and exit.",
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
    """placeholder"""
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

    # Configure logging system using CLI options
    configure_logging_from_cli_options(
        log_level=log_level,
        module_log_levels=module_log_levels,
        structured_logging=structured_logging,
        quiet_external=quiet_external,
    )

    # Set environment variable for inventory if provided
    if inventory:
        os.environ["NETWORK_INVENTORY"] = inventory

    # If no command provided, show help
    if ctx.invoked_subcommand is None:
        # Display complete unified help output
        help_output = build_complete_help_output(ctx)
        click.echo(help_output)


def configure_logging_from_cli_options(
    log_level: str,
    module_log_levels: Optional[str] = None,
    structured_logging: bool = False,
    quiet_external: bool = True,
):
    """
    Configure the logging system using CLI options.

    Args:
        log_level: Global logging level from CLI
        module_log_levels: Module-specific levels string (format: module1=level1,module2=level2)
        structured_logging: Whether to enable structured JSON logging
        quiet_external: Whether to reduce external library noise
    """
    # Parse module-specific log levels from string format
    parsed_module_levels = {}
    if module_log_levels:
        # Validate format first
        is_valid, error_msg = validate_module_log_levels(module_log_levels)
        if not is_valid:
            print(
                f"❌ Invalid module log levels: {error_msg}", file=sys.stderr
            )
            print(
                "💡 Use --module-log-help to see available modules and examples",
                file=sys.stderr,
            )
            sys.exit(1)

        try:
            pairs = module_log_levels.split(",")
            for pair in pairs:
                if "=" in pair:
                    module, level = pair.strip().split("=", 1)
                    parsed_module_levels[module.strip()] = level.strip()
        except Exception as e:
            # Log parsing error but continue with defaults
            print(
                f"Warning: Failed to parse module log levels '{module_log_levels}': {e}",
                file=sys.stderr,
            )

    # Add external library settings if quiet_external is enabled
    if quiet_external:
        parsed_module_levels.setdefault("pygnmi", "warning")
        parsed_module_levels.setdefault("grpc", "error")
        parsed_module_levels.setdefault("urllib3", "warning")
        parsed_module_levels.setdefault("asyncio", "warning")

    # Configure the logging system
    try:
        LoggingConfig.configure(
            global_level=log_level,
            module_levels=parsed_module_levels,
            enable_structured=structured_logging,
            enable_file_output=True,  # Always enable file output
        )

        # Log the successful configuration
        app_logger = get_logger(__name__)
        app_logger.debug(
            "Logging configured from CLI options",
            extra={
                "global_level": log_level,
                "module_levels": parsed_module_levels,
                "structured": structured_logging,
                "quiet_external": quiet_external,
            },
        )

    except Exception as e:
        # If logging configuration fails, show error and continue
        print(f"Warning: Failed to configure logging: {e}", file=sys.stderr)
        print(
            "Continuing with default logging configuration.", file=sys.stderr
        )


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
