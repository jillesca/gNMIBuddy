#!/usr/bin/env python3
"""Base utilities for command implementations"""
from typing import Callable, List
import click

from src.logging.config import get_logger
from src.cmd.formatters import format_output
from src.inventory.manager import InventoryManager
from src.cmd.batch import DeviceListParser, BatchOperationExecutor
from src.schemas.models import DeviceErrorResult
from src.schemas.responses import (
    NetworkOperationResult,
    OperationStatus,
    ErrorResponse,
)
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
        return _execute_batch_operation(
            ctx, batch_devices, operation_func, output, **kwargs
        )

    # Single device operation
    if not device:
        # Show help instead of error when no device is specified
        click.echo(ctx.get_help())
        ctx.exit()

    logger.info("Getting %s for device: %s", operation_name, device)
    return _execute_single_operation(device, operation_func, output, **kwargs)


def _execute_batch_operation(
    ctx,
    batch_devices: List[str],
    operation_func: Callable,
    output: str,
    **kwargs,
):
    """Execute batch operation on multiple devices"""
    max_workers = getattr(ctx.obj, "max_workers", 5)
    executor = BatchOperationExecutor(max_workers=max_workers)

    # Extract operation type from context or function
    operation_type = getattr(ctx.command, "name", "unknown_operation")
    if hasattr(ctx, "info_name"):
        operation_type = ctx.info_name

    def single_device_operation(device_name: str):
        device_obj = InventoryManager.get_device(device_name)
        if isinstance(device_obj, DeviceErrorResult):
            return NetworkOperationResult(
                device_name=device_name,
                ip_address=device_obj.ip_address,
                nos=device_obj.nos,
                operation_type=operation_type,
                status=OperationStatus.FAILED,
                data={},
                metadata={},
                error_response=ErrorResponse(
                    type="device_not_found",
                    message=f"Device not found: {device_obj.msg}",
                ),
            )

        result = operation_func(device_obj, **kwargs)

        if not isinstance(result, NetworkOperationResult):
            return NetworkOperationResult(
                device_name=device_name,
                ip_address=device_obj.ip_address,
                nos=device_obj.nos,
                operation_type=operation_type,
                status=OperationStatus.SUCCESS,
                data=(
                    result
                    if isinstance(result, dict)
                    else {"raw_result": result}
                ),
                metadata={},
            )
        return result

    click.echo(f"Executing batch operation on {len(batch_devices)} devices...")
    batch_result = executor.execute_batch_operation(
        devices=batch_devices,
        operation_func=single_device_operation,
        operation_type=operation_type,
        show_progress=True,
    )

    # Format batch results using the new schema
    batch_data = {
        "summary": {
            "total_devices": batch_result.summary.total_devices,
            "successful": batch_result.summary.successful,
            "failed": batch_result.summary.failed,
            "success_rate": batch_result.summary.success_rate,
            "execution_time": batch_result.summary.execution_time,
            "operation_type": batch_result.summary.operation_type,
        },
        "results": [
            {
                "device": result.device_name,
                "ip_address": result.ip_address,
                "nos": result.nos,
                "operation_type": result.operation_type,
                "status": result.status.value,
                "success": result.status
                == OperationStatus.SUCCESS,  # For backward compatibility
                "data": result.data,
                "metadata": result.metadata,
                "error": (
                    result.error_response.message
                    if result.error_response
                    else None
                ),
                "execution_time": result.metadata.get("execution_time", 0.0),
            }
            for result in batch_result.results
        ],
    }

    formatted_output = format_output(batch_data, output.lower())
    click.echo(formatted_output)
    return batch_result


def _execute_single_operation(
    device: str, operation_func: Callable, output: str, **kwargs
):
    """Execute operation on a single device"""
    try:
        device_obj = InventoryManager.get_device(device)
        if isinstance(device_obj, DeviceErrorResult):
            click.echo(f"Error: {device_obj.msg}", err=True)
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


# Atomic decorators for common options
def add_output_option(func):
    """Decorator to add output format option to commands"""
    func = click.option(
        "--output",
        "-o",
        type=click.Choice(["json", "yaml"], case_sensitive=False),
        default="json",
        help="Output format (json, yaml)",
    )(func)
    return func


def add_detail_option(help_text="Show detailed information"):
    """Decorator factory to add detail flag option to commands"""

    def decorator(func):
        func = click.option("--detail", is_flag=True, help=help_text)(func)
        return func

    return decorator


def validate_device_option(ctx, param, value):
    """Validate device option and handle special cases like --help being passed as device name"""
    if value == "--help" or value == "-h":
        # User typed something like "--device --help", show help instead
        click.echo(ctx.get_help())
        ctx.exit()
    return value


def add_device_selection_options(func):
    """Decorator to add device selection options to commands"""
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


def add_common_device_options(func):
    """Decorator to add common device-related options to commands"""
    # Use atomic decorators to compose the common options
    func = add_output_option(func)
    func = add_device_selection_options(func)
    return func
