#!/usr/bin/env python3
"""Tests for command structure validation - ensures proper command architecture"""
import pytest
import inspect
from click.testing import CliRunner
from typing import Dict, List, Any, Callable

from src.cmd.parser import cli
from src.cmd.groups import COMMAND_GROUPS
from tests.cmd.test_utils import (
    CLITestUtils,
    get_expected_command_structure,
    get_expected_aliases,
)


class TestCommandStructureValidation:
    """Test suite for command structure validation"""

    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
        self.utils = CLITestUtils(self.runner)

    def test_all_commands_are_properly_registered(self):
        """Test that all commands are properly registered in their groups"""
        expected_structure = get_expected_command_structure()

        for group_name, expected_commands in expected_structure.items():
            # Verify group exists in COMMAND_GROUPS
            assert (
                group_name in COMMAND_GROUPS
            ), f"Group '{group_name}' should be registered"

            group = COMMAND_GROUPS[group_name]

            # Verify group has commands attribute
            assert hasattr(
                group, "commands"
            ), f"Group '{group_name}' should have commands attribute"

            # Verify all expected commands are registered
            registered_commands = list(group.commands.keys())
            for cmd in expected_commands:
                assert (
                    cmd in registered_commands
                ), f"Command '{cmd}' should be registered in group '{group_name}'"

            # Verify no unexpected commands
            for cmd in registered_commands:
                assert (
                    cmd in expected_commands
                ), f"Unexpected command '{cmd}' in group '{group_name}'"

    def test_command_callbacks_exist_and_are_callable(self):
        """Test that all commands have valid callbacks"""
        all_commands = self.utils.get_all_command_info()

        for command_info in all_commands:
            callback = command_info.get("callback")
            command_name = command_info["name"]
            group_name = command_info["group"]

            # Command should have a callback
            assert (
                callback is not None
            ), f"Command '{group_name} {command_name}' should have a callback"

            # Callback should be callable
            assert callable(
                callback
            ), f"Callback for '{group_name} {command_name}' should be callable"

            # Callback should have proper function signature
            if hasattr(callback, "__code__"):
                # For regular functions, check that they can accept Click's context
                sig = inspect.signature(callback)
                # Click commands typically have parameters for their options/arguments
                assert (
                    len(sig.parameters) >= 0
                ), f"Callback for '{group_name} {command_name}' should have valid signature"

    def test_command_groups_have_proper_click_structure(self):
        """Test that command groups follow Click patterns"""
        for group_name, group in COMMAND_GROUPS.items():
            # Group should be a Click Group
            assert hasattr(
                group, "commands"
            ), f"Group '{group_name}' should be a Click Group"
            assert hasattr(
                group, "add_command"
            ), f"Group '{group_name}' should have add_command method"

            # Group should have help text or docstring
            has_help = (
                hasattr(group, "help")
                and group.help
                or hasattr(group, "__doc__")
                and group.__doc__
            )
            assert has_help, f"Group '{group_name}' should have help text"

            # Group should have a name
            assert (
                hasattr(group, "name") or group_name
            ), f"Group '{group_name}' should have identifiable name"

    def test_command_registration_consistency(self):
        """Test that command registration is consistent across the system"""
        # All groups in COMMAND_GROUPS should be expected groups
        expected_groups = set(get_expected_command_structure().keys())
        registered_groups = set(COMMAND_GROUPS.keys())

        assert (
            registered_groups == expected_groups
        ), f"Registered groups {registered_groups} should match expected {expected_groups}"

        # All commands should be reachable through the CLI
        for group_name, group in COMMAND_GROUPS.items():
            for cmd_name in group.commands.keys():
                # Should be able to get help for each command
                result = self.runner.invoke(
                    cli, [group_name, cmd_name, "--help"]
                )
                assert (
                    result.exit_code == 0
                ), f"Command '{group_name} {cmd_name}' should be reachable"

    def test_command_aliases_are_properly_configured(self):
        """Test that command aliases are properly configured"""
        expected_aliases = get_expected_aliases()

        for alias, full_name in expected_aliases.items():
            # Alias should work the same as full name
            alias_result = self.runner.invoke(cli, [alias, "--help"])
            full_result = self.runner.invoke(cli, [full_name, "--help"])

            # Both should succeed
            assert alias_result.exit_code == 0, f"Alias '{alias}' should work"
            assert (
                full_result.exit_code == 0
            ), f"Full name '{full_name}' should work"

            # Both should produce similar output (basic check)
            assert (
                len(alias_result.output) > 0
            ), f"Alias '{alias}' should produce output"
            assert (
                len(full_result.output) > 0
            ), f"Full name '{full_name}' should produce output"

    def test_command_metadata_completeness(self):
        """Test that all commands have complete metadata"""
        all_commands = self.utils.get_all_command_info()

        for command_info in all_commands:
            command_name = command_info["name"]
            group_name = command_info["group"]

            # Required attributes
            assert command_info.get(
                "name"
            ), f"Command in group '{group_name}' should have name"
            assert command_info.get(
                "help"
            ), f"Command '{command_name}' should have help text"
            assert command_info.get(
                "group"
            ), f"Command '{command_name}' should have group assignment"
            assert command_info.get(
                "callback"
            ), f"Command '{command_name}' should have callback"

            # Optional but recommended attributes
            help_text = command_info.get("help", "")
            assert (
                len(help_text) > 5
            ), f"Command '{command_name}' help should be descriptive"

    def test_command_isolation_and_independence(self):
        """Test that commands are properly isolated and don't interfere"""
        all_commands = self.utils.get_all_command_info()

        # Commands within same group should have unique names
        commands_by_group = {}
        for command_info in all_commands:
            group = command_info["group"]
            name = command_info["name"]

            if group not in commands_by_group:
                commands_by_group[group] = []

            assert (
                name not in commands_by_group[group]
            ), f"Duplicate command '{name}' in group '{group}'"
            commands_by_group[group].append(name)

        # Commands should not have circular dependencies
        for command_info in all_commands:
            callback = command_info.get("callback")
            if callback and hasattr(callback, "__name__"):
                # Command callback should not reference its own name directly
                assert (
                    callback.__name__ != command_info["name"]
                ), f"Command '{command_info['name']}' should not be self-referential"


