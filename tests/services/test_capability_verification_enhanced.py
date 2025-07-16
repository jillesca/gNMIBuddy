#!/usr/bin/env python3
"""
Tests for enhanced capability verification service.
"""

from unittest.mock import patch
from src.services.capability_verification import (
    verify_single_model,
    verify_models,
    verify_openconfig_network_instance,
)
from src.schemas.models import Device
from src.schemas.openconfig_models import OpenConfigModel
from src.schemas.verification_results import (
    VerificationStatus,
    ModelVerificationResult,
    MultiModelVerificationResult,
)
from src.schemas.responses import SuccessResponse, ErrorResponse
from src.schemas.capabilities import CapabilityInfo, DeviceCapabilities


class TestVerifySingleModel:
    """Test cases for verify_single_model function."""

    def test_verify_single_model_success(self):
        """Test successful single model verification."""
        device = Device(name="test-device", ip_address="192.168.1.1")

        # Mock the capability info
        capability_info = CapabilityInfo(
            name="openconfig-network-instance",
            version="1.4.0",
            organization="openconfig",
        )

        device_capabilities = DeviceCapabilities(
            device_name="test-device",
            gnmi_version="0.8.0",
            supported_models=[capability_info],
        )

        success_response = SuccessResponse(
            data=[
                {
                    "device_name": "test-device",
                    "gnmi_version": "0.8.0",
                    "supported_models": [capability_info],
                }
            ]
        )

        with (
            patch(
                "src.services.capability_verification.get_device_capabilities"
            ) as mock_get_caps,
            patch(
                "src.services.capability_verification.extract_capabilities_from_response"
            ) as mock_extract,
        ):

            mock_get_caps.return_value = success_response
            mock_extract.return_value = device_capabilities

            result = verify_single_model(
                device, OpenConfigModel.NETWORK_INSTANCE
            )

            assert isinstance(result, ModelVerificationResult)
            assert result.model == OpenConfigModel.NETWORK_INSTANCE
            assert result.status == VerificationStatus.SUPPORTED
            assert result.found_version == "1.4.0"
            assert result.required_version == "1.3.0"
            assert result.warning_message is None
            assert result.error_message is None

    def test_verify_single_model_version_warning(self):
        """Test single model verification with version warning."""
        device = Device(name="test-device", ip_address="192.168.1.1")

        # Mock the capability info with older version
        capability_info = CapabilityInfo(
            name="openconfig-network-instance",
            version="1.2.0",
            organization="openconfig",
        )

        device_capabilities = DeviceCapabilities(
            device_name="test-device",
            gnmi_version="0.8.0",
            supported_models=[capability_info],
        )

        success_response = SuccessResponse(
            data=[
                {
                    "device_name": "test-device",
                    "gnmi_version": "0.8.0",
                    "supported_models": [capability_info],
                }
            ]
        )

        with (
            patch(
                "src.services.capability_verification.get_device_capabilities"
            ) as mock_get_caps,
            patch(
                "src.services.capability_verification.extract_capabilities_from_response"
            ) as mock_extract,
        ):

            mock_get_caps.return_value = success_response
            mock_extract.return_value = device_capabilities

            result = verify_single_model(
                device, OpenConfigModel.NETWORK_INSTANCE
            )

            assert isinstance(result, ModelVerificationResult)
            assert result.model == OpenConfigModel.NETWORK_INSTANCE
            assert result.status == VerificationStatus.VERSION_WARNING
            assert result.found_version == "1.2.0"
            assert result.required_version == "1.3.0"
            assert result.warning_message is not None
            assert (
                "Some features may not work correctly"
                in result.warning_message
            )

    def test_verify_single_model_not_found(self):
        """Test single model verification when model not found."""
        device = Device(name="test-device", ip_address="192.168.1.1")

        # Mock device capabilities without the required model
        device_capabilities = DeviceCapabilities(
            device_name="test-device",
            gnmi_version="0.8.0",
            supported_models=[],
        )

        success_response = SuccessResponse(
            data=[
                {
                    "device_name": "test-device",
                    "gnmi_version": "0.8.0",
                    "supported_models": [],
                }
            ]
        )

        with (
            patch(
                "src.services.capability_verification.get_device_capabilities"
            ) as mock_get_caps,
            patch(
                "src.services.capability_verification.extract_capabilities_from_response"
            ) as mock_extract,
        ):

            mock_get_caps.return_value = success_response
            mock_extract.return_value = device_capabilities

            result = verify_single_model(
                device, OpenConfigModel.NETWORK_INSTANCE
            )

            assert isinstance(result, ModelVerificationResult)
            assert result.model == OpenConfigModel.NETWORK_INSTANCE
            assert result.status == VerificationStatus.NOT_FOUND
            assert result.found_version is None
            assert result.required_version == "1.3.0"
            assert result.error_message is not None
            assert "not found" in result.error_message

    def test_verify_single_model_connection_error(self):
        """Test single model verification with connection error."""
        device = Device(name="test-device", ip_address="192.168.1.1")

        error_response = ErrorResponse(
            type="connection_error",
            message="Failed to connect to device",
        )

        with patch(
            "src.services.capability_verification.get_device_capabilities"
        ) as mock_get_caps:
            mock_get_caps.return_value = error_response

            result = verify_single_model(
                device, OpenConfigModel.NETWORK_INSTANCE
            )

            assert isinstance(result, ModelVerificationResult)
            assert result.model == OpenConfigModel.NETWORK_INSTANCE
            assert result.status == VerificationStatus.ERROR
            assert result.error_message is not None
            assert "Failed to retrieve capabilities" in result.error_message

    def test_verify_single_model_no_data(self):
        """Test single model verification with no data."""
        device = Device(name="test-device", ip_address="192.168.1.1")

        success_response = SuccessResponse(data=[])

        with patch(
            "src.services.capability_verification.get_device_capabilities"
        ) as mock_get_caps:
            mock_get_caps.return_value = success_response

            result = verify_single_model(
                device, OpenConfigModel.NETWORK_INSTANCE
            )

            assert isinstance(result, ModelVerificationResult)
            assert result.model == OpenConfigModel.NETWORK_INSTANCE
            assert result.status == VerificationStatus.ERROR
            assert result.error_message is not None
            assert "No capability data received" in result.error_message

    def test_verify_single_model_extraction_error(self):
        """Test single model verification with extraction error."""
        device = Device(name="test-device", ip_address="192.168.1.1")

        success_response = SuccessResponse(data=[{"some": "data"}])

        with (
            patch(
                "src.services.capability_verification.get_device_capabilities"
            ) as mock_get_caps,
            patch(
                "src.services.capability_verification.extract_capabilities_from_response"
            ) as mock_extract,
        ):

            mock_get_caps.return_value = success_response
            mock_extract.return_value = None

            result = verify_single_model(
                device, OpenConfigModel.NETWORK_INSTANCE
            )

            assert isinstance(result, ModelVerificationResult)
            assert result.model == OpenConfigModel.NETWORK_INSTANCE
            assert result.status == VerificationStatus.ERROR
            assert result.error_message is not None
            assert "Failed to extract capabilities" in result.error_message


