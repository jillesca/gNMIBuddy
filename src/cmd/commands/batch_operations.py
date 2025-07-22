#!/usr/bin/env python3
"""
Batch operations functionality for command implementations.

This module provides dedicated functionality for executing CLI commands
across multiple devices in parallel, with proper error handling, progress
reporting, and result formatting.

Separated from base.py for improved code organization and clarity.
"""
from typing import Callable, List
import click

from src.logging.config import get_logger
from src.cmd.formatters import format_output
from src.inventory.manager import InventoryManager
from src.cmd.batch import BatchOperationExecutor
from src.schemas.models import DeviceErrorResult
from src.schemas.responses import (
    NetworkOperationResult,
    OperationStatus,
    ErrorResponse,
)

logger = get_logger(__name__)


def execute_batch_operation(
    ctx,
    batch_devices: List[str],
    operation_func: Callable,
    output: str,
    **kwargs,
):
    """Execute batch operation on multiple devices

    This function handles the execution of operations across multiple devices
    in parallel, with proper error handling and progress reporting.

    Args:
        ctx: Click context containing configuration
        batch_devices: List of device names to process
        operation_func: Function to execute on each device
        output: Output format for results
        **kwargs: Additional arguments to pass to operation_func

    Returns:
        BatchOperationResult: Results from all device operations
    """
    max_workers = getattr(ctx.obj, "max_workers", 5)
    executor = BatchOperationExecutor(max_workers=max_workers)

    # Extract operation type from context or function
    operation_type = getattr(ctx.command, "name", "unknown_operation")
    if hasattr(ctx, "info_name"):
        operation_type = ctx.info_name

    def single_device_operation(device_name: str):
        """Execute operation on a single device with error handling"""
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

    # Show progress for long-running operations
    show_progress = len(batch_devices) > 2

    try:
        batch_result = executor.execute_batch_operation(
            devices=batch_devices,
            operation_func=single_device_operation,
            operation_type=operation_type,
            show_progress=show_progress,
        )

        # Format and display the results
        formatted_output = format_output(batch_result, output.lower())
        click.echo(formatted_output)

        return batch_result

    except Exception as e:
        logger.error("Batch operation failed: %s", e)
        click.echo(f"Batch operation failed: {e}", err=True)
        raise click.Abort()

    return batch_result
