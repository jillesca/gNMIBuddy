#!/usr/bin/env python3
"""Test helper functions for CLI design compliance testing"""
import re
from typing import List, Dict, Any, Tuple, Optional
from click.testing import CliRunner
from src.cmd.parser import cli
from src.cmd.groups import COMMAND_GROUPS


class CLITestUtils:
    """Utility class for CLI testing operations"""

    def __init__(self, cli_runner: CliRunner):
        self.runner = cli_runner
        self.cli = cli

    def get_all_command_info(self) -> List[Dict[str, Any]]:
        """Get comprehensive information about all commands"""
        commands = []

        for group_name, group in COMMAND_GROUPS.items():
            if hasattr(group, "commands"):
                for cmd_name, cmd in group.commands.items():
                    command_info = {
                        "name": cmd_name,
                        "group": group_name,
                        "command": cmd,
                        "help": getattr(cmd, "help", ""),
                        "short_help": getattr(cmd, "short_help", ""),
                        "callback": getattr(cmd, "callback", None),
                        "params": getattr(cmd, "params", []),
                        "hidden": getattr(cmd, "hidden", False),
                    }
                    commands.append(command_info)

        return commands

    def validate_command_structure(
        self, command_info: Dict[str, Any]
    ) -> Dict[str, bool]:
        """Validate that a command follows the expected structure"""
        checks = {
            "has_name": bool(command_info.get("name")),
            "has_help": bool(command_info.get("help")),
            "has_group": bool(command_info.get("group")),
            "has_callback": command_info.get("callback") is not None,
            "name_follows_kebab_case": self.is_kebab_case(
                command_info.get("name", "")
            ),
            "help_is_descriptive": len(command_info.get("help", "")) > 10,
            "help_no_trailing_period": not command_info.get("help", "")
            .strip()
            .endswith("."),
        }
        return checks

    def is_kebab_case(self, name: str) -> bool:
        """Check if a name follows kebab-case convention"""
        if not name:
            return False
        return bool(re.match(r"^[a-z]+(-[a-z]+)*$", name))

    def get_help_structure(self, command_path: List[str]) -> Dict[str, Any]:
        """Analyze the structure of help output"""
        result = self.runner.invoke(self.cli, command_path + ["--help"])

        if result.exit_code != 0:
            return {
                "error": f"Command failed with exit code {result.exit_code}"
            }

        help_text = result.output

        structure = {
            "has_usage": "Usage:" in help_text,
            "has_description": len(help_text.split("\n")) > 3,
            "has_options": "Options:" in help_text,
            "has_commands": "Commands:" in help_text,
            "has_examples": "Examples:" in help_text
            or "Usage examples:" in help_text,
            "has_banner": self._check_banner_presence(help_text),
            "line_count": len(help_text.split("\n")),
            "exit_code": result.exit_code,
        }

        return structure

    def _check_banner_presence(self, text: str) -> bool:
        """Check if ASCII banner is present in text"""
        banner_patterns = [
            r"g[Nn][Mm][Ii][Bb]uddy",
            r"={3,}",
            r"#{3,}",
            r"\/\\",
            r"\\/",
        ]

        for pattern in banner_patterns:
            if re.search(pattern, text):
                return True
        return False

    def extract_command_list_from_help(self, help_text: str) -> List[str]:
        """Extract command names from help output"""
        commands = []
        lines = help_text.split("\n")
        in_commands_section = False

        for line in lines:
            if "Commands:" in line:
                in_commands_section = True
                continue
            elif in_commands_section and line.strip():
                if line.startswith("  ") and not line.startswith("    "):
                    # This is likely a command line
                    parts = line.strip().split()
                    if parts:
                        # Extract command name (remove aliases in parentheses)
                        cmd_name = parts[0].split("(")[0].strip()
                        if cmd_name and not cmd_name.endswith(":"):
                            commands.append(cmd_name)
                elif not line.startswith(" "):
                    # End of commands section
                    break

        return commands

    def test_command_execution(
        self, command_path: List[str], args: List[str] = None
    ) -> Dict[str, Any]:
        """Test command execution and return result analysis"""
        if args is None:
            args = []

        full_command = command_path + args
        result = self.runner.invoke(self.cli, full_command)

        analysis = {
            "exit_code": result.exit_code,
            "output_length": len(result.output),
            "has_output": bool(result.output.strip()),
            "has_error": (
                bool(result.stderr_bytes) if result.stderr_bytes else False
            ),
            "exception": result.exception,
            "command": " ".join(full_command),
        }

        return analysis

    def validate_group_structure(self, group_name: str) -> Dict[str, Any]:
        """Validate the structure of a command group"""
        if group_name not in COMMAND_GROUPS:
            return {"error": f"Group {group_name} not found"}

        group = COMMAND_GROUPS[group_name]
        help_structure = self.get_help_structure([group_name])

        validation = {
            "group_exists": True,
            "has_help": help_structure.get("has_description", False),
            "has_commands": help_structure.get("has_commands", False),
            "help_structure": help_structure,
            "command_count": len(getattr(group, "commands", {})),
        }

        return validation

    def check_alias_functionality(self, alias: str, full_name: str) -> bool:
        """Check if an alias works the same as the full command name"""
        alias_result = self.runner.invoke(self.cli, [alias, "--help"])
        full_result = self.runner.invoke(self.cli, [full_name, "--help"])

        # Both should succeed and have similar output
        return (
            alias_result.exit_code == 0
            and full_result.exit_code == 0
            and len(alias_result.output) > 0
            and len(full_result.output) > 0
        )

    def analyze_error_message_quality(
        self, invalid_command: str
    ) -> Dict[str, Any]:
        """Analyze the quality of error messages for invalid commands"""
        result = self.runner.invoke(self.cli, [invalid_command])

        if result.exit_code == 0:
            return {"error": "Command should have failed but succeeded"}

        error_output = result.output or ""

        analysis = {
            "has_suggestion": "did you mean" in error_output.lower()
            or "similar" in error_output.lower(),
            "has_help_reference": "--help" in error_output
            or "help" in error_output.lower(),
            "is_user_friendly": not (
                "traceback" in error_output.lower()
                or "exception" in error_output.lower()
            ),
            "output_length": len(error_output),
            "exit_code": result.exit_code,
        }

        return analysis

    def get_command_coverage_report(self) -> Dict[str, Any]:
        """Generate a comprehensive coverage report for all commands"""
        all_commands = self.get_all_command_info()

        report = {
            "total_commands": len(all_commands),
            "groups": {},
            "compliance_summary": {
                "kebab_case_compliant": 0,
                "has_help": 0,
                "has_examples": 0,
                "structure_compliant": 0,
            },
        }

        for cmd in all_commands:
            group_name = cmd["group"]
            if group_name not in report["groups"]:
                report["groups"][group_name] = {
                    "commands": [],
                    "count": 0,
                }

            cmd_structure = self.validate_command_structure(cmd)

            report["groups"][group_name]["commands"].append(
                {
                    "name": cmd["name"],
                    "structure_checks": cmd_structure,
                    "compliant": all(cmd_structure.values()),
                }
            )
            report["groups"][group_name]["count"] += 1

            # Update compliance summary
            if cmd_structure["name_follows_kebab_case"]:
                report["compliance_summary"]["kebab_case_compliant"] += 1
            if cmd_structure["has_help"]:
                report["compliance_summary"]["has_help"] += 1
            if all(cmd_structure.values()):
                report["compliance_summary"]["structure_compliant"] += 1

        return report


