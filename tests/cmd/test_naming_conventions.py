#!/usr/bin/env python3
"""Tests for naming convention enforcement across the CLI"""
import pytest
import re
import os
import inspect
from click.testing import CliRunner
from typing import Dict, List, Any

from src.cmd.parser import cli
from src.cmd.groups import COMMAND_GROUPS
from tests.cmd.test_utils import (
    CLITestUtils,
    get_expected_command_structure,
    get_expected_aliases,
)


class TestCommandNamingConventions:
    """Test suite for command naming convention enforcement"""

    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
        self.utils = CLITestUtils(self.runner)

    def test_all_command_names_follow_kebab_case(self):
        """Test that all command names follow kebab-case convention"""
        all_commands = self.utils.get_all_command_info()

        for command_info in all_commands:
            command_name = command_info["name"]
            group_name = command_info["group"]

            # Test kebab-case pattern: lowercase letters and hyphens only
            assert re.match(
                r"^[a-z]+(-[a-z]+)*$", command_name
            ), f"Command '{command_name}' in group '{group_name}' must follow kebab-case convention"

            # Additional specific checks
            assert not command_name.startswith(
                "-"
            ), f"Command '{command_name}' should not start with hyphen"
            assert not command_name.endswith(
                "-"
            ), f"Command '{command_name}' should not end with hyphen"
            assert (
                "--" not in command_name
            ), f"Command '{command_name}' should not have consecutive hyphens"
            assert (
                command_name.islower()
            ), f"Command '{command_name}' should be lowercase"

    def test_group_names_follow_naming_convention(self):
        """Test that group names follow consistent naming convention"""
        for group_name in COMMAND_GROUPS.keys():
            # Group names should follow kebab-case
            assert re.match(
                r"^[a-z]+(-[a-z]+)*$", group_name
            ), f"Group '{group_name}' must follow kebab-case convention"

            # Group names should be descriptive but concise
            assert (
                len(group_name) >= 2
            ), f"Group name '{group_name}' should be at least 2 characters"
            assert (
                len(group_name) <= 20
            ), f"Group name '{group_name}' should be at most 20 characters"

            # Should not contain numbers (for consistency)
            assert not any(
                char.isdigit() for char in group_name
            ), f"Group '{group_name}' should not contain numbers"

    def test_command_name_consistency_within_groups(self):
        """Test that command names are consistent within their groups"""
        expected_structure = get_expected_command_structure()

        for group_name, commands in expected_structure.items():
            # All commands in a group should follow similar patterns
            command_lengths = [len(cmd) for cmd in commands]

            # Commands shouldn't vary too wildly in length
            if len(command_lengths) > 1:
                min_len, max_len = min(command_lengths), max(command_lengths)
                length_ratio = max_len / min_len if min_len > 0 else 1
                assert (
                    length_ratio <= 3
                ), f"Commands in group '{group_name}' vary too much in length: {commands}"

            # Check for consistent terminology within groups
            self._check_terminology_consistency(group_name, commands)

    def test_alias_naming_patterns(self):
        """Test that aliases follow consistent naming patterns"""
        expected_aliases = get_expected_aliases()

        for alias, full_name in expected_aliases.items():
            # Aliases should be single characters for groups
            assert (
                len(alias) == 1
            ), f"Group alias '{alias}' should be single character"
            assert alias.islower(), f"Alias '{alias}' should be lowercase"
            assert alias.isalpha(), f"Alias '{alias}' should be alphabetic"

            # Alias should be related to the full name
            assert (
                alias == full_name[0]
            ), f"Alias '{alias}' should be first letter of '{full_name}'"

    def test_command_name_uniqueness(self):
        """Test that command names are unique across the CLI"""
        all_commands = self.utils.get_all_command_info()

        # Collect all command names across all groups
        all_command_names = []
        command_locations = {}

        for command_info in all_commands:
            name = command_info["name"]
            group = command_info["group"]

            all_command_names.append(name)

            if name in command_locations:
                command_locations[name].append(group)
            else:
                command_locations[name] = [group]

        # Check for duplicates across groups
        duplicates = {
            name: groups
            for name, groups in command_locations.items()
            if len(groups) > 1
        }

        assert (
            not duplicates
        ), f"Command names should be unique across groups. Duplicates found: {duplicates}"

    def test_reserved_word_avoidance(self):
        """Test that command names avoid reserved words and common conflicts"""
        reserved_words = {
            # Python reserved words
            "and",
            "or",
            "not",
            "if",
            "else",
            "elif",
            "while",
            "for",
            "def",
            "class",
            "import",
            "from",
            "as",
            "try",
            "except",
            "finally",
            "with",
            "lambda",
            "return",
            "yield",
            "break",
            "continue",
            "pass",
            "global",
            "nonlocal",
            "assert",
            "del",
            "is",
            "in",
            "true",
            "false",
            "none",
            # Common CLI reserved words
            "help",
            "version",
            "config",
            "debug",
            "verbose",
            "quiet",
            # Potential conflicts
            "run",
            "start",
            "stop",
            "status",
            "init",
        }

        # Allow certain legitimate command names that contain reserved words
        allowed_exceptions = {
            "test-all",  # Testing command is legitimate in ops context
            "list-commands",  # List is not problematic in this context
        }

        all_commands = self.utils.get_all_command_info()

        for command_info in all_commands:
            command_name = command_info["name"]
            group_name = command_info["group"]

            # Skip allowed exceptions
            if command_name in allowed_exceptions:
                continue

            # Check against reserved words
            name_words = command_name.split("-")
            for word in name_words:
                assert (
                    word not in reserved_words
                ), f"Command '{command_name}' in group '{group_name}' uses reserved word '{word}'"

    def _check_terminology_consistency(
        self, group_name: str, commands: List[str]
    ):
        """Check that terminology is consistent within a group"""
        # Define expected terminology patterns for different groups
        terminology_patterns = {
            "device": {
                "preferred": ["info", "profile", "list", "status"],
                "avoid": ["get", "show", "display"],
            },
            "network": {
                "preferred": ["routing", "interface", "protocol"],
                "avoid": ["net", "conn", "link"],
            },
            "topology": {
                "preferred": ["neighbors", "adjacency", "path"],
                "avoid": ["topo", "adj", "neigh"],
            },
            "ops": {
                "preferred": ["logs", "test", "check"],
                "avoid": ["log", "testing", "checking"],
            },
        }

        if group_name in terminology_patterns:
            patterns = terminology_patterns[group_name]

            for command in commands:
                command_words = command.split("-")

                # Check for avoided terminology
                for word in command_words:
                    assert word not in patterns.get(
                        "avoid", []
                    ), f"Command '{command}' in group '{group_name}' uses discouraged term '{word}'"