class TestVerifyModels:
    """Test cases for verify_models function."""

    def test_verify_models_all_supported(self):
        """Test verifying multiple models - all supported."""
        device = Device(name="test-device", ip_address="192.168.1.1")
        models = {OpenConfigModel.NETWORK_INSTANCE, OpenConfigModel.INTERFACES}

        # Mock successful verification for both models
        with patch(
            "src.services.capability_verification.verify_single_model"
        ) as mock_verify:
            mock_verify.side_effect = [
                ModelVerificationResult(
                    model=OpenConfigModel.NETWORK_INSTANCE,
                    status=VerificationStatus.SUPPORTED,
                    found_version="1.4.0",
                    required_version="1.3.0",
                ),
                ModelVerificationResult(
                    model=OpenConfigModel.INTERFACES,
                    status=VerificationStatus.SUPPORTED,
                    found_version="3.1.0",
                    required_version="3.0.0",
                ),
            ]

            result = verify_models(device, models)

            assert isinstance(result, MultiModelVerificationResult)
            assert result.overall_status == VerificationStatus.SUPPORTED
            assert len(result.model_results) == 2
            assert result.is_model_supported(OpenConfigModel.NETWORK_INSTANCE)
            assert result.is_model_supported(OpenConfigModel.INTERFACES)
            assert not result.has_warnings()
            assert not result.has_errors()

    def test_verify_models_with_warnings(self):
        """Test verifying multiple models - with warnings."""
        device = Device(name="test-device", ip_address="192.168.1.1")
        models = {OpenConfigModel.NETWORK_INSTANCE, OpenConfigModel.INTERFACES}

        # Mock verification with one warning
        with patch(
            "src.services.capability_verification.verify_single_model"
        ) as mock_verify:
            mock_verify.side_effect = [
                ModelVerificationResult(
                    model=OpenConfigModel.NETWORK_INSTANCE,
                    status=VerificationStatus.SUPPORTED,
                    found_version="1.4.0",
                    required_version="1.3.0",
                ),
                ModelVerificationResult(
                    model=OpenConfigModel.INTERFACES,
                    status=VerificationStatus.VERSION_WARNING,
                    found_version="2.9.0",
                    required_version="3.0.0",
                    warning_message="Version is older than required",
                ),
            ]

            result = verify_models(device, models)

            assert isinstance(result, MultiModelVerificationResult)
            assert result.overall_status == VerificationStatus.VERSION_WARNING
            assert len(result.model_results) == 2
            assert result.is_model_supported(OpenConfigModel.NETWORK_INSTANCE)
            assert result.is_model_supported(OpenConfigModel.INTERFACES)
            assert result.has_warnings()
            assert not result.has_errors()

    def test_verify_models_with_errors(self):
        """Test verifying multiple models - with errors."""
        device = Device(name="test-device", ip_address="192.168.1.1")
        models = {OpenConfigModel.NETWORK_INSTANCE, OpenConfigModel.SYSTEM}

        # Mock verification with one error - use side_effect function to return correct model
        def mock_verify_single_model(_device, model):
            if model == OpenConfigModel.NETWORK_INSTANCE:
                return ModelVerificationResult(
                    model=OpenConfigModel.NETWORK_INSTANCE,
                    status=VerificationStatus.SUPPORTED,
                    found_version="1.4.0",
                    required_version="1.3.0",
                )
            elif model == OpenConfigModel.SYSTEM:
                return ModelVerificationResult(
                    model=OpenConfigModel.SYSTEM,
                    status=VerificationStatus.NOT_FOUND,
                    required_version="0.17.1",
                    error_message="Model not found",
                )
            return None

        with patch(
            "src.services.capability_verification.verify_single_model",
            side_effect=mock_verify_single_model,
        ):
            result = verify_models(device, models)

            assert isinstance(result, MultiModelVerificationResult)
            assert result.overall_status == VerificationStatus.ERROR
            assert len(result.model_results) == 2
            assert result.is_model_supported(OpenConfigModel.NETWORK_INSTANCE)
            assert not result.is_model_supported(OpenConfigModel.SYSTEM)
            assert not result.has_warnings()
            assert result.has_errors()

    def test_verify_models_empty_set(self):
        """Test verifying empty set of models."""
        device = Device(name="test-device", ip_address="192.168.1.1")
        models = set()

        result = verify_models(device, models)

        assert isinstance(result, MultiModelVerificationResult)
        assert result.overall_status == VerificationStatus.SUPPORTED
        assert len(result.model_results) == 0
        assert not result.has_warnings()
        assert not result.has_errors()

    def test_verify_models_mixed_results(self):
        """Test verifying models with mixed results."""
        device = Device(name="test-device", ip_address="192.168.1.1")
        models = {
            OpenConfigModel.NETWORK_INSTANCE,
            OpenConfigModel.INTERFACES,
            OpenConfigModel.SYSTEM,
        }

        # Mock verification with mixed results
        def mock_verify_single_model(_device, model):
            if model == OpenConfigModel.NETWORK_INSTANCE:
                return ModelVerificationResult(
                    model=OpenConfigModel.NETWORK_INSTANCE,
                    status=VerificationStatus.SUPPORTED,
                    found_version="1.4.0",
                    required_version="1.3.0",
                )
            elif model == OpenConfigModel.INTERFACES:
                return ModelVerificationResult(
                    model=OpenConfigModel.INTERFACES,
                    status=VerificationStatus.VERSION_WARNING,
                    found_version="2.9.0",
                    required_version="3.0.0",
                    warning_message="Version is older than required",
                )
            elif model == OpenConfigModel.SYSTEM:
                return ModelVerificationResult(
                    model=OpenConfigModel.SYSTEM,
                    status=VerificationStatus.NOT_FOUND,
                    required_version="0.17.1",
                    error_message="Model not found",
                )
            return None

        with patch(
            "src.services.capability_verification.verify_single_model",
            side_effect=mock_verify_single_model,
        ):
            result = verify_models(device, models)

            assert isinstance(result, MultiModelVerificationResult)
            assert (
                result.overall_status == VerificationStatus.ERROR
            )  # Errors take precedence
            assert len(result.model_results) == 3
            assert result.is_model_supported(OpenConfigModel.NETWORK_INSTANCE)
            assert result.is_model_supported(
                OpenConfigModel.INTERFACES
            )  # Warning still counts as supported
            assert not result.is_model_supported(OpenConfigModel.SYSTEM)
            assert result.has_warnings()
            assert result.has_errors()

            # Test the helper methods
            supported_models = result.get_supported_models()
            assert len(supported_models) == 2
            assert OpenConfigModel.NETWORK_INSTANCE in supported_models
            assert OpenConfigModel.INTERFACES in supported_models

            unsupported_models = result.get_unsupported_models()
            assert len(unsupported_models) == 1
            assert OpenConfigModel.SYSTEM in unsupported_models


