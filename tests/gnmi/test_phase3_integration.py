#!/usr/bin/env python3
"""
Tests for Phase 3 integration - capability verification in gNMI client and decorators.
"""

import os
from unittest.mock import patch
from src.schemas.models import Device
from src.gnmi.error_handlers import handle_capability_error
from src.decorators.capability_verification import (
    verify_capabilities,
    _extract_device_from_args,
)
from src.schemas.responses import NetworkOperationResult, OperationStatus


class TestCapabilityErrorHandler:
    """Test the new capability error handler."""

    def test_handle_capability_error(self):
        """Test capability error handler creates proper error response."""
        device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            port=9339,
            username="admin",
            password="admin",
            insecure=True,
            nos="iosxr",
        )

        error_message = "Device does not support openconfig-network-instance"

        error_response = handle_capability_error(device, error_message)

        assert error_response.type == "CAPABILITY_NOT_SUPPORTED"
        assert "test-device" in (error_response.message or "")
        assert "192.168.1.1:9339" in (error_response.message or "")
        assert error_message in (error_response.message or "")
        assert error_response.details["device_name"] == "test-device"
        assert error_response.details["device_ip"] == "192.168.1.1"
        assert error_response.details["device_port"] == 9339
        assert error_response.details["capability_error"] == error_message

    def test_handle_capability_error_custom_type(self):
        """Test capability error handler with custom error type."""
        device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            port=9339,
            username="admin",
            password="admin",
            insecure=True,
            nos="iosxr",
        )

        error_message = "Version too old"
        error_type = "CAPABILITY_VERSION_TOO_OLD"

        error_response = handle_capability_error(
            device, error_message, error_type
        )

        assert error_response.type == error_type
        assert error_message in (error_response.message or "")


