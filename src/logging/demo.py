#!/usr/bin/env python3
"""
Example demonstrating the enhanced logging capabilities of gNMIBuddy.

This script shows how to use the new logging features:
1. Module-specific log levels
2. Structured logging
3. Operation tracking
4. OTel-compatible logging
"""

import json
import sys
from src.logging.config import (
    LoggingConfig,
    LoggerNames,
    get_logger,
    log_operation,
)
from src.inventory import initialize_inventory, get_device
from src.collectors.interfaces import get_interfaces


# Configure logging with examples
def demo_basic_logging():
    """Demo basic logging configuration."""
    print("=== Basic Logging Demo ===")

    # Configure with global INFO level
    LoggingConfig.configure(global_level="info")
    logger = get_logger(__name__)

    logger.info("This is an info message")
    logger.debug("This debug message won't show (global level is INFO)")
    logger.warning("This is a warning")

    print("\n")


def demo_module_specific_logging():
    """Demo module-specific logging levels."""
    print("=== Module-Specific Logging Demo ===")

    # Configure different levels for different modules
    module_levels = {
        LoggerNames.COLLECTORS: "debug",
        LoggerNames.GNMI: "warning",
        LoggerNames.PYGNMI: "error",
    }

    LoggingConfig.configure(global_level="info", module_levels=module_levels)

    # Get loggers for different modules
    collectors_logger = get_logger("gnmibuddy.collectors.interfaces")
    gnmi_logger = get_logger("gnmibuddy.gnmi")
    app_logger = get_logger(__name__)

    app_logger.info("App logger at INFO level")
    collectors_logger.debug(
        "Collectors logger at DEBUG level - this will show"
    )
    gnmi_logger.info("gNMI logger info - this won't show (level is WARNING)")
    gnmi_logger.warning("gNMI logger warning - this will show")

    print("\n")


def demo_structured_logging():
    """Demo structured JSON logging."""
    print("=== Structured Logging Demo ===")

    LoggingConfig.configure(global_level="info", enable_structured=True)

    logger = get_logger(__name__)

    # Log with structured data
    logger.info(
        "Processing device operation",
        extra={
            "device_name": "xrd-1",
            "operation": "get_interfaces",
            "duration_ms": 150.5,
        },
    )

    print("\n")


@log_operation("demo_operation")
def demo_operation_tracking(device_name: str):
    """Demo operation tracking with decorator."""
    logger = get_logger(__name__)
    logger.info(f"Performing operation on {device_name}")
    return {"result": "success", "device": device_name}


def demo_dynamic_log_level_changes():
    """Demo changing log levels at runtime."""
    print("=== Dynamic Log Level Changes Demo ===")

    LoggingConfig.configure(global_level="info")
    logger = get_logger("gnmibuddy.collectors.interfaces")

    logger.debug("This debug message won't show initially")
    logger.info("This info message will show")

    # Change log level dynamically
    print("Changing gnmibuddy.collectors.interfaces to DEBUG level...")
    LoggingConfig.set_module_level("gnmibuddy.collectors.interfaces", "debug")

    logger.debug("This debug message will now show after level change")
    logger.info("This info message still shows")

    # Show current levels
    current_levels = LoggingConfig.get_module_levels()
    print(f"Current module levels: {json.dumps(current_levels, indent=2)}")

    print("\n")


def demo_real_network_operation():
    """Demo logging in real network operations."""
    print("=== Real Network Operation Demo ===")

    try:
        # Initialize with debug logging for collectors only
        module_levels = {
            LoggerNames.COLLECTORS: "debug",
            LoggerNames.GNMI: "info",
            LoggerNames.PYGNMI: "warning",
        }

        LoggingConfig.configure(
            global_level="info", module_levels=module_levels
        )

        # Initialize inventory
        initialize_inventory()

        # Get a device (you'll need to have NETWORK_INVENTORY set)
        device_info, success = get_device(
            "xrd-1"
        )  # Change to your device name

        if success:
            print(
                f"Successfully got device info, performing interface query..."
            )
            # This will show debug logs from the collectors module
            result = get_interfaces(device_info)  # type: ignore
            print(f"Operation completed with status: {result.status}")
        else:
            print(f"Failed to get device: {device_info}")

    except Exception as e:
        print(f"Demo failed: {e}")
        print("Make sure NETWORK_INVENTORY environment variable is set")

    print("\n")


def demo_cli_integration():
    """Show how the CLI would use these logging features."""
    print("=== CLI Integration Example ===")
    print("You can now use these CLI options:")
    print()
    print("# Basic log level control:")
    print("python cli_app.py --log-level debug --device xrd-1 interfaces")
    print()
    print("# Module-specific logging:")
    print("python cli_app.py --log-level info \\")
    print("  --module-log-levels 'gnmibuddy.collectors=debug,pygnmi=error' \\")
    print("  --device xrd-1 interfaces")
    print()
    print("# Structured logging for observability:")
    print("python cli_app.py --log-level info --structured-logging \\")
    print("  --device xrd-1 interfaces")
    print()
    print("# Dynamic log level management:")
    print("python cli_app.py --device xrd-1 log-level show")
    print(
        "python cli_app.py --device xrd-1 log-level set gnmibuddy.gnmi debug"
    )
    print("python cli_app.py --device xrd-1 log-level modules")
    print()


if __name__ == "__main__":
    print("gNMIBuddy Enhanced Logging Demo")
    print("===============================\n")

    # Run all demos
    demo_basic_logging()
    demo_module_specific_logging()
    demo_structured_logging()

    print("=== Operation Tracking Demo ===")
    LoggingConfig.configure(global_level="info")
    result = demo_operation_tracking("demo-device")
    print(f"Operation result: {result}\n")

    demo_dynamic_log_level_changes()
    demo_real_network_operation()
    demo_cli_integration()

    print("Demo completed! Check the logs/ directory for log files.")
