#!/usr/bin/env python3
"""Display functions for CLI output"""
from typing import Dict, List, Tuple, Any
from src.cmd.commands import COMMANDS


def display_all_commands(detailed=False):
    """
    Display all available commands and their options.

    Args:
        detailed: Whether to show detailed option descriptions
    """

    _print_header()
    _print_available_commands(COMMANDS, detailed)
    _print_usage_examples()


def _print_header():
    print("=== AVAILABLE CLI COMMANDS ===")
    print("BASIC SYNTAX:")
    print("  python main.py --device DEVICE_NAME COMMAND [OPTIONS]")
    print(
        "  python main.py --all-devices [--max-workers NUM] COMMAND [OPTIONS]"
    )
    print("AVAILABLE COMMANDS:")


def _print_available_commands(commands: Dict, detailed: bool):
    for cmd_name, cmd in commands.items():
        print(f"\n  {cmd_name}:")
        description = cmd.description or cmd.help
        print(f"    {description}")

        if detailed and cmd.parser:
            _print_command_options(cmd)


def _print_command_options(cmd: Any):
    options = _extract_command_options(cmd)
    if options:
        print("    Options:")
        for option_strings, dest, help_text in options:
            option_str = ", ".join(option_strings) if option_strings else dest
            print(f"      {option_str}: {help_text}")


def _extract_command_options(cmd: Any) -> List[Tuple]:
    options = []
    for action in cmd.parser._actions:  # pylint: disable=protected-access
        if action.dest != "help":
            options.append((action.option_strings, action.dest, action.help))
    return options


def _print_usage_examples():
    """Print example usage of commands."""
    print("\nFor more help on a specific command:")
    print("  python main.py COMMAND --help")
    print("\nExample usage:")
    print("  python main.py --device sandbox routing --protocol bgp")
    print(
        "  python main.py --device sandbox interface --name GigabitEthernet0/0"
    )
    print('  python main.py --device sandbox query "Show me BGP neighbors"')
    print("\nConcurrent execution on all devices:")
    print("  python main.py --all-devices routing --protocol ospf")
    print("  python main.py --all-devices --max-workers 10 interface")
    print('  python main.py --all-devices query "Show MPLS forwarding table"')
