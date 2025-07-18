#!/usr/bin/env python3
"""Migration tests for Click-based CLI to ensure backward compatibility"""
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
        assert "gNMIBuddy CLI tool" in result.output
        assert "--device" in result.output
        assert "--all-devices" in result.output
        assert "--log-level" in result.output

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
        assert ctx.validate_device_options("list-devices") == True

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

    @patch("src.cmd.parser.get_legacy_commands_dict")
    def test_legacy_command_execution(self, mock_get_commands):
        """Test that legacy commands are executed correctly through Click"""
        # Mock a simple command
        mock_command = Mock()
        mock_command.name = "test-command"
        mock_command.help = "Test command help"
        mock_command.execute.return_value = {"test": "result"}
        mock_command.configure_parser = Mock()

        mock_get_commands.return_value = {"test-command": mock_command}

        # Test the command execution
        result = self.runner.invoke(cli, ["--device", "R1", "test-command"])

        # Should have attempted to execute the command
        assert mock_command.execute.called

    def test_global_options_parsing(self):
        """Test that global options are parsed correctly"""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(
                cli,
                [
                    "--log-level",
                    "debug",
                    "--module-log-levels",
                    "gnmi=info,collectors=warning",
                    "--structured-logging",
                    "--device",
                    "R1",
                    "--max-workers",
                    "10",
                    "--help",
                ],
            )

            assert result.exit_code == 0
            assert "gNMIBuddy CLI tool" in result.output

    @patch("src.cmd.parser.initialize_inventory")
    def test_inventory_initialization(self, mock_init_inventory):
        """Test that inventory is initialized when specified"""
        result = self.runner.invoke(
            cli, ["--inventory", "/path/to/inventory.json", "--help"]
        )

        assert result.exit_code == 0
        mock_init_inventory.assert_called_once_with("/path/to/inventory.json")

    def test_run_cli_mode_function(self):
        """Test the run_cli_mode function for compatibility"""
        with patch("src.cmd.parser.cli") as mock_cli:
            mock_ctx = Mock()
            mock_ctx.obj = Mock()
            mock_ctx.obj._last_result = {"test": "result"}

            mock_cli.make_context.return_value = mock_ctx
            mock_cli.invoke.return_value = None

            result, ctx = run_cli_mode()

            assert mock_cli.make_context.called
            assert mock_cli.invoke.called

    def test_error_handling_in_commands(self):
        """Test that errors in commands are handled gracefully"""
        with patch(
            "src.cmd.parser.get_legacy_commands_dict"
        ) as mock_get_commands:
            # Mock a command that raises an exception
            mock_command = Mock()
            mock_command.name = "error-command"
            mock_command.help = "Command that errors"
            mock_command.execute.side_effect = Exception("Test error")
            mock_command.configure_parser = Mock()

            mock_get_commands.return_value = {"error-command": mock_command}

            result = self.runner.invoke(
                cli, ["--device", "R1", "error-command"]
            )

            assert result.exit_code != 0
            assert "Error executing command" in result.output

    def test_device_validation_error_handling(self):
        """Test device validation error handling"""
        with patch(
            "src.cmd.parser.get_legacy_commands_dict"
        ) as mock_get_commands:
            mock_command = Mock()
            mock_command.name = "routing"
            mock_command.help = "Routing command"
            mock_command.configure_parser = Mock()

            mock_get_commands.return_value = {"routing": mock_command}

            # Should fail without device or all-devices
            result = self.runner.invoke(cli, ["routing"])

            assert result.exit_code != 0
            assert "Device validation failed" in result.output

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
        result = self.runner.invoke(
            cli,
            [
                "--device",
                "R1",
                "--log-level",
                "debug",
                "--all-devices",
                "--max-workers",
                "10",
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
