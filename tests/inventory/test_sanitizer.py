#!/usr/bin/env python3
"""
Tests for the DeviceDataSanitizer class in src/inventory/sanitizer.py.

Tests sensitive data redaction, non-sensitive data preservation,
class-based data structures, and edge cases.
"""

import pytest
from typing import List
from src.inventory.sanitizer import DeviceDataSanitizer
from src.schemas.models import Device, DeviceListResult, NetworkOS


class TestDeviceDataSanitizer:
    """Test suite for the DeviceDataSanitizer class."""

    @pytest.fixture
    def sanitizer(self):
        """Create a DeviceDataSanitizer instance for testing."""
        return DeviceDataSanitizer()

    @pytest.fixture
    def test_device_with_sensitive_data(self):
        """Create a test device with sensitive authentication data."""
        return Device(
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
            show_diff="true",
            insecure=False,
        )

    @pytest.fixture
    def test_device_without_sensitive_data(self):
        """Create a test device without sensitive authentication data."""
        return Device(
            name="test-device-minimal",
            ip_address="10.1.1.1",
            port=830,
            nos=NetworkOS.IOSXR,
            username="user",
            password=None,
            path_cert=None,
            path_key=None,
            path_root="/path/to/root.ca",
            override=None,
            skip_verify=True,
            gnmi_timeout=5,
            grpc_options=None,
            show_diff=None,
            insecure=True,
        )

    def test_sanitize_device_with_sensitive_data(
        self, sanitizer, test_device_with_sensitive_data
    ):
        """Test that sensitive data is properly redacted in a single device."""
        sanitized = sanitizer.sanitize_device(test_device_with_sensitive_data)

        # Verify it returns a Device class instance
        assert isinstance(sanitized, Device)

        # Verify sensitive data is redacted
        assert sanitized.password == "***"
        assert sanitized.path_cert == "***"
        assert sanitized.path_key == "***"

        # Verify non-sensitive data is preserved
        assert sanitized.name == "test-device"
        assert sanitized.ip_address == "192.168.1.1"
        assert sanitized.port == 57777
        assert sanitized.nos == NetworkOS.IOSXR
        assert sanitized.username == "admin"
        assert sanitized.path_root == "/path/to/root.ca"  # Not sensitive
        assert sanitized.override == "override.example.com"
        assert sanitized.skip_verify is False
        assert sanitized.gnmi_timeout == 10
        assert sanitized.grpc_options == ["grpc.keepalive_time_ms=30000"]
        assert sanitized.show_diff == "true"
        assert sanitized.insecure is False

        # Verify original device is unchanged
        assert test_device_with_sensitive_data.password == "secret123"
        assert test_device_with_sensitive_data.path_cert == "/path/to/cert.pem"
        assert (
            test_device_with_sensitive_data.path_key == "/path/to/private.key"
        )

    def test_sanitize_device_without_sensitive_data(
        self, sanitizer, test_device_without_sensitive_data
    ):
        """Test that devices without sensitive data are handled correctly."""
        sanitized = sanitizer.sanitize_device(
            test_device_without_sensitive_data
        )

        # Verify it returns a Device class instance
        assert isinstance(sanitized, Device)

        # Verify None values are preserved as None (not redacted)
        assert sanitized.password is None
        assert sanitized.path_cert is None
        assert sanitized.path_key is None

        # Verify all other data is preserved
        assert sanitized.name == "test-device-minimal"
        assert sanitized.ip_address == "10.1.1.1"
        assert sanitized.port == 830
        assert sanitized.nos == NetworkOS.IOSXR
        assert sanitized.username == "user"
        assert sanitized.path_root == "/path/to/root.ca"
        assert sanitized.override is None
        assert sanitized.skip_verify is True
        assert sanitized.gnmi_timeout == 5
        assert sanitized.grpc_options is None
        assert sanitized.show_diff is None
        assert sanitized.insecure is True

    def test_sanitize_device_list(
        self,
        sanitizer,
        test_device_with_sensitive_data,
        test_device_without_sensitive_data,
    ):
        """Test sanitization of a list of devices."""
        device_list = [
            test_device_with_sensitive_data,
            test_device_without_sensitive_data,
        ]
        sanitized_list = sanitizer.sanitize_device_list(device_list)

        # Verify it returns a list of Device class instances
        assert isinstance(sanitized_list, list)
        assert len(sanitized_list) == 2
        assert all(isinstance(device, Device) for device in sanitized_list)

        # Verify first device (with sensitive data) is sanitized
        device1 = sanitized_list[0]
        assert device1.password == "***"
        assert device1.path_cert == "***"
        assert device1.path_key == "***"
        assert device1.name == "test-device"

        # Verify second device (without sensitive data) preserves None values
        device2 = sanitized_list[1]
        assert device2.password is None
        assert device2.path_cert is None
        assert device2.path_key is None
        assert device2.name == "test-device-minimal"

    def test_sanitize_device_list_result(
        self,
        sanitizer,
        test_device_with_sensitive_data,
        test_device_without_sensitive_data,
    ):
        """Test sanitization of a DeviceListResult object."""
        device_list = [
            test_device_with_sensitive_data,
            test_device_without_sensitive_data,
        ]
        device_list_result = DeviceListResult(devices=device_list)

        sanitized_result = sanitizer.sanitize_device_list_result(
            device_list_result
        )

        # Verify it returns a DeviceListResult class instance
        assert isinstance(sanitized_result, DeviceListResult)

        # Verify devices are sanitized
        assert len(sanitized_result.devices) == 2
        assert sanitized_result.devices[0].password == "***"
        assert sanitized_result.devices[0].path_cert == "***"
        assert sanitized_result.devices[0].path_key == "***"
        assert sanitized_result.devices[1].password is None
        assert sanitized_result.devices[1].path_cert is None
        assert sanitized_result.devices[1].path_key is None

    def test_sanitize_empty_device_list(self, sanitizer):
        """Test sanitization of an empty device list."""
        empty_list = []
        sanitized_list = sanitizer.sanitize_device_list(empty_list)

        assert isinstance(sanitized_list, list)
        assert len(sanitized_list) == 0

    def test_sanitize_empty_device_list_result(self, sanitizer):
        """Test sanitization of an empty DeviceListResult."""
        empty_result = DeviceListResult(devices=[])

        sanitized_result = sanitizer.sanitize_device_list_result(empty_result)

        assert isinstance(sanitized_result, DeviceListResult)
        assert len(sanitized_result.devices) == 0

    def test_edge_case_empty_string_password(self, sanitizer):
        """Test handling of empty string password."""
        device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            nos=NetworkOS.IOSXR,
            password="",  # Empty string
            path_cert="",  # Empty string
            path_key="",  # Empty string
        )

        sanitized = sanitizer.sanitize_device(device)

        # Empty strings are falsy and should not be redacted (preserved as-is)
        assert sanitized.password == ""
        assert sanitized.path_cert == ""
        assert sanitized.path_key == ""

    def test_edge_case_whitespace_only_password(self, sanitizer):
        """Test handling of whitespace-only sensitive fields."""
        device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            nos=NetworkOS.IOSXR,
            password="   ",  # Whitespace only
            path_cert="\t\n",  # Tabs and newlines
            path_key=" ",  # Single space
        )

        sanitized = sanitizer.sanitize_device(device)

        # Whitespace-only strings should be redacted
        assert sanitized.password == "***"
        assert sanitized.path_cert == "***"
        assert sanitized.path_key == "***"

    def test_custom_redaction_marker(self):
        """Test sanitizer with custom redaction marker."""
        custom_sanitizer = DeviceDataSanitizer()
        # Access private attribute for testing
        custom_sanitizer._redaction_marker = "[REDACTED]"

        device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            nos=NetworkOS.IOSXR,
            password="secret123",
        )

        sanitized = custom_sanitizer.sanitize_device(device)
        assert sanitized.password == "[REDACTED]"

    def test_class_based_data_structures(
        self, sanitizer, test_device_with_sensitive_data
    ):
        """Test that all returned data uses class-based structures, not dictionaries."""
        # Test single device sanitization
        sanitized_device = sanitizer.sanitize_device(
            test_device_with_sensitive_data
        )
        assert isinstance(sanitized_device, Device)
        assert not isinstance(sanitized_device, dict)

        # Test device list sanitization
        device_list = [test_device_with_sensitive_data]
        sanitized_list = sanitizer.sanitize_device_list(device_list)
        assert isinstance(sanitized_list, list)
        assert all(
            isinstance(device, Device) and not isinstance(device, dict)
            for device in sanitized_list
        )

        # Test device list result sanitization
        device_list_result = DeviceListResult(devices=device_list)
        sanitized_result = sanitizer.sanitize_device_list_result(
            device_list_result
        )
        assert isinstance(sanitized_result, DeviceListResult)
        assert not isinstance(sanitized_result, dict)
        assert all(
            isinstance(device, Device) and not isinstance(device, dict)
            for device in sanitized_result.devices
        )

    def test_immutability_original_data_unchanged(
        self, sanitizer, test_device_with_sensitive_data
    ):
        """Test that original data structures are not modified during sanitization."""
        original_password = test_device_with_sensitive_data.password
        original_cert = test_device_with_sensitive_data.path_cert
        original_key = test_device_with_sensitive_data.path_key

        # Sanitize the device
        sanitized = sanitizer.sanitize_device(test_device_with_sensitive_data)

        # Verify original device is unchanged
        assert test_device_with_sensitive_data.password == original_password
        assert test_device_with_sensitive_data.path_cert == original_cert
        assert test_device_with_sensitive_data.path_key == original_key

        # Verify sanitized device has redacted data
        assert sanitized.password == "***"
        assert sanitized.path_cert == "***"
        assert sanitized.path_key == "***"
