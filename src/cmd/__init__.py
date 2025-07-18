#!/usr/bin/env python3
"""Command-line interface module for gNMIBuddy - Click-based CLI"""
from src.cmd.parser import run_cli_mode, parse_args, execute_command, cli
from src.cmd.base import (
    command_registry,
    ClickCommand,
    get_legacy_commands_dict,
)
from src.cmd.context import CLIContext, service_registry

__all__ = [
    "run_cli_mode",
    "parse_args",
    "execute_command",
    "cli",
    "command_registry",
    "ClickCommand",
    "get_legacy_commands_dict",
    "CLIContext",
    "service_registry",
]
