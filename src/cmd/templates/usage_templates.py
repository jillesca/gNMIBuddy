#!/usr/bin/env python3
"""Usage message templates for CLI with OOP organization"""

from dataclasses import dataclass


@dataclass
class UsageTemplateData:
    """Base class for usage template data"""

    pass


@dataclass
class InventoryUsageData(UsageTemplateData):
    """Data for inventory usage template"""

    inventory_example: str
    env_example: str


class UsageTemplates:
    """Centralized usage message templates using OOP principles"""

    INVENTORY_ERROR_TEMPLATE = """❌ Inventory Error
═══════════════════════════════════════════════════════════

The inventory file is required but not found.

💡 How to fix this:
  1. Use --inventory option:
     {inventory_example}

  2. Or set environment variable:
     export NETWORK_INVENTORY=path/to/your/devices.json
     {env_example}

📁 Example inventory files:
  • xrd_sandbox.json (in project root)
  • Any JSON file with device definitions"""

    COMMAND_HELP_FALLBACK_TEMPLATE = """Run 'uv run gnmibuddy.py {group_command} --help' for usage information."""

    USAGE_ERROR_TEMPLATE = """Error: Invalid option or argument.
Use --help for detailed usage information."""

    CLI_ARGUMENT_ERROR_TEMPLATE = (
        """Command line argument error. Use --help for usage information."""
    )

    @classmethod
    def format_inventory_error(cls, data: InventoryUsageData) -> str:
        """Format inventory error message"""
        return cls.INVENTORY_ERROR_TEMPLATE.format(
            inventory_example=data.inventory_example,
            env_example=data.env_example,
        )

    @classmethod
    def format_command_help_fallback(cls, group_command: str) -> str:
        """Format command help fallback message"""
        return cls.COMMAND_HELP_FALLBACK_TEMPLATE.format(
            group_command=group_command
        )

    @classmethod
    def get_usage_error(cls) -> str:
        """Get usage error message"""
        return cls.USAGE_ERROR_TEMPLATE

    @classmethod
    def get_cli_argument_error(cls) -> str:
        """Get CLI argument error message"""
        return cls.CLI_ARGUMENT_ERROR_TEMPLATE
