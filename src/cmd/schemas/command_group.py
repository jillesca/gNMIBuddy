#!/usr/bin/env python3
"""Command group definitions with integrated alias functionality"""

from enum import Enum
from typing import Optional, List


class CommandGroup(Enum):
    """Enumeration of command groups with their details and aliases"""

    DEVICE = (
        "device",
        "d",
        "Device Information",
        "Commands for device management and information",
    )
    NETWORK = (
        "network",
        "n",
        "Network Protocols",
        "Commands for network protocol analysis",
    )
    TOPOLOGY = (
        "topology",
        "t",
        "Network Topology",
        "Commands for topology discovery and analysis",
    )
    OPS = (
        "ops",
        "o",
        "Operations",
        "Commands for operational tasks and testing",
    )

    def __init__(
        self, group_name: str, alias: str, title: str, description: str
    ):
        self.group_name = group_name
        self.alias = alias
        self.title = title
        self.description = description

    @classmethod
    def get_by_name(cls, group_name: str) -> Optional["CommandGroup"]:
        """Get command group by full name"""
        for group in cls:
            if group.group_name == group_name:
                return group
        return None

    @classmethod
    def get_by_alias(cls, alias: str) -> Optional["CommandGroup"]:
        """Get command group by alias"""
        for group in cls:
            if group.alias == alias:
                return group
        return None

    @classmethod
    def resolve_name_or_alias(
        cls, name_or_alias: str
    ) -> Optional["CommandGroup"]:
        """Resolve either full name or alias to CommandGroup"""
        # Try full name first
        group = cls.get_by_name(name_or_alias)
        if group:
            return group

        # Try alias
        return cls.get_by_alias(name_or_alias)

    @classmethod
    def get_full_name_from_alias(cls, alias: str) -> Optional[str]:
        """Get full group name from alias"""
        group = cls.get_by_alias(alias)
        return group.group_name if group else None

    @classmethod
    def get_alias_from_name(cls, group_name: str) -> Optional[str]:
        """Get alias from full group name"""
        group = cls.get_by_name(group_name)
        return group.alias if group else None

    @classmethod
    def get_all_names(cls) -> List[str]:
        """Get all command group names"""
        return [group.group_name for group in cls]

    @classmethod
    def get_all_aliases(cls) -> List[str]:
        """Get all command group aliases"""
        return [group.alias for group in cls]

    @classmethod
    def get_all_names_and_aliases(cls) -> List[str]:
        """Get all valid command names and aliases"""
        result = []
        for group in cls:
            result.append(group.group_name)
            result.append(group.alias)
        return result

    @classmethod
    def is_valid_name_or_alias(cls, name: str) -> bool:
        """Check if name is a valid command name or alias"""
        return cls.resolve_name_or_alias(name) is not None

    @classmethod
    def is_alias(cls, name: str) -> bool:
        """Check if name is an alias (not full name)"""
        return cls.get_by_alias(name) is not None

    @classmethod
    def is_full_name(cls, name: str) -> bool:
        """Check if name is a full command name"""
        return cls.get_by_name(name) is not None

    def get_usage_line(self) -> str:
        """Get usage line showing both full name and alias"""
        return f"{self.group_name} ({self.alias})"

    def __str__(self) -> str:
        return self.group_name

    def __repr__(self) -> str:
        return f"CommandGroup({self.group_name}, {self.alias})"