class TestBackwardCompatibility:
    """Test cases for backward compatibility with existing verify_openconfig_network_instance."""

    def test_verify_openconfig_network_instance_still_works(self):
        """Test that the original function still works."""
        device = Device(name="test-device", ip_address="192.168.1.1")

        # Mock successful verification
        capability_info = CapabilityInfo(
            name="openconfig-network-instance",
            version="1.4.0",
            organization="openconfig",
        )

        device_capabilities = DeviceCapabilities(
            device_name="test-device",
            gnmi_version="0.8.0",
            supported_models=[capability_info],
        )

        success_response = SuccessResponse(
            data=[
                {
                    "device_name": "test-device",
                    "gnmi_version": "0.8.0",
                    "supported_models": [capability_info],
                }
            ]
        )

        with (
            patch(
                "src.services.capability_verification.get_device_capabilities"
            ) as mock_get_caps,
            patch(
                "src.services.capability_verification.extract_capabilities_from_response"
            ) as mock_extract,
        ):

            mock_get_caps.return_value = success_response
            mock_extract.return_value = device_capabilities

            result = verify_openconfig_network_instance(device)

            # Should return the old dictionary format
            assert isinstance(result, dict)
            assert "is_supported" in result
            assert "model_capability" in result
            assert result["is_supported"] is True
            assert (
                result["model_capability"]["model_name"]
                == "openconfig-network-instance"
            )
            assert result["model_capability"]["found_version"] == "1.4.0"
            assert result["model_capability"]["required_version"] == "1.3.0"
