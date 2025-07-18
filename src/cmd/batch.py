#!/usr/bin/env python3
"""Batch operations support for CLI commands with parallel execution"""
import asyncio
import time
from typing import List, Dict, Any, Callable, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import click
from src.logging.config import get_logger
from src.inventory.manager import InventoryManager

logger = get_logger(__name__)


@dataclass
class BatchResult:
    """Result of a batch operation on a single device"""

    device_name: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0


@dataclass
class BatchOperationSummary:
    """Summary of a complete batch operation"""

    total_devices: int
    successful: int
    failed: int
    execution_time: float
    results: List[BatchResult]

    @property
    def success_rate(self) -> float:
        """Calculate success rate as a percentage"""
        if self.total_devices == 0:
            return 0.0
        return (self.successful / self.total_devices) * 100


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
        operation_func: Callable[[str], Any],
        show_progress: bool = True,
        fail_fast: bool = False,
    ) -> BatchOperationSummary:
        """
        Execute an operation on multiple devices in parallel

        Args:
            devices: List of device names
            operation_func: Function to execute on each device (takes device name as argument)
            show_progress: Whether to show progress indicator
            fail_fast: Whether to stop on first failure

        Returns:
            BatchOperationSummary with results
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
                        if result.success:
                            logger.debug(
                                "Successfully processed device %s in %.2fs",
                                device,
                                result.execution_time,
                            )
                        else:
                            logger.warning(
                                "Failed to process device %s: %s",
                                device,
                                result.error,
                            )

                        # Fail fast if requested and we hit an error
                        if fail_fast and not result.success:
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
                        results.append(
                            BatchResult(
                                device_name=device,
                                success=False,
                                error=f"Unexpected error: {str(e)}",
                            )
                        )
                        progress.update()

        finally:
            progress.finish()

        # Calculate summary
        execution_time = time.time() - start_time
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful

        summary = BatchOperationSummary(
            total_devices=len(devices),
            successful=successful,
            failed=failed,
            execution_time=execution_time,
            results=results,
        )

        # Log summary
        logger.info(
            "Batch operation completed: %d/%d successful (%.1f%%) in %.2fs",
            successful,
            len(devices),
            summary.success_rate,
            execution_time,
        )

        return summary

    def _execute_single_device(
        self, device_name: str, operation_func: Callable[[str], Any]
    ) -> BatchResult:
        """Execute operation on a single device"""
        start_time = time.time()

        try:
            result_data = operation_func(device_name)
            execution_time = time.time() - start_time

            return BatchResult(
                device_name=device_name,
                success=True,
                data=result_data,
                execution_time=execution_time,
            )
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)

            return BatchResult(
                device_name=device_name,
                success=False,
                error=error_msg,
                execution_time=execution_time,
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
            with open(file_path, "r") as f:
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
        """
        try:
            # Get the InventoryManager instance and retrieve all device names
            manager = InventoryManager.get_instance()
            if not manager.is_initialized():
                InventoryManager.initialize()
            devices = manager.get_devices()
            return list(devices.keys())
        except Exception as e:
            logger.error("Error getting devices from inventory: %s", e)
            return []


def create_batch_operation_wrapper(
    operation_func: Callable[[Any], Any],
    extract_device_from_ctx: Callable[[Any], str] = lambda ctx: ctx.obj.device,
):
    """
    Create a wrapper for Click commands to support batch operations

    Args:
        operation_func: The original operation function
        extract_device_from_ctx: Function to extract device name from Click context

    Returns:
        Wrapped function that supports batch operations
    """

    def batch_wrapper(ctx, **kwargs):
        # Check if this is a batch operation
        devices_list = kwargs.get("devices")
        device_file = kwargs.get("device_file")
        all_devices = kwargs.get("all_devices", False)

        # Determine device list
        devices = []
        if all_devices:
            devices = DeviceListParser.get_all_inventory_devices()
            if not devices:
                click.echo("No devices found in inventory", err=True)
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

        # Create operation function for batch execution
        def single_device_operation(device_name: str):
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
                return operation_func(ctx, **new_kwargs)
            finally:
                # Restore original device
                ctx.obj.device = original_device

        # Execute batch operation
        click.echo(f"Executing batch operation on {len(devices)} devices...")
        summary = executor.execute_batch_operation(
            devices=devices,
            operation_func=single_device_operation,
            show_progress=True,
        )

        # Display results summary
        click.echo(f"\nBatch Operation Summary:")
        click.echo(f"  Total devices: {summary.total_devices}")
        click.echo(f"  Successful: {summary.successful}")
        click.echo(f"  Failed: {summary.failed}")
        click.echo(f"  Success rate: {summary.success_rate:.1f}%")
        click.echo(f"  Total time: {summary.execution_time:.2f}s")

        # Show failed devices if any
        failed_devices = [r for r in summary.results if not r.success]
        if failed_devices:
            click.echo(f"\nFailed devices:")
            for result in failed_devices:
                click.echo(f"  {result.device_name}: {result.error}")

        return summary

    return batch_wrapper


# Global batch executor instance
batch_executor = BatchOperationExecutor()


def add_batch_options(func):
    """
    Decorator to add batch operation options to Click commands

    This decorator adds the following options:
    - --devices: Comma-separated list of devices
    - --device-file: Path to file containing device names
    - --all-devices: Run on all devices in inventory
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

    return func
