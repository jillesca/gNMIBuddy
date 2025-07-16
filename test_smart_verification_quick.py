#!/usr/bin/env python3
"""
Quick test to verify the smart verification decorator works after fixing circular import.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.decorators.smart_capability_verification import verify_required_models
from src.schemas.models import Device
from src.schemas.responses import NetworkOperationResult, OperationStatus
from src.gnmi.parameters import GnmiRequest
from src.schemas.openconfig_models import OpenConfigModel


def test_smart_verification_decorator_basic():
    """Test that the smart verification decorator can be imported and used."""

    # Mock the verify_models function to avoid actual network calls
    with patch(
        "src.decorators.smart_capability_verification.verify_models"
    ) as mock_verify:
        # Mock successful verification
        mock_verify.return_value = MagicMock()
        mock_verify.return_value.overall_status.value = "supported"
        mock_verify.return_value.has_errors.return_value = False

        @verify_required_models()
        def test_function(device: Device) -> NetworkOperationResult:
            return NetworkOperationResult(
                device_name=device.name,
                ip_address=device.ip_address,
                nos=device.nos,
                operation_type="test",
                status=OperationStatus.SUCCESS,
                data={"test": "data"},
            )

        # Test that the decorator works
        device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            port=57400,
            username="admin",
            password="password",
            nos="iosxr",
        )

        result = test_function(device)

        # Verify that the function executed successfully
        assert result.device_name == "test-device"
        assert result.status == OperationStatus.SUCCESS
        assert result.data == {"test": "data"}
        print("✓ Smart verification decorator test passed!")


def test_smart_verification_with_gnmi_request():
    """Test that the decorator can extract models from GnmiRequest."""

    with patch(
        "src.decorators.smart_capability_verification.verify_models"
    ) as mock_verify:
        # Mock successful verification
        mock_verify.return_value = MagicMock()
        mock_verify.return_value.overall_status.value = "supported"
        mock_verify.return_value.has_errors.return_value = False

        @verify_required_models()
        def test_function_with_request(
            device: Device, request: GnmiRequest
        ) -> NetworkOperationResult:
            return NetworkOperationResult(
                device_name=device.name,
                ip_address=device.ip_address,
                nos=device.nos,
                operation_type="test",
                status=OperationStatus.SUCCESS,
                data={"models": list(request.get_required_models())},
            )

        device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            port=57400,
            username="admin",
            password="password",
            nos="iosxr",
        )

        request = GnmiRequest(path=["openconfig-system:/system"])

        result = test_function_with_request(device, request)

        # Verify that the function executed successfully
        assert result.device_name == "test-device"
        assert result.status == OperationStatus.SUCCESS

        # Verify that the models were detected
        detected_models = result.data["models"]
        assert OpenConfigModel.SYSTEM in detected_models
        print("✓ Smart verification with GnmiRequest test passed!")


if __name__ == "__main__":
    test_smart_verification_decorator_basic()
    test_smart_verification_with_gnmi_request()
    print("All tests passed! The circular import issue has been fixed.")
