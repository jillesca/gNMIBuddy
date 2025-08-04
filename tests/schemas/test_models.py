#!/usr/bin/env python3
"""
Tests for device models in src/schemas/models.py.

Tests the Device dataclass and related TypedDict classes to ensure
proper validation and functionality.
"""

from dataclasses import fields
from typing import get_type_hints, Optional
from src.schemas.models import (
    Device,
    DeviceListResult,
    DeviceErrorResult,
    NetworkOS,
)


class TestDeviceModel:
    """Test suite for the Device model."""

    def test_device_creation_with_minimal_fields(self):
        """Test Device creation with only required fields."""
        device = Device(
            name="test-device", ip_address="192.168.1.1", nos=NetworkOS.IOSXR
        )

        assert device.name == "test-device"
        assert device.ip_address == "192.168.1.1"
        assert device.nos == NetworkOS.IOSXR
        assert device.port == 830  # Default value
        assert device.username is None  # Default value (optional)
        assert device.password is None  # Default value (optional)
        assert device.skip_verify is False  # Default value
        assert device.gnmi_timeout == 5  # Default value
        assert device.insecure is True  # Default value

    def test_device_creation_with_all_fields(self):
        """Test Device creation with all fields specified."""
        device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            port=57400,
            nos=NetworkOS.IOSXR,
            username="admin",
            password="admin123",
            path_cert="/path/to/cert.pem",
            path_key="/path/to/key.pem",
            path_root="/path/to/root.pem",
            override="override.example.com",
            skip_verify=True,
            gnmi_timeout=10,
            grpc_options=["grpc.keepalive_time_ms", 30000],
            show_diff="unified",
            insecure=False,
        )

        assert device.name == "test-device"
        assert device.ip_address == "192.168.1.1"
        assert device.port == 57400
        assert device.nos == NetworkOS.IOSXR
        assert device.username == "admin"
        assert device.password == "admin123"
        assert device.path_cert == "/path/to/cert.pem"
        assert device.path_key == "/path/to/key.pem"
        assert device.path_root == "/path/to/root.pem"
        assert device.override == "override.example.com"
        assert device.skip_verify is True
        assert device.gnmi_timeout == 10
        assert device.grpc_options == ["grpc.keepalive_time_ms", 30000]
        assert device.show_diff == "unified"
        assert device.insecure is False

    def test_device_default_values(self):
        """Test that Device has proper default values."""
        device = Device()

        # Test all default values
        assert device.name == ""
        assert device.ip_address == ""
        assert device.port == 830
        assert device.nos == NetworkOS.IOSXR
        assert device.username is None  # Now optional
        assert device.password is None  # Now optional
        assert device.path_cert is None
        assert device.path_key is None
        assert device.path_root is None
        assert device.override is None
        assert device.skip_verify is False
        assert device.gnmi_timeout == 5
        assert device.grpc_options is None
        assert device.show_diff is None
        assert device.insecure is True

    def test_device_to_device_info_method(self):
        """Test the to_device_info method."""
        device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            port=57400,
            nos=NetworkOS.IOSXR,
            username="admin",
            password="secret123",
        )

        device_info = device.to_device_info()

        # Should only include non-sensitive information
        expected_info = {
            "name": "test-device",
            "ip_address": "192.168.1.1",
            "port": 57400,
            "nos": "iosxr",
        }

        assert device_info == expected_info

        # Ensure sensitive information is not included
        assert "username" not in device_info
        assert "password" not in device_info
        assert "path_cert" not in device_info
        assert "path_key" not in device_info

    def test_device_model_dataclass_fields(self):
        """Test that Device has all expected fields."""
        device_fields = [f.name for f in fields(Device)]

        expected_fields = [
            "name",
            "ip_address",
            "port",
            "nos",
            "username",
            "password",
            "path_cert",
            "path_key",
            "path_root",
            "override",
            "skip_verify",
            "gnmi_timeout",
            "grpc_options",
            "show_diff",
            "insecure",
        ]

        for field_name in expected_fields:
            assert field_name in device_fields, f"Missing field: {field_name}"

    def test_device_field_types(self):
        """Test that Device fields have correct type annotations."""
        type_hints = get_type_hints(Device)

        # Test key field types
        assert type_hints["name"] == str
        assert type_hints["ip_address"] == str
        assert type_hints["port"] == int
        assert type_hints["nos"] == NetworkOS
        assert type_hints["username"] == Optional[str]  # Now optional
        assert type_hints["password"] == Optional[str]  # Now optional
        assert type_hints["skip_verify"] == bool
        assert type_hints["gnmi_timeout"] == int
        assert type_hints["insecure"] == bool

    def test_device_equality(self):
        """Test Device equality comparison."""
        device1 = Device(
            name="test-device", ip_address="192.168.1.1", nos=NetworkOS.IOSXR
        )

        device2 = Device(
            name="test-device", ip_address="192.168.1.1", nos=NetworkOS.IOSXR
        )

        device3 = Device(
            name="different-device",
            ip_address="192.168.1.1",
            nos=NetworkOS.IOSXR,
        )

        assert device1 == device2
        assert device1 != device3

    def test_device_string_representation(self):
        """Test Device string representation."""
        device = Device(
            name="test-device", ip_address="192.168.1.1", nos=NetworkOS.IOSXR
        )

        device_str = str(device)
        assert "test-device" in device_str
        assert "192.168.1.1" in device_str
        assert "iosxr" in device_str


