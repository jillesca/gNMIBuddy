#!/usr/bin/env python3
"""CLI module for network tools application"""
from src.cli.parser import run_cli_mode, parse_args, execute_command
from src.cli.commands import COMMANDS

__all__ = ["run_cli_mode", "parse_args", "execute_command", "COMMANDS"]
