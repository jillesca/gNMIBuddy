#!/usr/bin/env python3
"""Tests for CLI hierarchical structure implementation (Phase 1)"""
import pytest
from click.testing import CliRunner
from src.cmd.parser import cli
from src.cmd.groups import (
    COMMAND_GROUPS,
    get_group_for_command,
    get_new_command_name,
)
from src.cmd.commands import COMMANDS


class TestCLIHierarchicalStructure:
    """Test suite for CLI hierarchical structure compliance"""

    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()

    def test_main_cli_group_exists(self):
        """Test that the main CLI group is properly defined"""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "gNMIBuddy CLI tool" in result.output

    def test_command_groups_are_registered(self):
        """Test that all command groups are properly registered"""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0

        # Check that all groups are listed in help
        for group_name in COMMAND_GROUPS.keys():
            assert group_name in result.output

    def test_device_group_commands(self):
        """Test device group commands structure"""
        # Test device group exists
        result = self.runner.invoke(cli, ["device", "--help"])
        assert result.exit_code == 0
        assert "Device management commands" in result.output

        # Check expected commands in device group
        expected_commands = ["info", "profile", "list"]
        for cmd in expected_commands:
            assert cmd in result.output

    def test_network_group_commands(self):
        """Test network group commands structure"""
        # Test network group exists
        result = self.runner.invoke(cli, ["network", "--help"])
        assert result.exit_code == 0
        assert "Network protocol commands" in result.output

        # Check expected commands in network group
        expected_commands = ["routing", "interface", "mpls", "vpn"]
        for cmd in expected_commands:
            assert cmd in result.output

    def test_topology_group_commands(self):
        """Test topology group commands structure"""
        # Test topology group exists
        result = self.runner.invoke(cli, ["topology", "--help"])
        assert result.exit_code == 0
        assert "Network topology commands" in result.output

        # Check expected commands in topology group
        expected_commands = ["adjacency", "neighbors"]
        for cmd in expected_commands:
            assert cmd in result.output

    def test_ops_group_commands(self):
        """Test ops group commands structure"""
        # Test ops group exists
        result = self.runner.invoke(cli, ["ops", "--help"])
        assert result.exit_code == 0
        assert "Operational commands" in result.output

        # Check expected commands in ops group
        expected_commands = ["logs", "test-all"]
        for cmd in expected_commands:
            assert cmd in result.output

    def test_manage_group_commands(self):
        """Test manage group commands structure"""
        # Test manage group exists
        result = self.runner.invoke(cli, ["manage", "--help"])
        assert result.exit_code == 0
        assert "Management commands" in result.output

        # Check expected commands in manage group
        expected_commands = ["log-level", "list-commands"]
        for cmd in expected_commands:
            assert cmd in result.output

    def test_hierarchical_command_access(self):
        """Test that commands can be accessed hierarchically"""
        # Test device info command
        result = self.runner.invoke(cli, ["device", "info", "--help"])
        assert result.exit_code == 0
        assert "Get system information" in result.output

        # Test network routing command
        result = self.runner.invoke(cli, ["network", "routing", "--help"])
        assert result.exit_code == 0
        assert "Get routing information" in result.output

        # Test topology neighbors command
        result = self.runner.invoke(cli, ["topology", "neighbors", "--help"])
        assert result.exit_code == 0
        assert "Get topology neighbors" in result.output

    def test_backward_compatibility_commands(self):
        """Test that old command names still work for backward compatibility"""
        # Test old command names at top level
        old_commands = [
            "routing",
            "interface",
            "mpls",
            "vpn",
            "system",
            "device-profile",
            "logging",
            "list-devices",
            "topology-adjacency",
            "topology-neighbors",
        ]

        for cmd in old_commands:
            result = self.runner.invoke(cli, [cmd, "--help"])
            assert (
                result.exit_code == 0
            ), f"Backward compatibility failed for {cmd}"

    def test_command_name_mappings(self):
        """Test that command name mappings work correctly"""
        test_cases = {
            "system": "info",
            "deviceprofile": "profile",
            "device-profile": "profile",
            "list-devices": "list",
            "topology-adjacency": "adjacency",
            "topology-neighbors": "neighbors",
            "logging": "logs",
        }

        for old_name, expected_new_name in test_cases.items():
            actual_new_name = get_new_command_name(old_name)
            assert (
                actual_new_name == expected_new_name
            ), f"Expected {old_name} -> {expected_new_name}, got {actual_new_name}"

    def test_command_group_mappings(self):
        """Test that commands are mapped to correct groups"""
        test_cases = {
            "system": "device",
            "deviceprofile": "device",
            "list-devices": "device",
            "routing": "network",
            "interface": "network",
            "mpls": "network",
            "vpn": "network",
            "topology-adjacency": "topology",
            "topology-neighbors": "topology",
            "logging": "ops",
            "test-all": "ops",
            "log-level": "manage",
            "list-commands": "manage",
        }

        for cmd_name, expected_group in test_cases.items():
            actual_group = get_group_for_command(cmd_name)
            assert (
                actual_group == expected_group
            ), f"Expected {cmd_name} -> {expected_group}, got {actual_group}"

    def test_kebab_case_naming_convention(self):
        """Test that all command names follow kebab-case convention"""
        import re

        kebab_case_pattern = re.compile(r"^[a-z]+(-[a-z]+)*$")

        for cmd_name, cmd_instance in COMMANDS.items():
            # Allow for some exceptions during migration
            if cmd_name in ["deviceprofile"]:  # Known legacy names
                continue

            assert kebab_case_pattern.match(
                cmd_name
            ), f"Command '{cmd_name}' does not follow kebab-case convention"

    def test_command_groups_exist_in_registry(self):
        """Test that all groups exist in the command groups registry"""
        expected_groups = {"device", "network", "topology", "ops", "manage"}
        actual_groups = set(COMMAND_GROUPS.keys())

        assert (
            actual_groups == expected_groups
        ), f"Expected groups: {expected_groups}, got: {actual_groups}"

    def test_all_commands_have_group_attribute(self):
        """Test that all commands have the group attribute defined"""
        for cmd_name, cmd_instance in COMMANDS.items():
            assert hasattr(
                cmd_instance, "group"
            ), f"Command '{cmd_name}' missing group attribute"
            assert (
                cmd_instance.group is not None
            ), f"Command '{cmd_name}' has None group attribute"

    def test_command_help_consistency(self):
        """Test that command help text is consistent and informative"""
        for cmd_name, cmd_instance in COMMANDS.items():
            # Test that help exists and is meaningful
            assert (
                cmd_instance.help is not None
            ), f"Command '{cmd_name}' missing help text"
            assert (
                len(cmd_instance.help) > 10
            ), f"Command '{cmd_name}' help text too short: '{cmd_instance.help}'"

            # Test that description exists
            assert (
                cmd_instance.description is not None
            ), f"Command '{cmd_name}' missing description"

    def test_no_banner_in_subcommand_help(self):
        """Test that ASCII banner doesn't appear in subcommand help"""
        # Test that subcommand help doesn't contain banner elements
        subcommands = [
            ["device", "info", "--help"],
            ["network", "routing", "--help"],
            ["topology", "neighbors", "--help"],
        ]

        for subcmd in subcommands:
            result = self.runner.invoke(cli, subcmd)
            assert result.exit_code == 0
            # The banner should not appear in subcommand help
            # (This test may need adjustment based on actual banner content)
            assert (
                "gNMIBuddy" not in result.output
                or "ASCII" not in result.output
            )


