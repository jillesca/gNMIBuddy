#!/usr/bin/env python3
"""Tests for the enhanced CLI help system and user experience"""
import pytest
from click.testing import CliRunner
from unittest.mock import patch, Mock
import re

from src.cmd.parser import cli
from src.cmd.display import GroupedHelpFormatter, display_all_commands
from src.cmd.error_handler import CLIErrorHandler, error_handler


class TestHelpSystemStructure:
    """Test the structure and organization of the help system"""

    def test_grouped_help_formatter_initialization(self):
        """Test that GroupedHelpFormatter initializes correctly"""
        formatter = GroupedHelpFormatter()

        assert hasattr(formatter, "command_descriptions")
        assert hasattr(formatter, "group_descriptions")

        # Check that all expected groups are present
        expected_groups = ["device", "network", "topology", "ops", "manage"]
        for group in expected_groups:
            assert group in formatter.group_descriptions

    def test_grouped_help_format_structure(self):
        """Test that grouped help follows the expected structure"""
        formatter = GroupedHelpFormatter()
        help_text = formatter.format_grouped_help(show_examples=False)

        # Check for key sections
        assert "Usage: gnmibuddy" in help_text
        assert "Options:" in help_text
        assert "Commands:" in help_text

        # Check for command groups
        assert "Device Information:" in help_text
        assert "Network Protocols:" in help_text
        assert "Network Topology:" in help_text
        assert "Operations:" in help_text
        assert "Management:" in help_text

    def test_grouped_help_with_examples(self):
        """Test that examples are included when requested"""
        formatter = GroupedHelpFormatter()
        help_text = formatter.format_grouped_help(show_examples=True)

        # Check for examples section
        assert "Examples:" in help_text
        assert "uv run gnmibuddy.py device info --device R1" in help_text
        assert "uv run gnmibuddy.py network routing --device R1" in help_text
        assert (
            "uv run gnmibuddy.py d info --device R1" in help_text
        )  # Alias example

    def test_group_aliases_displayed(self):
        """Test that group aliases are displayed in help"""
        formatter = GroupedHelpFormatter()
        help_text = formatter.format_grouped_help()

        # Check for alias display
        assert "(d)" in help_text  # device alias
        assert "(n)" in help_text  # network alias
        assert "(t)" in help_text  # topology alias
        assert "(o)" in help_text  # ops alias
        assert "(m)" in help_text  # manage alias


class TestMainHelpBehavior:
    """Test the main CLI help behavior and banner display"""

    def test_main_help_shows_banner(self):
        """Test that main help shows the banner"""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        # Should include banner
        assert "▗▄▄▖▗▖  ▗▖▗▖  ▗▖▗▄▄▄▖" in result.output  # Part of ASCII banner
        assert "gNMIBuddy" in result.output
        assert result.exit_code == 0

    def test_main_help_no_subcommand(self):
        """Test help when no subcommand is provided"""
        runner = CliRunner()
        result = runner.invoke(cli, [])

        # Should show banner and grouped help
        assert "▗▄▄▖▗▖  ▗▖▗▖  ▗▖▗▄▄▄▖" in result.output  # Banner
        assert "Device Information:" in result.output
        assert "Examples:" in result.output
        assert result.exit_code == 0

    def test_subcommand_help_no_banner(self):
        """Test that subcommand help doesn't show banner"""
        runner = CliRunner()
        result = runner.invoke(cli, ["device", "--help"])

        # Should not include banner but should show group help
        assert "▗▄▄▖▗▖  ▗▖▗▖  ▗▖▗▄▄▄▖" not in result.output  # No banner
        assert "device" in result.output.lower()
        assert result.exit_code == 0


