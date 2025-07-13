#!/usr/bin/env python3
"""
Simplified network command service for executing commands with standardized error handling and formatting.
"""

import json
import logging
from dataclasses import is_dataclass, asdict
from typing import Dict, Any, Protocol, runtime_checkable, Union, List

import src.inventory
from src.inventory.models import Device

logger = logging.getLogger(__name__)


@runtime_checkable
class NetworkCommand(Protocol):
    """Protocol defining what a network command function should look like"""

    def __call__(self, device: Device, *args: Any) -> Union[
        Dict[str, Any],
        List[Dict[str, Any]],
    ]: ...


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
        logger.warning(f"Failed to retrieve device: {device_name}")
        return device  # device is a dict with error info when success is False

    logger.debug(f"Executing command on device: {device_name}")

    command_result = command_func(device, *args)

    result = {
        "device": device.name,
        "ip_address": device.ip_address,
        "nos": device.nos,
        "response": command_result,
    }

    serializable_result = _make_serializable(result)
    return json.loads(json.dumps(serializable_result))


def _make_serializable(obj: Any) -> Any:
    """
    Convert dataclass objects to dictionaries for JSON serialization.
    """
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    elif isinstance(obj, dict):
        return {key: _make_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_make_serializable(item) for item in obj]
    else:
        return obj