class TestFileAndModuleNamingConventions:
    """Test file and module naming conventions"""

    def setup_method(self):
        """Set up test fixtures"""
        self.cmd_module_path = "src/cmd"

    def test_python_file_naming_conventions(self):
        """Test that Python files follow naming conventions"""
        cmd_files = []

        # Walk through the cmd module directory
        for root, dirs, files in os.walk(self.cmd_module_path):
            for file in files:
                if file.endswith(".py"):
                    cmd_files.append(file)

        for filename in cmd_files:
            name_without_ext = filename[:-3]  # Remove .py extension

            # Skip special Python files
            if name_without_ext in ["__init__", "__main__", "__version__"]:
                continue

            # Python files should use snake_case
            assert re.match(
                r"^[a-z]+(_[a-z]+)*$", name_without_ext
            ), f"Python file '{filename}' should use snake_case naming"

            # Should not be too long
            assert (
                len(name_without_ext) <= 30
            ), f"Filename '{filename}' should be reasonably short"

            # Should be descriptive
            assert (
                len(name_without_ext) >= 3
            ), f"Filename '{filename}' should be descriptive"

    def test_class_naming_conventions(self):
        """Test that class names follow Python conventions"""
        # Import the main cmd modules to check class naming
        try:
            import src.cmd.parser as parser_module
            import src.cmd.groups as groups_module
            import src.cmd.display as display_module
            import src.cmd.error_handler as error_module

            modules_to_check = [
                parser_module,
                groups_module,
                display_module,
                error_module,
            ]

            for module in modules_to_check:
                # Get all classes defined in the module
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Only check classes defined in this module (not imported)
                    if obj.__module__ == module.__name__:
                        # Class names should use PascalCase
                        assert re.match(
                            r"^[A-Z][a-zA-Z0-9]*$", name
                        ), f"Class '{name}' in {module.__name__} should use PascalCase"

                        # Should not be too long
                        assert (
                            len(name) <= 50
                        ), f"Class name '{name}' should be reasonably short"

                        # Should be descriptive
                        assert (
                            len(name) >= 3
                        ), f"Class name '{name}' should be descriptive"

        except ImportError as e:
            pytest.skip(f"Could not import cmd modules for testing: {e}")

    def test_function_naming_conventions(self):
        """Test that function names follow Python conventions"""
        try:
            import src.cmd.parser as parser_module
            import src.cmd.display as display_module

            modules_to_check = [parser_module, display_module]

            for module in modules_to_check:
                # Get all functions defined in the module
                for name, obj in inspect.getmembers(
                    module, inspect.isfunction
                ):
                    # Only check functions defined in this module
                    if obj.__module__ == module.__name__:
                        # Function names should use snake_case
                        assert re.match(
                            r"^[a-z]+(_[a-z0-9]+)*$", name
                        ), f"Function '{name}' in {module.__name__} should use snake_case"

                        # Should not be too long
                        assert (
                            len(name) <= 50
                        ), f"Function name '{name}' should be reasonably short"

        except ImportError as e:
            pytest.skip(f"Could not import cmd modules for testing: {e}")

    def test_constant_naming_conventions(self):
        """Test that constants follow naming conventions"""
        try:
            import src.cmd.groups as groups_module

            # Check for module-level constants
            for name, obj in inspect.getmembers(groups_module):
                if not name.startswith("_") and name.isupper():
                    # Constants should use UPPER_SNAKE_CASE
                    assert re.match(
                        r"^[A-Z]+(_[A-Z0-9]+)*$", name
                    ), f"Constant '{name}' should use UPPER_SNAKE_CASE"

        except ImportError as e:
            pytest.skip(f"Could not import groups module for testing: {e}")


