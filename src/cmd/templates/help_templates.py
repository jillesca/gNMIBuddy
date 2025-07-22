#!/usr/bin/env python3
"""Help message templates for CLI with OOP organization"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class HelpTemplateData:
    """Base class for help template data"""

    pass


@dataclass
class MainHelpData(HelpTemplateData):
    """Data for main help template"""

    commands_section: str
    examples_section: str = ""


@dataclass
class GroupHelpData(HelpTemplateData):
    """Data for group help template"""

    group_name: str
    alias_usage: str = ""
    group_description: str = ""
    commands_list: str = ""


class HelpTemplates:
    """Centralized help message templates using OOP principles"""

    MAIN_HELP_TEMPLATE = """Usage: gnmibuddy [OPTIONS] COMMAND [ARGS]...

📋 INVENTORY REQUIREMENT:
  You must provide device inventory via either:
  • --inventory PATH_TO_FILE.json
  • Set NETWORK_INVENTORY environment variable

Options:
  -h, --help               Show this message and exit
  --log-level [debug|info|warning|error]
                           Set the global logging level
  --all-devices            Run command on all devices concurrently
  --inventory TEXT         Path to inventory JSON file (REQUIRED)

Commands:

{commands_section}

{examples_section}

Run 'uv run gnmibuddy.py COMMAND --help' for more information on a specific command.
Run 'uv run gnmibuddy.py GROUP --help' to see commands in a specific group."""

    GROUP_HELP_TEMPLATE = """Usage: gnmibuddy {group_name} [OPTIONS] COMMAND [ARGS]...{alias_usage}

{group_description}

Commands:
{commands_list}

Run 'uv run gnmibuddy.py {group_name} COMMAND --help' for more information on a specific command."""

    EXAMPLES_SECTION_TEMPLATE = """Examples:
{example_lines}"""

    @classmethod
    def format_main_help(cls, data: MainHelpData) -> str:
        """Format main help output"""
        return cls.MAIN_HELP_TEMPLATE.format(
            commands_section=data.commands_section,
            examples_section=data.examples_section,
        ).strip()

    @classmethod
    def format_group_help(cls, data: GroupHelpData) -> str:
        """Format group help output"""
        return cls.GROUP_HELP_TEMPLATE.format(
            group_name=data.group_name,
            alias_usage=data.alias_usage,
            group_description=data.group_description,
            commands_list=data.commands_list,
        ).strip()

    @classmethod
    def format_examples_section(cls, examples: List[str]) -> str:
        """Format examples section"""
        if not examples:
            return ""

        example_lines = "\n".join(examples)
        return cls.EXAMPLES_SECTION_TEMPLATE.format(
            example_lines=example_lines
        )
