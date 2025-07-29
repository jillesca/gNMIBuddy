#!/usr/bin/env python3
"""
Inventory manager module.
Manages device inventory with a singleton pattern.
"""

from typing import Dict, Optional, Union
import sys

from src.logging import get_logger
from src.schemas.models import Device, DeviceListResult, DeviceErrorResult
from src.schemas.responses import ValidationStatus, ValidationResult

from .file_handler import get_inventory_path, load_inventory
from .validator import InventoryValidator

# Setup module logger
logger = get_logger(__name__)


def _display_validation_errors_detailed(result: ValidationResult) -> None:
    """
    Display validation errors in user-friendly format with detailed layout.

    This function provides the same formatting as the inventory validate command
    to ensure consistent user experience across automatic and manual validation.

    Args:
        result: ValidationResult object containing errors to display
    """
    print("\n" + "=" * 50)
    print("Inventory Validation Failed")
    print("=" * 50)
    print(f"File: {result.file_path}")
    print(f"Total Devices: {result.total_devices}")
    print(f"Valid Devices: {result.valid_devices}")
    print(f"Invalid Devices: {result.invalid_devices}")
    print()
    print("❌ Validation failed with the following errors:")
    print("-------")

    for error in result.errors:
        # Format error message based on whether it's device-specific or file-level
        if error.device_name:
            error_line = f"Device {error.device_name}"
            if error.device_index is not None:
                error_line += f" [index: {error.device_index}]"
            if error.field:
                error_line += f" (field: {error.field})"
            error_line += f": {error.message}"
        else:
            error_line = f"File-level error: {error.message}"

        print(error_line)

        if error.suggestion:
            print(f"  → Suggestion: {error.suggestion}")
        print()

    print(
        "💡 For detailed validation analysis, use: 'gnmibuddy inventory validate'"
    )
    print("=" * 50)


class InventoryManager:
    """Manages device inventory with a singleton-like pattern."""

    _instance: Optional["InventoryManager"] = None
    _devices: Dict[str, Device] = {}
    _initialized: bool = False

    def _display_validation_errors_wrapper(
        self, validation_result: ValidationResult
    ) -> None:
        """Display validation errors using the detailed formatting function."""
        # Use the standalone function for consistent formatting
        _display_validation_errors_detailed(validation_result)

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
            try:
                inventory_path = get_inventory_path(cli_path)
            except (FileNotFoundError, RuntimeError) as e:
                logger.error(f"Cannot initialize InventoryManager: {e}")
                sys.exit(1)

            logger.debug(
                "Initializing inventory from path: %s", inventory_path
            )

            # Validate inventory file before loading
            logger.debug("Validating inventory file before initialization")

            validator = InventoryValidator()
            try:
                validation_result = validator.validate_inventory_file(
                    inventory_path
                )
            except FileNotFoundError as e:
                # Handle file not found with user-friendly message
                print(f"\n❌ Inventory file not found")
                print("=" * 50)
                print(f"File: {inventory_path}")
                print(f"Error: {str(e)}")
                print("\n💡 How to fix this:")
                print("  1. Check that the file path is correct")
                print("  2. Ensure the file exists")
                if cli_path:
                    print(f"  3. You specified: --inventory {cli_path}")
                else:
                    print("  3. Set NETWORK_INVENTORY environment variable")
                print("=" * 50)
                sys.exit(1)

            if validation_result.status == ValidationStatus.FAILED:
                # Display user-friendly error messages
                _display_validation_errors_detailed(validation_result)
                sys.exit(1)

            logger.debug(
                "Inventory validation passed: %d/%d devices valid",
                validation_result.valid_devices,
                validation_result.total_devices,
            )

            try:
                instance.set_devices(load_inventory(inventory_path))
            except FileNotFoundError as e:
                # This shouldn't happen after validation, but just in case
                print(f"\n❌ Error loading inventory: {e}")
                sys.exit(1)

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
