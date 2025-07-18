#!/usr/bin/env python3
"""Tests for inventory error handling in the CLI"""
import os
import tempfile
import json
from pathlib import Path
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from src.cmd.parser import cli, _handle_inventory_error


class TestInventoryErrorHandling:
    """Test suite for inventory error handling"""

    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
        # Create a temporary inventory file for testing
        self.test_inventory = [
            {
                "name": "test-device",
                "ip_address": "192.168.1.1",
                "port": 57777,
                "nos": "iosxr",
                "username": "admin",
                "password": "admin",
            }
        ]

    def test_inventory_error_message_format(self):
        """Test that inventory error message is properly formatted"""
        # Test the error handler directly
        from io import StringIO
        import sys

        captured_output = StringIO()
        original_stderr = sys.stderr
        sys.stderr = captured_output

        try:
            _handle_inventory_error("Test error message")
            error_output = captured_output.getvalue()

            # Check for key components of the error message
            assert "❌ Inventory Error" in error_output
            assert "══════════════" in error_output  # Visual separator
            assert "💡 How to fix this:" in error_output
            assert "--inventory" in error_output
            assert "NETWORK_INVENTORY" in error_output
            assert "xrd_sandbox.json" in error_output

        finally:
            sys.stderr = original_stderr

    def test_cli_without_inventory_shows_clear_error(self):
        """Test that CLI shows clear error when inventory is missing"""
        # Ensure no environment variable is set
        with patch.dict(os.environ, {}, clear=True):
            result = self.runner.invoke(
                cli, ["device", "info", "--device", "test-device"]
            )

            # Should exit with non-zero code
            assert result.exit_code != 0

            # Check error output contains our improved messaging
            # Click captures both stdout and stderr in result.output
            assert "❌ Inventory Error" in result.output
            assert "💡 How to fix this:" in result.output
            assert "--inventory" in result.output

    def test_cli_with_inventory_file_works(self):
        """Test that CLI works when inventory file is provided"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp_file:
            json.dump(self.test_inventory, temp_file)
            temp_file_path = temp_file.name

        try:
            # Mock the actual gNMI operation to avoid network calls
            with patch(
                "src.collectors.system.get_system_info"
            ) as mock_get_system:
                mock_get_system.return_value = {
                    "status": "success",
                    "data": {"hostname": "test-device"},
                }

                result = self.runner.invoke(
                    cli,
                    [
                        "--inventory",
                        temp_file_path,
                        "device",
                        "info",
                        "--device",
                        "test-device",
                    ],
                )

                # Should succeed
                assert result.exit_code == 0
                # Should not contain error messages
                assert "❌ Inventory Error" not in result.output

        finally:
            os.unlink(temp_file_path)

    def test_cli_with_environment_variable_works(self):
        """Test that CLI works when NETWORK_INVENTORY environment variable is set"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp_file:
            json.dump(self.test_inventory, temp_file)
            temp_file_path = temp_file.name

        try:
            # Mock the actual gNMI operation to avoid network calls
            with patch(
                "src.collectors.system.get_system_info"
            ) as mock_get_system:
                mock_get_system.return_value = {
                    "status": "success",
                    "data": {"hostname": "test-device"},
                }

                # Set environment variable
                with patch.dict(
                    os.environ, {"NETWORK_INVENTORY": temp_file_path}
                ):
                    result = self.runner.invoke(
                        cli, ["device", "info", "--device", "test-device"]
                    )

                    # Should succeed
                    assert result.exit_code == 0
                    # Should not contain error messages
                    assert "❌ Inventory Error" not in result.output

        finally:
            os.unlink(temp_file_path)

    def test_help_shows_inventory_requirement(self):
        """Test that help output prominently shows inventory requirement"""
        result = self.runner.invoke(cli, ["--help"])

        # Should show inventory requirement
        assert "📋 INVENTORY REQUIREMENT:" in result.output
        assert "You must provide device inventory via either:" in result.output
        assert "• --inventory PATH_TO_FILE.json" in result.output
        assert "• Set NETWORK_INVENTORY environment variable" in result.output
        assert (
            "--inventory TEXT         Path to inventory JSON file (REQUIRED)"
            in result.output
        )

    def test_invalid_inventory_file_shows_clear_error(self):
        """Test that invalid inventory file shows clear error"""
        # Test with non-existent file
        result = self.runner.invoke(
            cli,
            [
                "--inventory",
                "/path/that/does/not/exist.json",
                "device",
                "info",
                "--device",
                "test-device",
            ],
        )

        # Should exit with error and show our friendly error message
        assert result.exit_code != 0
        # Now our error handling should show the friendly message instead of sys.exit
        assert (
            "❌ Inventory Error" in result.output
            or "File not found" in result.output
        )

    def test_inventory_file_with_invalid_json_shows_clear_error(self):
        """Test that inventory file with invalid JSON shows clear error"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp_file:
            temp_file.write("{ invalid json content")
            temp_file_path = temp_file.name

        try:
            result = self.runner.invoke(
                cli,
                [
                    "--inventory",
                    temp_file_path,
                    "device",
                    "info",
                    "--device",
                    "test-device",
                ],
            )

            # Should exit with error and show error message (either friendly or technical)
            assert result.exit_code != 0
            # Should show some kind of error message
            assert len(result.output) > 0

        finally:
            os.unlink(temp_file_path)

    def test_device_not_found_in_inventory_shows_clear_error(self):
        """Test that device not found in inventory shows clear error"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp_file:
            json.dump(self.test_inventory, temp_file)
            temp_file_path = temp_file.name

        try:
            result = self.runner.invoke(
                cli,
                [
                    "--inventory",
                    temp_file_path,
                    "device",
                    "info",
                    "--device",
                    "nonexistent-device",
                ],
            )

            # Should exit with error
            assert result.exit_code != 0
            # Check output for error message
            assert "not found" in result.output

        finally:
            os.unlink(temp_file_path)

    def test_no_traceback_in_user_facing_errors(self):
        """Test that users don't see Python tracebacks for common errors"""
        # Test without inventory - this should trigger inventory error
        with patch.dict(os.environ, {}, clear=True):
            result = self.runner.invoke(
                cli, ["device", "info", "--device", "test-device"]
            )

            # Should not contain traceback indicators
            assert "Traceback" not in result.output
            assert 'File "/Users/' not in result.output
            assert "line " not in result.output
            # Should contain our friendly error message (inventory error in this case)
            assert "❌ Inventory Error" in result.output

    def test_environment_variable_takes_precedence_over_missing_cli_option(
        self,
    ):
        """Test that environment variable works when CLI option is not provided"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp_file:
            json.dump(self.test_inventory, temp_file)
            temp_file_path = temp_file.name

        try:
            with patch(
                "src.collectors.system.get_system_info"
            ) as mock_get_system:
                mock_get_system.return_value = {
                    "status": "success",
                    "data": {"hostname": "test-device"},
                }

                with patch.dict(
                    os.environ, {"NETWORK_INVENTORY": temp_file_path}
                ):
                    # Don't provide --inventory option, rely on environment variable
                    result = self.runner.invoke(
                        cli, ["device", "info", "--device", "test-device"]
                    )

                    assert result.exit_code == 0
                    assert "❌ Inventory Error" not in result.output

        finally:
            os.unlink(temp_file_path)

    def test_cli_option_overrides_environment_variable(self):
        """Test that --inventory option overrides environment variable"""
        # Create two different inventory files
        inventory1 = [
            {
                "name": "device1",
                "ip_address": "192.168.1.1",
                "port": 57777,
                "nos": "iosxr",
                "username": "admin",
                "password": "admin",
            }
        ]
        inventory2 = [
            {
                "name": "device2",
                "ip_address": "192.168.1.2",
                "port": 57777,
                "nos": "iosxr",
                "username": "admin",
                "password": "admin",
            }
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp_file1:
            json.dump(inventory1, temp_file1)
            temp_file1_path = temp_file1.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp_file2:
            json.dump(inventory2, temp_file2)
            temp_file2_path = temp_file2.name

        try:
            with patch(
                "src.collectors.system.get_system_info"
            ) as mock_get_system:
                mock_get_system.return_value = {
                    "status": "success",
                    "data": {"hostname": "device2"},
                }

                # Set environment variable to first file, but use CLI option for second file
                with patch.dict(
                    os.environ, {"NETWORK_INVENTORY": temp_file1_path}
                ):
                    result = self.runner.invoke(
                        cli,
                        [
                            "--inventory",
                            temp_file2_path,
                            "device",
                            "info",
                            "--device",
                            "device2",
                        ],
                    )

                    # Should succeed with device2 (from CLI option file)
                    assert result.exit_code == 0

                    # Try with device1 - should fail because we're using the CLI option file
                    result = self.runner.invoke(
                        cli,
                        [
                            "--inventory",
                            temp_file2_path,
                            "device",
                            "info",
                            "--device",
                            "device1",
                        ],
                    )

                    # Should fail because device1 is not in the CLI option file
                    assert result.exit_code != 0
                    assert "not found" in result.output

        finally:
            os.unlink(temp_file1_path)
            os.unlink(temp_file2_path)


if __name__ == "__main__":
    pytest.main([__file__])
