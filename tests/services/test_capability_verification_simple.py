#!/usr/bin/env python3
"""
Simple tests for capability_verification service.

Basic tests for OpenConfig model capability verification functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.services.capability_verification import (
    verify_openconfig_network_instance,
    verify_models,
    verify_single_model,
    get_verification_summary,
)
from src.schemas.models import Device
from src.schemas.openconfig_models import OpenConfigModel
from src.schemas.responses import SuccessResponse, ErrorResponse
from src.schemas.verification_results import (
    ModelVerificationResult,
    MultiModelVerificationResult,
    VerificationStatus,
)


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
                data=[mock_capabilities], timestamp="2023-05-15T12:00:00Z"
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

    def test_verify_single_model_success(self, mock_device):
        """Test successful single model verification."""
        # Mock successful capabilities response
        mock_capabilities = {
            "supported_models": [
                {
                    "name": "openconfig-interfaces",
                    "version": "4.0.0",
                    "organization": "OpenConfig working group",
                }
            ]
        }

        with patch(
            "src.services.capability_verification.get_device_capabilities"
        ) as mock_get_caps:
            mock_get_caps.return_value = SuccessResponse(
                data=[mock_capabilities], timestamp="2023-05-15T12:00:00Z"
            )

            result = verify_single_model(
                mock_device, OpenConfigModel.INTERFACES
            )

            assert result.status == VerificationStatus.SUPPORTED
            assert result.model == OpenConfigModel.INTERFACES
            assert result.error_message is None

    def test_verify_single_model_not_found(self, mock_device):
        """Test single model verification when model is not found."""
        # Mock capabilities response without the requested model
        mock_capabilities = {
            "supported_models": [
                {
                    "name": "openconfig-system",
                    "version": "0.17.1",
                    "organization": "OpenConfig working group",
                }
            ]
        }

        with patch(
            "src.services.capability_verification.get_device_capabilities"
        ) as mock_get_caps:
            mock_get_caps.return_value = SuccessResponse(
                data=[mock_capabilities], timestamp="2023-05-15T12:00:00Z"
            )

            result = verify_single_model(
                mock_device, OpenConfigModel.INTERFACES
            )

            assert result.status == VerificationStatus.NOT_FOUND
            assert result.model == OpenConfigModel.INTERFACES
            assert result.found_version is None

    def test_verify_models_multiple_success(self, mock_device):
        """Test verification of multiple models."""
        # Mock capabilities response with multiple models
        mock_capabilities = {
            "supported_models": [
                {
                    "name": "openconfig-interfaces",
                    "version": "4.0.0",
                    "organization": "OpenConfig working group",
                },
                {
                    "name": "openconfig-system",
                    "version": "0.17.1",
                    "organization": "OpenConfig working group",
                },
            ]
        }

        models = {OpenConfigModel.INTERFACES, OpenConfigModel.SYSTEM}

        with patch(
            "src.services.capability_verification.get_device_capabilities"
        ) as mock_get_caps:
            mock_get_caps.return_value = SuccessResponse(
                data=[mock_capabilities], timestamp="2023-05-15T12:00:00Z"
            )

            result = verify_models(mock_device, models)

            assert isinstance(result, MultiModelVerificationResult)
            assert result.overall_status == VerificationStatus.SUPPORTED
            assert len(result.model_results) == 2
            assert OpenConfigModel.INTERFACES in result.model_results
            assert OpenConfigModel.SYSTEM in result.model_results

    def test_verify_models_mixed_results(self, mock_device):
        """Test verification of multiple models with mixed results."""
        # Mock capabilities response with only one model
        mock_capabilities = {
            "supported_models": [
                {
                    "name": "openconfig-interfaces",
                    "version": "4.0.0",
                    "organization": "OpenConfig working group",
                }
            ]
        }

        models = {OpenConfigModel.INTERFACES, OpenConfigModel.SYSTEM}

        with patch(
            "src.services.capability_verification.get_device_capabilities"
        ) as mock_get_caps:
            mock_get_caps.return_value = SuccessResponse(
                data=[mock_capabilities], timestamp="2023-05-15T12:00:00Z"
            )

            result = verify_models(mock_device, models)

            assert isinstance(result, MultiModelVerificationResult)
            assert result.overall_status == VerificationStatus.ERROR
            assert len(result.model_results) == 2

            # Check individual results
            interfaces_result = result.model_results[
                OpenConfigModel.INTERFACES
            ]
            system_result = result.model_results[OpenConfigModel.SYSTEM]

            assert interfaces_result.status == VerificationStatus.SUPPORTED
            assert system_result.status == VerificationStatus.NOT_FOUND

    def test_get_verification_summary(self, mock_device):
        """Test verification summary generation."""
        # Test with a successful verification result
        mock_result = {
            "is_supported": True,
            "model_capability": {
                "model_name": "openconfig-network-instance",
                "found_version": "1.3.0",
                "status": "supported",
            },
            "warning_message": None,
            "error_message": None,
        }

        summary = get_verification_summary(mock_result)

        assert "✓" in summary
        assert "openconfig-network-instance" in summary

        # Test with an error result
        mock_error_result = {
            "is_supported": False,
            "model_capability": {
                "model_name": "openconfig-network-instance",
                "found_version": None,
                "status": "not_found",
            },
            "warning_message": None,
            "error_message": "Model not found",
        }

        error_summary = get_verification_summary(mock_error_result)

        assert "✗" in error_summary
        assert "openconfig-network-instance" in error_summary

        error_summary = get_verification_summary(mock_error_result)

        assert "✗" in error_summary
        assert "openconfig-network-instance" in error_summary


if __name__ == "__main__":
    pytest.main([__file__])
