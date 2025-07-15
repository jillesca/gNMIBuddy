#!/usr/bin/env python3
"""
Tests for capability_verification service.

Tests OpenConfig model capability verification functionality.
"""

import pytest
from unittest.mock import patch
from src.services.capability_verification import (
    verify_openconfig_network_instance,
    VerificationResult,
    get_verification_summary,
    _parse_device_capabilities,
)
from src.schemas.models import Device
from src.schemas.capabilities import (
    ModelCapability,
    CapabilityVerificationStatus,
)
from src.schemas.responses import SuccessResponse, ErrorResponse


class TestVerificationResult:
    """Test VerificationResult dataclass."""

    def test_verification_result_creation(self):
        """Test creating VerificationResult objects."""
        model_capability = ModelCapability(
            model_name="openconfig-network-instance",
            required_version="1.3.0",
            found_version="1.3.1",
            status=CapabilityVerificationStatus.SUPPORTED,
        )

        result = VerificationResult(
            is_supported=True,
            model_capability=model_capability,
            warning_message="Test warning",
            error_message="Test error",
        )

        assert result.is_supported is True
        assert (
            result.model_capability.model_name == "openconfig-network-instance"
        )
        assert result.warning_message == "Test warning"
        assert result.error_message == "Test error"
        assert isinstance(result.metadata, dict)

    def test_verification_result_to_dict(self):
        """Test converting VerificationResult to dictionary."""
        model_capability = ModelCapability(
            model_name="openconfig-network-instance",
            required_version="1.3.0",
            found_version="1.3.1",
            status=CapabilityVerificationStatus.SUPPORTED,
        )

        result = VerificationResult(
            is_supported=True,
            model_capability=model_capability,
            metadata={"test": "value"},
        )

        result_dict = result.to_dict()

        assert result_dict["is_supported"] is True
        assert (
            result_dict["model_capability"]["model_name"]
            == "openconfig-network-instance"
        )
        assert result_dict["model_capability"]["required_version"] == "1.3.0"
        assert result_dict["model_capability"]["found_version"] == "1.3.1"
        assert result_dict["model_capability"]["status"] == "supported"
        assert result_dict["metadata"]["test"] == "value"


class TestParseDeviceCapabilities:
    """Test parsing device capabilities from raw data."""

    def test_parse_device_capabilities_basic(self):
        """Test parsing basic device capabilities."""
        capabilities_data = {
            "gNMI_version": "0.7.0",
            "supported_encodings": ["JSON", "PROTO"],
            "supported_models": [
                {
                    "name": "openconfig-network-instance",
                    "version": "1.3.0",
                    "organization": "openconfig",
                    "module": "openconfig-network-instance",
                }
            ],
        }

        device_capabilities = _parse_device_capabilities(
            capabilities_data, "test-device"
        )

        assert device_capabilities.device_name == "test-device"
        assert device_capabilities.gnmi_version == "0.7.0"
        assert device_capabilities.supported_encodings == ["JSON", "PROTO"]
        assert len(device_capabilities.supported_models) == 1

        model = device_capabilities.supported_models[0]
        assert model.name == "openconfig-network-instance"
        assert model.version == "1.3.0"
        assert model.organization == "openconfig"

    def test_parse_device_capabilities_empty(self):
        """Test parsing empty device capabilities."""
        capabilities_data = {}

        device_capabilities = _parse_device_capabilities(
            capabilities_data, "test-device"
        )

        assert device_capabilities.device_name == "test-device"
        assert device_capabilities.gnmi_version == "unknown"
        assert device_capabilities.supported_encodings == []
        assert len(device_capabilities.supported_models) == 0

    def test_parse_device_capabilities_malformed_models(self):
        """Test parsing capabilities with malformed model data."""
        capabilities_data = {
            "supported_models": [
                "invalid_model_entry",
                {
                    "name": "openconfig-network-instance",
                    "version": "1.3.0",
                    "organization": "openconfig",
                },
            ]
        }

        device_capabilities = _parse_device_capabilities(
            capabilities_data, "test-device"
        )

        # Should only parse the valid model entry
        assert len(device_capabilities.supported_models) == 1
        assert (
            device_capabilities.supported_models[0].name
            == "openconfig-network-instance"
        )


