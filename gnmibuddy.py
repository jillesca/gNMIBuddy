#!/usr/bin/env python3
"""
CLI entry point for gNMIBuddy - Click-based CLI with backward compatibility.
"""
import sys

from src.utils.thread_safety import apply_thread_safety_patches

# Apply thread safety patches first
apply_thread_safety_patches()

from api import get_devices
from src.cmd import run_cli_mode
from src.logging.config import get_logger
from src.utils.serialization import to_json_string


def main():
    """
    Main entry point for CLI mode using the new Click-based architecture.
    """
    try:
        result, cli_context = run_cli_mode()

        if result is None:
            return

        if (
            result is not None
            and hasattr(result, "get")
            and result.get("command") == "list-devices"
        ):
            result = get_devices()

        if result is not None:
            print(to_json_string(result))

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger = get_logger(__name__)
        logger.error("Error executing command: %s", e)
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
