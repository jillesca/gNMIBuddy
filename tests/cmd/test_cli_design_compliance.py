#!/usr/bin/env python3
"""Tests for CLI design compliance - ensures CLI follows established design patterns"""
import pytest
import re
from click.testing import CliRunner
from typing import Dict, List, Any

from src.cmd.parser import cli
from src.cmd.groups import COMMAND_GROUPS
from tests.cmd.test_utils import (
    CLITestUtils,
    assert_command_structure_valid,
    assert_kebab_case,
    assert_help_quality,
    get_expected_command_structure,
    get_expected_aliases,
)


class TestCLIDesignCompliance:
    """Test suite for CLI design compliance"""

    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
        self.utils = CLITestUtils(self.runner)

    def test_all_commands_follow_hierarchical_structure(self):
        """Test that all commands follow the established hierarchical structure"""
        expected_structure = get_expected_command_structure()

        for group_name, expected_commands in expected_structure.items():
            # Verify group exists
            assert (
                group_name in COMMAND_GROUPS
            ), f"Group '{group_name}' should exist"

            group = COMMAND_GROUPS[group_name]
            actual_commands = list(getattr(group, "commands", {}).keys())

            # Verify all expected commands are present
            for cmd in expected_commands:
                assert (
                    cmd in actual_commands
                ), f"Command '{cmd}' should be in group '{group_name}'"

            # Verify no unexpected commands
            for cmd in actual_commands:
                assert (
                    cmd in expected_commands
                ), f"Unexpected command '{cmd}' in group '{group_name}'"

    def test_command_names_use_kebab_case_convention(self):
        """Test that all command names use consistent kebab-case convention"""
        all_commands = self.utils.get_all_command_info()

        for command_info in all_commands:
            command_name = command_info["name"]
            assert_kebab_case(command_name)

    def test_all_commands_belong_to_appropriate_groups(self):
        """Test that all commands belong to appropriate groups"""
        expected_groups = {"device", "network", "topology", "ops", "manage"}
        all_commands = self.utils.get_all_command_info()

        for command_info in all_commands:
            group = command_info["group"]
            assert (
                group in expected_groups
            ), f"Command '{command_info['name']}' belongs to unexpected group '{group}'"

    def test_command_descriptions_meet_quality_standards(self):
        """Test that command descriptions and help text meet quality standards"""
        all_commands = self.utils.get_all_command_info()

        for command_info in all_commands:
            help_text = command_info["help"]
            command_name = command_info["name"]

            # Help text should exist and be descriptive
            assert help_text, f"Command '{command_name}' must have help text"
            assert (
                len(help_text) > 10
            ), f"Command '{command_name}' help text should be descriptive (> 10 chars)"

            # Help text should start with capital letter
            assert help_text[
                0
            ].isupper(), f"Command '{command_name}' help text should start with capital letter"

            # Help text should not end with period (Click convention)
            assert not help_text.strip().endswith(
                "."
            ), f"Command '{command_name}' help text should not end with period"

    def test_all_commands_have_required_structure(self):
        """Test that all commands have the required structural elements"""
        all_commands = self.utils.get_all_command_info()

        for command_info in all_commands:
            assert_command_structure_valid(command_info)

            # Additional structural checks
            structure_checks = self.utils.validate_command_structure(
                command_info
            )
            failed_checks = [
                check
                for check, passed in structure_checks.items()
                if not passed
            ]

            assert (
                not failed_checks
            ), f"Command '{command_info['name']}' failed checks: {failed_checks}"

    def test_command_groups_have_proper_metadata(self):
        """Test that command groups have proper metadata and structure"""
        for group_name, group in COMMAND_GROUPS.items():
            # Group should have help/docstring
            assert hasattr(group, "help") or hasattr(
                group, "__doc__"
            ), f"Group '{group_name}' should have help text"

            # Group should have commands
            assert hasattr(
                group, "commands"
            ), f"Group '{group_name}' should have commands attribute"

            # Group name should follow naming convention
            assert_kebab_case(group_name)

    def test_no_orphaned_commands(self):
        """Test that there are no commands without proper group assignment"""
        all_commands = self.utils.get_all_command_info()

        for command_info in all_commands:
            group_name = command_info["group"]

            # Command should be properly registered in its group
            assert (
                group_name in COMMAND_GROUPS
            ), f"Command '{command_info['name']}' references non-existent group '{group_name}'"

            group = COMMAND_GROUPS[group_name]
            command_name = command_info["name"]

            assert hasattr(
                group, "commands"
            ), f"Group '{group_name}' should have commands attribute"
            assert (
                command_name in group.commands
            ), f"Command '{command_name}' not properly registered in group '{group_name}'"

    def test_command_help_consistency(self):
        """Test that command help text is consistent across the CLI"""
        all_commands = self.utils.get_all_command_info()

        for command_info in all_commands:
            command_name = command_info["name"]
            group_name = command_info["group"]

            # Test help structure for each command
            help_structure = self.utils.get_help_structure(
                [group_name, command_name]
            )

            assert (
                "error" not in help_structure
            ), f"Help for '{group_name} {command_name}' failed: {help_structure.get('error')}"
            assert help_structure[
                "has_usage"
            ], f"Help for '{group_name} {command_name}' should have usage section"
            assert (
                help_structure["exit_code"] == 0
            ), f"Help for '{group_name} {command_name}' should exit successfully"

    def test_command_registration_completeness(self):
        """Test that command registration is complete and consistent"""
        # All groups should be registered in COMMAND_GROUPS
        expected_groups = get_expected_command_structure().keys()

        for group_name in expected_groups:
            assert (
                group_name in COMMAND_GROUPS
            ), f"Group '{group_name}' should be registered in COMMAND_GROUPS"

    def test_cli_follows_unix_conventions(self):
        """Test that CLI follows standard Unix CLI conventions"""
        # Test main help
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0, "Main help should exit successfully"

        help_text = result.output

        # Should have standard sections
        assert "Usage:" in help_text, "Help should have Usage section"
        assert "Options:" in help_text, "Help should have Options section"
        assert "Commands:" in help_text, "Help should have Commands section"

        # Should show help option
        assert "--help" in help_text, "Help should mention --help option"

    def test_command_structure_scalability(self):
        """Test that command structure supports future expansion"""
        # Verify that the structure supports adding new commands
        all_commands = self.utils.get_all_command_info()

        # Each group should have reasonable number of commands (not too many)
        group_command_counts = {}
        for command_info in all_commands:
            group = command_info["group"]
            group_command_counts[group] = (
                group_command_counts.get(group, 0) + 1
            )

        for group, count in group_command_counts.items():
            assert (
                count <= 10
            ), f"Group '{group}' has too many commands ({count}), consider sub-grouping"
            assert (
                count >= 1
            ), f"Group '{group}' should have at least one command"