class TestVerifyOpenconfigNetworkInstance:
    """Test the main verification function."""

    def create_test_device(self):
        """Create a test device for verification."""
        return Device(
            name="test-device",
            ip_address="192.168.1.1",
            port=830,
            nos="iosxr",
            username="admin",
            password="admin",
        )

    @patch("src.services.capability_verification.get_device_capabilities")
    def test_verify_model_supported(self, mock_get_capabilities):
        """Test verification when model is supported."""
        device = self.create_test_device()

        # Mock successful capabilities response
        mock_get_capabilities.return_value = SuccessResponse(
            data=[
                {
                    "gNMI_version": "0.7.0",
                    "supported_models": [
                        {
                            "name": "openconfig-network-instance",
                            "version": "1.3.0",
                            "organization": "openconfig",
                        }
                    ],
                }
            ]
        )

        result = verify_openconfig_network_instance(device)

        assert result["is_supported"] is True
        assert result["model_capability"]["status"] == "supported"
        assert result["model_capability"]["found_version"] == "1.3.0"
        assert result["error_message"] is None

    @patch("src.services.capability_verification.get_device_capabilities")
    def test_verify_model_newer_version(self, mock_get_capabilities):
        """Test verification when model has newer version."""
        device = self.create_test_device()

        # Mock successful capabilities response with newer version
        mock_get_capabilities.return_value = SuccessResponse(
            data=[
                {
                    "gNMI_version": "0.7.0",
                    "supported_models": [
                        {
                            "name": "openconfig-network-instance",
                            "version": "1.4.0",
                            "organization": "openconfig",
                        }
                    ],
                }
            ]
        )

        result = verify_openconfig_network_instance(device)

        assert result["is_supported"] is True
        assert result["model_capability"]["status"] == "supported"
        assert result["model_capability"]["found_version"] == "1.4.0"
        assert result["error_message"] is None

    @patch("src.services.capability_verification.get_device_capabilities")
    def test_verify_model_older_version(self, mock_get_capabilities):
        """Test verification when model has older version."""
        device = self.create_test_device()

        # Mock successful capabilities response with older version
        mock_get_capabilities.return_value = SuccessResponse(
            data=[
                {
                    "gNMI_version": "0.7.0",
                    "supported_models": [
                        {
                            "name": "openconfig-network-instance",
                            "version": "1.2.0",
                            "organization": "openconfig",
                        }
                    ],
                }
            ]
        )

        result = verify_openconfig_network_instance(device)

        assert (
            result["is_supported"] is True
        )  # Still supported but with warning
        assert result["model_capability"]["status"] == "version_warning"
        assert result["model_capability"]["found_version"] == "1.2.0"
        assert result["warning_message"] is not None
        assert "older than tested version" in result["warning_message"]

    @patch("src.services.capability_verification.get_device_capabilities")
    def test_verify_model_not_found(self, mock_get_capabilities):
        """Test verification when model is not found."""
        device = self.create_test_device()

        # Mock successful capabilities response without the model
        mock_get_capabilities.return_value = SuccessResponse(
            data=[
                {
                    "gNMI_version": "0.7.0",
                    "supported_models": [
                        {
                            "name": "openconfig-interfaces",
                            "version": "1.0.0",
                            "organization": "openconfig",
                        }
                    ],
                }
            ]
        )

        result = verify_openconfig_network_instance(device)

        assert result["is_supported"] is False
        assert result["model_capability"]["status"] == "not_found"
        assert result["error_message"] is not None
        assert "not found" in result["error_message"]

    @patch("src.services.capability_verification.get_device_capabilities")
    def test_verify_model_missing_version(self, mock_get_capabilities):
        """Test verification when model exists but version is missing."""
        device = self.create_test_device()

        # Mock successful capabilities response without version
        mock_get_capabilities.return_value = SuccessResponse(
            data=[
                {
                    "gNMI_version": "0.7.0",
                    "supported_models": [
                        {
                            "name": "openconfig-network-instance",
                            "version": "",
                            "organization": "openconfig",
                        }
                    ],
                }
            ]
        )

        result = verify_openconfig_network_instance(device)

        assert result["is_supported"] is True  # Allow usage but with warning
        assert result["model_capability"]["status"] == "version_warning"
        assert result["warning_message"] is not None
        assert "version information is missing" in result["warning_message"]

    @patch("src.services.capability_verification.get_device_capabilities")
    def test_verify_capabilities_request_failed(self, mock_get_capabilities):
        """Test verification when capabilities request fails."""
        device = self.create_test_device()

        # Mock failed capabilities response
        mock_get_capabilities.return_value = ErrorResponse(
            type="connection_error", message="Failed to connect to device"
        )

        result = verify_openconfig_network_instance(device)

        assert result["is_supported"] is False
        assert result["model_capability"]["status"] == "not_found"
        assert result["error_message"] is not None
        assert "Failed to retrieve capabilities" in result["error_message"]

    @patch("src.services.capability_verification.get_device_capabilities")
    def test_verify_empty_capabilities_data(self, mock_get_capabilities):
        """Test verification when capabilities data is empty."""
        device = self.create_test_device()

        # Mock empty capabilities response
        mock_get_capabilities.return_value = SuccessResponse(data=[])

        result = verify_openconfig_network_instance(device)

        assert result["is_supported"] is False
        assert result["model_capability"]["status"] == "not_found"
        assert result["error_message"] is not None
        assert "No capability data received" in result["error_message"]

    @patch("src.services.capability_verification.get_device_capabilities")
    def test_verify_malformed_version(self, mock_get_capabilities):
        """Test verification when version format is malformed."""
        device = self.create_test_device()

        # Mock successful capabilities response with malformed version
        mock_get_capabilities.return_value = SuccessResponse(
            data=[
                {
                    "gNMI_version": "0.7.0",
                    "supported_models": [
                        {
                            "name": "openconfig-network-instance",
                            "version": "invalid-version",
                            "organization": "openconfig",
                        }
                    ],
                }
            ]
        )

        result = verify_openconfig_network_instance(device)

        assert result["is_supported"] is True  # Allow usage but with warning
        assert result["model_capability"]["status"] == "version_warning"
        assert result["warning_message"] is not None
        assert "Unable to compare version" in result["warning_message"]


