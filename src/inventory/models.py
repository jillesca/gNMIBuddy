#!/usr/bin/env python3
"""
Models module for inventory items.
Contains dataclasses for representing network devices.
"""

from dataclasses import dataclass
from typing import Dict, Any


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
    """

    name: str
    ip_address: str
    port: int
    nos: str
    username: str
    password: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Device":
        """
        Create a Device object from a dictionary.

        Args:
            data: Dictionary containing device attributes

        Returns:
            A new Device instance with attributes from the dictionary
        """
        return cls(**data)
