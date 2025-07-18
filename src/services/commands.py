#!/usr/bin/env python3
"""
Simplified network command service for executing commands with standardized error handling and formatting.
"""

from typing import Dict, Any, Protocol, runtime_checkable

import src.inventory
from src.schemas.models import Device
from src.logging.config import get_logger
from src.schemas.responses import NetworkOperationResult

logger = get_logger(__name__)


@runtime_checkable
class NetworkCommand(Protocol):
    """Protocol defining what a network command function should look like"""

    def __call__(
        self, device: Device, *args: Any
    ) -> NetworkOperationResult: ...


def run(
    device_name: str, command_func: NetworkCommand, *args: Any
) -> Dict[str, Any]:
    """
    Execute a network command with standardized error handling and formatting.

    This function handles device retrieval, command execution, and result formatting
    in a consistent way for all network operations.

    Args:
        device_name: Name of the device in inventory
        command_func: Network command function to execute
        *args: Arguments to pass to the command function

    Returns:
        NetworkOperationResult: The result of the network operation
    """
    device, success = src.inventory.get_device(device_name)

    if not success:
        logger.warning("Failed to retrieve device: %s", device_name)
        return device

    logger.debug("Executing command on device: %s", device_name)

    command_result = command_func(device, *args)

    assert isinstance(command_result, NetworkOperationResult), (
        f"Network command function must return NetworkOperationResult, "
        f"but got {type(command_result).__name__}. "
        f"Please ensure the network command function implements the NetworkOperationResult schema."
    )

    return command_result
