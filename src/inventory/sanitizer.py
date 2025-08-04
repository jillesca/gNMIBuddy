#!/usr/bin/env python3
"""
Device data sanitization module.

Provides sanitization capabilities for device data to remove sensitive
authentication information when exposing device lists to external consumers
such as CLI commands and MCP servers.
"""

from typing import List
from src.schemas.models import Device, DeviceListResult
from src.logging import get_logger

# Setup module logger
logger = get_logger(__name__)


class DeviceDataSanitizer:
    """
    Handles sanitization of device data to remove sensitive authentication information.

    This class provides different levels of data sanitization while maintaining
    proper class-based data structures. It follows the single responsibility
    principle and provides a clean interface for future extensibility.
    """

    def __init__(self):
        """Initialize the sanitizer with default configuration."""
        self._redaction_marker = "***"
        logger.debug(
            "Initialized DeviceDataSanitizer with redaction marker: %s",
            self._redaction_marker,
        )

    def sanitize_device(self, device: Device) -> Device:
        """
        Create a sanitized copy of a device with sensitive fields redacted.

        Args:
            device: The original Device object to sanitize

        Returns:
            A new Device object with sensitive fields redacted
        """
        logger.debug("Sanitizing device: %s", device.name)

        # Create a copy of the device with sensitive fields redacted
        sanitized_device = Device(
            name=device.name,
            ip_address=device.ip_address,
            port=device.port,
            nos=device.nos,
            username=device.username,  # Keep username for identification
            password=(
                self._redaction_marker if device.password else device.password
            ),
            path_cert=(
                self._redaction_marker
                if device.path_cert
                else device.path_cert
            ),
            path_key=(
                self._redaction_marker if device.path_key else device.path_key
            ),
            path_root=device.path_root,  # Not sensitive (public CA)
            override=device.override,
            skip_verify=device.skip_verify,
            gnmi_timeout=device.gnmi_timeout,
            grpc_options=device.grpc_options,
            show_diff=device.show_diff,
            insecure=device.insecure,
        )

        logger.debug(
            "Sanitized device %s - redacted %d sensitive fields",
            device.name,
            sum(
                [
                    1
                    for field in [
                        device.password,
                        device.path_cert,
                        device.path_key,
                    ]
                    if field
                ]
            ),
        )

        return sanitized_device

    def sanitize_device_list(self, devices: List[Device]) -> List[Device]:
        """
        Sanitize a list of devices by redacting sensitive fields from each device.

        Args:
            devices: List of Device objects to sanitize

        Returns:
            List of sanitized Device objects
        """
        logger.debug("Sanitizing device list with %d devices", len(devices))

        sanitized_devices = [
            self.sanitize_device(device) for device in devices
        ]

        logger.debug(
            "Successfully sanitized %d devices", len(sanitized_devices)
        )
        return sanitized_devices

    def sanitize_device_list_result(
        self, device_list_result: DeviceListResult
    ) -> DeviceListResult:
        """
        Sanitize a DeviceListResult by redacting sensitive fields from all contained devices.

        Args:
            device_list_result: DeviceListResult object to sanitize

        Returns:
            New DeviceListResult with sanitized devices
        """
        logger.debug(
            "Sanitizing DeviceListResult with %d devices",
            len(device_list_result.devices),
        )

        sanitized_devices = self.sanitize_device_list(
            device_list_result.devices
        )
        sanitized_result = DeviceListResult(devices=sanitized_devices)

        logger.debug("Successfully created sanitized DeviceListResult")
        return sanitized_result

    def get_redaction_marker(self) -> str:
        """
        Get the current redaction marker used for sensitive field replacement.

        Returns:
            The redaction marker string
        """
        return self._redaction_marker

    def set_redaction_marker(self, marker: str) -> None:
        """
        Set a custom redaction marker for sensitive field replacement.

        Args:
            marker: The new redaction marker to use
        """
        logger.debug(
            "Changing redaction marker from '%s' to '%s'",
            self._redaction_marker,
            marker,
        )
        self._redaction_marker = marker
