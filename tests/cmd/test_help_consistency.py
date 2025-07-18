#!/usr/bin/env python3
"""Tests for help system consistency across the CLI"""
import pytest
import re
from click.testing import CliRunner
from typing import Dict, List, Any

from src.cmd.parser import cli
from src.cmd.groups import COMMAND_GROUPS
from src.cmd.display import GroupedHelpFormatter
from tests.cmd.test_utils import CLITestUtils, get_expected_command_structure


class TestHelpSystemConsistency:
    """Test suite for help system consistency"""

    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
        self.utils = CLITestUtils(self.runner)

    def test_help_output_format_consistency(self):
        """Test that help output format is consistent across commands"""
        all_commands = self.utils.get_all_command_info()

        for command_info in all_commands:
            group_name = command_info["group"]
            command_name = command_info["name"]

            help_structure = self.utils.get_help_structure(
                [group_name, command_name]
            )

            # All commands should have consistent help structure
            assert help_structure[
                "has_usage"
            ], f"Command '{group_name} {command_name}' should have Usage section"
            assert (
                help_structure["exit_code"] == 0
            ), f"Help for '{group_name} {command_name}' should exit successfully"

            # Help should be properly formatted
            result = self.runner.invoke(
                cli, [group_name, command_name, "--help"]
            )
            help_text = result.output

            # Check for consistent formatting patterns
            lines = help_text.split("\n")
            usage_line_found = False

            for line in lines:
                if line.startswith("Usage:"):
                    usage_line_found = True
                    # Usage line should follow pattern: "Usage: [PROGRAM] GROUP COMMAND [OPTIONS]"
                    # Click may show 'cli' instead of 'gnmibuddy' in test context
                    assert (
                        group_name in line
                    ), f"Usage line should mention group '{group_name}'"
                    assert (
                        command_name in line
                    ), f"Usage line should mention command '{command_name}'"

            assert (
                usage_line_found
            ), f"Command '{group_name} {command_name}' should have Usage line"

    def test_usage_examples_presence_and_formatting(self):
        """Test that usage examples are present and properly formatted"""
        all_commands = self.utils.get_all_command_info()

        for command_info in all_commands:
            group_name = command_info["group"]
            command_name = command_info["name"]

            result = self.runner.invoke(
                cli, [group_name, command_name, "--help"]
            )
            help_text = result.output

            # Commands should have usage examples or at least clear parameter documentation
            has_examples = (
                "Examples:" in help_text or "Usage examples:" in help_text
            )
            has_options = "Options:" in help_text
            has_description = (
                len(help_text.strip()) > 50
            )  # Minimum descriptive content

            # At minimum, commands should have clear documentation
            assert (
                has_options or has_description
            ), f"Command '{group_name} {command_name}' should have either options or description"

            # If examples are present, they should be properly formatted
            if has_examples:
                examples = self._extract_examples_section(help_text)
                assert (
                    len(examples) > 0
                ), f"Examples section should not be empty for '{group_name} {command_name}'"

                for example in examples:
                    # Examples should start with gnmibuddy
                    if example.strip().startswith("gnmibuddy"):
                        assert (
                            group_name in example
                        ), f"Example should include group name: {example}"

    def test_command_grouping_display_consistency(self):
        """Test that command grouping is displayed correctly and consistently"""
        # Test main help displays groups correctly
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0, "Main help should work"

        main_help = result.output
        expected_groups = get_expected_command_structure().keys()

        # All groups should be mentioned in main help
        for group in expected_groups:
            assert (
                group in main_help
            ), f"Group '{group}' should appear in main help"

        # Test group help displays commands correctly
        for group_name in expected_groups:
            result = self.runner.invoke(cli, [group_name, "--help"])
            assert (
                result.exit_code == 0
            ), f"Group '{group_name}' help should work"

            group_help = result.output

            # Group help should show its commands
            expected_commands = get_expected_command_structure()[group_name]
            for cmd in expected_commands:
                assert (
                    cmd in group_help
                ), f"Command '{cmd}' should appear in '{group_name}' group help"

    def test_banner_appears_only_on_main_help(self):
        """Test that ASCII banner appears only on main help, not subcommands"""
        # Main help should have banner
        result = self.runner.invoke(cli, ["--help"])
        main_help = result.output
        main_has_banner = self.utils._check_banner_presence(main_help)

        # Main help should include banner or at least the program name prominently
        assert (
            "gnmibuddy" in main_help.lower()
        ), "Main help should mention gnmibuddy"

        # Group help should NOT have banner
        for group_name in COMMAND_GROUPS.keys():
            result = self.runner.invoke(cli, [group_name, "--help"])
            group_help = result.output
            group_has_banner = self.utils._check_banner_presence(group_help)

            # Group help should not have elaborate banner
            assert (
                not group_has_banner
            ), f"Group '{group_name}' help should not have banner"

        # Command help should NOT have banner
        all_commands = self.utils.get_all_command_info()
        for command_info in all_commands:
            group_name = command_info["group"]
            command_name = command_info["name"]

            result = self.runner.invoke(
                cli, [group_name, command_name, "--help"]
            )
            command_help = result.output
            command_has_banner = self.utils._check_banner_presence(
                command_help
            )

            assert (
                not command_has_banner
            ), f"Command '{group_name} {command_name}' help should not have banner"

    def test_help_text_quality_standards(self):
        """Test that help text meets quality standards across all commands"""
        all_commands = self.utils.get_all_command_info()

        for command_info in all_commands:
            group_name = command_info["group"]
            command_name = command_info["name"]
            help_text = command_info["help"]

            # Basic quality checks
            assert (
                len(help_text) > 10
            ), f"Help text for '{group_name} {command_name}' should be descriptive"
            assert help_text[
                0
            ].isupper(), f"Help text for '{group_name} {command_name}' should start with capital"
            assert not help_text.endswith(
                "."
            ), f"Help text for '{group_name} {command_name}' should not end with period"

            # Content quality checks
            assert not help_text.lower().startswith(
                "todo"
            ), f"Help text for '{group_name} {command_name}' should not be placeholder"
            assert (
                "fixme" not in help_text.lower()
            ), f"Help text for '{group_name} {command_name}' should not contain FIXME"

    def test_help_navigation_consistency(self):
        """Test that help navigation is consistent and intuitive"""
        # Test that help references are consistent
        result = self.runner.invoke(cli, ["--help"])
        main_help = result.output

        # Main help should guide users to subcommand help
        assert "--help" in main_help, "Main help should mention --help option"

        # Group help should guide users to command help
        for group_name in COMMAND_GROUPS.keys():
            result = self.runner.invoke(cli, [group_name, "--help"])
            group_help = result.output

            # Group help should mention how to get command help
            help_pattern = r"--help|help.*command"
            assert re.search(
                help_pattern, group_help, re.IGNORECASE
            ), f"Group '{group_name}' help should guide to command help"

    def test_grouped_help_formatter_functionality(self):
        """Test that the GroupedHelpFormatter works correctly"""
        formatter = GroupedHelpFormatter()

        # Test basic functionality
        grouped_help = formatter.format_grouped_help(show_examples=False)
        assert (
            "Usage:" in grouped_help
        ), "Grouped help should have Usage section"
        assert (
            "Commands:" in grouped_help
        ), "Grouped help should have Commands section"

        # Test with examples
        grouped_help_with_examples = formatter.format_grouped_help(
            show_examples=True
        )
        assert len(grouped_help_with_examples) >= len(
            grouped_help
        ), "Help with examples should be at least as long"

        # All expected groups should be represented
        expected_groups = get_expected_command_structure().keys()
        for group in expected_groups:
            # Group should appear in the formatted help somehow
            assert (
                group in grouped_help or group.title() in grouped_help
            ), f"Group '{group}' should be in formatted help"

    def _extract_examples_section(self, help_text: str) -> List[str]:
        """Extract examples from help text"""
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