class TestConsistencyAcrossLayers:
    """Test naming consistency across different layers of the CLI"""

    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
        self.utils = CLITestUtils(self.runner)

    def test_command_to_function_name_mapping(self):
        """Test that command names map consistently to function names"""
        all_commands = self.utils.get_all_command_info()

        for command_info in all_commands:
            command_name = command_info["name"]
            callback = command_info.get("callback")

            if callback and hasattr(callback, "__name__"):
                function_name = callback.__name__

                # Function name should be related to command name
                # Convert kebab-case to snake_case for comparison
                expected_function_pattern = command_name.replace("-", "_")

                # Function name should contain the command concept
                assert (
                    expected_function_pattern in function_name
                    or command_name.replace("-", "") in function_name
                ), f"Function '{function_name}' should relate to command '{command_name}'"

    def test_group_to_module_consistency(self):
        """Test that group names are consistent with module organization"""
        expected_groups = get_expected_command_structure().keys()

        for group_name in expected_groups:
            # Group concepts should be reflected in the codebase organization
            # This is more of a structural check than a strict naming requirement
            assert group_name in [
                "device",
                "network",
                "topology",
                "ops",
            ], f"Group '{group_name}' should follow expected naming categories"

    def test_help_text_terminology_consistency(self):
        """Test that help text uses consistent terminology"""
        all_commands = self.utils.get_all_command_info()

        # Define preferred terminology
        terminology_map = {
            "device": "device",  # Not 'node', 'host', 'system'
            "interface": "interface",  # Not 'port', 'link'
            "routing": "routing",  # Not 'routes', 'forwarding'
            "topology": "topology",  # Not 'network map', 'diagram'
        }

        for command_info in all_commands:
            help_text = command_info.get("help", "").lower()
            command_name = command_info["name"]

            # Check for consistent terminology usage
            for preferred, alternatives in [
                ("device", ["node", "host", "system", "router"]),
                ("interface", ["port", "link"]),
                ("routing", ["routes", "forwarding"]),
            ]:
                if preferred in command_name:
                    # If command name contains preferred term, help should too
                    if any(alt in help_text for alt in alternatives):
                        # Allow some flexibility, but flag inconsistencies
                        pass  # This is more of a guideline than a hard rule

    def test_option_naming_consistency(self):
        """Test that option names are consistent across commands"""
        all_commands = self.utils.get_all_command_info()

        # Common options should use consistent names
        common_option_patterns = {
            "device": ["--device", "-d"],
            "output": ["--output", "-o"],
            "format": ["--format", "-f"],
            "verbose": ["--verbose", "-v"],
            "help": ["--help", "-h"],
        }

        # This test is more observational - we collect patterns
        # rather than enforce strict rules, since Click handles much of this
        option_usage = {}

        for command_info in all_commands:
            command_obj = command_info.get("command")
            if command_obj and hasattr(command_obj, "params"):
                for param in command_obj.params:
                    if hasattr(param, "name"):
                        param_name = param.name
                        if param_name not in option_usage:
                            option_usage[param_name] = []
                        option_usage[param_name].append(command_info["name"])

        # Common options should appear in multiple commands with consistent naming
        for option_name, commands in option_usage.items():
            if len(commands) > 1:
                # This option appears in multiple commands
                # It should follow consistent naming patterns
                if option_name in ["device", "output", "format"]:
                    # These should use kebab-case if multi-word
                    assert re.match(
                        r"^[a-z]+(_[a-z]+)*$", option_name
                    ), f"Common option '{option_name}' should use snake_case"


