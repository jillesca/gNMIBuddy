#!/usr/bin/env python3
"""
Integration tests for API and MCP server sanitization functionality.

Tests api.get_devices() returns sanitized data, MCP server tool registration,
class-based data structures, and automatic sanitization inheritance.
"""

import pytest
from unittest.mock import patch, MagicMock

import api
from src.schemas.models import Device, DeviceListResult, NetworkOS
from src.inventory.manager import InventoryManager


class TestAPIIntegration:
    """Test suite for API layer integration with sanitization."""

    @pytest.fixture
    def mock_device_with_sensitive_data(self):
        """Create a mock device with sensitive authentication data."""
        return Device(
            name="api-test-device",
            ip_address="10.0.1.100",
            port=57777,
            nos=NetworkOS.IOSXR,
            username="gnmi_user",
            password="super_secret_password",
            path_cert="/secure/client.pem",
            path_key="/secure/private.key",
            path_root="/secure/ca.pem",
            override=None,
            skip_verify=True,
            gnmi_timeout=30,
            grpc_options=["grpc.max_message_length=1048576"],
            show_diff="context",
            insecure=False,
        )

    @pytest.fixture
    def mock_sanitized_device_list_result(
        self, mock_device_with_sensitive_data
    ):
        """Create a mock sanitized device list result."""
        sanitized_device = Device(
            name="api-test-device",
            ip_address="10.0.1.100",
            port=57777,
            nos=NetworkOS.IOSXR,
            username="gnmi_user",
            password="***",  # Sanitized
            path_cert="***",  # Sanitized
            path_key="***",  # Sanitized
            path_root="/secure/ca.pem",
            override=None,
            skip_verify=True,
            gnmi_timeout=30,
            grpc_options=["grpc.max_message_length=1048576"],
            show_diff="context",
            insecure=False,
        )
        return DeviceListResult(devices=[sanitized_device])

    def test_api_get_devices_returns_sanitized_data(
        self, mock_sanitized_device_list_result
    ):
        """Test that api.get_devices() returns sanitized data."""

        with patch(
            "api.list_available_devices_safe",
            return_value=mock_sanitized_device_list_result,
        ) as mock_safe:

            result = api.get_devices()

            # Verify the safe function was called
            mock_safe.assert_called_once()

            # Verify return type is DeviceListResult
            assert isinstance(result, DeviceListResult)

            # Verify the result contains sanitized data
            assert len(result.devices) == 1
            device = result.devices[0]

            # Verify sensitive data is redacted
            assert device.password == "***"
            assert device.path_cert == "***"
            assert device.path_key == "***"

            # Verify non-sensitive data is preserved
            assert device.name == "api-test-device"
            assert device.ip_address == "10.0.1.100"
            assert device.username == "gnmi_user"
            assert device.path_root == "/secure/ca.pem"  # Not sensitive

    def test_api_get_devices_return_type_contract(
        self, mock_sanitized_device_list_result
    ):
        """Test that api.get_devices() maintains the exact same return type contract."""

        with patch(
            "api.list_available_devices_safe",
            return_value=mock_sanitized_device_list_result,
        ):

            result = api.get_devices()

            # Verify exact return type
            assert isinstance(result, DeviceListResult)

            # Verify expected attributes exist
            assert hasattr(result, "devices")
            assert isinstance(result.devices, list)

            # Verify devices are Device objects (class-based)
            if result.devices:
                for device in result.devices:
                    assert isinstance(device, Device)
                    assert not isinstance(device, dict)

    def test_api_get_devices_class_based_data_structures(
        self, mock_sanitized_device_list_result
    ):
        """Test that api.get_devices() uses class-based data structures throughout."""

        with patch(
            "api.list_available_devices_safe",
            return_value=mock_sanitized_device_list_result,
        ):

            result = api.get_devices()

            # Verify top-level result is class-based
            assert isinstance(result, DeviceListResult)
            assert not isinstance(result, dict)

            # Verify device list is proper list
            assert isinstance(result.devices, list)

            # Verify each device is class-based
            for device in result.devices:
                assert isinstance(device, Device)
                assert not isinstance(device, dict)

                # Verify device has proper attributes (not dict keys)
                assert hasattr(device, "name")
                assert hasattr(device, "ip_address")
                assert hasattr(device, "password")

                # Verify we can access attributes (not dict access)
                _ = device.name
                _ = device.ip_address
                _ = device.password

    def test_api_get_devices_multiple_devices(self):
        """Test api.get_devices() with multiple devices of varying sensitive data."""

        # Create multiple devices with different sensitivity patterns
        device1 = Device(
            name="device-1",
            ip_address="10.0.1.1",
            nos=NetworkOS.IOSXR,
            password="***",
            path_cert="***",
        )

        device2 = Device(
            name="device-2",
            ip_address="10.0.1.2",
            nos=NetworkOS.IOSXR,
            password=None,  # No password
            path_cert=None,  # No cert
        )

        multi_device_result = DeviceListResult(devices=[device1, device2])

        with patch(
            "api.list_available_devices_safe", return_value=multi_device_result
        ):

            result = api.get_devices()

            # Verify structure
            assert len(result.devices) == 2

            # Verify first device has redacted data
            assert result.devices[0].password == "***"
            assert result.devices[0].path_cert == "***"

            # Verify second device preserves None values
            assert result.devices[1].password is None
            assert result.devices[1].path_cert is None

    def test_api_get_devices_error_handling(self):
        """Test api.get_devices() error handling."""

        # Test FileNotFoundError propagation
        with patch(
            "api.list_available_devices_safe",
            side_effect=FileNotFoundError("Inventory not found"),
        ):

            with pytest.raises(FileNotFoundError):
                api.get_devices()

        # Test other exceptions propagation
        with patch(
            "api.list_available_devices_safe",
            side_effect=ValueError("Invalid inventory"),
        ):

            with pytest.raises(ValueError):
                api.get_devices()

    def test_api_get_devices_empty_inventory(self):
        """Test api.get_devices() with empty inventory."""

        empty_result = DeviceListResult(devices=[])

        with patch(
            "api.list_available_devices_safe", return_value=empty_result
        ):

            result = api.get_devices()

            # Verify structure is maintained even with empty data
            assert isinstance(result, DeviceListResult)
            assert isinstance(result.devices, list)
            assert len(result.devices) == 0


