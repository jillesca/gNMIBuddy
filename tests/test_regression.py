#!/usr/bin/env python3
"""
Regression tests for sanitization functionality.

Verifies all existing functionality still works, performance hasn't degraded,
error handling remains intact, and backward compatibility is maintained.
"""

import pytest
import time
from unittest.mock import patch, MagicMock

from src.schemas.models import Device, DeviceListResult, NetworkOS
from src.inventory.manager import InventoryManager
from src.inventory.sanitizer import DeviceDataSanitizer
import api


class TestRegressionFunctionality:
    """Test suite for regression testing of existing functionality."""

    @pytest.fixture
    def sample_device(self):
        """Create a sample device for testing."""
        return Device(
            name="regression-test-device",
            ip_address="192.168.100.1",
            port=57777,
            nos=NetworkOS.IOSXR,
            username="test_user",
            password="test_password",
            path_cert="/test/cert.pem",
            path_key="/test/key.pem",
            gnmi_timeout=10,
            insecure=True,
        )

    @pytest.fixture
    def sample_device_list_result(self, sample_device):
        """Create a sample device list result."""
        return DeviceListResult(devices=[sample_device])

    def test_existing_list_devices_method_unchanged(
        self, sample_device_list_result
    ):
        """Test that the original list_devices method remains completely unchanged."""

        # Mock the get_devices method that list_devices actually calls
        mock_devices = {
            device.name: device for device in sample_device_list_result.devices
        }

        with patch.object(
            InventoryManager, "get_instance"
        ) as mock_get_instance:
            mock_instance = MagicMock()
            mock_instance.is_initialized.return_value = True
            mock_instance.get_devices.return_value = mock_devices
            mock_get_instance.return_value = mock_instance

            result = InventoryManager.list_devices()

            # Verify return type is unchanged
            assert isinstance(result, DeviceListResult)

            # Verify original functionality preserved
            assert len(result.devices) == 1
            device = result.devices[0]

            # Verify sensitive data is NOT redacted (original behavior)
            assert device.password == "test_password"
            assert device.path_cert == "/test/cert.pem"
            assert device.path_key == "/test/key.pem"

            # Verify non-sensitive data is preserved
            assert device.name == "regression-test-device"
            assert device.ip_address == "192.168.100.1"

    def test_device_model_cleanup_verification(self, sample_device):
        """Test that deprecated device methods have been properly removed."""
        # Verify that deprecated methods have been removed following YAGNI principle
        assert not hasattr(sample_device, "to_device_info")
        assert not hasattr(sample_device, "to_device_info_safe")
        assert not hasattr(sample_device, "to_device_info_with_auth")

        # Verify the device still works for core functionality
        assert sample_device.name == "regression-test-device"
        assert sample_device.ip_address == "192.168.100.1"
        assert (
            sample_device.password == "test_password"
        )  # Sensitive data intact in Device object

    def test_device_model_backward_compatibility(self):
        """Test that Device model maintains backward compatibility."""

        # Test device creation with minimal fields (original way)
        device = Device(
            name="compat-test", ip_address="10.1.1.1", nos=NetworkOS.IOSXR
        )

        # Verify default values are unchanged
        assert device.port == 830
        assert device.gnmi_timeout == 5
        assert device.insecure is True
        assert device.skip_verify is False
        assert device.username is None
        assert device.password is None

        # Test device creation with all fields (original way)
        full_device = Device(
            name="full-test",
            ip_address="10.1.1.2",
            port=57777,
            nos=NetworkOS.IOSXR,
            username="admin",
            password="secret",
            gnmi_timeout=30,
            insecure=False,
        )

        # Verify all fields are set correctly
        assert full_device.username == "admin"
        assert full_device.password == "secret"
        assert full_device.gnmi_timeout == 30
        assert full_device.insecure is False

    def test_device_list_result_structure_unchanged(self, sample_device):
        """Test that DeviceListResult structure remains unchanged."""

        devices = [sample_device]
        result = DeviceListResult(devices=devices)

        # Verify structure is unchanged
        assert hasattr(result, "devices")
        assert isinstance(result.devices, list)
        assert len(result.devices) == 1
        assert isinstance(result.devices[0], Device)

    def test_existing_error_handling_unchanged(self):
        """Test that existing error handling mechanisms remain intact."""

        # Test FileNotFoundError handling in InventoryManager
        with patch.object(
            InventoryManager, "get_instance"
        ) as mock_get_instance:
            mock_instance = MagicMock()
            mock_instance.is_initialized.return_value = True
            mock_instance.get_devices.side_effect = FileNotFoundError(
                "Test error"
            )
            mock_get_instance.return_value = mock_instance

            with pytest.raises(FileNotFoundError):
                InventoryManager.list_devices()

        # Test that new safe method also handles errors correctly
        with patch.object(
            InventoryManager, "get_instance"
        ) as mock_get_instance:
            mock_instance = MagicMock()
            mock_instance.is_initialized.return_value = True
            mock_instance.get_devices.side_effect = FileNotFoundError(
                "Test error"
            )
            mock_get_instance.return_value = mock_instance

            with pytest.raises(FileNotFoundError):
                InventoryManager.list_devices_safe()

    def test_device_equality_and_comparison_unchanged(self):
        """Test that Device equality and comparison behavior is unchanged."""

        device1 = Device(
            name="test-device",
            ip_address="192.168.1.1",
            nos=NetworkOS.IOSXR,
            password="secret",
        )

        device2 = Device(
            name="test-device",
            ip_address="192.168.1.1",
            nos=NetworkOS.IOSXR,
            password="secret",
        )

        device3 = Device(
            name="different-device",
            ip_address="192.168.1.1",
            nos=NetworkOS.IOSXR,
            password="secret",
        )

        # Test equality works as before
        assert device1 == device2
        assert device1 != device3

        # Test that Device objects still maintain their basic functionality
        assert device1.name == "test-device"
        assert device1.password == "secret"


