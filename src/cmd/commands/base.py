#!/usr/bin/env python3
"""
Base utilities for command implementations.

This module provides core utilities for CLI commands including:
- Device command execution orchestration
- Single device operation handling
- Error handling for device operations
- Command error provider classes

Related modules:
- batch_operations.py: Handles batch operations across multiple devices
- decorators.py: Provides command option decorators
"""
from typing import Callable, List
import click

from src.logging import get_logger
from src.schemas.models import DeviceErrorResult
from src.inventory.manager import InventoryManager
from src.cmd.formatters import format_output
from src.cmd.batch import DeviceListParser
from src.cmd.commands.batch_operations import execute_batch_operation
from src.cmd.examples.example_builder import ExampleBuilder, ExampleSet

logger = get_logger(__name__)


class CommandErrorProvider:
    """
    Base class for providing command-specific error examples.

    This implements the duck typing pattern where each command module can
    create an instance of this class (or similar) to provide error examples.
    The error handler can then use getattr() to check for specific error methods.
    """

    def __init__(self, command_name: str, group_name: str = ""):
        self.command_name = command_name
        self.group_name = group_name
        self.examples = ExampleSet(f"{command_name}_error_examples")

    def get_missing_device_examples(self) -> ExampleSet:
        """Get examples for missing --device option errors."""
        return ExampleBuilder.missing_device_error_examples(
            command=self.command_name, group=self.group_name
        )

    def get_unexpected_argument_examples(self) -> ExampleSet:
        """Get examples for unexpected argument errors."""
        return ExampleBuilder.unexpected_argument_error_examples(
            command=self.command_name, group=self.group_name
        )

    def get_device_not_found_examples(self) -> ExampleSet:
        """Get examples for device not found errors."""
        return ExampleBuilder.device_not_found_error_examples()

    def get_inventory_missing_examples(self) -> ExampleSet:
        """Get examples for inventory missing errors."""
        return ExampleBuilder.inventory_missing_error_examples()

    def get_invalid_choice_examples(
        self, option: str, valid_choices: List[str]
    ) -> ExampleSet:
        """Get examples for invalid choice errors."""
        full_command = (
            f"{self.group_name} {self.command_name}"
            if self.group_name
            else self.command_name
        )
        return ExampleBuilder.invalid_choice_error_examples(
            option=option, valid_choices=valid_choices, command=full_command
        )

    def get_examples_for_error_type(
        self, error_type: str, **kwargs
    ) -> ExampleSet:
        """
        Generic method to get examples for any error type.

        This enables the duck typing pattern - the error handler can call this
        method and the command provider can return appropriate examples.

        Args:
            error_type: Type of error (e.g., "missing_device", "unexpected_arg")
            **kwargs: Additional context for the error

        Returns:
            ExampleSet with relevant examples, or empty set if not supported
        """
        method_map = {
            "missing_device": self.get_missing_device_examples,
            "unexpected_argument": self.get_unexpected_argument_examples,
            "device_not_found": self.get_device_not_found_examples,
            "inventory_missing": self.get_inventory_missing_examples,
        }

        if error_type == "invalid_choice":
            option = kwargs.get("option", "--option")
            valid_choices = kwargs.get("valid_choices", [])
            return self.get_invalid_choice_examples(option, valid_choices)

        method = method_map.get(error_type)
        if method:
            return method()

        # Return empty set if error type not supported
        return ExampleSet(f"unsupported_{error_type}_examples")


def handle_inventory_error_in_command(error_msg: str):
    """
    Handle inventory-related errors with clear user guidance in command context

    Args:
        error_msg: The original error message
    """
    click.echo("\n❌ Inventory Error", err=True)
    click.echo("═" * 50, err=True)

    click.echo("\nThe inventory file is required but not found.", err=True)
    click.echo("\n💡 How to fix this:", err=True)
    click.echo("  1. Use --inventory option:", err=True)
    click.echo(
        "     gnmibuddy --inventory path/to/your/devices.json device info --device R1",
        err=True,
    )
    click.echo("\n  2. Or set environment variable:", err=True)
    click.echo(
        "     export NETWORK_INVENTORY=path/to/your/devices.json", err=True
    )
    click.echo("     gnmibuddy device info --device R1", err=True)

    click.echo("\n📁 Example inventory files:", err=True)
    click.echo("  • xrd_sandbox.json (in project root)", err=True)


