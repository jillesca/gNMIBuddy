#!/usr/bin/env python3
"""
Simplified network command service for executing commands with standardized error handling and formatting.
"""

import json
import logging
from typing import Dict, Any, Protocol, runtime_checkable, Union, List

import src.inventory
from src.inventory.models import Device
from src.gnmi.responses import NetworkResponse
from src.network_tools.responses import NetworkToolsResponse

logger = logging.getLogger(__name__)


@runtime_checkable
class NetworkCommand(Protocol):
    """Protocol defining what a network command function should look like"""

    def __call__(self, device: Device, *args: Any) -> Union[
        Dict[str, Any],
        NetworkResponse,
        NetworkToolsResponse,
        List[NetworkToolsResponse],
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
        return device

    logger.debug(f"Executing command on device: {device_name}")

    command_result = command_func(device, *args)

    # Handle different types of responses
    if isinstance(command_result, list):
        # If the result is a list (like from routing_info), convert each item
        serialized_results = []
        for item in command_result:
            if hasattr(item, "to_dict") and callable(item.to_dict):
                serialized_results.append(item.to_dict())
            else:
                serialized_results.append(item)
        command_result = serialized_results
    elif hasattr(command_result, "to_dict") and callable(
        command_result.to_dict
    ):
        # If the result has a to_dict method (like our response objects), use it
        command_result = command_result.to_dict()

    result = {
        "device": device.name,
        "ip_address": device.ip_address,
        "nos": device.nos,
        "response": command_result,
    }

    return json.loads(json.dumps(result))
