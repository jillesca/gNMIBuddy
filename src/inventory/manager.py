#!/usr/bin/env python3
"""
Inventory manager module.
Manages device inventory with a singleton pattern.
"""

import logging
from typing import Dict, Optional, Tuple, Union

from .file_handler import get_inventory_path, load_inventory
from src.schemas.models import Device, DeviceListResult, DeviceErrorResult

# Setup module logger
logger = logging.getLogger(__name__)


class InventoryManager:
    """Manages device inventory with a singleton-like pattern."""

    _instance: Optional["InventoryManager"] = None
    _devices: Dict[str, Device] = {}
    _initialized: bool = False

    @classmethod
    def get_instance(cls) -> "InventoryManager":
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = InventoryManager()
            # logger.debug("Created new InventoryManager instance")
        return cls._instance

    @classmethod
    def initialize(cls, cli_path: Optional[str] = None) -> None:
        """Initialize the inventory with the specified path."""
        instance = cls.get_instance()
        if not instance.is_initialized() or cli_path is not None:
            inventory_path = get_inventory_path(cli_path)
            logger.info(f"Initializing inventory from path: {inventory_path}")
            instance.set_devices(load_inventory(inventory_path))
            instance.set_initialized(True)
            device_count = len(instance.get_devices())
            logger.debug(f"Initialized inventory with {device_count} devices")
            if logger.isEnabledFor(logging.DEBUG):
                device_names = list(instance.get_devices().keys())
                logger.debug(f"Loaded devices: {device_names}")

    @classmethod
    def get_device(
        cls, device_name: str
    ) -> Tuple[Union[Device, DeviceErrorResult], bool]:
        """
        Get device by name from the initialized inventory.

        Args:
            device_name: Name of the device to retrieve

        Returns:
            Tuple containing either the Device object or an error dict,
            along with a boolean indicating success
        """
        # logger.debug(f"Looking up device: {device_name}")
        instance = cls.get_instance()
        if not instance.is_initialized():
            logger.debug("Inventory not initialized, initializing now")
            cls.initialize()

        devices = instance.get_devices()
        if not devices:
            error_msg = "No inventory file specified or the inventory is empty. Please provide a path via --inventory option or set the NETWORK_INVENTORY environment variable."
            logger.warning(error_msg)
            return (
                DeviceErrorResult(error=error_msg, device_info=None),
                False,
            )

        if device_name not in devices:
            logger.warning(f"Device '{device_name}' not found in inventory")
            return (
                DeviceErrorResult(
                    error=f"Device '{device_name}' not found in inventory",
                    device_info=None,
                ),
                False,
            )

        # logger.debug(
        #     f"Found device: {device_name}, IP: {devices[device_name].ip_address}"
        # )
        return (devices[device_name], True)

    @classmethod
    def list_devices(cls) -> DeviceListResult:
        """
        List all available devices in the inventory.

        Returns:
            Dictionary with a "devices" key containing a list of device info
        """
        # logger.debug("Listing all devices in inventory")
        instance = cls.get_instance()
        if not instance.is_initialized():
            logger.debug("Inventory not initialized, initializing now")
            cls.initialize()

        devices = instance.get_devices()
        if not devices:
            logger.warning("No devices found in inventory")
            return DeviceListResult(devices=[])

        device_list = [device.to_device_info() for device in devices.values()]
        # logger.info(f"Listed {len(device_list)} devices from inventory")
        return DeviceListResult(devices=device_list)

    def is_initialized(self) -> bool:
        """Check if the inventory is initialized."""
        return self._initialized

    def set_initialized(self, value: bool) -> None:
        """Set the initialization status."""
        self._initialized = value

    def get_devices(self) -> Dict[str, Device]:
        """Get the devices dictionary."""
        return self._devices

    def set_devices(self, devices: Dict[str, Device]) -> None:
        """Set the devices dictionary."""
        self._devices = devices