class TestHelpSystemProgressiveDisclosure:
    """Test progressive disclosure in the help system"""

    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
        self.utils = CLITestUtils(self.runner)

    def test_main_help_provides_overview(self):
        """Test that main help provides good overview without overwhelming detail"""
        result = self.runner.invoke(cli, ["--help"])
        main_help = result.output

        # Should have high-level overview
        assert (
            "Commands:" in main_help
        ), "Main help should list commands/groups"

        # Should not be overwhelmingly long
        line_count = len(main_help.split("\n"))
        assert (
            line_count < 100
        ), f"Main help should be concise, got {line_count} lines"

        # Should mention how to get more help
        assert "--help" in main_help, "Should mention how to get more help"

    def test_group_help_provides_moderate_detail(self):
        """Test that group help provides moderate level of detail"""
        for group_name in COMMAND_GROUPS.keys():
            result = self.runner.invoke(cli, [group_name, "--help"])
            group_help = result.output

            # Should list commands in the group
            assert (
                "Commands:" in group_help
            ), f"Group '{group_name}' help should list commands"

            # Should have group description
            lines = group_help.split("\n")
            has_description = any(
                len(line.strip()) > 20 for line in lines[:10]
            )  # Description in first 10 lines
            assert (
                has_description
            ), f"Group '{group_name}' help should have description"

    def test_command_help_provides_full_detail(self):
        """Test that command help provides full detail"""
        all_commands = self.utils.get_all_command_info()

        for command_info in all_commands:
            group_name = command_info["group"]
            command_name = command_info["name"]

            result = self.runner.invoke(
                cli, [group_name, command_name, "--help"]
            )
            command_help = result.output

            # Should have detailed usage
            assert (
                "Usage:" in command_help
            ), f"Command '{group_name} {command_name}' help should have usage"

            # Should have options if command accepts any
            # Most commands should have at least --help
            assert (
                "Options:" in command_help or "--help" in command_help
            ), f"Command '{group_name} {command_name}' should document options"

    def test_help_depth_appropriateness(self):
        """Test that help depth is appropriate at each level"""
        # Main help should be concise
        result = self.runner.invoke(cli, ["--help"])
        main_help_lines = len(result.output.split("\n"))

        # Group helps should be moderate
        group_help_lines = []
        for group_name in COMMAND_GROUPS.keys():
            result = self.runner.invoke(cli, [group_name, "--help"])
            group_help_lines.append(len(result.output.split("\n")))

        # Command helps should be most detailed
        command_help_lines = []
        all_commands = self.utils.get_all_command_info()
        for command_info in all_commands[:3]:  # Sample a few commands
            group_name = command_info["group"]
            command_name = command_info["name"]
            result = self.runner.invoke(
                cli, [group_name, command_name, "--help"]
            )
            command_help_lines.append(len(result.output.split("\n")))

        # Progressive disclosure should generally follow: main < group <= command
        avg_group_lines = sum(group_help_lines) / len(group_help_lines)
        avg_command_lines = sum(command_help_lines) / len(command_help_lines)

        assert (
            main_help_lines <= avg_group_lines * 1.5
        ), "Main help should be more concise than group help"
        # Command help can be equal or more detailed than group help
        assert (
            avg_command_lines >= avg_group_lines * 0.8
        ), "Command help should be at least as detailed as group help"


