#!/usr/bin/env python3
"""Individual command definitions for CLI organization"""

from enum import Enum
from typing import Optional, List


class Command(Enum):
    """Enumeration of individual commands with their details"""

    # Device commands
    DEVICE_INFO = ("info", "Get system information from a network device")
    DEVICE_PROFILE = ("profile", "Get device profile and role information")
    DEVICE_LIST = ("list", "List all available devices in the inventory")

    # Network commands
    NETWORK_ROUTING = (
        "routing",
        "Get routing protocol information (BGP, ISIS, OSPF)",
    )
    NETWORK_INTERFACE = ("interface", "Get interface status and configuration")
    NETWORK_MPLS = ("mpls", "Get MPLS forwarding and label information")
    NETWORK_VPN = ("vpn", "Get VPN/VRF configuration and status")

    # Topology commands
    TOPOLOGY_NEIGHBORS = (
        "neighbors",
        "Get direct neighbor information via LLDP/CDP",
    )
    TOPOLOGY_NETWORK = (
        "network",
        "Get complete network topology information. Queries all devices in inventory.",
    )

    # Operations commands
    OPS_LOGS = ("logs", "Retrieve and filter device logs")
    OPS_VALIDATE = (
        "validate",
        "Validate all collector functions (development tool)",
    )

    # Inventory commands
    INVENTORY_VALIDATE = (
        "validate",
        "Validate inventory file format and schema",
    )

    def __init__(self, command_name: str, description: str):
        self.command_name = command_name
        self.description = description

    @classmethod
    def get_by_name(cls, command_name: str) -> Optional["Command"]:
        """Get command enum by command name"""
        for command in cls:
            if command.command_name == command_name:
                return command
        return None

    @classmethod
    def get_commands_for_group_name(cls, group_name: str) -> List["Command"]:
        """Get all commands for a specific group by group name"""
        prefix = group_name.upper() + "_"
        return [cmd for cmd in cls if cmd.name.startswith(prefix)]

    @classmethod
    def get_all_command_names(cls) -> List[str]:
        """Get all command names"""
        return [command.command_name for command in cls]

    def __str__(self) -> str:
        return self.command_name

    def __repr__(self) -> str:
        return f"Command({self.command_name})"
