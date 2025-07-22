#!/usr/bin/env python3
"""
Command decorators for CLI implementations.

This module provides reusable decorators for adding common options to CLI commands:
- Output format options (--output)
- Detail flags (--detail)
- Device selection options (--device, --devices, --device-file, --all-devices)
- Validation functions for device options

Separated from base.py for improved code organization and reusability.
"""
import sys
from typing import Callable

import click


def validate_device_option(ctx, param, value):
    """Validate device option and handle special cases like --help being passed as device name"""
    if value == "--help" or value == "-h":
        # User typed something like "--device --help", show help instead
        click.echo(ctx.get_help())
        ctx.exit()
    return value


def validate_device_selection_mutual_exclusivity(ctx, param, value):
    """
    Validate that device selection options are mutually exclusive and appear only once.

    Ensures:
    1. Only one of --device, --devices, --device-file, or --all-devices is specified
    2. Each option appears only once per command line

    Args:
        ctx: Click context
        param: Click parameter that was triggered
        value: Value of the parameter

    Returns:
        The original value if validation passes

    Raises:
        click.BadParameter: If multiple device selection options are specified
                          or if the same option appears multiple times
    """
    # If no value provided, no validation needed
    if not value:
        return value

    # Check for duplicate options in command line arguments
    current_option = f"--{param.name.replace('_', '-')}"

    # Count occurrences of this option in sys.argv
    option_count = sys.argv.count(current_option)
    if option_count > 1:
        raise click.BadParameter(
            f"\n❌ Duplicate Device Option Error\n"
            f"{'=' * 50}\n\n"
            f"The option '{current_option}' can only be specified once per command.\n"
            f"Found {option_count} occurrences in command line.\n\n"
            f"💡 How to fix this:\n"
            f"  • Remove duplicate '{current_option}' options\n"
            f"  • Use --devices for multiple devices: --devices device1,device2,device3\n"
            f"  • Use --device-file for many devices: --device-file path/to/devices.txt"
        )

    # Check for existing device selection parameters in context
    device_params = {
        "device": "--device",
        "devices": "--devices",
        "device_file": "--device-file",
        "all_devices": "--all-devices",
    }

    # Count how many device selection options have been set
    set_options = []
    current_param_name = param.name

    # Check other parameters that have already been processed
    for param_name, option_name in device_params.items():
        if param_name == current_param_name:
            # This is the current parameter being validated
            if value:
                set_options.append(option_name)
        else:
            # Check if this parameter was already set in the context
            param_value = ctx.params.get(param_name)
            if param_value:
                set_options.append(option_name)

    # If more than one device selection option is set, raise error
    if len(set_options) > 1:
        raise click.BadParameter(
            f"\n❌ Mutually Exclusive Options Error\n"
            f"{'=' * 50}\n\n"
            f"Device selection options are mutually exclusive.\n"
            f"Found: {', '.join(set_options)}\n\n"
            f"💡 How to fix this:\n"
            f"  Please specify only ONE of the following options:\n"
            f"  • --device DEVICE_NAME          (single device)\n"
            f"  • --devices DEVICE1,DEVICE2     (multiple devices)\n"
            f"  • --device-file PATH_TO_FILE    (devices from file)\n"
            f"  • --all-devices                 (all inventory devices)"
        )

    # Apply original device validation for --device option
    if param.name == "device":
        return validate_device_option(ctx, param, value)

    return value


def add_output_option(func: Callable) -> Callable:
    """Decorator to add output format option to commands"""
    func = click.option(
        "--output",
        "-o",
        type=click.Choice(["json", "yaml"], case_sensitive=False),
        default="json",
        help="Output format (json, yaml)",
    )(func)
    return func


def add_detail_option(help_text: str = "Show detailed information"):
    """Decorator factory to add detail flag option to commands"""

    def decorator(func: Callable) -> Callable:
        func = click.option("--detail", is_flag=True, help=help_text)(func)
        return func

    return decorator


def add_device_selection_options(func: Callable) -> Callable:
    """Decorator to add device selection options to commands

    Adds the following options with mutual exclusivity validation:
    - --device: Single device name from inventory
    - --devices: Comma-separated list of device names
    - --device-file: Path to file containing device names
    - --all-devices: Run command on all devices in inventory

    These options are mutually exclusive - only one can be specified per command.
    Each option can only appear once per command line.
    """
    func = click.option(
        "--all-devices",
        is_flag=True,
        help="Run command on all devices in inventory",
        callback=validate_device_selection_mutual_exclusivity,
    )(func)
    func = click.option(
        "--device-file",
        type=click.Path(exists=True),
        help="Path to file containing device names (one per line)",
        callback=validate_device_selection_mutual_exclusivity,
    )(func)
    func = click.option(
        "--devices",
        type=str,
        help="Comma-separated list of device names",
        callback=validate_device_selection_mutual_exclusivity,
    )(func)
    func = click.option(
        "--device",
        help="Device name from inventory",
        callback=validate_device_selection_mutual_exclusivity,
    )(func)
    return func


def add_common_device_options(func: Callable) -> Callable:
    """Decorator to add common device-related options to commands"""
    # Use atomic decorators to compose the common options
    func = add_output_option(func)
    func = add_device_selection_options(func)
    return func
