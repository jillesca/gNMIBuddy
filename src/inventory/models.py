#!/usr/bin/env python3
"""
Models module for inventory items.
Contains dataclasses for representing network devices.
"""

from dataclasses import dataclass
from typing import Optional, List, TypedDict


class DeviceInfo(TypedDict):
    """Type definition for device information dictionary.

    Contains non-sensitive device information that is safe to expose.
    This is a subset of the Device dataclass fields.
    """

    name: str
    ip_address: str
    port: int
    nos: str


class DeviceListResult(TypedDict):
    """Type definition for the device list result."""

    devices: List[DeviceInfo]


class DeviceErrorResult(TypedDict):
    """Type definition for device error result.

    Enhanced to include device context when available.
    """

    error: str
    device_info: Optional[DeviceInfo]


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