class TestGetVerificationSummary:
    """Test verification summary formatting."""

    def test_get_verification_summary_supported(self):
        """Test summary for supported model."""
        verification_result = {
            "is_supported": True,
            "model_capability": {
                "model_name": "openconfig-network-instance",
                "required_version": "1.3.0",
                "found_version": "1.3.1",
                "status": "supported",
            },
        }

        summary = get_verification_summary(verification_result)

        assert "✓" in summary
        assert "openconfig-network-instance" in summary
        assert "1.3.1" in summary
        assert "supported" in summary

    def test_get_verification_summary_warning(self):
        """Test summary for model with version warning."""
        verification_result = {
            "is_supported": True,
            "model_capability": {
                "model_name": "openconfig-network-instance",
                "required_version": "1.3.0",
                "found_version": "1.2.0",
                "status": "version_warning",
            },
        }

        summary = get_verification_summary(verification_result)

        assert "⚠" in summary
        assert "openconfig-network-instance" in summary
        assert "1.2.0" in summary
        assert "limited functionality" in summary

    def test_get_verification_summary_not_supported(self):
        """Test summary for unsupported model."""
        verification_result = {
            "is_supported": False,
            "model_capability": {
                "model_name": "openconfig-network-instance",
                "required_version": "1.3.0",
                "found_version": "not found",
                "status": "not_found",
            },
        }

        summary = get_verification_summary(verification_result)

        assert "✗" in summary
        assert "openconfig-network-instance" in summary
        assert "not supported" in summary
