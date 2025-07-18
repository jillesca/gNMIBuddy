#!/usr/bin/env python3
"""Click-based CLI parser for gNMIBuddy"""
import sys
import json
from typing import Optional, Dict, Any, Tuple
import click
from src.logging.config import get_logger
from src.cmd.context import CLIContext
from src.cmd.base import (
    command_registry,
    get_legacy_commands_dict,
    create_backward_compatible_args,
)
from src.inventory import initialize_inventory
from src.utils.version_utils import load_gnmibuddy_version
from src.cmd.cli_utils import display_program_banner, get_python_version

logger = get_logger(__name__)


def show_help_with_banner(ctx, param, value):
    """Custom help callback that shows banner only for main command"""
    if not value or ctx.resilient_parsing:
        return

    # Show banner only for main command help
    banner = display_program_banner()
    click.echo(banner)
    click.echo(ctx.get_help())
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
@click.option("--device", type=str, help="Device name from inventory")
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
    device,
    all_devices,
    max_workers,
    inventory,
):
    """gNMIBuddy CLI tool for network device management"""

    # If no command provided, show banner and help
    if ctx.invoked_subcommand is None:
        banner = display_program_banner()
        click.echo(banner)
        click.echo(ctx.get_help())
        return

    # Create CLI context for dependency injection
    cli_ctx = CLIContext(
        log_level=log_level,
        module_log_levels=module_log_levels,
        structured_logging=structured_logging,
        quiet_external=quiet_external,
        device=device,
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


# Legacy command integration for backward compatibility
def register_legacy_commands():
    """Register legacy commands as Click commands for backward compatibility"""
    try:
        legacy_commands = get_legacy_commands_dict()

        for cmd_name, legacy_cmd in legacy_commands.items():
            # Create a closure to capture the current command properly
            def create_command_wrapper(command_name, command_instance):
                @click.command(name=command_name, help=command_instance.help)
                @click.help_option("-h", "--help")
                @click.pass_context
                def legacy_command_wrapper(ctx, **kwargs):
                    """Wrapper for legacy commands"""
                    cli_ctx = ctx.obj

                    # Validate device options if needed
                    if not cli_ctx.validate_device_options(command_name):
                        click.echo(
                            f"Error: Device validation failed for command '{command_name}'",
                            err=True,
                        )
                        raise click.Abort()

                    try:
                        # Create backward-compatible args object
                        args = create_backward_compatible_args(
                            cli_ctx, **kwargs
                        )
                        args.command = command_name

                        # Execute legacy command
                        result = command_instance.execute(args)

                        # Store result for processing
                        cli_ctx._last_result = result

                        return result

                    except Exception as e:
                        logger.error(
                            "Error executing legacy command %s: %s",
                            command_name,
                            e,
                        )
                        click.echo(f"Error executing command: {e}", err=True)
                        raise click.Abort()

                # Add command-specific options based on legacy command configuration
                try:
                    # Create a temporary parser to extract options
                    import argparse

                    temp_parser = argparse.ArgumentParser()
                    command_instance.configure_parser(temp_parser)

                    # Convert argparse options to Click options
                    if hasattr(temp_parser, "_actions"):
                        for action in temp_parser._actions:
                            if action.dest == "help":
                                continue

                            option_names = action.option_strings
                            if not option_names:
                                continue

                                # Convert argparse action to Click option
                        click_kwargs = {"help": action.help or ""}

                        # Check the action class type instead of action.action
                        if action.__class__.__name__ == "_StoreTrueAction":
                            click_kwargs["is_flag"] = True
                        elif action.__class__.__name__ == "_StoreAction":
                            if action.type:
                                click_kwargs["type"] = action.type
                            if action.default is not None:
                                click_kwargs["default"] = action.default

                            # Apply the option to the command
                            option_decorator = click.option(
                                *option_names, **click_kwargs
                            )
                            legacy_command_wrapper = option_decorator(
                                legacy_command_wrapper
                            )

                except Exception as e:
                    logger.warning(
                        "Could not extract options from legacy command %s: %s",
                        command_name,
                        e,
                    )

                return legacy_command_wrapper

            # Create and register the wrapped command
            wrapped_command = create_command_wrapper(cmd_name, legacy_cmd)
            cli.add_command(wrapped_command)

    except Exception as e:
        logger.error("Error registering legacy commands: %s", e)


def run_cli_mode():
    """
    Run the CLI in Click mode

    Returns:
        Tuple of (result, parser_equivalent)
    """
    try:
        # Register legacy commands
        register_legacy_commands()

        # Invoke the CLI
        ctx = cli.make_context("gnmibuddy", sys.argv[1:])
        result = cli.invoke(ctx)

        # Get the result from the context if available
        cli_result = getattr(ctx.obj, "_last_result", None)

        return cli_result, ctx

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
    except SystemExit as e:
        if e.code != 0:
            click.echo(
                "Command line argument error. Use --help for usage information.",
                err=True,
            )
        return None, None
    except Exception as e:
        import traceback

        logger.error("Error in CLI mode: %s", e)
        logger.error("Traceback: %s", traceback.format_exc())
        click.echo(f"Unexpected error: {e}", err=True)
        return None, None


def execute_command(args):
    """
    Legacy compatibility function for execute_command

    Args:
        args: argparse-like namespace with command arguments

    Returns:
        Command result or None
    """
    # This function is kept for backward compatibility
    # In the new Click architecture, command execution is handled by Click
    logger.warning(
        "execute_command called in Click mode - this is for legacy compatibility only"
    )
    return None


# Legacy compatibility functions
def parse_args(args=None):
    """Legacy compatibility function for parse_args"""
    logger.warning(
        "parse_args called in Click mode - this is for legacy compatibility only"
    )

    # Create a mock args object for compatibility
    class MockArgs:
        def __init__(self):
            self.command = None
            self.device = None
            self.all_devices = False
            self.max_workers = 5
            self.log_level = "info"
            self.module_log_levels = None
            self.structured_logging = False
            self.inventory = None

    class MockParser:
        def print_help(self):
            from click.testing import CliRunner

            runner = CliRunner()
            result = runner.invoke(cli, ["--help"])
            print(result.output)

    return MockArgs(), MockParser()


def create_parser():
    """Legacy compatibility function for create_parser"""
    logger.warning(
        "create_parser called in Click mode - this is for legacy compatibility only"
    )

    # Create a mock args object for compatibility
    class MockArgs:
        def __init__(self):
            self.command = None
            self.device = None
            self.all_devices = False
            self.max_workers = 5
            self.log_level = "info"
            self.module_log_levels = None
            self.structured_logging = False
            self.inventory = None

    class MockParser:
        def print_help(self):
            from click.testing import CliRunner

            runner = CliRunner()
            result = runner.invoke(cli, ["--help"])
            print(result.output)

        def parse_args(self, args=None):
            return MockArgs(), self

    return MockParser()


if __name__ == "__main__":
    # For testing purposes
    cli.main(standalone_mode=True)
