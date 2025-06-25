#!/usr/bin/env python3
"""Main CLI argument parser for network tools application"""
import argparse
import sys
from typing import Optional, Tuple, Dict, Any

from src.utils.logging_config import get_logger, configure_logging
from src.cli.commands import COMMANDS
from src.cli.display import display_all_commands
from src.inventory import initialize_inventory

logger = get_logger(__name__)


def run_cli_mode() -> None:
    """
    Run the toolkit in CLI mode.

    This is the main entry point for CLI operations.
    """
    # Parse the command line arguments
    try:
        args, parser = parse_args()

        # If no command was specified, show help
        if not hasattr(args, "command") or not args.command:
            parser.print_help()
            return None, parser

        # Configure logging with the specified log level
        if hasattr(args, "log_level") and args.log_level:
            from src.utils.logging_config import configure_logging

            configure_logging(args.log_level.lower())

        # Special handling for list-commands to show all available commands
        if args.command == "list-commands":
            logger.info("Listing all available commands")
            # The execute_command will call display_all_commands
            execute_command(args)
            return None, parser

        # Initialize inventory if specified
        if hasattr(args, "inventory") and args.inventory:
            initialize_inventory(args.inventory)

        # Execute the specified command
        result = execute_command(args)

        # Return result for use in main.py or other callers
        return result, parser

    except SystemExit as e:
        # Catch the SystemExit exception from argparse
        print(
            f"Command line argument error. Use --help for usage information."
        )
        return None, None


def parse_args(
    args=None,
) -> Tuple[argparse.Namespace, argparse.ArgumentParser]:
    """
    Parse command line arguments.

    Args:
        args: Command line arguments to parse (defaults to sys.argv)

    Returns:
        Tuple of (parsed args, parser instance)
    """
    parser = create_parser()

    # Debug: Print arguments that will be parsed
    if args is None:
        args = sys.argv[1:]
    logger.debug(f"DEBUG: Parsing arguments: {args}")

    try:
        # Parse arguments
        parsed_args = parser.parse_args(args)

        # Debug: Print parsed arguments
        logger.debug(
            f"DEBUG: Successfully parsed arguments: {vars(parsed_args)}"
        )

        # Configure logging with the specified log level
        if hasattr(parsed_args, "log_level") and parsed_args.log_level:
            configure_logging(parsed_args.log_level.lower())

        # Log the parsed command
        if hasattr(parsed_args, "command") and parsed_args.command:
            device_info = (
                f", device={parsed_args.device}"
                if hasattr(parsed_args, "device")
                else ""
            )
            logger.debug(
                f"Command line arguments parsed: command={parsed_args.command}{device_info}"
            )
            logger.debug(f"All parsed arguments: {vars(parsed_args)}")

        return parsed_args, parser
    except Exception as e:
        logger.error(f"DEBUG: Error parsing arguments: {e}")
        raise


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the main argument parser.

    Returns:
        The configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(description="Network Information CLI")

    # Global options
    parser.add_argument(
        "--log-level",
        type=str.lower,
        choices=["debug", "info", "warning", "error"],
        help="Set the logging level (debug, info, warning, error)",
        default="info",
    )
    parser.add_argument(
        "--device",
        help="Device name from inventory (required for most commands)",
        required=False,  # Make this optional to allow --all-devices
    )
    parser.add_argument(
        "--all-devices",
        action="store_true",
        help="Run command on all devices in inventory concurrently",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=5,
        help="Maximum number of concurrent workers when using --all-devices (default: 5)",
    )
    parser.add_argument(
        "--inventory",
        help="Path to inventory JSON file (overrides NETWORK_INVENTORY env var)",
    )

    # Add subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command type")

    # Register all commands from the COMMANDS dictionary
    for _, command in COMMANDS.items():
        command.register(subparsers)

    return parser


def execute_command(args: argparse.Namespace) -> Optional[Dict[str, Any]]:
    """
    Execute the command specified in the parsed arguments.

    Args:
        args: Parsed command line arguments

    Returns:
        Command result or None for special commands like list-commands
    """
    # Validate that either --device or --all-devices is present for commands that need it
    needs_device = args.command not in ["list-commands", "list-devices"]

    if needs_device:
        has_device = hasattr(args, "device") and args.device
        has_all_devices = hasattr(args, "all_devices") and args.all_devices

        if not (has_device or has_all_devices):
            logger.error(
                "Either --device or --all-devices is required for this command"
            )
            print(
                "Error: Either --device or --all-devices is required for this command."
            )
            sys.exit(1)

        if has_device and has_all_devices:
            logger.error("Cannot specify both --device and --all-devices")
            print(
                "Error: Cannot specify both --device and --all-devices options."
            )
            sys.exit(1)

    # Find and execute the command
    if args.command in COMMANDS:
        return COMMANDS[args.command].execute(args)
    else:
        logger.error(f"Unknown command: {args.command}")
        print(f"Error: Unknown command '{args.command}'")
        sys.exit(1)