class TestDeviceListResult:
    """Test suite for DeviceListResult TypedDict."""

    def test_device_list_result_structure(self):
        """Test that DeviceListResult has correct structure."""
        # This is a TypedDict, so we test with actual data
        device_list: DeviceListResult = {
            "devices": [
                {"name": "device1", "ip_address": "192.168.1.1"},
                {"name": "device2", "ip_address": "192.168.1.2"},
            ]
        }

        assert "devices" in device_list
        assert isinstance(device_list["devices"], list)
        assert len(device_list["devices"]) == 2
        assert device_list["devices"][0]["name"] == "device1"
        assert device_list["devices"][1]["name"] == "device2"

    def test_device_list_result_empty(self):
        """Test DeviceListResult with empty device list."""
        device_list: DeviceListResult = {"devices": []}

        assert "devices" in device_list
        assert isinstance(device_list["devices"], list)
        assert len(device_list["devices"]) == 0


class TestDeviceErrorResult:
    """Test suite for DeviceErrorResult TypedDict."""

    def test_device_error_result_with_device_info(self):
        """Test DeviceErrorResult with device information."""
        error_result: DeviceErrorResult = {
            "error": "Connection failed",
            "device_info": {
                "name": "test-device",
                "ip_address": "192.168.1.1",
                "port": 57400,
                "nos": "iosxr",
            },
        }

        assert "error" in error_result
        assert "device_info" in error_result
        assert error_result["error"] == "Connection failed"
        assert error_result["device_info"] is not None
        assert error_result["device_info"]["name"] == "test-device"

    def test_device_error_result_without_device_info(self):
        """Test DeviceErrorResult without device information."""
        error_result: DeviceErrorResult = {
            "error": "Generic error",
            "device_info": None,
        }

        assert "error" in error_result
        assert "device_info" in error_result
        assert error_result["error"] == "Generic error"
        assert error_result["device_info"] is None


