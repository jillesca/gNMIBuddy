#!/usr/bin/env python3
"""
Integration tests for the device list CLI command with sanitization.

Tests CLI output redaction, class-based data handling, and no sensitive data leakage.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from src.cmd.commands.device.list import device_list
from src.schemas.models import Device, DeviceListResult, NetworkOS
from src.inventory.manager import InventoryManager


class TestDeviceListCLIIntegration:
    """Test suite for device list CLI command integration with sanitization."""

    @pytest.fixture
    def cli_runner(self):
        """Create a CLI runner for testing commands."""
        return CliRunner()

    @pytest.fixture
    def mock_device_with_sensitive_data(self):
        """Create a mock device with sensitive authentication data."""
        return Device(
            name="test-device-1",
            ip_address="192.168.1.1",
            port=57777,
            nos=NetworkOS.IOSXR,
            username="admin",
            password="secret123",
            path_cert="/path/to/cert.pem",
            path_key="/path/to/private.key",
            path_root="/path/to/root.ca",
            override="override.example.com",
            skip_verify=False,
            gnmi_timeout=10,
            grpc_options=["grpc.keepalive_time_ms=30000"],
            show_diff="unified",
            insecure=False,
        )

    @pytest.fixture
    def mock_device_list_result(self, mock_device_with_sensitive_data):
        """Create a mock device list result with sensitive data."""
        devices = [mock_device_with_sensitive_data]
        return DeviceListResult(devices=devices)

    @pytest.fixture
    def mock_sanitized_device_list_result(
        self, mock_device_with_sensitive_data
    ):
        """Create a mock sanitized device list result."""
        sanitized_device = Device(
            name="test-device-1",
            ip_address="192.168.1.1",
            port=57777,
            nos=NetworkOS.IOSXR,
            username="admin",
            password="***",  # Sanitized
            path_cert="***",  # Sanitized
            path_key="***",  # Sanitized
            path_root="/path/to/root.ca",
            override="override.example.com",
            skip_verify=False,
            gnmi_timeout=10,
            grpc_options=["grpc.keepalive_time_ms=30000"],
            show_diff="unified",
            insecure=False,
        )
        return DeviceListResult(devices=[sanitized_device])

    def test_device_list_detail_output_redaction(
        self,
        cli_runner,
        mock_sanitized_device_list_result,
        mock_device_list_result,
    ):
        """Test that CLI --detail output properly redacts sensitive data."""

        # Mock the inventory manager methods
        with (
            patch.object(
                InventoryManager,
                "list_devices_safe",
                return_value=mock_sanitized_device_list_result,
            ) as mock_safe,
            patch.object(
                InventoryManager,
                "list_devices",
                return_value=mock_device_list_result,
            ) as mock_regular,
        ):

            result = cli_runner.invoke(
                device_list, ["--detail", "--output", "json"]
            )

            # Verify the command succeeded
            assert result.exit_code == 0

            # Verify list_devices_safe was called (not list_devices)
            mock_safe.assert_called_once()
            mock_regular.assert_not_called()

            # Parse the JSON output
            output_data = json.loads(result.output)

            # Verify structure uses class-based data
            assert "devices" in output_data
            assert "count" in output_data
            assert "detail" in output_data
            assert output_data["detail"] is True
            assert output_data["count"] == 1

            # Verify sensitive data is redacted in output
            device_data = output_data["devices"][0]
            assert device_data["password"] == "***"
            assert device_data["path_cert"] == "***"
            assert device_data["path_key"] == "***"

            # Verify non-sensitive data is preserved
            assert device_data["name"] == "test-device-1"
            assert device_data["ip_address"] == "192.168.1.1"
            assert device_data["username"] == "admin"
            assert device_data["path_root"] == "/path/to/root.ca"

            # Verify no sensitive data appears anywhere in output
            assert "secret123" not in result.output
            assert "/path/to/cert.pem" not in result.output
            assert "/path/to/private.key" not in result.output

    def test_device_list_basic_output_unchanged(
        self,
        cli_runner,
        mock_device_list_result,
        mock_sanitized_device_list_result,
    ):
        """Test that CLI basic output (no --detail) remains unchanged and uses regular data."""

        with (
            patch.object(
                InventoryManager,
                "list_devices",
                return_value=mock_device_list_result,
            ) as mock_regular,
            patch.object(
                InventoryManager,
                "list_devices_safe",
                return_value=mock_sanitized_device_list_result,
            ) as mock_safe,
        ):

            result = cli_runner.invoke(device_list, ["--output", "json"])

            # Verify the command succeeded
            assert result.exit_code == 0

            # Verify list_devices was called (not list_devices_safe)
            mock_regular.assert_called_once()
            mock_safe.assert_not_called()

            # Parse the JSON output
            output_data = json.loads(result.output)

            # Verify structure
            assert "devices" in output_data
            assert "count" in output_data
            assert "detail" in output_data
            assert output_data["detail"] is False
            assert output_data["count"] == 1

            # Verify only device names are shown (no sensitive data exposure risk)
            assert output_data["devices"] == ["test-device-1"]

            # Verify no sensitive information is exposed
            assert "secret123" not in result.output
            assert "admin" not in result.output
            assert "192.168.1.1" not in result.output

    def test_device_list_class_based_data_handling(
        self, cli_runner, mock_sanitized_device_list_result
    ):
        """Test that CLI processing uses class-based data structures throughout."""

        with patch.object(
            InventoryManager,
            "list_devices_safe",
            return_value=mock_sanitized_device_list_result,
        ):

            result = cli_runner.invoke(device_list, ["--detail"])

            # Verify the command succeeded
            assert result.exit_code == 0

            # The fact that the command works without errors indicates that
            # class-based data structures are being handled correctly
            # If dictionaries were used incorrectly, we'd get attribute errors

            # Parse the output and verify it contains structured data
            # (not just strings or malformed data)
            output_lines = result.output.strip().split("\n")
            json_output = "\n".join(output_lines)

            try:
                parsed_data = json.loads(json_output)
                # If we can parse it as JSON and access device data,
                # it means class-based structures were properly serialized
                assert isinstance(parsed_data, dict)
                assert "devices" in parsed_data
                assert len(parsed_data["devices"]) > 0
            except json.JSONDecodeError:
                pytest.fail(
                    "CLI output is not valid JSON, indicating data structure issues"
                )

    def test_device_list_no_sensitive_data_leakage_any_format(
        self, cli_runner, mock_sanitized_device_list_result
    ):
        """Test that no sensitive data appears in any output format."""

        with patch.object(
            InventoryManager,
            "list_devices_safe",
            return_value=mock_sanitized_device_list_result,
        ):

            # Test JSON format
            result_json = cli_runner.invoke(
                device_list, ["--detail", "--output", "json"]
            )
            assert result_json.exit_code == 0
            assert "secret123" not in result_json.output
            assert "/path/to/cert.pem" not in result_json.output
            assert "/path/to/private.key" not in result_json.output

            # Test table format (default)
            result_table = cli_runner.invoke(device_list, ["--detail"])
            assert result_table.exit_code == 0
            assert "secret123" not in result_table.output
            assert "/path/to/cert.pem" not in result_table.output
            assert "/path/to/private.key" not in result_table.output

            # Test YAML format
            result_yaml = cli_runner.invoke(
                device_list, ["--detail", "--output", "yaml"]
            )
            assert result_yaml.exit_code == 0
            assert "secret123" not in result_yaml.output
            assert "/path/to/cert.pem" not in result_yaml.output
            assert "/path/to/private.key" not in result_yaml.output

    def test_device_list_empty_inventory_handling(self, cli_runner):
        """Test CLI behavior with empty inventory."""

        empty_result = DeviceListResult(devices=[])

        with patch.object(
            InventoryManager, "list_devices_safe", return_value=empty_result
        ):

            result = cli_runner.invoke(
                device_list, ["--detail", "--output", "json"]
            )

            # Verify the command succeeded
            assert result.exit_code == 0

            # Parse the JSON output
            output_data = json.loads(result.output)

            # Verify empty structure
            assert output_data["devices"] == []
            assert output_data["count"] == 0
            assert output_data["detail"] is True
            assert "No devices found in inventory" in output_data["message"]

    def test_device_list_error_handling(self, cli_runner):
        """Test CLI error handling when inventory operations fail."""

        with patch.object(
            InventoryManager,
            "list_devices_safe",
            side_effect=FileNotFoundError("Inventory file not found"),
        ):

            result = cli_runner.invoke(device_list, ["--detail"])

            # Verify the command fails gracefully
            assert result.exit_code != 0

    def test_device_list_method_selection_logic(
        self,
        cli_runner,
        mock_device_list_result,
        mock_sanitized_device_list_result,
    ):
        """Test that the correct inventory method is called based on detail flag."""

        with (
            patch.object(
                InventoryManager,
                "list_devices",
                return_value=mock_device_list_result,
            ) as mock_regular,
            patch.object(
                InventoryManager,
                "list_devices_safe",
                return_value=mock_sanitized_device_list_result,
            ) as mock_safe,
        ):

            # Test detail=True calls safe method
            result_detail = cli_runner.invoke(device_list, ["--detail"])
            assert result_detail.exit_code == 0
            mock_safe.assert_called_once()
            mock_regular.assert_not_called()

            # Reset mocks
            mock_safe.reset_mock()
            mock_regular.reset_mock()

            # Test detail=False calls regular method
            result_basic = cli_runner.invoke(device_list)
            assert result_basic.exit_code == 0
            mock_regular.assert_called_once()
            mock_safe.assert_not_called()

    def test_device_list_output_format_consistency(
        self, cli_runner, mock_sanitized_device_list_result
    ):
        """Test that output format is consistent across different options."""

        with patch.object(
            InventoryManager,
            "list_devices_safe",
            return_value=mock_sanitized_device_list_result,
        ):

            # Get JSON output
            result_json = cli_runner.invoke(
                device_list, ["--detail", "--output", "json"]
            )
            assert result_json.exit_code == 0

            # Parse and verify structure
            json_data = json.loads(result_json.output)

            # Verify required fields are present
            required_fields = ["devices", "count", "detail"]
            for field in required_fields:
                assert field in json_data, f"Missing required field: {field}"

            # Verify device data structure
            if json_data["devices"]:
                device = json_data["devices"][0]
                device_required_fields = ["name", "ip_address", "port", "nos"]
                for field in device_required_fields:
                    assert (
                        field in device
                    ), f"Missing required device field: {field}"

    def test_device_list_regression_compatibility(
        self, cli_runner, mock_device_list_result
    ):
        """Test that existing functionality still works (regression test)."""

        with patch.object(
            InventoryManager,
            "list_devices",
            return_value=mock_device_list_result,
        ):

            # Test basic functionality that existed before sanitization
            result = cli_runner.invoke(device_list)
            assert result.exit_code == 0

            # Parse output
            output_data = json.loads(result.output)

            # Verify basic structure remains the same
            assert "devices" in output_data
            assert "count" in output_data
            assert "detail" in output_data
            assert output_data["detail"] is False

            # Verify device names are returned (original behavior)
            assert isinstance(output_data["devices"], list)
            assert len(output_data["devices"]) > 0
            assert all(
                isinstance(name, str) for name in output_data["devices"]
            )

    def test_device_list_multiple_devices_handling(self, cli_runner):
        """Test CLI handling of multiple devices with mixed sensitive data."""

        # Create multiple devices with different sensitive data patterns
        device1 = Device(
            name="device-1",
            ip_address="192.168.1.1",
            nos=NetworkOS.IOSXR,
            username="admin",
            password="secret1",
            path_cert="/cert1.pem",
        )

        device2 = Device(
            name="device-2",
            ip_address="192.168.1.2",
            nos=NetworkOS.IOSXR,
            username="user",
            password=None,  # No password
            path_cert=None,  # No cert
        )

        # Create sanitized versions
        sanitized_device1 = Device(
            name="device-1",
            ip_address="192.168.1.1",
            nos=NetworkOS.IOSXR,
            username="admin",
            password="***",
            path_cert="***",
        )

        sanitized_device2 = Device(
            name="device-2",
            ip_address="192.168.1.2",
            nos=NetworkOS.IOSXR,
            username="user",
            password=None,
            path_cert=None,
        )

        multi_device_result = DeviceListResult(
            devices=[sanitized_device1, sanitized_device2]
        )

        with patch.object(
            InventoryManager,
            "list_devices_safe",
            return_value=multi_device_result,
        ):

            result = cli_runner.invoke(
                device_list, ["--detail", "--output", "json"]
            )
            assert result.exit_code == 0

            output_data = json.loads(result.output)

            # Verify multiple devices are handled correctly
            assert len(output_data["devices"]) == 2
            assert output_data["count"] == 2

            # Verify first device has redacted data
            device1_data = output_data["devices"][0]
            assert device1_data["password"] == "***"
            assert device1_data["path_cert"] == "***"

            # Verify second device preserves None values
            device2_data = output_data["devices"][1]
            assert device2_data["password"] is None
            assert device2_data["path_cert"] is None

            # Verify no original sensitive data appears in output
            assert "secret1" not in result.output
            assert "/cert1.pem" not in result.output
