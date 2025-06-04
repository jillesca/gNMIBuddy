#!/usr/bin/env python3
"""
Inventory manager module.
Manages device inventory with a singleton pattern.
"""

import logging
from typing import Dict, Optional, Tuple, Union, List, TypedDict

from .models import Device
from .file_handler import get_inventory_path, load_inventory

# Setup module logger
logger = logging.getLogger(__name__)


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
            logger.info(f"Initialized inventory with {device_count} devices")
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
            return ({"error": error_msg}, False)

        if device_name not in devices:
            logger.warning(f"Device '{device_name}' not found in inventory")
            return (
                {"error": f"Device '{device_name}' not found in inventory"},
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
            return {
                "devices": [],
                "message": "No inventory file specified or the inventory is empty. Please provide a path via --inventory option or set the NETWORK_INVENTORY environment variable.",
            }

        device_list = [
            {
                "name": name,
                "ip_address": device.ip_address,
                "port": device.port,
                "nos": device.nos,
            }
            for name, device in devices.items()
        ]
        # logger.info(f"Listed {len(device_list)} devices from inventory")
        return {"devices": device_list}

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
