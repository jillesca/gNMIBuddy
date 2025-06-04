#!/usr/bin/env python3
"""
Inventory package.
Provides functions and classes for managing network device inventory.
"""

import logging
from typing import List, Optional, Tuple, Union, TypedDict

from .models import Device
from .manager import InventoryManager

# Setup module logger
logger = logging.getLogger(__name__)


# Type definitions for improved type safety
class DeviceInfo(TypedDict):
    """Type definition for device information dictionary."""

    name: str
    ip_address: str
    port: int


class DeviceListResult(TypedDict):
    """Type definition for the device list result."""

    devices: List[DeviceInfo]


class DeviceErrorResult(TypedDict):
    """Type definition for device error result."""

    error: str


def initialize_inventory(cli_path: Optional[str] = None) -> None:
    """
    Initialize the inventory module with the appropriate inventory file.

    Args:
        cli_path: Optional path provided via command-line argument
    """
    # logger.info(
    #     f"Initializing inventory with CLI path: {cli_path or 'default'}"
    # )
    InventoryManager.initialize(cli_path)


def get_device(
    device_name: str,
) -> Tuple[Union[Device, DeviceErrorResult], bool]:
    """
    Get device information by name from the inventory.

    Args:
        device_name: Name of the device in the inventory

    Returns:
        Tuple of (device_info, success_flag)
        If device is found, returns (device_info, True)
        If device is not found, returns ({"error": error_message}, False)
    """
    # logger.debug(f"Getting device from inventory: {device_name}")
    return InventoryManager.get_device(device_name)


def list_available_devices() -> DeviceListResult:
    """
    List all available devices in the inventory.

    Returns:
        Dictionary with device names and their details
    """
    logger.debug("Listing all available devices")
    return InventoryManager.list_devices()
