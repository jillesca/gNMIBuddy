#!/usr/bin/env python3
"""
CLI entry point for gNMIBuddy - Provides command-line interface to network tools.
"""
import sys
import json
import argparse

from src.utils.thread_safety import apply_thread_safety_patches

# Apply thread safety patches first
apply_thread_safety_patches()

from api import get_devices
from src.cmd import run_cli_mode
from src.logging.config import LoggingConfig, get_logger
from src.utils.version_utils import load_gnmibuddy_version


def main():
    """
    Main entry point for CLI mode. Parses arguments and executes commands.
    """
    # Get log level from command line before initializing
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--log-level", type=str)
    parser.add_argument("--module-log-levels", type=str)
    parser.add_argument("--structured-logging", action="store_true")
    args, remaining_args = parser.parse_known_args(sys.argv[1:])

    # Parse module-specific log levels
    module_levels = {}
    if args.module_log_levels:
        try:
            for item in args.module_log_levels.split(","):
                if "=" in item:
                    module, level = item.strip().split("=", 1)
                    module_levels[module.strip()] = level.strip()
        except ValueError:
            print(
                "Warning: Invalid module-log-levels format. Use 'module1=debug,module2=warning'"
            )

    LoggingConfig.configure(
        global_level=args.log_level,
        module_levels=module_levels,
        enable_structured=args.structured_logging,
    )
    logger = get_logger(__name__)

    if not (
        "-h" in remaining_args
        or "--help" in remaining_args
        or not remaining_args
    ):
        # Load and log gNMIBuddy version
        gnmibuddy_version = load_gnmibuddy_version()
        logger.info("Running gNMIBuddy version: %s", gnmibuddy_version)
        logger.info("Python version: %s", sys.version)

    try:
        result, parser = run_cli_mode()

        # If result is None, there was an error or help was displayed
        if result is None:
            return

        # Process command results - check if result is a dictionary with a command key
        if (
            isinstance(result, dict)
            and result.get("command") == "list-devices"
        ):

            result = get_devices()

        if result is not None:
            print(json.dumps(result, indent=2))
    except Exception as e:
        logger.error("Error executing command: %s", e)
        return


if __name__ == "__main__":
    main()
