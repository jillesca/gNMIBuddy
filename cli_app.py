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
from src.utils.logging_config import configure_logging, get_logger


def main():
    """
    Main entry point for CLI mode. Parses arguments and executes commands.
    """
    # Get log level from command line before initializing
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--log-level", type=str)
    args, _ = parser.parse_known_args(sys.argv[1:])

    configure_logging(args.log_level if hasattr(args, "log_level") else None)
    logger = get_logger(__name__)

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
            # logger.debug("Command result: %s...", json.dumps(result)[:1000])
            print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error executing command: {e}")
        return


if __name__ == "__main__":
    main()