def execute_device_command(
    ctx,
    device,
    devices,
    device_file,
    all_devices,
    output,
    operation_func,
    operation_name="operation",
    **kwargs,
):
    """
    Execute a device command with batch support

    Args:
        ctx: Click context
        device: Single device name
        devices: Comma-separated device names
        device_file: Path to file with device names
        all_devices: Flag to run on all devices
        output: Output format
        operation_func: Function that takes device_obj and returns result
        operation_name: Name of the operation for logging
        **kwargs: Additional arguments for operation_func
    """
    # Handle batch operations
    batch_devices = []
    effective_all_devices = all_devices or getattr(
        ctx.obj, "all_devices", False
    )

    if effective_all_devices:
        try:
            batch_devices = DeviceListParser.get_all_inventory_devices()
            if not batch_devices:
                click.echo("No devices found in inventory", err=True)
                raise click.Abort()
        except FileNotFoundError as e:
            # Handle inventory not found error gracefully using the template
            from src.cmd.templates.usage_templates import (
                UsageTemplates,
                InventoryUsageData,
            )

            # Build example commands
            inventory_example = "uv run gnmibuddy.py --inventory path/to/your/devices.json --all-devices ops logs"
            env_example = "uv run gnmibuddy.py --all-devices ops logs"

            data = InventoryUsageData(
                inventory_example=inventory_example, env_example=env_example
            )

            formatted_message = UsageTemplates.format_inventory_error(data)
            click.echo(formatted_message, err=True)
            raise click.Abort()
    elif devices:
        batch_devices = DeviceListParser.parse_device_list(devices)
    elif device_file:
        batch_devices = DeviceListParser.parse_device_file(device_file)

    if batch_devices:
        return execute_batch_operation(
            ctx, batch_devices, operation_func, output, **kwargs
        )

    # Single device operation
    if not device:
        # Show help instead of error when no device is specified
        click.echo(ctx.get_help())
        ctx.exit()

    logger.info("Getting %s for device: %s", operation_name, device)
    return _execute_single_operation(
        ctx, device, operation_func, output, **kwargs
    )


def _execute_single_operation(
    ctx, device: str, operation_func: Callable, output: str, **kwargs
):
    """Execute operation on a single device"""
    try:
        device_obj = InventoryManager.get_device(device)
        if isinstance(device_obj, DeviceErrorResult):
            # Check if the device string contains commas (indicating user probably meant --devices)
            if "," in device:
                click.echo(f"Error: {device_obj.msg}", err=True)
                click.echo("\n❌ Multiple Device Names Detected", err=True)
                click.echo("═" * 50, err=True)
                click.echo(
                    f"\nIt looks like you're trying to specify multiple devices: '{device}'",
                    err=True,
                )
                click.echo("\n💡 How to fix this:", err=True)
                click.echo(
                    "  Use --devices (plural) for multiple devices:", err=True
                )
                click.echo(f"    --devices {device}", err=True)
                click.echo(
                    "\n  Or run separate commands for individual devices:",
                    err=True,
                )
                device_names = [
                    d.strip() for d in device.split(",") if d.strip()
                ]

                # Build the command parts by walking up the context
                command_parts = []
                current_ctx = ctx
                while (
                    current_ctx
                    and hasattr(current_ctx, "info_name")
                    and current_ctx.info_name
                ):
                    # Skip the root script name
                    if current_ctx.info_name != "gnmibuddy.py":
                        command_parts.insert(0, current_ctx.info_name)
                    current_ctx = getattr(current_ctx, "parent", None)

                # Build the full command
                full_command = "uv run gnmibuddy.py"
                if command_parts:
                    full_command += " " + " ".join(command_parts)

                # Show examples for first 2 devices
                for device_name in device_names[:2]:
                    click.echo(
                        f"    {full_command} --device {device_name}", err=True
                    )

                # Show the actual command help
                click.echo("\n" + "═" * 50, err=True)
                click.echo("Command Help:", err=True)
                click.echo("═" * 50, err=True)
                try:
                    help_text = ctx.get_help()
                    click.echo(help_text, err=True)
                except Exception:
                    # Fallback if we can't get help
                    click.echo(
                        "Run the command with --help to see all available options",
                        err=True,
                    )
            else:
                # Regular device not found error
                click.echo(f"Error: {device_obj.msg}", err=True)
                click.echo(
                    "\n💡 To see available devices, run: uv run gnmibuddy.py device list",
                    err=True,
                )

                # Show the actual command help for regular device not found errors too
                click.echo("\n" + "═" * 50, err=True)
                click.echo("Command Help:", err=True)
                click.echo("═" * 50, err=True)
                try:
                    help_text = ctx.get_help()
                    click.echo(help_text, err=True)
                except Exception:
                    # Fallback if we can't get help
                    click.echo(
                        "Run the command with --help to see all available options",
                        err=True,
                    )

            raise click.Abort()
    except FileNotFoundError as e:
        error_msg = str(e)
        if "inventory file" in error_msg.lower():
            handle_inventory_error_in_command(error_msg)
        else:
            click.echo(f"File not found: {error_msg}", err=True)
        raise click.Abort()

    result = operation_func(device_obj, **kwargs)
    formatted_output = format_output(result, output.lower())
    click.echo(formatted_output)
    return result
