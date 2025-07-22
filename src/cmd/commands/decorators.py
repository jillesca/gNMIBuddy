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
from typing import Callable
import click


def validate_device_option(ctx, param, value):
    """Validate device option and handle special cases like --help being passed as device name"""
    if value == "--help" or value == "-h":
        # User typed something like "--device --help", show help instead
        click.echo(ctx.get_help())
        ctx.exit()
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
    """Decorator factory to add detail flag option to commands

    Args:
        help_text: Custom help text for the detail option

    Returns:
        Decorator function that adds the --detail flag
    """

    def decorator(func: Callable) -> Callable:
        func = click.option("--detail", is_flag=True, help=help_text)(func)
        return func

    return decorator


def add_device_selection_options(func: Callable) -> Callable:
    """Decorator to add device selection options to commands

    Adds the following options:
    - --device: Single device name from inventory
    - --devices: Comma-separated list of device names
    - --device-file: Path to file containing device names
    - --all-devices: Run command on all devices in inventory
    """
    func = click.option(
        "--all-devices",
        is_flag=True,
        help="Run command on all devices in inventory",
    )(func)
    func = click.option(
        "--device-file",
        type=click.Path(exists=True),
        help="Path to file containing device names (one per line)",
    )(func)
    func = click.option(
        "--devices", type=str, help="Comma-separated list of device names"
    )(func)
    func = click.option(
        "--device",
        help="Device name from inventory",
        callback=validate_device_option,
    )(func)
    return func


def add_common_device_options(func: Callable) -> Callable:
    """Decorator to add common device-related options to commands

    This is a convenience decorator that combines:
    - Output format options (add_output_option)
    - Device selection options (add_device_selection_options)

    Use this for commands that need standard device operation capabilities.
    """
    # Use atomic decorators to compose the common options
    func = add_output_option(func)
    func = add_device_selection_options(func)
    return func
