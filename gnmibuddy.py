#!/usr/bin/env python3
"""
CLI entry point for gNMIBuddy - Click-based CLI with clean architecture.
"""
import sys

from src.utils.thread_safety import apply_thread_safety_patches

# Apply thread safety patches first
apply_thread_safety_patches()

from src.cmd import run_cli_mode
from src.logging.config import get_logger


def setup_error_handling() -> None:
    """Configure global error handling for the application."""

    def handle_exception(exc_type, exc_value, exc_traceback):
        """Global exception handler that logs unhandled exceptions."""
        if issubclass(exc_type, KeyboardInterrupt):
            # Don't log keyboard interrupts
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logger = get_logger(__name__)
        logger.error(
            "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
        )

    sys.excepthook = handle_exception


def handle_keyboard_interrupt() -> None:
    """Handle keyboard interrupt gracefully."""
    print("\nOperation cancelled by user.", file=sys.stderr)
    sys.exit(1)


def handle_general_exception(error: Exception) -> None:
    """Handle general exceptions with proper logging."""
    logger = get_logger(__name__)
    logger.error("Error executing command: %s", error)
    print(f"Error: {error}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    """
    Main entry point for CLI mode using the new Click-based architecture.

    This function orchestrates the CLI execution with proper error handling
    and follows the single responsibility principle.
    """
    setup_error_handling()

    try:
        run_cli_mode()

    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        handle_general_exception(e)


if __name__ == "__main__":
    main()