class TestCapabilityVerificationDecorator:
    """Test the capability verification decorator."""

    def setup_method(self):
        """Enable capability verification for these tests."""
        self.original_env = os.environ.get(
            "GNMIBUDDY_DISABLE_CAPABILITY_VERIFICATION"
        )
        # Temporarily enable capability verification for these tests
        if "GNMIBUDDY_DISABLE_CAPABILITY_VERIFICATION" in os.environ:
            del os.environ["GNMIBUDDY_DISABLE_CAPABILITY_VERIFICATION"]

    def teardown_method(self):
        """Restore original environment."""
        if self.original_env is not None:
            os.environ["GNMIBUDDY_DISABLE_CAPABILITY_VERIFICATION"] = (
                self.original_env
            )

    def test_extract_device_from_args_positional(self):
        """Test extracting device from positional arguments."""
        device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            port=9339,
            username="admin",
            password="admin",
            insecure=True,
            nos="iosxr",
        )

        extracted = _extract_device_from_args(device, "other_arg")
        assert extracted == device

        extracted = _extract_device_from_args("other_arg", device)
        assert extracted == device

    def test_extract_device_from_args_keyword(self):
        """Test extracting device from keyword arguments."""
        device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            port=9339,
            username="admin",
            password="admin",
            insecure=True,
            nos="iosxr",
        )

        extracted = _extract_device_from_args(device=device)
        assert extracted == device

        extracted = _extract_device_from_args(target_device=device)
        assert extracted == device

    def test_extract_device_from_args_not_found(self):
        """Test extracting device when no device is present."""
        extracted = _extract_device_from_args("arg1", "arg2", param1="value1")
        assert extracted is None

    @patch("src.decorators.capability_verification.is_device_verified")
    @patch(
        "src.decorators.capability_verification.verify_openconfig_network_instance"
    )
    @patch("src.decorators.capability_verification.cache_verification_result")
    def test_decorator_with_supported_device(
        self, mock_cache, mock_verify, mock_is_verified
    ):
        """Test decorator with device that supports required capability."""
        device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            port=9339,
            username="admin",
            password="admin",
            insecure=True,
            nos="iosxr",
        )

        # Mock that device is not verified initially
        mock_is_verified.return_value = False

        # Mock successful verification
        mock_verify.return_value = {
            "is_supported": True,
            "model_capability": {
                "model_name": "openconfig-network-instance",
                "found_version": "1.3.0",
                "required_version": "1.3.0",
                "status": "supported",
            },
        }

        @verify_capabilities()
        def mock_function(device: Device):
            return NetworkOperationResult(
                device_name=device.name,
                ip_address=device.ip_address,
                nos=device.nos,
                operation_type="test",
                status=OperationStatus.SUCCESS,
            )

        result = mock_function(device)

        assert result.status == OperationStatus.SUCCESS
        assert result.device_name == "test-device"

        # Verify that verification was called
        mock_verify.assert_called_once_with(device)

        # Verify that result was cached
        mock_cache.assert_called_once()

    @patch("src.decorators.capability_verification.is_device_verified")
    @patch(
        "src.decorators.capability_verification.verify_openconfig_network_instance"
    )
    @patch("src.decorators.capability_verification.cache_verification_result")
    def test_decorator_with_unsupported_device(
        self, mock_cache, mock_verify, mock_is_verified
    ):
        """Test decorator with device that doesn't support required capability."""
        device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            port=9339,
            username="admin",
            password="admin",
            insecure=True,
            nos="iosxr",
        )

        # Mock that device is not verified initially
        mock_is_verified.return_value = False

        # Mock failed verification
        mock_verify.return_value = {
            "is_supported": False,
            "error_message": "Device does not support openconfig-network-instance",
            "model_capability": {
                "model_name": "openconfig-network-instance",
                "required_version": "1.3.0",
                "status": "NOT_FOUND",
            },
        }

        @verify_capabilities()
        def mock_function(device: Device):
            return NetworkOperationResult(
                device_name=device.name,
                ip_address=device.ip_address,
                nos=device.nos,
                operation_type="test",
                status=OperationStatus.SUCCESS,
            )

        result = mock_function(device)

        assert result.status == OperationStatus.FAILED
        assert result.error_response is not None
        assert result.error_response.type == "CAPABILITY_VERIFICATION_FAILED"
        assert "openconfig-network-instance" in (
            result.error_response.message or ""
        )

        # Verify that verification was called
        mock_verify.assert_called_once_with(device)

        # Verify that failure was cached
        mock_cache.assert_called_once()

    @patch("src.decorators.capability_verification.is_device_verified")
    @patch(
        "src.decorators.capability_verification.verify_openconfig_network_instance"
    )
    @patch("src.decorators.capability_verification.cache_verification_result")
    def test_decorator_with_fail_on_unsupported_false(
        self, mock_cache, mock_verify, mock_is_verified
    ):
        """Test decorator with fail_on_unsupported=False."""
        device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            port=9339,
            username="admin",
            password="admin",
            insecure=True,
            nos="iosxr",
        )

        # Mock that device is not verified initially
        mock_is_verified.return_value = False

        # Mock failed verification
        mock_verify.return_value = {
            "is_supported": False,
            "error_message": "Device does not support openconfig-network-instance",
            "model_capability": {
                "model_name": "openconfig-network-instance",
                "required_version": "1.3.0",
                "status": "NOT_FOUND",
            },
        }

        @verify_capabilities(fail_on_unsupported=False)
        def mock_function(device: Device):
            return NetworkOperationResult(
                device_name=device.name,
                ip_address=device.ip_address,
                nos=device.nos,
                operation_type="test",
                status=OperationStatus.SUCCESS,
            )

        result = mock_function(device)

        # Should succeed even with unsupported device
        assert result.status == OperationStatus.SUCCESS
        assert result.device_name == "test-device"

        # Verify that verification was called
        mock_verify.assert_called_once_with(device)

        # Verify that failure was cached
        mock_cache.assert_called_once()

    @patch("src.decorators.capability_verification.is_device_verified")
    def test_decorator_with_already_verified_device(self, mock_is_verified):
        """Test decorator skips verification for already verified device."""
        device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            port=9339,
            username="admin",
            password="admin",
            insecure=True,
            nos="iosxr",
        )

        # Mock that device is already verified
        mock_is_verified.return_value = True

        @verify_capabilities()
        def mock_function(device: Device):
            return NetworkOperationResult(
                device_name=device.name,
                ip_address=device.ip_address,
                nos=device.nos,
                operation_type="test",
                status=OperationStatus.SUCCESS,
            )

        result = mock_function(device)

        assert result.status == OperationStatus.SUCCESS
        assert result.device_name == "test-device"

        # Verify that verification was not called since device is already verified
        mock_is_verified.assert_called_once_with("test-device")

    def test_decorator_with_no_device_argument(self):
        """Test decorator handles case where no device is found in arguments."""

        @verify_capabilities()
        def mock_function(
            some_other_arg: str,
        ):  # pylint: disable=unused-argument
            return "should not reach here"

        result = mock_function("test")

        assert isinstance(result, NetworkOperationResult)
        assert result.status == OperationStatus.FAILED
        assert result.error_response is not None
        assert "Could not extract device" in (
            result.error_response.message or ""
        )