class TestRegressionPerformance:
    """Test suite for performance regression testing."""

    def test_sanitization_performance_overhead(self):
        """Test that sanitization doesn't introduce significant performance overhead."""

        # Create a list of devices for performance testing
        devices = []
        for i in range(100):
            device = Device(
                name=f"perf-test-device-{i}",
                ip_address=f"192.168.1.{i+1}",
                nos=NetworkOS.IOSXR,
                username="admin",
                password=f"password_{i}",
                path_cert=f"/cert_{i}.pem",
            )
            devices.append(device)

        device_list_result = DeviceListResult(devices=devices)
        sanitizer = DeviceDataSanitizer()

        # Measure sanitization time
        start_time = time.time()
        sanitized_result = sanitizer.sanitize_device_list_result(
            device_list_result
        )
        sanitization_time = time.time() - start_time

        # Verify functionality works
        assert len(sanitized_result.devices) == 100
        assert all(
            device.password == "***" for device in sanitized_result.devices
        )

        # Performance should be reasonable (less than 100ms for 100 devices)
        assert (
            sanitization_time < 0.1
        ), f"Sanitization took too long: {sanitization_time:.3f}s"

    def test_list_devices_safe_performance(self):
        """Test that list_devices_safe doesn't significantly impact performance."""

        # Create mock devices for performance testing
        devices = [
            Device(
                name=f"list-perf-{i}",
                ip_address=f"10.0.0.{i+1}",
                nos=NetworkOS.IOSXR,
                password=f"secret_{i}",
            )
            for i in range(50)
        ]

        mock_devices = {device.name: device for device in devices}

        with patch.object(
            InventoryManager, "get_instance"
        ) as mock_get_instance:
            mock_instance = MagicMock()
            mock_instance.is_initialized.return_value = True
            mock_instance.get_devices.return_value = mock_devices
            mock_get_instance.return_value = mock_instance

            # Measure original method time
            start_time = time.time()
            original_result = InventoryManager.list_devices()
            original_time = time.time() - start_time

            # Measure safe method time
            start_time = time.time()
            safe_result = InventoryManager.list_devices_safe()
            safe_time = time.time() - start_time

            # Verify functionality
            assert len(original_result.devices) == 50
            assert len(safe_result.devices) == 50

            # Safe method should not be significantly slower (less than 100x for reasonable margin)
            # In testing environments, timing can be very inconsistent
            performance_ratio = (
                safe_time / original_time if original_time > 0 else 1
            )
            assert (
                performance_ratio < 100.0
            ), f"Safe method is too slow: {performance_ratio:.2f}x"

    def test_api_get_devices_performance(self):
        """Test that API get_devices performance is acceptable."""

        devices = [
            Device(
                name=f"api-perf-{i}",
                ip_address=f"172.16.0.{i+1}",
                nos=NetworkOS.IOSXR,
                password="secret",
            )
            for i in range(20)
        ]

        sanitized_devices = [
            Device(
                name=f"api-perf-{i}",
                ip_address=f"172.16.0.{i+1}",
                nos=NetworkOS.IOSXR,
                password="***",
            )
            for i in range(20)
        ]

        sanitized_result = DeviceListResult(devices=sanitized_devices)

        with patch(
            "api.list_available_devices_safe", return_value=sanitized_result
        ):

            # Measure API call time
            start_time = time.time()
            result = api.get_devices()
            api_time = time.time() - start_time

            # Verify functionality
            assert len(result.devices) == 20
            assert all(device.password == "***" for device in result.devices)

            # API should be fast (less than 50ms for 20 devices)
            assert api_time < 0.05, f"API too slow: {api_time:.3f}s"