class TestDeviceModelIntegration:
    """Integration tests for Device model with real-world scenarios."""

    def test_device_creation_from_inventory_data(self):
        """Test Device creation from typical inventory data."""
        from src.inventory.file_handler import _convert_device_data

        inventory_data = {
            "name": "PE1-NYC",
            "ip_address": "10.0.1.100",
            "port": 57400,
            "nos": "iosxr",
            "username": "gnmi",
            "password": "gnmi123",
            "insecure": True,
            "skip_verify": True,
            "gnmi_timeout": 30,
        }

        # Convert data as it would be done in inventory loading
        converted_data = _convert_device_data(inventory_data)
        device = Device(**converted_data)

        assert device.name == "PE1-NYC"
        assert device.ip_address == "10.0.1.100"
        assert device.port == 57400
        assert device.nos == NetworkOS.IOSXR
        assert device.username == "gnmi"
        assert device.password == "gnmi123"
        assert device.insecure is True
        assert device.skip_verify is True
        assert device.gnmi_timeout == 30

    def test_device_info_serialization(self):
        """Test that device info can be serialized/deserialized."""
        device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            port=57400,
            nos=NetworkOS.IOSXR,
        )

        device_info = device.to_device_info()

        # Should be JSON serializable
        import json

        json_str = json.dumps(device_info)
        deserialized = json.loads(json_str)

        assert deserialized == device_info
        assert deserialized["name"] == "test-device"
        assert deserialized["ip_address"] == "192.168.1.1"
        assert deserialized["port"] == 57400
        assert deserialized["nos"] == "iosxr"

    def test_device_model_extensibility(self):
        """Test that Device model can be extended if needed."""
        # Create a subclass to test extensibility
        from dataclasses import dataclass

        @dataclass
        class ExtendedDevice(Device):
            region: str = ""
            datacenter: str = ""

        extended_device = ExtendedDevice(
            name="test-device",
            ip_address="192.168.1.1",
            nos=NetworkOS.IOSXR,
            region="us-east",
            datacenter="dc1",
        )

        assert extended_device.name == "test-device"
        assert extended_device.region == "us-east"
        assert extended_device.datacenter == "dc1"

        # Should still have base Device functionality
        device_info = extended_device.to_device_info()
        assert device_info["name"] == "test-device"


