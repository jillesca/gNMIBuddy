#!/usr/bin/env python3
"""Batch operations support for CLI commands with parallel execution"""
import time
from typing import List, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

import click
from src.schemas.responses import (
    NetworkOperationResult,
    BatchOperationResult,
    BatchOperationSummary,
    OperationStatus,
    ErrorResponse,
)
from src.logging import get_logger
from src.inventory.manager import InventoryManager

logger = get_logger(__name__)


class ProgressIndicator:
    """Simple progress indicator for batch operations"""

    def __init__(self, total: int, show_progress: bool = True):
        self.total = total
        self.completed = 0
        self.show_progress = show_progress
        self.start_time = time.time()

    def update(self, increment: int = 1):
        """Update progress"""
        self.completed += increment
        if self.show_progress and self.total > 1:
            percentage = (self.completed / self.total) * 100
            elapsed = time.time() - self.start_time
            estimated_total = (
                elapsed / (self.completed / self.total)
                if self.completed > 0
                else 0
            )
            remaining = estimated_total - elapsed

            click.echo(
                f"\rProgress: {self.completed}/{self.total} "
                f"({percentage:.1f}%) - "
                f"Elapsed: {elapsed:.1f}s, "
                f"Remaining: {remaining:.1f}s",
                nl=False,
                err=True,
            )

    def finish(self):
        """Finish progress indication"""
        if self.show_progress and self.total > 1:
            click.echo("", err=True)  # New line


class BatchOperationExecutor:
    """Executor for batch operations with parallel processing"""

    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers

    def execute_batch_operation(
        self,
        devices: List[str],
        operation_func: Callable[[str], NetworkOperationResult],
        operation_type: str,
        show_progress: bool = True,
        fail_fast: bool = False,
    ) -> BatchOperationResult:
        """
        Execute an operation on multiple devices in parallel

        Args:
            devices: List of device names
            operation_func: Function to execute on each device (takes device name as argument)
            operation_type: Type of operation being performed (for metadata)
            show_progress: Whether to show progress indicator
            fail_fast: Whether to stop on first failure

        Returns:
            BatchOperationResult with consistent NetworkOperationResult structure
        """
        start_time = time.time()
        results = []
        progress = ProgressIndicator(len(devices), show_progress)

        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_device = {
                    executor.submit(
                        self._execute_single_device, device, operation_func
                    ): device
                    for device in devices
                }

                # Process completed tasks
                for future in as_completed(future_to_device):
                    device = future_to_device[future]
                    try:
                        result = future.result()
                        results.append(result)
                        progress.update()

                        # Log individual results
                        if result.status == OperationStatus.SUCCESS:
                            execution_time = result.metadata.get(
                                "execution_time", 0.0
                            )
                            logger.debug(
                                "Successfully processed device %s in %.2fs",
                                device,
                                execution_time,
                            )
                        else:
                            error_msg = (
                                result.error_response.message
                                if result.error_response
                                else "Unknown error"
                            )
                            logger.warning(
                                "Failed to process device %s: %s",
                                device,
                                error_msg,
                            )

                        # Fail fast if requested and we hit an error
                        if (
                            fail_fast
                            and result.status != OperationStatus.SUCCESS
                        ):
                            # Cancel remaining futures
                            for remaining_future in future_to_device:
                                if not remaining_future.done():
                                    remaining_future.cancel()
                            break

                    except Exception as e:
                        logger.error(
                            "Unexpected error processing device %s: %s",
                            device,
                            e,
                        )
                        # Create a failed NetworkOperationResult for unexpected errors
                        error_result = self._create_error_result(
                            device,
                            operation_type,
                            f"Unexpected error: {str(e)}",
                        )
                        results.append(error_result)
                        progress.update()

        finally:
            progress.finish()

        # Calculate summary
        execution_time = time.time() - start_time
        successful = sum(
            1 for r in results if r.status == OperationStatus.SUCCESS
        )
        failed = len(results) - successful

        summary = BatchOperationSummary(
            total_devices=len(devices),
            successful=successful,
            failed=failed,
            execution_time=execution_time,
            operation_type=operation_type,
        )

        # Create batch result
        batch_result = BatchOperationResult(
            results=results,
            summary=summary,
            metadata={
                "max_workers": self.max_workers,
                "fail_fast": fail_fast,
                "show_progress": show_progress,
            },
        )

        # Log summary
        logger.info(
            "Batch operation completed: %d/%d successful (%.1f%%) in %.2fs",
            successful,
            len(devices),
            summary.success_rate,
            execution_time,
        )

        return batch_result

    def _execute_single_device(
        self,
        device_name: str,
        operation_func: Callable[[str], NetworkOperationResult],
    ) -> NetworkOperationResult:
        """Execute operation on a single device"""
        start_time = time.time()

        try:
            result = operation_func(device_name)
            execution_time = time.time() - start_time

            # Add execution time to metadata if not already present
            if "execution_time" not in result.metadata:
                result.metadata["execution_time"] = execution_time

            return result
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)

            # Create a failed NetworkOperationResult
            return self._create_error_result(
                device_name, "unknown", error_msg, execution_time
            )

    def _create_error_result(
        self,
        device_name: str,
        operation_type: str,
        error_msg: str,
        execution_time: float = 0.0,
    ) -> NetworkOperationResult:
        """Create a NetworkOperationResult for errors"""
        return NetworkOperationResult(
            device_name=device_name,
            ip_address="unknown",  # We might not have this info in error cases
            nos="unknown",
            operation_type=operation_type,
            status=OperationStatus.FAILED,
            data={},
            metadata={"execution_time": execution_time},
            error_response=ErrorResponse(
                type="execution_error", message=error_msg
            ),
        )