def assert_command_structure_valid(command_info: Dict[str, Any]):
    """Assert that a command has valid structure (for use in tests)"""
    assert command_info.get("name"), "Command must have a name"
    assert command_info.get("help"), "Command must have help text"
    assert command_info.get("group"), "Command must belong to a group"
    assert command_info.get(
        "callback"
    ), "Command must have a callback function"


def assert_kebab_case(name: str):
    """Assert that a name follows kebab-case convention"""
    assert re.match(
        r"^[a-z]+(-[a-z]+)*$", name
    ), f"'{name}' must follow kebab-case convention"


def assert_help_quality(help_text: str):
    """Assert that help text meets quality standards"""
    assert (
        len(help_text) > 10
    ), "Help text must be descriptive (> 10 characters)"
    assert not help_text.strip().endswith(
        "."
    ), "Help text should not end with a period"
    assert help_text[
        0
    ].isupper(), "Help text should start with a capital letter"


def get_expected_command_structure() -> Dict[str, List[str]]:
    """Get the expected command structure for validation"""
    return {
        "device": ["info", "profile", "list"],
        "network": ["routing", "interface", "mpls", "vpn"],
        "topology": ["neighbors", "adjacency"],
        "ops": ["logs", "test-all"],
        "manage": ["list-commands", "log-level"],
    }


def get_expected_aliases() -> Dict[str, str]:
    """Get the expected command aliases"""
    return {
        "d": "device",
        "n": "network",
        "t": "topology",
        "o": "ops",
        "m": "manage",
    }