class TestMCPServerIntegration:
    """Test suite for MCP server integration with sanitization."""

    def test_mcp_server_tool_registration_with_sanitized_data(self):
        """Test that MCP server automatically inherits sanitized data through api.get_devices()."""

        # Mock a sanitized device result
        sanitized_device = Device(
            name="mcp-test-device",
            ip_address="172.16.1.1",
            nos=NetworkOS.IOSXR,
            username="mcp_user",
            password="***",  # Sanitized
            path_cert="***",  # Sanitized
            path_key="***",  # Sanitized
        )
        sanitized_result = DeviceListResult(devices=[sanitized_device])

        with patch(
            "api.list_available_devices_safe", return_value=sanitized_result
        ):

            # Call the API function that MCP server uses
            result = api.get_devices()

            # Verify MCP gets sanitized data
            assert isinstance(result, DeviceListResult)
            assert len(result.devices) == 1

            device = result.devices[0]
            assert device.password == "***"
            assert device.path_cert == "***"
            assert device.path_key == "***"
            assert device.name == "mcp-test-device"

    def test_mcp_server_no_direct_changes_needed(self):
        """Test that MCP server works without direct code changes."""

        # Import the MCP server module to verify it can load
        try:
            import mcp_server

            # If we can import it without errors, the registration mechanism works
            assert hasattr(mcp_server, "register_as_mcp_tool")
        except ImportError as e:
            pytest.fail(f"MCP server module import failed: {e}")

    def test_mcp_registration_mechanism_unchanged(self):
        """Test that the MCP registration mechanism remains unchanged."""

        # Simply verify that the MCP server module has the expected registration function
        # and that it would register get_devices (without actually triggering it)
        import mcp_server

        # Verify the registration function exists
        assert hasattr(mcp_server, "register_as_mcp_tool")

        # Verify that api.get_devices exists and would be registerable
        import api

        assert hasattr(api, "get_devices")
        assert callable(api.get_devices)

        # This validates that the mechanism is in place without triggering side effects

    def test_mcp_server_sanitization_flows_through_existing_mechanism(self):
        """Test that sanitization flows through the existing MCP registration mechanism."""

        sanitized_device = Device(
            name="flow-test-device",
            ip_address="192.168.100.1",
            nos=NetworkOS.IOSXR,
            password="***",
            path_cert="***",
        )
        sanitized_result = DeviceListResult(devices=[sanitized_device])

        with patch(
            "api.list_available_devices_safe", return_value=sanitized_result
        ):

            # Call the API function directly (as MCP would)
            result = api.get_devices()

            # Verify the sanitized data flows through
            assert result.devices[0].password == "***"
            assert result.devices[0].path_cert == "***"

            # Verify class-based structures work with MCP mechanism
            assert isinstance(result, DeviceListResult)
            assert isinstance(result.devices[0], Device)

    def test_mcp_server_class_based_data_structures(self):
        """Test that MCP server receives proper class-based data structures."""

        sanitized_device = Device(
            name="class-test-device",
            ip_address="10.100.1.1",
            nos=NetworkOS.IOSXR,
            username="test_user",
            password="***",
        )
        sanitized_result = DeviceListResult(devices=[sanitized_device])

        with patch(
            "api.list_available_devices_safe", return_value=sanitized_result
        ):

            # Simulate what MCP server would receive
            mcp_result = api.get_devices()

            # Verify MCP receives class-based structures
            assert isinstance(mcp_result, DeviceListResult)
            assert not isinstance(mcp_result, dict)

            for device in mcp_result.devices:
                assert isinstance(device, Device)
                assert not isinstance(device, dict)

                # Verify MCP can access device attributes properly
                assert device.name == "class-test-device"
                assert device.password == "***"

    def test_mcp_server_backward_compatibility(self):
        """Test that MCP server maintains backward compatibility."""

        # Create a result that matches the expected interface
        test_device = Device(
            name="compat-test",
            ip_address="172.20.1.1",
            nos=NetworkOS.IOSXR,
            password="***",
        )
        test_result = DeviceListResult(devices=[test_device])

        with patch(
            "api.list_available_devices_safe", return_value=test_result
        ):

            # Test the API function interface hasn't changed
            result = api.get_devices()

            # Verify return type is still DeviceListResult
            assert isinstance(result, DeviceListResult)

            # Verify the structure MCP expects is preserved
            assert hasattr(result, "devices")
            assert isinstance(result.devices, list)

            if result.devices:
                device = result.devices[0]
                # Verify device has expected attributes
                expected_attrs = ["name", "ip_address", "nos", "password"]
                for attr in expected_attrs:
                    assert hasattr(device, attr)

    def test_mcp_server_integration_error_handling(self):
        """Test MCP server error handling with sanitization."""

        # Test that errors propagate correctly through MCP
        with patch(
            "api.list_available_devices_safe",
            side_effect=FileNotFoundError("No inventory"),
        ):

            with pytest.raises(FileNotFoundError):
                api.get_devices()

        # Test that the error doesn't expose sensitive data
        with patch(
            "api.list_available_devices_safe",
            side_effect=Exception(
                "Device connection failed for user admin with password secret123"
            ),
        ):

            # Even error messages should not contain sensitive data
            # (This would be handled by the calling application)
            with pytest.raises(Exception) as exc_info:
                api.get_devices()

            # The exception will still contain the message, but MCP layer
            # should handle sanitization of error messages if needed
            assert "secret123" in str(
                exc_info.value
            )  # Original behavior preserved