class TestCLIStructuralIntegrity:
    """Test structural integrity of the CLI architecture"""

    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
        self.utils = CLITestUtils(self.runner)

    def test_no_circular_dependencies(self):
        """Test that there are no circular dependencies in command structure"""
        # This is mainly relevant for the architecture
        # For Click-based CLI, this is less of an issue, but we can check imports

        all_commands = self.utils.get_all_command_info()
        command_names = [cmd["name"] for cmd in all_commands]

        # No command should reference itself or create cycles
        for command_info in all_commands:
            callback = command_info.get("callback")
            if callback and hasattr(callback, "__name__"):
                assert (
                    callback.__name__ != command_info["name"]
                ), f"Command '{command_info['name']}' should not reference itself"

    def test_command_isolation(self):
        """Test that commands are properly isolated and don't interfere with each other"""
        all_commands = self.utils.get_all_command_info()

        # Each command should have unique name within its scope
        command_names_by_group = {}

        for command_info in all_commands:
            group = command_info["group"]
            name = command_info["name"]

            if group not in command_names_by_group:
                command_names_by_group[group] = []

            assert (
                name not in command_names_by_group[group]
            ), f"Duplicate command name '{name}' in group '{group}'"
            command_names_by_group[group].append(name)

    def test_group_hierarchy_consistency(self):
        """Test that group hierarchy is consistent and logical"""
        expected_structure = get_expected_command_structure()

        # Verify logical grouping
        network_commands = expected_structure["network"]
        device_commands = expected_structure["device"]

        # Network commands should be protocol-related
        protocol_keywords = ["routing", "interface", "mpls", "vpn"]
        for cmd in network_commands:
            assert any(
                keyword in cmd for keyword in protocol_keywords
            ), f"Network command '{cmd}' should be protocol-related"

        # Device commands should be device-management related
        device_keywords = ["info", "profile", "list"]
        for cmd in device_commands:
            assert any(
                keyword in cmd for keyword in device_keywords
            ), f"Device command '{cmd}' should be device-management related"

    def test_architecture_extensibility(self):
        """Test that the architecture supports future extensions"""
        # The CLI should be structured to allow easy addition of new commands

        # All groups should follow the same pattern
        for group_name, group in COMMAND_GROUPS.items():
            # Should have Click group decorator
            assert hasattr(
                group, "commands"
            ), f"Group '{group_name}' should be a Click group"

            # Should have help text
            help_text = getattr(group, "help", "") or getattr(
                group, "__doc__", ""
            )
            assert (
                help_text
            ), f"Group '{group_name}' should have help text for documentation"