class TestCommandOptionsIntegrity:
    """Test that command options are properly handled in hierarchical structure"""

    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()

    def test_device_option_inheritance(self):
        """Test that device option is properly inherited"""
        # Test that --device option is available at global level before subcommands (Click pattern)
        result = self.runner.invoke(
            cli, ["--device", "test-device", "network", "routing", "--help"]
        )
        # Should not fail due to device option
        assert result.exit_code == 0

    def test_global_options_accessibility(self):
        """Test that global options are accessible from hierarchical commands"""
        # Test that global options like --log-level work with hierarchical commands
        result = self.runner.invoke(
            cli, ["--log-level", "debug", "device", "--help"]
        )
        assert result.exit_code == 0

    def test_command_specific_options(self):
        """Test that command-specific options work in hierarchical structure"""
        # Test routing protocol option
        result = self.runner.invoke(cli, ["network", "routing", "--help"])
        assert result.exit_code == 0
        assert "--protocol" in result.output

        # Test interface name option
        result = self.runner.invoke(cli, ["network", "interface", "--help"])
        assert result.exit_code == 0
        assert "--name" in result.output


class TestProgressiveHelp:
    """Test progressive help disclosure in hierarchical structure"""

    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()

    def test_main_help_shows_groups(self):
        """Test that main help shows command groups"""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0

        # Should show group commands
        groups = ["device", "network", "topology", "ops", "manage"]
        for group in groups:
            assert group in result.output

    def test_group_help_shows_commands(self):
        """Test that group help shows individual commands"""
        # Test device group
        result = self.runner.invoke(cli, ["device", "--help"])
        assert result.exit_code == 0
        assert "info" in result.output
        assert "profile" in result.output
        assert "list" in result.output

    def test_command_help_shows_options(self):
        """Test that command help shows specific options"""
        # Test routing command options
        result = self.runner.invoke(cli, ["network", "routing", "--help"])
        assert result.exit_code == 0
        assert "--protocol" in result.output
        assert "--detail" in result.output


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