class TestDeviceSanitizationMethods:
    """Test suite for Device sanitization methods added in Phase 1."""

    def test_device_to_device_info_safe_method(self):
        """Test the to_device_info_safe method redacts sensitive data."""
        device = Device(
            name="test-device",
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

        safe_device = device.to_device_info_safe()

        # Verify it returns a Device class instance
        assert isinstance(safe_device, Device)

        # Verify sensitive data is redacted
        assert safe_device.password == "***"
        assert safe_device.path_cert == "***"
        assert safe_device.path_key == "***"

        # Verify non-sensitive data is preserved
        assert safe_device.name == "test-device"
        assert safe_device.ip_address == "192.168.1.1"
        assert safe_device.port == 57777
        assert safe_device.nos == NetworkOS.IOSXR
        assert safe_device.username == "admin"
        assert safe_device.path_root == "/path/to/root.ca"  # Not sensitive
        assert safe_device.override == "override.example.com"
        assert safe_device.skip_verify is False
        assert safe_device.gnmi_timeout == 10
        assert safe_device.grpc_options == ["grpc.keepalive_time_ms=30000"]
        assert safe_device.show_diff == "unified"
        assert safe_device.insecure is False

        # Verify original device is unchanged
        assert device.password == "secret123"
        assert device.path_cert == "/path/to/cert.pem"
        assert device.path_key == "/path/to/private.key"

    def test_device_to_device_info_with_auth_method(self):
        """Test the to_device_info_with_auth method preserves all data."""
        device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            port=57777,
            nos=NetworkOS.IOSXR,
            username="admin",
            password="secret123",
            path_cert="/path/to/cert.pem",
            path_key="/path/to/private.key",
            path_root="/path/to/root.ca",
            override="override.example.com",
            skip_verify=True,
            gnmi_timeout=15,
            grpc_options=None,
            show_diff=None,
            insecure=True,
        )

        auth_device = device.to_device_info_with_auth()

        # Verify it returns a Device class instance
        assert isinstance(auth_device, Device)

        # Verify all data is preserved (including sensitive)
        assert auth_device.name == "test-device"
        assert auth_device.ip_address == "192.168.1.1"
        assert auth_device.port == 57777
        assert auth_device.nos == NetworkOS.IOSXR
        assert auth_device.username == "admin"
        assert auth_device.password == "secret123"  # Not redacted
        assert auth_device.path_cert == "/path/to/cert.pem"  # Not redacted
        assert auth_device.path_key == "/path/to/private.key"  # Not redacted
        assert auth_device.path_root == "/path/to/root.ca"
        assert auth_device.override == "override.example.com"
        assert auth_device.skip_verify is True
        assert auth_device.gnmi_timeout == 15
        assert auth_device.grpc_options is None
        assert auth_device.show_diff is None
        assert auth_device.insecure is True

    def test_device_sanitization_methods_with_none_values(self):
        """Test sanitization methods handle None values correctly."""
        device = Device(
            name="minimal-device",
            ip_address="10.1.1.1",
            nos=NetworkOS.IOSXR,
            username="user",
            password=None,
            path_cert=None,
            path_key=None,
        )

        # Test safe method with None values
        safe_device = device.to_device_info_safe()
        assert safe_device.password is None
        assert safe_device.path_cert is None
        assert safe_device.path_key is None

        # Test auth method with None values
        auth_device = device.to_device_info_with_auth()
        assert auth_device.password is None
        assert auth_device.path_cert is None
        assert auth_device.path_key is None

    def test_device_sanitization_methods_class_based_structures(self):
        """Test that sanitization methods return class-based structures, not dictionaries."""
        device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            nos=NetworkOS.IOSXR,
            password="secret123",
        )

        # Test safe method returns class, not dict
        safe_device = device.to_device_info_safe()
        assert isinstance(safe_device, Device)
        assert not isinstance(safe_device, dict)

        # Test auth method returns class, not dict
        auth_device = device.to_device_info_with_auth()
        assert isinstance(auth_device, Device)
        assert not isinstance(auth_device, dict)

    def test_device_sanitization_backward_compatibility(self):
        """Test that existing to_device_info method is unchanged."""
        device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            port=57777,
            nos=NetworkOS.IOSXR,
            username="admin",
            password="secret123",
        )

        device_info = device.to_device_info()

        # Should return a dictionary (original behavior)
        assert isinstance(device_info, dict)
        assert not isinstance(device_info, Device)

        # Should only include non-sensitive information (original behavior)
        expected_info = {
            "name": "test-device",
            "ip_address": "192.168.1.1",
            "port": 57777,
            "nos": "iosxr",
        }

        assert device_info == expected_info

        # Ensure sensitive information is not included (original behavior)
        assert "username" not in device_info
        assert "password" not in device_info
        assert "path_cert" not in device_info
        assert "path_key" not in device_info

    def test_device_sanitization_edge_cases(self):
        """Test sanitization methods with edge case values."""
        device = Device(
            name="edge-case-device",
            ip_address="192.168.1.1",
            nos=NetworkOS.IOSXR,
            password="",  # Empty string
            path_cert="   ",  # Whitespace only
            path_key="actual_key",  # Normal value
        )

        safe_device = device.to_device_info_safe()

        # Empty string should remain (truthy check in sanitizer)
        assert safe_device.password == ""
        # Whitespace should be redacted (truthy)
        assert safe_device.path_cert == "***"
        # Normal value should be redacted
        assert safe_device.path_key == "***"

    def test_device_sanitization_immutability(self):
        """Test that sanitization methods don't modify the original device."""
        original_password = "original_secret"
        original_cert = "/original/cert.pem"

        device = Device(
            name="immutable-test",
            ip_address="192.168.1.1",
            nos=NetworkOS.IOSXR,
            password=original_password,
            path_cert=original_cert,
        )

        # Call both sanitization methods
        safe_device = device.to_device_info_safe()
        auth_device = device.to_device_info_with_auth()

        # Original device should be unchanged
        assert device.password == original_password
        assert device.path_cert == original_cert

        # Safe device should have redacted data
        assert safe_device.password == "***"
        assert safe_device.path_cert == "***"

        # Auth device should have original data
        assert auth_device.password == original_password
        assert auth_device.path_cert == original_cert