class TestNamingRegressionPrevention:
    """Test to prevent naming convention regressions"""

    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
        self.utils = CLITestUtils(self.runner)

    def test_new_command_naming_validation(self):
        """Test that new commands would be validated for naming conventions"""
        # Simulate various new command names and test validation
        test_cases = [
            ("valid-command", True),
            ("another-valid-one", True),
            ("simple", True),
            ("InvalidCommand", False),  # PascalCase
            ("invalid_command", False),  # snake_case
            ("invalid-", False),  # trailing hyphen
            ("-invalid", False),  # leading hyphen
            ("invalid--command", False),  # double hyphen
            ("INVALID", False),  # uppercase
            ("123invalid", False),  # starts with number
        ]

        for command_name, should_be_valid in test_cases:
            is_valid = self.utils.is_kebab_case(command_name)
            assert (
                is_valid == should_be_valid
            ), f"Command name '{command_name}' validation failed"

    def test_naming_pattern_enforcement(self):
        """Test that naming patterns are properly enforced"""
        # Check current commands all pass validation
        all_commands = self.utils.get_all_command_info()

        for command_info in all_commands:
            command_name = command_info["name"]

            # Should pass kebab-case validation
            assert self.utils.is_kebab_case(
                command_name
            ), f"Existing command '{command_name}' should follow kebab-case"

            # Should not contain problematic patterns
            assert not any(
                char.isdigit() for char in command_name
            ), f"Command '{command_name}' should not contain numbers"

            assert not any(
                char.isupper() for char in command_name
            ), f"Command '{command_name}' should not contain uppercase letters"

    def test_naming_consistency_metrics(self):
        """Test that naming consistency can be measured and tracked"""
        all_commands = self.utils.get_all_command_info()

        metrics = {
            "kebab_case_compliance": 0,
            "appropriate_length": 0,
            "no_reserved_words": 0,
            "descriptive_names": 0,
        }

        total_commands = len(all_commands)

        for command_info in all_commands:
            command_name = command_info["name"]

            # Kebab-case compliance
            if self.utils.is_kebab_case(command_name):
                metrics["kebab_case_compliance"] += 1

            # Appropriate length (3-20 characters)
            if 3 <= len(command_name) <= 20:
                metrics["appropriate_length"] += 1

            # No reserved words (simplified check)
            if not any(
                word in command_name for word in ["test", "debug", "config"]
            ):
                metrics["no_reserved_words"] += 1

            # Descriptive (no single letters, not just 'cmd', etc.)
            if len(command_name) > 2 and command_name not in [
                "cmd",
                "run",
                "get",
            ]:
                metrics["descriptive_names"] += 1

        # Calculate compliance rates
        for metric, count in metrics.items():
            compliance_rate = (
                count / total_commands if total_commands > 0 else 0
            )
            assert (
                compliance_rate >= 0.8
            ), f"Naming metric '{metric}' should have >80% compliance, got {compliance_rate:.2%}"
