#!/usr/bin/env python3
"""
Simplified network command service for executing commands with standardized error handling and formatting.
"""

from typing import Any, Protocol, runtime_checkable, Union, Optional

import src.inventory
from src.logging import get_logger
from src.schemas.responses import (
    NetworkOperationResult,
)
from src.schemas.models import Device, DeviceErrorResult, NetworkOS
from src.schemas.responses import ErrorResponse, OperationStatus

logger = get_logger(__name__)


@runtime_checkable
class NetworkCommand(Protocol):
    """Protocol defining what a network command function should look like"""

    def __call__(
        self, device: Optional[Device] = None, *args: Any
    ) -> NetworkOperationResult: ...


@runtime_checkable
class NetworkCommandNoDevice(Protocol):
    """Protocol for network commands that don't require a device"""

    def __call__(self, *args: Any) -> NetworkOperationResult: ...


def run(
    device_name: Optional[str],
    command_func: Union[NetworkCommand, NetworkCommandNoDevice],
    *args: Any,
) -> NetworkOperationResult:
    """
    Execute a network command with standardized error handling and formatting.

    This function handles device retrieval, command execution, and result formatting
    in a consistent way for all network operations.

    Args:
        device_name: Name of the device in inventory (None for network-wide operations)
        command_func: Network command function to execute
        *args: Arguments to pass to the command function

    Returns:
        NetworkOperationResult: The result of the network operation
    """
    logger.debug(
        "Running command %s for device: %s, args: %s",
        (
            command_func.__name__
            if hasattr(command_func, "__name__")
            else "unknown"
        ),
        device_name,
        str(args),
    )

    # Handle network-wide operations that don't need a device
    if device_name is None:
        logger.debug("Executing network-wide command")
        command_result = command_func(*args)
        logger.debug(
            "Network-wide command result type: %s, status: %s",
            type(command_result).__name__,
            getattr(command_result, "status", "N/A"),
        )

        assert isinstance(command_result, NetworkOperationResult), (
            f"Network command function must return NetworkOperationResult, "
            f"but got {type(command_result).__name__}. "
            f"Please ensure the network command function implements the NetworkOperationResult schema."
        )

        return command_result

    # Handle device-specific operations
    logger.debug("Getting device %s from inventory", device_name)
    device = src.inventory.get_device(device_name)

    if isinstance(device, DeviceErrorResult):
        logger.warning("Failed to retrieve device: %s", device_name)
        logger.debug("Device error details: %s", device.msg)

        # Return NetworkOperationResult for device errors
        error_response = ErrorResponse(
            type="DEVICE_ERROR",
            message=device.msg,
        )
        return NetworkOperationResult(
            device_name=device_name,
            ip_address="unknown",
            nos=NetworkOS.UNKNOWN,
            operation_type="device_retrieval",
            status=OperationStatus.FAILED,
            error_response=error_response,
            metadata={"error_type": "device_not_found"},
        )

    logger.debug(
        "Successfully retrieved device %s (%s, %s)",
        device_name,
        device.ip_address,
        device.nos,
    )
    logger.debug("Executing command on device: %s", device_name)

    command_result = command_func(device, *args)
    logger.debug(
        "Device command result type: %s, status: %s",
        type(command_result).__name__,
        getattr(command_result, "status", "N/A"),
    )

    assert isinstance(command_result, NetworkOperationResult), (
        f"Network command function must return NetworkOperationResult, "
        f"but got {type(command_result).__name__}. "
        f"Please ensure the network command function implements the NetworkOperationResult schema."
    )

    logger.debug("Command execution completed for device %s", device_name)
    return command_result


def run_network_wide(
    command_func: NetworkCommandNoDevice, *args: Any
) -> NetworkOperationResult:
    """
    Execute a network-wide command that doesn't require a specific device.

    This is a convenience function for network-wide operations.

    Args:
        command_func: Network command function to execute
        *args: Arguments to pass to the command function

    Returns:
        NetworkOperationResult: The result of the network operation
    """
    logger.debug(
        "Running network-wide command %s with args: %s",
        (
            command_func.__name__
            if hasattr(command_func, "__name__")
            else "unknown"
        ),
        str(args),
    )

    result = run(None, command_func, *args)
    logger.debug(
        "Network-wide command completed with status: %s",
        getattr(result, "status", "N/A"),
    )

    return result