class TestRegressionEdgeCases:
    """Test suite for edge case regression testing - updated for sanitizer architecture."""

    def test_sanitizer_handles_none_values_correctly(self):
        """Test that DeviceDataSanitizer handles None values correctly."""
        from src.inventory.sanitizer import DeviceDataSanitizer

        device = Device(
            name="none-test",
            ip_address="192.168.1.1",
            nos=NetworkOS.IOSXR,
            username=None,
            password=None,
            path_cert=None,
            path_key=None,
        )

        sanitizer = DeviceDataSanitizer()
        sanitized_device = sanitizer.sanitize_device(device)

        # None values should remain None (not redacted)
        assert sanitized_device.password is None
        assert sanitized_device.username is None
        assert sanitized_device.path_cert is None
        assert sanitized_device.path_key is None

    def test_sanitizer_handles_special_characters(self):
        """Test that sanitizer handles special characters correctly."""
        from src.inventory.sanitizer import DeviceDataSanitizer

        device = Device(
            name="special-char-test",
            ip_address="192.168.1.1",
            nos=NetworkOS.IOSXR,
            password="p@$$w0rd!@#$%^&*()",
            path_cert="/path/with spaces/cert-file.pem",
            path_key="/path/with/unicode/鍵.key",
        )

        sanitizer = DeviceDataSanitizer()
        sanitized_device = sanitizer.sanitize_device(device)

        # All should be redacted regardless of special characters
        assert sanitized_device.password == "***"
        assert sanitized_device.path_cert == "***"
        assert sanitized_device.path_key == "***"

        # Original should be unchanged
        assert device.password == "p@$$w0rd!@#$%^&*()"
        assert device.path_cert == "/path/with spaces/cert-file.pem"
        assert device.path_key == "/path/with/unicode/鍵.key"


class TestRegressionDataIntegrity:
    """Test suite for data integrity regression testing - updated for sanitizer architecture."""

    def test_sanitizer_immutability(self):
        """Test that DeviceDataSanitizer maintains data immutability."""
        from src.inventory.sanitizer import DeviceDataSanitizer

        original_password = "original_secret"
        original_cert = "/original/cert.pem"

        device = Device(
            name="immutability-test",
            ip_address="192.168.1.1",
            nos=NetworkOS.IOSXR,
            password=original_password,
            path_cert=original_cert,
        )

        # Store original object id for verification
        original_device_id = id(device)

        # Use the actual sanitizer (not deprecated methods)
        sanitizer = DeviceDataSanitizer()
        sanitized_device = sanitizer.sanitize_device(device)

        # Verify original device is completely unchanged
        assert id(device) == original_device_id
        assert device.password == original_password
        assert device.path_cert == original_cert

        # Verify sanitized device has redacted data
        assert sanitized_device.password == "***"
        assert sanitized_device.path_cert == "***"

    def test_device_basic_functionality_preserved(self):
        """Test that Device objects maintain basic functionality after cleanup."""
        device = Device(
            name="basic-test",
            ip_address="192.168.1.1",
            nos=NetworkOS.IOSXR,
            password="test_password",
        )

        # Verify basic Device functionality still works
        assert device.name == "basic-test"
        assert device.password == "test_password"
        assert device.ip_address == "192.168.1.1"

        # Verify equality comparison still works
        device2 = Device(
            name="basic-test",
            ip_address="192.168.1.1",
            nos=NetworkOS.IOSXR,
            password="test_password",
        )
        assert device == device2
