#!/usr/bin/env python3
"""Main CLI argument parser for network tools application"""
import argparse
import sys
from typing import Optional, Tuple, Dict, Any

from src.cmd.commands import COMMANDS
from src.logging.config import get_logger
from src.inventory import initialize_inventory
from src.cmd.display import display_all_commands
from src.utils.version_utils import load_gnmibuddy_version
from src.cmd.cli_utils import display_program_banner, get_python_version


logger = get_logger(__name__)


def run_cli_mode() -> (
    Tuple[Optional[Dict[str, Any]], Optional[argparse.ArgumentParser]]
):
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

        # Configure logging with the specified log level and module settings
        if hasattr(args, "log_level") and args.log_level:
            from src.logging.config import LoggingConfig

            # Parse module-specific log levels
            module_levels = {}
            if hasattr(args, "module_log_levels") and args.module_log_levels:
                try:
                    for item in args.module_log_levels.split(","):
                        if "=" in item:
                            module, level = item.strip().split("=", 1)
                            module_levels[module.strip()] = level.strip()
                except ValueError:
                    logger.warning(
                        "Invalid module-log-levels format. Use 'module1=debug,module2=warning'"
                    )

            LoggingConfig.configure(
                global_level=args.log_level.lower(),
                module_levels=module_levels,
                enable_structured=getattr(args, "structured_logging", False),
            )

        gnmibuddy_version = load_gnmibuddy_version()
        logger.info("Python version: %s", get_python_version())
        logger.info("gNMIBuddy version: %s", gnmibuddy_version)

        # Special handling for list-commands to show all available commands
        if args.command == "list-commands":
            logger.info("Listing all available commands")
            # The execute_command will call display_all_commands
            execute_command(args)
            return None, parser

        # Initialize inventory if specified
        if hasattr(args, "inventory") and args.inventory:
            initialize_inventory(args.inventory)

        result = execute_command(args)

        return result, parser

    except SystemExit as e:
        if e.code != 0:
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

    if args is None:
        args = sys.argv[1:]
    logger.debug("DEBUG: Parsing arguments: %s", args)

    try:
        parsed_args = parser.parse_args(args)

        logger.debug(
            "DEBUG: Successfully parsed arguments: %s", vars(parsed_args)
        )

        # Configure logging with the specified log level and module settings
        if hasattr(parsed_args, "log_level") and parsed_args.log_level:
            from src.logging.config import LoggingConfig

            # Parse module-specific log levels
            module_levels = {}
            if (
                hasattr(parsed_args, "module_log_levels")
                and parsed_args.module_log_levels
            ):
                try:
                    for item in parsed_args.module_log_levels.split(","):
                        if "=" in item:
                            module, level = item.strip().split("=", 1)
                            module_levels[module.strip()] = level.strip()
                except ValueError:
                    logger.warning(
                        "Invalid module-log-levels format. Use 'module1=debug,module2=warning'"
                    )

            LoggingConfig.configure(
                global_level=parsed_args.log_level.lower(),
                module_levels=module_levels,
                enable_structured=getattr(
                    parsed_args, "structured_logging", False
                ),
            )

        if hasattr(parsed_args, "command") and parsed_args.command:
            device_info = (
                f", device={parsed_args.device}"
                if hasattr(parsed_args, "device")
                else ""
            )
            logger.debug(
                "Command line arguments parsed: command=%s%s",
                parsed_args.command,
                device_info,
            )
            logger.debug("All parsed arguments: %s", vars(parsed_args))

        return parsed_args, parser
    except Exception as e:
        logger.error("DEBUG: Error parsing arguments: %s", e)
        raise


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the main argument parser.

    Returns:
        The configured ArgumentParser instance
    """
    banner = display_program_banner()

    class BannerHelpFormatter(argparse.RawDescriptionHelpFormatter):
        def __init__(self, *args, banner=None, **kwargs):
            self.banner = banner or ""
            super().__init__(*args, **kwargs)

        def format_help(self):
            help_text = super().format_help()
            return f"{self.banner}\n{help_text}"

    parser = argparse.ArgumentParser(
        description=None,  # We'll handle the banner in the formatter
        formatter_class=lambda *args, **kwargs: BannerHelpFormatter(
            *args, banner=banner, **kwargs
        ),
    )
    # Global options
    parser.add_argument(
        "--log-level",
        type=str.lower,
        choices=["debug", "info", "warning", "error"],
        help="Set the global logging level (debug, info, warning, error)",
        default="info",
    )
    parser.add_argument(
        "--module-log-levels",
        type=str,
        help="Set specific log levels for modules (format: 'module1=debug,module2=warning'). Available modules: gnmibuddy.collectors.*, gnmibuddy.gnmi, gnmibuddy.inventory, etc.",
    )
    parser.add_argument(
        "--structured-logging",
        action="store_true",
        help="Enable structured JSON logging (useful for observability tools)",
    )
    parser.add_argument(
        "--quiet-external",
        action="store_true",
        help="Reduce noise from external libraries (pygnmi, grpc, etc.)",
        default=True,
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
        logger.error("Unknown command: %s", args.command)
        print(f"Error: Unknown command '{args.command}'")
        sys.exit(1)
