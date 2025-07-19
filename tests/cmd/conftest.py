#!/usr/bin/env python3
"""Test fixtures and utilities for CLI testing"""
import pytest
from click.testing import CliRunner
from unittest.mock import Mock, patch
from typing import Dict, List, Any
import sys
import os

# Ensure src is in the path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
)

from src.cmd.parser import cli
from src.cmd.groups import COMMAND_GROUPS
from src.cmd.display import GroupedHelpFormatter
from src.cmd.error_handler import CLIErrorHandler


@pytest.fixture
def cli_runner():
    """Provide a CLI runner for testing"""
    return CliRunner()


@pytest.fixture
def mock_device_response():
    """Mock device response for testing"""
    return {
        "status": "success",
        "data": {
            "device": "R1",
            "system": {"hostname": "R1", "version": "7.0.0"},
            "interfaces": {"GigabitEthernet0/0/0/0": {"admin_state": "up"}},
        },
    }


@pytest.fixture
def mock_inventory():
    """Mock inventory for testing"""
    return {
        "devices": {
            "R1": {"host": "192.168.1.1", "port": 57400, "role": "PE"},
            "R2": {"host": "192.168.1.2", "port": 57400, "role": "P"},
            "R3": {"host": "192.168.1.3", "port": 57400, "role": "CE"},
        }
    }


@pytest.fixture
def help_formatter():
    """Provide a GroupedHelpFormatter instance"""
    return GroupedHelpFormatter()


@pytest.fixture
def error_handler():
    """Provide a CLIErrorHandler instance"""
    return CLIErrorHandler()


def get_all_commands() -> List[Dict[str, Any]]:
    """Get all registered commands for testing"""
    commands = []

    for group_name, group in COMMAND_GROUPS.items():
        if hasattr(group, "commands"):
            for cmd_name, cmd in group.commands.items():
                commands.append(
                    {
                        "name": cmd_name,
                        "group": group_name,
                        "command": cmd,
                        "help": getattr(cmd, "help", ""),
                        "callback": getattr(cmd, "callback", None),
                    }
                )

    return commands


def get_all_groups() -> List[str]:
    """Get all command group names"""
    return list(COMMAND_GROUPS.keys())


def get_command_help(cli_runner: CliRunner, command_path: List[str]) -> str:
    """Get help output for a specific command path"""
    result = cli_runner.invoke(cli, command_path + ["--help"])
    return result.output if result.exit_code == 0 else ""


def get_main_help(cli_runner: CliRunner) -> str:
    """Get main CLI help output"""
    result = cli_runner.invoke(cli, ["--help"])
    return result.output if result.exit_code == 0 else ""


def get_group_help(cli_runner: CliRunner, group_name: str) -> str:
    """Get help output for a specific group"""
    result = cli_runner.invoke(cli, [group_name, "--help"])
    return result.output if result.exit_code == 0 else ""


def validate_kebab_case(name: str) -> bool:
    """Validate that a name follows kebab-case convention"""
    import re

    return bool(re.match(r"^[a-z]+(-[a-z]+)*$", name))


def extract_usage_examples(help_text: str) -> List[str]:
    """Extract usage examples from help text"""
    examples = []
    lines = help_text.split("\n")
    in_examples = False

    for line in lines:
        if "Examples:" in line or "Usage examples:" in line:
            in_examples = True
            continue
        elif in_examples and line.strip() and not line.startswith(" "):
            # End of examples section
            break
        elif in_examples and line.strip():
            examples.append(line.strip())

    return examples


def check_banner_presence(help_text: str) -> bool:
    """Check if ASCII banner is present in help text"""
    banner_indicators = [
        "gNMIBuddy",
        "ASCII",
        "==",
        "##",
        "/\\",
    ]

    for indicator in banner_indicators:
        if indicator in help_text:
            return True
    return False


@pytest.fixture
def command_test_data():
    """Provide test data for command validation"""
    return {
        "expected_groups": ["device", "network", "topology", "ops"],
        "expected_aliases": {
            "d": "device",
            "n": "network",
            "t": "topology",
            "o": "ops",
        },
        "required_device_commands": ["info", "profile", "list"],
        "required_network_commands": ["routing", "interface", "mpls", "vpn"],
        "required_topology_commands": ["neighbors", "adjacency"],
        "required_ops_commands": ["logs", "test-all"],
        "required_manage_commands": ["list-commands", "log-level"],
    }


@pytest.fixture(scope="session")
def sample_cli_outputs():
    """Provide sample CLI outputs for testing"""
    return {
        "main_help": """Usage: gnmibuddy [OPTIONS] COMMAND [ARGS]...

  gNMIBuddy CLI tool for network device management

Options:
  -h, --help            Show this message and exit.
  --log-level [debug|info|warning|error]
                        Set the global logging level

Commands:
  Device Information:
    device (d)          Device management commands
  
  Network Protocols:
    network (n)         Network protocol commands
""",
        "device_help": """Usage: gnmibuddy device [OPTIONS] COMMAND [ARGS]...

  Device management commands

Commands:
  info     Get system information from a network device
  profile  Get device profile and role information
  list     List all available devices in the inventory
""",
    }
