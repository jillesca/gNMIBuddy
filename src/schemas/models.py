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

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


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