class TestFutureProofing:
    """Tests that ensure the CLI will remain compliant as it evolves"""

    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
        self.utils = CLITestUtils(self.runner)

    def test_compliance_automation_ready(self):
        """Test that compliance checking can be automated for future changes"""
        # Generate a comprehensive compliance report
        report = self.utils.get_command_coverage_report()

        # The report should be comprehensive
        assert report["total_commands"] > 0, "Should detect existing commands"
        assert len(report["groups"]) == 5, "Should detect all 5 groups"

        # Compliance metrics should be measurable
        summary = report["compliance_summary"]
        total = report["total_commands"]

        compliance_rate = summary["structure_compliant"] / total
        assert (
            compliance_rate >= 0.9
        ), f"Compliance rate should be >= 90%, got {compliance_rate:.2%}"

    def test_new_command_validation_framework(self):
        """Test that the framework can validate new commands automatically"""
        # This test simulates adding a new command and validates it would pass compliance

        mock_command_info = {
            "name": "new-test-command",
            "group": "device",
            "help": "Test command for validation framework",
            "callback": lambda: None,
        }

        # The validation framework should work for new commands
        structure_checks = self.utils.validate_command_structure(
            mock_command_info
        )

        # All checks should be verifiable
        assert isinstance(
            structure_checks, dict
        ), "Validation should return checkable results"
        assert "has_name" in structure_checks, "Should check for name presence"
        assert (
            "name_follows_kebab_case" in structure_checks
        ), "Should check naming convention"
        assert "has_help" in structure_checks, "Should check for help text"

    def test_regression_detection_capability(self):
        """Test that the framework can detect regressions in CLI design"""
        # Test various scenarios that could cause regressions

        # Test 1: Invalid command name would be caught
        invalid_command_info = {
            "name": "InvalidCommandName",  # Not kebab-case
            "group": "device",
            "help": "Invalid command name",
            "callback": lambda: None,
        }

        checks = self.utils.validate_command_structure(invalid_command_info)
        assert not checks[
            "name_follows_kebab_case"
        ], "Should detect invalid naming"

        # Test 2: Missing help would be caught
        missing_help_command = {
            "name": "valid-name",
            "group": "device",
            "help": "",  # Empty help
            "callback": lambda: None,
        }

        checks = self.utils.validate_command_structure(missing_help_command)
        assert not checks["has_help"], "Should detect missing help"

    def test_continuous_integration_readiness(self):
        """Test that these tests are suitable for CI/CD pipeline"""
        # Tests should be fast
        import time

        start_time = time.time()

        # Run a basic compliance check
        all_commands = self.utils.get_all_command_info()
        for command_info in all_commands:
            self.utils.validate_command_structure(command_info)

        elapsed_time = time.time() - start_time
        assert (
            elapsed_time < 10
        ), f"Compliance tests should run quickly, took {elapsed_time:.2f}s"

        # Tests should be deterministic (no random behavior)
        # Re-run the same test multiple times
        results = []
        for _ in range(3):
            report = self.utils.get_command_coverage_report()
            results.append(report["total_commands"])

        assert all(
            r == results[0] for r in results
        ), "Tests should be deterministic"