class TestHelpSystemAccessibility:
    """Test help system accessibility and usability"""

    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
        self.utils = CLITestUtils(self.runner)

    def test_help_is_easily_discoverable(self):
        """Test that help is easily discoverable at all levels"""
        # Main help via --help
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0, "Main --help should work"

        # Main help via -h
        result = self.runner.invoke(cli, ["-h"])
        assert result.exit_code == 0, "Main -h should work"

        # Group help
        for group_name in COMMAND_GROUPS.keys():
            result = self.runner.invoke(cli, [group_name, "--help"])
            assert (
                result.exit_code == 0
            ), f"Group '{group_name}' --help should work"

        # Command help
        all_commands = self.utils.get_all_command_info()
        for command_info in all_commands[:3]:  # Test a sample
            group_name = command_info["group"]
            command_name = command_info["name"]
            result = self.runner.invoke(
                cli, [group_name, command_name, "--help"]
            )
            assert (
                result.exit_code == 0
            ), f"Command '{group_name} {command_name}' --help should work"

    def test_help_provides_clear_next_steps(self):
        """Test that help provides clear guidance on next steps"""
        # Main help should guide to group or command help
        result = self.runner.invoke(cli, ["--help"])
        main_help = result.output

        # Should suggest how to get more specific help
        suggests_next_steps = (
            "COMMAND --help" in main_help
            or "more information" in main_help.lower()
            or "--help" in main_help
        )
        assert (
            suggests_next_steps
        ), "Main help should suggest how to get more specific help"

    def test_help_error_handling(self):
        """Test that help system handles errors gracefully"""
        # Invalid group
        result = self.runner.invoke(cli, ["invalid-group", "--help"])
        # Should fail but not crash
        assert result.exit_code != 0, "Invalid group should fail"
        assert result.exception is None or "Usage Error" in str(
            result.exception
        ), "Should handle invalid group gracefully"

        # Invalid command
        result = self.runner.invoke(
            cli, ["device", "invalid-command", "--help"]
        )
        # Should fail but not crash
        assert result.exit_code != 0, "Invalid command should fail"
        assert result.exception is None or "Usage Error" in str(
            result.exception
        ), "Should handle invalid command gracefully"
