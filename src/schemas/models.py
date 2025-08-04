#!/usr/bin/env python3
"""
Device and inventory models for gNMIBuddy.

Contains data models for representing network devices and related
inventory structures used throughout the application.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Union


class NetworkOS(Enum):
    """Supported Network Operating Systems"""

    IOSXR = "iosxr"


@dataclass
class DeviceListResult:
    """Result class for device list operations."""

    devices: List["Device"]


@dataclass
class DeviceListCommandResult:
    """Result class for device list command output."""

    devices: Union[List["Device"], List[str]]
    count: int
    detail: bool
    message: Optional[str] = None


@dataclass
class DeviceErrorResult:
    """Result class for device error conditions."""

    msg: str
    nos: str = "unknown"
    ip_address: str = "unknown"
    device_info: Optional[Dict[str, Any]] = None


@dataclass
class Device:
    """
    Device representation with all attributes from src.inventory.

    Attributes:
        name: Device hostname or identifier
        ip_address: IP address for device management
        port: Port number for device connections
        nos: Network Operating System identifier
        username: Authentication username (optional, required if not using certificates)
        password: Authentication password (optional, required if not using certificates)
        path_cert: Path to client certificate file (optional, required if not using username/password)
        path_key: Path to client private key file (optional, required if not using username/password)
        path_root: Path to root CA certificate file (optional)
        override: Override server name for certificate validation (optional)
        skip_verify: Skip certificate verification (defaults to False)
        gnmi_timeout: Timeout for gNMI requests in seconds (defaults to 5)
        grpc_options: List of gRPC options (optional)
        show_diff: Show differences in responses (optional)
        insecure: Use insecure connection (defaults to True)

    Authentication:
        gNMI clients require authentication. Two methods are supported:
        1. Username/Password: Provide both 'username' and 'password' fields
        2. Certificate-based: Provide both 'path_cert' and 'path_key' fields
        At least one authentication method must be configured.
    """

    name: str = ""
    ip_address: str = ""
    port: int = 830
    nos: NetworkOS = NetworkOS.IOSXR
    username: Optional[str] = None
    password: Optional[str] = None
    path_cert: Optional[str] = None
    path_key: Optional[str] = None
    path_root: Optional[str] = None
    override: Optional[str] = None
    skip_verify: bool = False
    gnmi_timeout: int = 5
    grpc_options: Optional[list] = None
    show_diff: Optional[str] = None
    insecure: bool = True

    def to_device_info(self) -> Dict[str, Any]:
        """
        Convert Device to device info dictionary, excluding sensitive information.

        Returns:
            Dictionary with non-sensitive device information
        """
        # Handle both enum and string values for backward compatibility
        nos_value = (
            self.nos.value if isinstance(self.nos, NetworkOS) else self.nos
        )

        return {
            "name": self.name,
            "ip_address": self.ip_address,
            "port": self.port,
            "nos": nos_value,
        }

    def to_device_info_safe(self) -> "Device":
        """
        Convert Device to a sanitized Device object with sensitive fields redacted.

        This method creates a new Device instance with sensitive authentication
        information redacted for safe exposure to external consumers.

        Returns:
            Device object with sensitive fields redacted using "***"
        """
        redaction_marker = "***"

        return Device(
            name=self.name,
            ip_address=self.ip_address,
            port=self.port,
            nos=self.nos,
            username=self.username,  # Keep username for identification
            password=redaction_marker if self.password else self.password,
            path_cert=redaction_marker if self.path_cert else self.path_cert,
            path_key=redaction_marker if self.path_key else self.path_key,
            path_root=self.path_root,  # Not sensitive (public CA)
            override=self.override,
            skip_verify=self.skip_verify,
            gnmi_timeout=self.gnmi_timeout,
            grpc_options=self.grpc_options,
            show_diff=self.show_diff,
            insecure=self.insecure,
        )

    def to_device_info_with_auth(self) -> "Device":
        """
        Convert Device to a complete Device object including sensitive authentication fields.

        This method returns a copy of the device with all authentication information
        intact for internal use where sensitive data access is required.

        Returns:
            Device object with all fields including sensitive authentication data
        """
        return Device(
            name=self.name,
            ip_address=self.ip_address,
            port=self.port,
            nos=self.nos,
            username=self.username,
            password=self.password,
            path_cert=self.path_cert,
            path_key=self.path_key,
            path_root=self.path_root,
            override=self.override,
            skip_verify=self.skip_verify,
            gnmi_timeout=self.gnmi_timeout,
            grpc_options=self.grpc_options,
            show_diff=self.show_diff,
            insecure=self.insecure,
        )