class TestCommandAliases:
    """Test command alias functionality"""

    def test_group_aliases_work(self):
        """Test that all group aliases are functional"""
        runner = CliRunner()

        # Test device alias
        result = runner.invoke(cli, ["d", "--help"])
        assert result.exit_code == 0
        assert "device" in result.output.lower()

        # Test network alias
        result = runner.invoke(cli, ["n", "--help"])
        assert result.exit_code == 0
        assert "network" in result.output.lower()

        # Test topology alias
        result = runner.invoke(cli, ["t", "--help"])
        assert result.exit_code == 0
        assert "topology" in result.output.lower()

        # Test ops alias
        result = runner.invoke(cli, ["o", "--help"])
        assert result.exit_code == 0

        # Test manage alias
        result = runner.invoke(cli, ["m", "--help"])
        assert result.exit_code == 0

    def test_alias_equivalence(self):
        """Test that aliases produce equivalent help to full names"""
        runner = CliRunner()

        # Compare device vs d
        full_result = runner.invoke(cli, ["device", "--help"])
        alias_result = runner.invoke(cli, ["d", "--help"])

        # Should have similar content (allowing for some differences in formatting)
        assert full_result.exit_code == alias_result.exit_code == 0

        # Both should mention device commands
        assert "device" in full_result.output.lower()
        assert "device" in alias_result.output.lower()


class TestCommandHelp:
    """Test individual command help with examples"""

    def test_device_info_help_has_examples(self):
        """Test that device info command help includes examples"""
        runner = CliRunner()
        result = runner.invoke(cli, ["device", "info", "--help"])

        assert result.exit_code == 0
        assert "Examples:" in result.output
        assert "uv run gnmibuddy.py device info --device R1" in result.output
        assert (
            "uv run gnmibuddy.py d info --device R1" in result.output
        )  # Alias example

    def test_network_routing_help_has_examples(self):
        """Test that network routing command help includes examples"""
        runner = CliRunner()
        result = runner.invoke(cli, ["network", "routing", "--help"])

        assert result.exit_code == 0
        assert "Examples:" in result.output
        assert (
            "uv run gnmibuddy.py network routing --device R1" in result.output
        )
        assert "--protocol bgp" in result.output
        assert (
            "uv run gnmibuddy.py n routing" in result.output
        )  # Alias example

    def test_interface_help_has_examples(self):
        """Test that interface command help includes examples"""
        runner = CliRunner()
        result = runner.invoke(cli, ["network", "interface", "--help"])

        assert result.exit_code == 0
        assert "Examples:" in result.output
        assert "GigabitEthernet0/0/0/1" in result.output
        assert (
            "uv run gnmibuddy.py n interface" in result.output
        )  # Alias example


class TestErrorHandling:
    """Test enhanced error handling with suggestions"""

    def test_error_handler_initialization(self):
        """Test that error handler initializes correctly"""
        handler = CLIErrorHandler()

        assert hasattr(handler, "all_groups")
        assert hasattr(handler, "all_commands")
        assert hasattr(handler, "group_aliases")

        # Check that aliases are mapped correctly
        assert handler.group_aliases["d"] == "device"
        assert handler.group_aliases["n"] == "network"

    def test_unknown_command_suggestions(self):
        """Test suggestions for unknown commands"""
        handler = CLIErrorHandler()

        # Test suggestion for similar group name
        error_msg = handler.handle_unknown_command("devic", "root")
        assert "Did you mean one of these groups?" in error_msg
        assert "device" in error_msg

    def test_missing_device_option_help(self):
        """Test help for missing --device option"""
        handler = CLIErrorHandler()

        error_msg = handler.handle_missing_option("info", "--device")
        assert "Missing required option '--device'" in error_msg
        assert (
            "uv run gnmibuddy.py device list" in error_msg
        )  # Suggestion to see devices
        assert "Examples:" in error_msg

    def test_unknown_command_in_group_context(self):
        """Test unknown command suggestions in group context"""
        handler = CLIErrorHandler()

        error_msg = handler.handle_unknown_command("rout", "network")
        assert "Did you mean one of these commands in 'network'?" in error_msg
        assert "routing" in error_msg

    def test_fuzzy_matching_quality(self):
        """Test the quality of fuzzy string matching"""
        handler = CLIErrorHandler()

        # Test that close matches are found
        candidates = ["routing", "interface", "mpls", "vpn"]
        matches = handler._find_similar_items("rout", candidates)
        assert "routing" in matches

        matches = handler._find_similar_items("interf", candidates)
        assert "interface" in matches

    def test_device_not_found_suggestions(self):
        """Test suggestions when device is not found"""
        handler = CLIErrorHandler()

        # Mock the inventory manager
        with patch("src.inventory.manager.InventoryManager") as mock_inventory:
            mock_instance = Mock()
            mock_instance.get_devices.return_value = {
                "R1": Mock(),
                "R2": Mock(),
                "PE1": Mock(),
            }
            mock_inventory.get_instance.return_value = mock_instance

            error_msg = handler.handle_device_not_found("R")
            assert "Device 'R' not found" in error_msg
            assert "Did you mean one of these devices?" in error_msg
            assert "R1" in error_msg or "R2" in error_msg


