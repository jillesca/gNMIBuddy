#!/usr/bin/env python3
"""
Device and inventory models for gNMIBuddy.

Contains data models for representing network devices and related
inventory structures used throughout the application.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Union


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
        username: Authentication username
        password: Authentication password
        path_cert: Path to client certificate file (optional)
        path_key: Path to client private key file (optional)
        path_root: Path to root CA certificate file (optional)
        override: Override server name for certificate validation (optional)
        skip_verify: Skip certificate verification (defaults to False)
        gnmi_timeout: Timeout for gNMI requests in seconds (defaults to 5)
        grpc_options: List of gRPC options (optional)
        show_diff: Show differences in responses (optional)
    """

    name: str = ""
    ip_address: str = ""
    port: int = 830
    nos: str = ""
    username: str = ""
    password: str = ""
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
        return {
            "name": self.name,
            "ip_address": self.ip_address,
            "port": self.port,
            "nos": self.nos,
        }
