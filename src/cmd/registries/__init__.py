#!/usr/bin/env python3
"""
Registration system for gNMIBuddy CLI commands

This package provides the registration infrastructure for CLI commands and groups.
"""

from .command_registry import command_registry
from .group_registry import group_registry
from .coordinator import coordinator
from .command_modules import (
    COMMAND_MODULES,
    get_command_modules,
    get_modules_by_group,
    get_groups,
)

__all__ = [
    "command_registry",
    "group_registry",
    "coordinator",
    "COMMAND_MODULES",
    "get_command_modules",
    "get_modules_by_group",
    "get_groups",
]