class DeviceListParser:
    """Parser for device lists from various sources"""

    @staticmethod
    def parse_device_list(devices_input: str) -> List[str]:
        """
        Parse device list from comma-separated string

        Args:
            devices_input: Comma-separated device names

        Returns:
            List of device names
        """
        if not devices_input:
            return []

        # Split by comma and clean up
        devices = [device.strip() for device in devices_input.split(",")]
        devices = [
            device for device in devices if device
        ]  # Remove empty strings

        return devices

    @staticmethod
    def parse_device_file(file_path: str) -> List[str]:
        """
        Parse device list from file

        Args:
            file_path: Path to file containing device names (one per line)

        Returns:
            List of device names
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                devices = []
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):  # Ignore comments
                        devices.append(line)
                return devices
        except FileNotFoundError:
            raise click.ClickException(f"Device file not found: {file_path}")
        except Exception as e:
            raise click.ClickException(
                f"Error reading device file {file_path}: {e}"
            )

    @staticmethod
    def get_all_inventory_devices() -> List[str]:
        """
        Get all devices from inventory

        Returns:
            List of all device names in inventory

        Raises:
            FileNotFoundError: If inventory file is not found or other inventory-related errors
        """
        try:
            # Get the InventoryManager instance and retrieve all device names
            manager = InventoryManager.get_instance()
            if not manager.is_initialized():
                InventoryManager.initialize()
            devices = manager.get_devices()
            return list(devices.keys())
        except FileNotFoundError:
            # Re-raise FileNotFoundError for proper inventory error handling
            raise
        except Exception as e:
            # Check if this is an inventory-related error
            error_msg = str(e).lower()
            if "inventory" in error_msg or "no inventory file" in error_msg:
                # Convert to FileNotFoundError for consistent handling
                raise FileNotFoundError(str(e)) from e
            logger.error("Error getting devices from inventory: %s", e)
            return []


def create_batch_operation_wrapper(
    operation_func: Callable[[Any], NetworkOperationResult],
    extract_device_from_ctx: Callable[[Any], str] = lambda ctx: ctx.obj.device,
):
    """
    Create a wrapper for Click commands to support batch operations

    Args:
        operation_func: The original operation function that returns NetworkOperationResult
        extract_device_from_ctx: Function to extract device name from Click context

    Returns:
        Wrapped function that supports batch operations and returns BatchOperationResult
    """

    def batch_wrapper(ctx, **kwargs):
        # Check if this is a batch operation
        devices_list = kwargs.get("devices")
        device_file = kwargs.get("device_file")
        all_devices = kwargs.get("all_devices", False)

        # Determine device list
        devices = []
        if all_devices:
            try:
                devices = DeviceListParser.get_all_inventory_devices()
                if not devices:
                    click.echo("No devices found in inventory", err=True)
                    raise click.Abort()
            except FileNotFoundError as e:
                # Handle inventory not found error gracefully using the template
                from src.cmd.templates.usage_templates import (
                    UsageTemplates,
                    InventoryUsageData,
                )

                # Build example commands
                inventory_example = "uv run gnmibuddy.py --inventory path/to/your/devices.json --all-devices command"
                env_example = "uv run gnmibuddy.py --all-devices command"

                data = InventoryUsageData(
                    inventory_example=inventory_example,
                    env_example=env_example,
                )

                formatted_message = UsageTemplates.format_inventory_error(data)
                click.echo(formatted_message, err=True)
                raise click.Abort()
        elif devices_list:
            devices = DeviceListParser.parse_device_list(devices_list)
        elif device_file:
            devices = DeviceListParser.parse_device_file(device_file)
        else:
            # Single device operation
            return operation_func(ctx, **kwargs)

        if not devices:
            click.echo("No devices specified for batch operation", err=True)
            raise click.Abort()

        # Prepare batch executor
        max_workers = getattr(ctx.obj, "max_workers", 5)
        executor = BatchOperationExecutor(max_workers=max_workers)

        # Extract operation type from the original function or command context
        operation_type = getattr(ctx.command, "name", "unknown_operation")
        if hasattr(ctx, "info_name"):
            operation_type = ctx.info_name

        # Create operation function for batch execution
        def single_device_operation(
            device_name: str,
        ) -> NetworkOperationResult:
            # Create a new context with the specific device
            new_kwargs = kwargs.copy()
            new_kwargs.pop("devices", None)
            new_kwargs.pop("device_file", None)
            new_kwargs.pop("all_devices", None)
            new_kwargs["device"] = device_name

            # Update context device
            original_device = ctx.obj.device
            ctx.obj.device = device_name

            try:
                result = operation_func(ctx, **new_kwargs)
                # Ensure we have a proper NetworkOperationResult
                if not isinstance(result, NetworkOperationResult):
                    # If the operation returns something else, we need to wrap it
                    # This is a fallback for operations that don't return NetworkOperationResult yet
                    from src.inventory.manager import InventoryManager

                    manager = InventoryManager.get_instance()
                    device_info = manager.get_device(device_name)

                    return NetworkOperationResult(
                        device_name=device_name,
                        ip_address=device_info.ip_address,
                        nos=device_info.nos,
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
            except Exception as e:
                # Create error result for any exceptions
                from src.inventory.manager import InventoryManager

                manager = InventoryManager.get_instance()
                device_info = manager.get_device(device_name)

                return NetworkOperationResult(
                    device_name=device_name,
                    ip_address=device_info.ip_address,
                    nos=device_info.nos,
                    operation_type=operation_type,
                    status=OperationStatus.FAILED,
                    data={},
                    metadata={},
                    error_response=ErrorResponse(
                        type="operation_error", message=str(e)
                    ),
                )
            finally:
                # Restore original device
                ctx.obj.device = original_device

        # Execute batch operation
        click.echo(f"Executing batch operation on {len(devices)} devices...")
        batch_result = executor.execute_batch_operation(
            devices=devices,
            operation_func=single_device_operation,
            operation_type=operation_type,
            show_progress=True,
            fail_fast=getattr(ctx.obj, "fail_fast", False),
        )

        # Display results summary
        click.echo(f"\nBatch Operation Summary:")
        click.echo(f"  Total devices: {batch_result.summary.total_devices}")
        click.echo(f"  Successful: {batch_result.summary.successful}")
        click.echo(f"  Failed: {batch_result.summary.failed}")
        click.echo(f"  Success rate: {batch_result.summary.success_rate:.1f}%")
        click.echo(f"  Total time: {batch_result.summary.execution_time:.2f}s")

        # Show failed devices if any
        failed_results = batch_result.failed_results
        if failed_results:
            click.echo(f"\nFailed devices:")
            for result in failed_results:
                error_msg = (
                    result.error_response.message
                    if result.error_response
                    else "Unknown error"
                )
                click.echo(f"  {result.device_name}: {error_msg}")

        return batch_result

    return batch_wrapper
