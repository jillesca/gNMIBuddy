#!/usr/bin/env python3
"""
Simplified network command service for executing commands with standardized error handling and formatting.
"""

import json
from enum import Enum
from dataclasses import is_dataclass, asdict
from typing import Dict, Any, Protocol, runtime_checkable

import src.inventory
from src.schemas.models import Device
from src.schemas.responses import NetworkOperationResult
from src.logging.config import get_logger

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
        Formatted and serialized command results
    """
    device, success = src.inventory.get_device(device_name)

    if not success:
        logger.warning("Failed to retrieve device: %s", device_name)
        return device  # device is a dict with error info when success is False

    logger.debug("Executing command on device: %s", device_name)

    command_result = command_func(device, *args)

    # Assertion to ensure NetworkOperationResult is always returned
    assert isinstance(command_result, NetworkOperationResult), (
        f"Network command function must return NetworkOperationResult, "
        f"but got {type(command_result).__name__}. "
        f"Please ensure the network command function implements the NetworkOperationResult schema."
    )

    serializable_result = _make_serializable(command_result)
    return json.loads(json.dumps(serializable_result))


def _make_serializable(obj: Any) -> Any:
    """
    Convert dataclass objects to dictionaries for JSON serialization.
    """
    if is_dataclass(obj) and not isinstance(obj, type):
        # Convert dataclass to dict and recursively process all fields
        result = {}
        for field_name, field_value in asdict(obj).items():
            result[field_name] = _make_serializable(field_value)
        return result
    elif isinstance(obj, Enum):
        return obj.value  # Convert enum to its string value
    elif isinstance(obj, dict):
        return {key: _make_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_make_serializable(item) for item in obj]
    else:
        return obj
