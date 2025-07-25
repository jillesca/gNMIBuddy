#!/usr/bin/env python3
"""
Inventory manager module.
Manages device inventory with a singleton pattern.
"""

from typing import Dict, Optional, Union

from src.logging import get_logger
from src.schemas.models import Device, DeviceListResult, DeviceErrorResult

from .file_handler import get_inventory_path, load_inventory

# Setup module logger
logger = get_logger(__name__)


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
            logger.debug(
                "Initializing inventory from path: %s", inventory_path
            )
            instance.set_devices(load_inventory(inventory_path))
            instance.set_initialized(True)
            device_count = len(instance.get_devices())
            logger.debug("Initialized inventory with %s devices", device_count)
            if logger.isEnabledFor(10):
                device_names = list(instance.get_devices().keys())
                logger.debug("Loaded devices: %s", device_names)

    @classmethod
    def get_device(cls, device_name: str) -> Union[Device, DeviceErrorResult]:
        """
        Get device by name from the initialized inventory.

        Args:
            device_name: Name of the device to retrieve

        Returns:
            Either the Device object if found, or DeviceErrorResult if an error occurred
        """
        # logger.debug("Looking up device: %s", device_name)
        instance = cls.get_instance()
        if not instance.is_initialized():
            logger.debug("Inventory not initialized, initializing now")
            cls.initialize()

        devices = instance.get_devices()
        if not devices:
            error_msg = "No inventory file specified or the inventory is empty. Please provide a path via --inventory option or set the NETWORK_INVENTORY environment variable."
            logger.warning(error_msg)
            return DeviceErrorResult(msg=error_msg, device_info=None)

        if device_name not in devices:
            logger.warning("Device '%s' not found in inventory", device_name)
            return DeviceErrorResult(
                msg=f"Device '{device_name}' not found in inventory",
                device_info=None,
            )

        # logger.debug(
        #     f"Found device: {device_name}, IP: {devices[device_name].ip_address}"
        # )
        return devices[device_name]

    @classmethod
    def list_devices(cls) -> DeviceListResult:
        """
        List all available devices in the inventory.

        Returns:
            DeviceListResult containing a list of Device objects
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

        device_list = list(devices.values())
        # logger.info("Listed %s devices from inventory", len(device_list))
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