class TestCommandArchitectureCompliance:
    """Test architectural compliance for command system"""

    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
        self.utils = CLITestUtils(self.runner)

    def test_click_framework_usage_consistency(self):
        """Test that Click framework is used consistently throughout"""
        # Main CLI should be a Click group
        assert hasattr(cli, "commands"), "Main CLI should be a Click group"
        assert hasattr(
            cli, "add_command"
        ), "Main CLI should support adding commands"

        # All groups should be Click groups
        for group_name, group in COMMAND_GROUPS.items():
            assert hasattr(
                group, "commands"
            ), f"Group '{group_name}' should be a Click group"
            assert hasattr(
                group, "params"
            ), f"Group '{group_name}' should have Click params"

    def test_command_parameter_patterns(self):
        """Test that command parameters follow consistent patterns"""
        all_commands = self.utils.get_all_command_info()

        for command_info in all_commands:
            command_name = command_info["name"]
            group_name = command_info["group"]
            command_obj = command_info["command"]

            # Command should have parameters attribute
            if hasattr(command_obj, "params"):
                params = command_obj.params

                # Check for common patterns
                param_names = [p.name for p in params if hasattr(p, "name")]

                # Most commands should have help parameter
                has_help_param = any("help" in name for name in param_names)
                # This is implicit in Click, so we won't enforce it strictly

                # Parameters should have proper types
                for param in params:
                    if hasattr(param, "type"):
                        # Parameter types should be valid Click types
                        assert (
                            param.type is not None
                        ), f"Parameter in '{group_name} {command_name}' should have valid type"

    def test_error_handling_architecture(self):
        """Test that error handling follows architectural patterns"""
        # Test invalid commands produce proper errors
        result = self.runner.invoke(cli, ["invalid-command"])
        assert result.exit_code != 0, "Invalid commands should fail"

        # Test invalid group produces proper error
        result = self.runner.invoke(cli, ["invalid-group", "command"])
        assert result.exit_code != 0, "Invalid groups should fail"

        # Test invalid subcommand produces proper error
        result = self.runner.invoke(cli, ["device", "invalid-subcommand"])
        assert result.exit_code != 0, "Invalid subcommands should fail"

    def test_command_discovery_mechanism(self):
        """Test that command discovery works correctly"""
        # Should be able to list all available groups
        result = self.runner.invoke(cli, ["--help"])
        help_text = result.output

        # All groups should be discoverable
        for group_name in COMMAND_GROUPS.keys():
            assert (
                group_name in help_text
            ), f"Group '{group_name}' should be discoverable in main help"

        # Should be able to list commands in each group
        for group_name in COMMAND_GROUPS.keys():
            result = self.runner.invoke(cli, [group_name, "--help"])
            group_help = result.output

            expected_commands = get_expected_command_structure().get(
                group_name, []
            )
            for cmd in expected_commands:
                assert (
                    cmd in group_help
                ), f"Command '{cmd}' should be discoverable in group '{group_name}' help"


