#!/usr/bin/env python3
"""
Inventory package.
Provides functions and classes for managing network device inventory.
"""

from typing import Optional, Union

from src.schemas.models import Device, DeviceListResult, DeviceErrorResult
from src.logging import get_logger
from .manager import InventoryManager

# Setup module logger
logger = get_logger(__name__)


def initialize_inventory(cli_path: Optional[str] = None) -> None:
    """
    Initialize the inventory module with the appropriate inventory file.

    Args:
        cli_path: Optional path provided via command-line argument
    """
    InventoryManager.initialize(cli_path)


def get_device(
    device_name: str,
) -> Union[Device, DeviceErrorResult]:
    """
    Get device information by name from the inventory.

    Args:
        device_name: Name of the device in the inventory

    Returns:
        Either the Device object if found, or DeviceErrorResult if an error occurred
    """
    return InventoryManager.get_device(device_name)


def list_available_devices() -> DeviceListResult:
    """
    List all available devices in the inventory.

    Returns:
        Dictionary with device names and their details
    """
    return InventoryManager.list_devices()
