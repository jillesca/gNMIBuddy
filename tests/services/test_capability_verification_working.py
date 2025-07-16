#!/usr/bin/env python3
"""
Simple working tests for capability_verification service.
"""

import pytest
from unittest.mock import patch
from src.services.capability_verification import (
    verify_openconfig_network_instance,
)
from src.schemas.models import Device
from src.schemas.responses import SuccessResponse, ErrorResponse


@pytest.fixture
def mock_device():
    """Create a mock device for testing."""
    return Device(
        name="test-device",
        ip_address="192.168.1.1",
        port=57400,
        username="admin",
        password="password",
        nos="iosxr",
    )


class TestCapabilityVerification:
    """Test OpenConfig capability verification functionality."""

    def test_verify_openconfig_network_instance_success(self, mock_device):
        """Test successful verification of openconfig-network-instance model."""
        # Mock successful capabilities response
        mock_capabilities = {
            "supported_models": [
                {
                    "name": "openconfig-network-instance",
                    "version": "1.3.0",
                    "organization": "OpenConfig working group",
                }
            ]
        }

        with patch(
            "src.services.capability_verification.get_device_capabilities"
        ) as mock_get_caps:
            mock_get_caps.return_value = SuccessResponse(
                data=[mock_capabilities]
            )

            result = verify_openconfig_network_instance(mock_device)

            assert result["is_supported"] is True
            assert "model_capability" in result
            assert result["error_message"] is None

    def test_verify_openconfig_network_instance_error(self, mock_device):
        """Test error handling in openconfig-network-instance verification."""
        with patch(
            "src.services.capability_verification.get_device_capabilities"
        ) as mock_get_caps:
            mock_get_caps.return_value = ErrorResponse(
                type="connection_error", message="Connection failed"
            )

            result = verify_openconfig_network_instance(mock_device)

            assert result["is_supported"] is False
            assert result["error_message"] is not None
            assert "Connection failed" in result["error_message"]


if __name__ == "__main__":
    pytest.main([__file__])
