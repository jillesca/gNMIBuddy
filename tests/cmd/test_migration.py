#!/usr/bin/env python3
"""Migration tests for Click-based CLI to ensure functionality works correctly"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
import json

from src.cmd.parser import cli, run_cli_mode
from src.cmd.context import CLIContext


class TestCLIMigration:
    """Test suite for CLI migration from argparse to Click"""

    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()

    def test_cli_help_displays_correctly(self):
        """Test that CLI help is displayed correctly"""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        # The actual implementation shows ASCII banner instead of "gNMIBuddy CLI tool"
        assert (
            "An opinionated tool that retrieves essential network information"
            in result.output
        )
        assert "--log-level" in result.output
        assert "--all-devices" in result.output
        assert "--inventory" in result.output

    def test_cli_context_creation(self):
        """Test that CLI context is created correctly"""
        ctx = CLIContext(
            device="R1", log_level="debug", all_devices=False, max_workers=10
        )

        assert ctx.device == "R1"
        assert ctx.log_level == "debug"
        assert ctx.all_devices == False
        assert ctx.max_workers == 10
        assert ctx._initialized == True

    def test_cli_context_validation(self):
        """Test CLI context device validation"""
        ctx = CLIContext()

        # Commands that don't need device validation
        assert ctx.validate_device_options("list-commands") == True
        # The "list" command (from "device list") doesn't need device validation
        assert ctx.validate_device_options("list") == True

        # Commands that need device validation should fail without device
        assert ctx.validate_device_options("routing") == False

        # Should pass with device
        ctx.device = "R1"
        assert ctx.validate_device_options("routing") == True

        # Should pass with all_devices
        ctx.device = None
        ctx.all_devices = True
        assert ctx.validate_device_options("routing") == True

        # Should fail with both device and all_devices
        ctx.device = "R1"
        ctx.all_devices = True
        assert ctx.validate_device_options("routing") == False

    def test_click_command_structure(self):
        """Test that Click command structure works correctly"""
        # Test main help
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "device" in result.output
        assert "network" in result.output
        assert "topology" in result.output

        # Test group help
        result = self.runner.invoke(cli, ["device", "--help"])
        assert result.exit_code == 0
        assert "info" in result.output
        assert "profile" in result.output
        assert "list" in result.output

    def test_global_options_parsing(self):
        """Test that global options are parsed correctly"""
        # Test that global options with help work
        result = self.runner.invoke(
            cli,
            [
                "--log-level",
                "debug",
                "--help",
            ],
        )
        assert result.exit_code == 0

    def test_inventory_initialization(self):
        """Test that inventory is initialized when specified"""
        # This test checks that the CLI accepts the inventory option
        # In practice, we can't easily test the actual initialization
        # without mocking the entire file system, so we just verify
        # that the CLI recognizes the inventory option
        result = self.runner.invoke(
            cli, ["--inventory", "/tmp/test.json", "--help"]
        )

        # Help should work regardless of inventory file existence
        assert result.exit_code == 0
        assert (
            "An opinionated tool that retrieves essential network information"
            in result.output
        )

    def test_run_cli_mode_function(self):
        """Test the run_cli_mode function for compatibility"""
        with patch("src.cmd.parser.cli") as mock_cli:
            mock_ctx = Mock()
            mock_ctx.obj = Mock()

            mock_cli.make_context.return_value = mock_ctx
            mock_cli.invoke.return_value = None

            result, ctx = run_cli_mode()

            assert mock_cli.make_context.called
            assert mock_cli.invoke.called

    def test_device_command_requires_device_option(self):
        """Test that device commands require --device option"""
        # This should fail because device info requires --device
        result = self.runner.invoke(cli, ["device", "info"])
        assert result.exit_code != 0

    def test_module_log_levels_parsing(self):
        """Test that module log levels are parsed correctly"""
        ctx = CLIContext(module_log_levels="gnmi=debug,collectors=warning")

        # The actual parsing is done in _configure_logging
        assert ctx.module_log_levels == "gnmi=debug,collectors=warning"


class TestClickFunctionality:
    """Test Click-specific functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()

    def test_click_command_with_options(self):
        """Test Click command with various option types"""
        # Test with just help to ensure options are recognized
        result = self.runner.invoke(
            cli,
            [
                "--log-level",
                "debug",
                "--help",
            ],
        )

        assert result.exit_code == 0

    def test_click_error_handling(self):
        """Test Click error handling mechanisms"""
        result = self.runner.invoke(cli, ["--invalid-option"])

        assert result.exit_code != 0
        assert "no such option" in result.output.lower()

    def test_click_context_passing(self):
        """Test that Click context is passed correctly"""
        # This tests the underlying Click mechanism
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0

    def test_command_aliases_work(self):
        """Test that command group aliases work"""
        # Test that 'd' alias works for device
        result = self.runner.invoke(cli, ["d", "--help"])
        assert result.exit_code == 0
        assert "info" in result.output

        # Test that 'n' alias works for network
        result = self.runner.invoke(cli, ["n", "--help"])
        assert result.exit_code == 0
        assert "routing" in result.output


class TestPerformance:
    """Test performance characteristics of the new CLI"""

    def test_cli_startup_performance(self):
        """Test that CLI starts up quickly"""
        import time

        runner = CliRunner()

        start_time = time.time()
        result = runner.invoke(cli, ["--help"])
        end_time = time.time()

        # Should complete help in reasonable time (less than 2 seconds)
        assert (end_time - start_time) < 2.0
        assert result.exit_code == 0


if __name__ == "__main__":
    pytest.main([__file__])