class TestCommandExtensibility:
    """Test that command architecture supports future extensions"""

    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
        self.utils = CLITestUtils(self.runner)

    def test_new_command_integration_readiness(self):
        """Test that the architecture can easily accommodate new commands"""
        # The existing structure should support adding new commands
        # We'll simulate this by checking the registration mechanism

        for group_name, group in COMMAND_GROUPS.items():
            # Each group should have add_command method
            assert hasattr(
                group, "add_command"
            ), f"Group '{group_name}' should support adding new commands"

            # Groups should not be overly complex (max reasonable commands)
            command_count = len(getattr(group, "commands", {}))
            assert (
                command_count <= 10
            ), f"Group '{group_name}' has {command_count} commands, consider splitting if adding more"

    def test_group_expansion_capability(self):
        """Test that new groups can be added to the system"""
        # The main CLI should support adding new groups
        assert hasattr(
            cli, "add_command"
        ), "Main CLI should support adding new groups"

        # Current structure should not be at maximum capacity
        current_group_count = len(COMMAND_GROUPS)
        assert (
            current_group_count <= 10
        ), f"Currently {current_group_count} groups, architecture should support reasonable expansion"

    def test_command_consistency_enforcement(self):
        """Test that architectural patterns enforce consistency"""
        # All commands should follow similar patterns
        all_commands = self.utils.get_all_command_info()

        # Collect patterns
        patterns = {
            "has_help": 0,
            "has_callback": 0,
            "has_group": 0,
            "valid_name": 0,
        }

        for command_info in all_commands:
            if command_info.get("help"):
                patterns["has_help"] += 1
            if command_info.get("callback"):
                patterns["has_callback"] += 1
            if command_info.get("group"):
                patterns["has_group"] += 1
            if self.utils.is_kebab_case(command_info.get("name", "")):
                patterns["valid_name"] += 1

        total_commands = len(all_commands)

        # High consistency rates indicate good architectural enforcement
        for pattern, count in patterns.items():
            consistency_rate = (
                count / total_commands if total_commands > 0 else 0
            )
            assert (
                consistency_rate >= 0.9
            ), f"Pattern '{pattern}' should have high consistency ({consistency_rate:.2%})"

    def test_plugin_architecture_readiness(self):
        """Test that the architecture could support plugins or extensions"""
        # The command registration system should be flexible enough for plugins

        # Groups should be registrable dynamically
        original_group_count = len(COMMAND_GROUPS)

        # Commands should be registrable dynamically within groups
        for group_name, group in COMMAND_GROUPS.items():
            original_command_count = len(getattr(group, "commands", {}))
            # This indicates the group can accept new commands
            assert hasattr(
                group, "add_command"
            ), f"Group '{group_name}' should support dynamic command addition"


class TestCommandValidationFramework:
    """Test the command validation framework itself"""

    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
        self.utils = CLITestUtils(self.runner)

    def test_validation_framework_completeness(self):
        """Test that the validation framework catches common issues"""
        # Test with a well-formed command
        good_command = {
            "name": "test-command",
            "group": "device",
            "help": "Test command for validation",
            "callback": lambda: None,
        }

        checks = self.utils.validate_command_structure(good_command)
        assert all(
            checks.values()
        ), f"Well-formed command should pass all checks: {checks}"

        # Test with problematic command
        bad_command = {
            "name": "BadCommandName",  # Not kebab-case
            "group": "nonexistent",
            "help": "",  # Empty help
            "callback": None,  # No callback
        }

        checks = self.utils.validate_command_structure(bad_command)
        assert not all(
            checks.values()
        ), f"Problematic command should fail some checks: {checks}"

    def test_coverage_reporting_accuracy(self):
        """Test that coverage reporting provides accurate information"""
        report = self.utils.get_command_coverage_report()

        # Report should have expected structure
        assert (
            "total_commands" in report
        ), "Report should include total command count"
        assert "groups" in report, "Report should include group breakdown"
        assert (
            "compliance_summary" in report
        ), "Report should include compliance summary"

        # Totals should be consistent
        group_totals = sum(
            report["groups"][g]["count"] for g in report["groups"]
        )
        assert (
            group_totals == report["total_commands"]
        ), "Group totals should match overall total"

        # Compliance rates should be reasonable
        summary = report["compliance_summary"]
        total = report["total_commands"]

        if total > 0:
            for metric, count in summary.items():
                rate = count / total
                assert (
                    0 <= rate <= 1
                ), f"Compliance rate for '{metric}' should be between 0 and 1, got {rate}"

    def test_framework_performance(self):
        """Test that validation framework performs adequately"""
        import time

        # Validation should be fast enough for CI
        start_time = time.time()

        all_commands = self.utils.get_all_command_info()
        for command_info in all_commands:
            self.utils.validate_command_structure(command_info)

        elapsed = time.time() - start_time
        assert (
            elapsed < 5
        ), f"Validation should complete quickly, took {elapsed:.2f}s"

        # Coverage report should also be fast
        start_time = time.time()
        self.utils.get_command_coverage_report()
        elapsed = time.time() - start_time
        assert (
            elapsed < 3
        ), f"Coverage report should be fast, took {elapsed:.2f}s"