class TestHelpSystemConsistency:
    """Test consistency across the help system"""

    def test_all_groups_have_descriptions(self):
        """Test that all command groups have descriptions"""
        formatter = GroupedHelpFormatter()

        from src.cmd.groups import COMMAND_GROUPS

        for group_name in COMMAND_GROUPS.keys():
            assert group_name in formatter.group_descriptions
            title, desc = formatter.group_descriptions[group_name]
            assert len(title) > 0
            assert len(desc) > 0

    def test_command_descriptions_exist(self):
        """Test that command descriptions exist for common commands"""
        formatter = GroupedHelpFormatter()

        common_commands = [
            "info",
            "profile",
            "list",
            "routing",
            "interface",
            "neighbors",
        ]
        for command in common_commands:
            assert command in formatter.command_descriptions
            assert (
                len(formatter.command_descriptions[command]) > 10
            )  # Reasonable length

    def test_group_alias_consistency(self):
        """Test that group aliases are consistent across the system"""
        formatter = GroupedHelpFormatter()
        handler = CLIErrorHandler()

        # Both should have the same aliases
        for group in ["device", "network", "topology", "ops", "manage"]:
            formatter_alias = formatter._get_group_alias(group)
            handler_reverse = handler.group_aliases.get(formatter_alias)
            if formatter_alias:  # If alias exists
                assert handler_reverse == group

    def test_help_format_consistency(self):
        """Test that help format is consistent across commands"""
        runner = CliRunner()

        # Test several commands for consistent format
        commands_to_test = [
            ["device", "info", "--help"],
            ["network", "routing", "--help"],
            ["network", "interface", "--help"],
            ["topology", "neighbors", "--help"],
        ]

        for cmd in commands_to_test:
            result = runner.invoke(cli, cmd)
            assert result.exit_code == 0

            # Each should have usage line
            assert "Usage:" in result.output

            # Each should have options section
            assert "Options:" in result.output


class TestProgressiveDisclosure:
    """Test progressive disclosure in the help system"""

    def test_main_help_overview(self):
        """Test that main help provides good overview"""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0

        # Should show all groups but not individual commands in detail
        assert "Device Information:" in result.output
        assert "Network Protocols:" in result.output

        # Should provide guidance for getting more specific help
        assert "Run 'uv run gnmibuddy.py COMMAND --help'" in result.output
        assert "Run 'uv run gnmibuddy.py GROUP --help'" in result.output

    def test_group_help_detail(self):
        """Test that group help provides appropriate detail"""
        runner = CliRunner()
        result = runner.invoke(cli, ["device", "--help"])

        assert result.exit_code == 0

        # Should show commands in this group
        assert "info" in result.output
        assert "profile" in result.output
        assert "list" in result.output

        # Should provide guidance for command-specific help
        assert (
            "Run 'uv run gnmibuddy.py device COMMAND --help'" in result.output
        )

    def test_command_help_specificity(self):
        """Test that command help is specific and actionable"""
        runner = CliRunner()
        result = runner.invoke(cli, ["device", "info", "--help"])

        assert result.exit_code == 0

        # Should show specific options
        assert "--device" in result.output
        assert "--detail" in result.output

        # Should show examples
        assert "Examples:" in result.output
        assert "uv run gnmibuddy.py device info --device R1" in result.output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
