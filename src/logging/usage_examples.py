#!/usr/bin/env python3
"""
Usage examples for the centralized external library suppression.

This file demonstrates how different parts of the gNMIBuddy codebase
can use the external suppression functionality.
"""

from src.logging import (
    configure_logging,
    get_logger,
    setup_mcp_suppression,
    setup_cli_suppression,
    setup_development_suppression,
    ExternalLibrarySuppressor,
)


def example_mcp_server_setup():
    """Example: Setting up logging for an MCP server."""
    # Early environment suppression (before any gRPC imports)
    ExternalLibrarySuppressor.setup_environment_suppression()

    # Configure logging with MCP-specific suppression
    configure_logging(log_level="info", external_suppression_mode="mcp")

    # Or use the convenience function
    # setup_mcp_suppression()

    logger = get_logger(__name__)
    logger.info("MCP server logging configured")


def example_cli_tool_setup():
    """Example: Setting up logging for CLI tools."""
    # Configure logging with CLI-friendly suppression
    configure_logging(log_level="info", external_suppression_mode="cli")

    # Or use the convenience function
    # setup_cli_suppression()

    logger = get_logger(__name__)
    logger.info("CLI tool logging configured")


def example_development_setup():
    """Example: Setting up logging for development/debugging."""
    # Configure logging with more verbose external library output
    configure_logging(
        log_level="debug", external_suppression_mode="development"
    )

    # Or use the convenience function
    # setup_development_suppression()

    logger = get_logger(__name__)
    logger.debug("Development logging configured")


def example_custom_suppression():
    """Example: Custom external library suppression levels."""
    # Configure with custom external library levels
    configure_logging(
        log_level="info",
        module_levels={
            "pygnmi": "warning",  # Custom pygnmi level
            "grpc": "error",  # Custom gRPC level
            "requests": "info",  # Allow requests info logs
        },
        external_suppression_mode="cli",
    )

    logger = get_logger(__name__)
    logger.info("Custom suppression configured")


def example_api_server_setup():
    """Example: Setting up logging for API servers."""
    # For API servers, we might want moderate suppression
    configure_logging(
        log_level="info",
        module_levels={
            "pygnmi": "warning",
            "grpc": "warning",
            "urllib3": "warning",
            "asyncio": "error",
        },
        external_suppression_mode="cli",
        structured=True,  # Structured logs for API servers
    )

    logger = get_logger(__name__)
    logger.info("API server logging configured")


def example_testing_setup():
    """Example: Setting up logging for tests."""
    # For tests, we might want to suppress most external noise
    configure_logging(
        log_level="warning",
        module_levels={
            "pygnmi": "error",
            "grpc": "error",
            "urllib3": "error",
            "asyncio": "error",
            "requests": "error",
        },
        external_suppression_mode="mcp",  # Aggressive suppression
    )

    logger = get_logger(__name__)
    logger.warning("Test logging configured")


def example_dynamic_suppression():
    """Example: Dynamically adjusting external library levels."""
    # Start with basic configuration
    configure_logging(log_level="info", external_suppression_mode="cli")

    # Dynamically adjust specific external libraries
    ExternalLibrarySuppressor.setup_python_logging_suppression(
        custom_levels={
            "pygnmi": "debug",  # Enable debug for pygnmi troubleshooting
        },
        include_defaults=False,
    )

    logger = get_logger(__name__)
    logger.info("Dynamic suppression example")


def example_checking_suppressed_libraries():
    """Example: Checking if a library is suppressed."""

    # Check if specific loggers are suppressed
    suppressed_libs = [
        "pygnmi",
        "grpc",
        "urllib3",
        "requests",
        "my_custom_lib",
    ]

    for lib in suppressed_libs:
        is_suppressed = ExternalLibrarySuppressor.is_suppressed_library(lib)
        print(f"{lib}: {'suppressed' if is_suppressed else 'not suppressed'}")

    # Get default suppression configuration
    defaults = ExternalLibrarySuppressor.get_default_suppressions()
    print(f"Default suppressions: {defaults}")


if __name__ == "__main__":
    print("=== External Library Suppression Examples ===\n")

    print("1. MCP Server Setup:")
    example_mcp_server_setup()

    print("\n2. CLI Tool Setup:")
    example_cli_tool_setup()

    print("\n3. Development Setup:")
    example_development_setup()

    print("\n4. Custom Suppression:")
    example_custom_suppression()

    print("\n5. API Server Setup:")
    example_api_server_setup()

    print("\n6. Testing Setup:")
    example_testing_setup()

    print("\n7. Dynamic Suppression:")
    example_dynamic_suppression()

    print("\n8. Checking Suppressed Libraries:")
    example_checking_suppressed_libraries()
