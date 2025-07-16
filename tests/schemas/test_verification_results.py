#!/usr/bin/env python3
"""
Tests for verification results schemas.
"""

import pytest
from src.schemas.verification_results import (
    VerificationStatus,
    ModelVerificationResult,
    MultiModelVerificationResult,
)
from src.schemas.openconfig_models import OpenConfigModel


class TestVerificationStatus:
    """Test cases for VerificationStatus enum."""

    def test_verification_status_values(self):
        """Test that VerificationStatus has the expected values."""
        assert VerificationStatus.SUPPORTED.value == "supported"
        assert VerificationStatus.VERSION_WARNING.value == "version_warning"
        assert VerificationStatus.NOT_FOUND.value == "not_found"
        assert VerificationStatus.ERROR.value == "error"


class TestModelVerificationResult:
    """Test cases for ModelVerificationResult."""

    def test_model_verification_result_creation(self):
        """Test creating a ModelVerificationResult."""
        result = ModelVerificationResult(
            model=OpenConfigModel.NETWORK_INSTANCE,
            status=VerificationStatus.SUPPORTED,
            found_version="1.4.0",
            required_version="1.3.0",
        )

        assert result.model == OpenConfigModel.NETWORK_INSTANCE
        assert result.status == VerificationStatus.SUPPORTED
        assert result.found_version == "1.4.0"
        assert result.required_version == "1.3.0"
        assert result.warning_message is None
        assert result.error_message is None

    def test_model_verification_result_with_warning(self):
        """Test creating a ModelVerificationResult with warning."""
        result = ModelVerificationResult(
            model=OpenConfigModel.INTERFACES,
            status=VerificationStatus.VERSION_WARNING,
            found_version="2.9.0",
            required_version="3.0.0",
            warning_message="Version is older than required",
        )

        assert result.model == OpenConfigModel.INTERFACES
        assert result.status == VerificationStatus.VERSION_WARNING
        assert result.warning_message == "Version is older than required"

    def test_model_verification_result_with_error(self):
        """Test creating a ModelVerificationResult with error."""
        result = ModelVerificationResult(
            model=OpenConfigModel.SYSTEM,
            status=VerificationStatus.ERROR,
            required_version="0.17.1",
            error_message="Failed to connect to device",
        )

        assert result.model == OpenConfigModel.SYSTEM
        assert result.status == VerificationStatus.ERROR
        assert result.error_message == "Failed to connect to device"
        assert result.found_version is None

    def test_model_verification_result_to_dict(self):
        """Test converting ModelVerificationResult to dictionary."""
        result = ModelVerificationResult(
            model=OpenConfigModel.NETWORK_INSTANCE,
            status=VerificationStatus.SUPPORTED,
            found_version="1.4.0",
            required_version="1.3.0",
        )

        result_dict = result.to_dict()

        assert result_dict["model"] == "openconfig-network-instance"
        assert result_dict["status"] == "supported"
        assert result_dict["found_version"] == "1.4.0"
        assert result_dict["required_version"] == "1.3.0"
        assert result_dict["warning_message"] is None
        assert result_dict["error_message"] is None

    def test_model_verification_result_from_dict(self):
        """Test creating ModelVerificationResult from dictionary."""
        data = {
            "model": "openconfig-interfaces",
            "status": "version_warning",
            "found_version": "2.9.0",
            "required_version": "3.0.0",
            "warning_message": "Version is older than required",
            "error_message": None,
        }

        result = ModelVerificationResult.from_dict(data)

        assert result.model == OpenConfigModel.INTERFACES
        assert result.status == VerificationStatus.VERSION_WARNING
        assert result.found_version == "2.9.0"
        assert result.required_version == "3.0.0"
        assert result.warning_message == "Version is older than required"
        assert result.error_message is None

    def test_model_verification_result_from_dict_invalid(self):
        """Test creating ModelVerificationResult from invalid dictionary."""
        data = {
            "model": "invalid-model",
            "status": "supported",
        }

        with pytest.raises(
            ValueError, match="Invalid ModelVerificationResult data"
        ):
            ModelVerificationResult.from_dict(data)


class TestMultiModelVerificationResult:
    """Test cases for MultiModelVerificationResult."""

    def test_multi_model_verification_result_creation(self):
        """Test creating a MultiModelVerificationResult."""
        result = MultiModelVerificationResult(
            overall_status=VerificationStatus.SUPPORTED,
            model_results={},
        )

        assert result.overall_status == VerificationStatus.SUPPORTED
        assert len(result.model_results) == 0

    def test_multi_model_verification_result_with_models(self):
        """Test creating a MultiModelVerificationResult with model results."""
        model_result_1 = ModelVerificationResult(
            model=OpenConfigModel.NETWORK_INSTANCE,
            status=VerificationStatus.SUPPORTED,
            found_version="1.4.0",
            required_version="1.3.0",
        )

        model_result_2 = ModelVerificationResult(
            model=OpenConfigModel.INTERFACES,
            status=VerificationStatus.VERSION_WARNING,
            found_version="2.9.0",
            required_version="3.0.0",
        )

        result = MultiModelVerificationResult(
            overall_status=VerificationStatus.VERSION_WARNING,
            model_results={
                OpenConfigModel.NETWORK_INSTANCE: model_result_1,
                OpenConfigModel.INTERFACES: model_result_2,
            },
        )

        assert result.overall_status == VerificationStatus.VERSION_WARNING
        assert len(result.model_results) == 2
        assert (
            result.model_results[OpenConfigModel.NETWORK_INSTANCE]
            == model_result_1
        )
        assert (
            result.model_results[OpenConfigModel.INTERFACES] == model_result_2
        )

    def test_multi_model_verification_result_to_dict(self):
        """Test converting MultiModelVerificationResult to dictionary."""
        model_result = ModelVerificationResult(
            model=OpenConfigModel.NETWORK_INSTANCE,
            status=VerificationStatus.SUPPORTED,
            found_version="1.4.0",
            required_version="1.3.0",
        )

        result = MultiModelVerificationResult(
            overall_status=VerificationStatus.SUPPORTED,
            model_results={OpenConfigModel.NETWORK_INSTANCE: model_result},
        )

        result_dict = result.to_dict()

        assert result_dict["overall_status"] == "supported"
        assert "model_results" in result_dict
        assert "openconfig-network-instance" in result_dict["model_results"]
        assert (
            result_dict["model_results"]["openconfig-network-instance"][
                "status"
            ]
            == "supported"
        )

    def test_multi_model_verification_result_from_dict(self):
        """Test creating MultiModelVerificationResult from dictionary."""
        data = {
            "overall_status": "supported",
            "model_results": {
                "openconfig-network-instance": {
                    "model": "openconfig-network-instance",
                    "status": "supported",
                    "found_version": "1.4.0",
                    "required_version": "1.3.0",
                    "warning_message": None,
                    "error_message": None,
                }
            },
        }

        result = MultiModelVerificationResult.from_dict(data)

        assert result.overall_status == VerificationStatus.SUPPORTED
        assert len(result.model_results) == 1
        assert OpenConfigModel.NETWORK_INSTANCE in result.model_results
        assert (
            result.model_results[OpenConfigModel.NETWORK_INSTANCE].status
            == VerificationStatus.SUPPORTED
        )

    def test_get_result_for_model(self):
        """Test getting result for a specific model."""
        model_result = ModelVerificationResult(
            model=OpenConfigModel.NETWORK_INSTANCE,
            status=VerificationStatus.SUPPORTED,
            found_version="1.4.0",
            required_version="1.3.0",
        )

        result = MultiModelVerificationResult(
            overall_status=VerificationStatus.SUPPORTED,
            model_results={OpenConfigModel.NETWORK_INSTANCE: model_result},
        )

        assert (
            result.get_result_for_model(OpenConfigModel.NETWORK_INSTANCE)
            == model_result
        )
        assert result.get_result_for_model(OpenConfigModel.INTERFACES) is None

    def test_is_model_supported(self):
        """Test checking if a model is supported."""
        supported_result = ModelVerificationResult(
            model=OpenConfigModel.NETWORK_INSTANCE,
            status=VerificationStatus.SUPPORTED,
            found_version="1.4.0",
            required_version="1.3.0",
        )

        warning_result = ModelVerificationResult(
            model=OpenConfigModel.INTERFACES,
            status=VerificationStatus.VERSION_WARNING,
            found_version="2.9.0",
            required_version="3.0.0",
        )

        not_found_result = ModelVerificationResult(
            model=OpenConfigModel.SYSTEM,
            status=VerificationStatus.NOT_FOUND,
            required_version="0.17.1",
        )

        result = MultiModelVerificationResult(
            overall_status=VerificationStatus.VERSION_WARNING,
            model_results={
                OpenConfigModel.NETWORK_INSTANCE: supported_result,
                OpenConfigModel.INTERFACES: warning_result,
                OpenConfigModel.SYSTEM: not_found_result,
            },
        )

        assert (
            result.is_model_supported(OpenConfigModel.NETWORK_INSTANCE) is True
        )
        assert result.is_model_supported(OpenConfigModel.INTERFACES) is True
        assert result.is_model_supported(OpenConfigModel.SYSTEM) is False

    def test_has_warnings(self):
        """Test checking if result has warnings."""
        warning_result = ModelVerificationResult(
            model=OpenConfigModel.INTERFACES,
            status=VerificationStatus.VERSION_WARNING,
            found_version="2.9.0",
            required_version="3.0.0",
        )

        result = MultiModelVerificationResult(
            overall_status=VerificationStatus.VERSION_WARNING,
            model_results={OpenConfigModel.INTERFACES: warning_result},
        )

        assert result.has_warnings() is True

        # Test with no warnings
        supported_result = ModelVerificationResult(
            model=OpenConfigModel.NETWORK_INSTANCE,
            status=VerificationStatus.SUPPORTED,
            found_version="1.4.0",
            required_version="1.3.0",
        )

        result_no_warnings = MultiModelVerificationResult(
            overall_status=VerificationStatus.SUPPORTED,
            model_results={OpenConfigModel.NETWORK_INSTANCE: supported_result},
        )

        assert result_no_warnings.has_warnings() is False

    def test_has_errors(self):
        """Test checking if result has errors."""
        error_result = ModelVerificationResult(
            model=OpenConfigModel.SYSTEM,
            status=VerificationStatus.ERROR,
            required_version="0.17.1",
            error_message="Connection failed",
        )

        result = MultiModelVerificationResult(
            overall_status=VerificationStatus.ERROR,
            model_results={OpenConfigModel.SYSTEM: error_result},
        )

        assert result.has_errors() is True

    def test_get_supported_models(self):
        """Test getting supported models."""
        supported_result = ModelVerificationResult(
            model=OpenConfigModel.NETWORK_INSTANCE,
            status=VerificationStatus.SUPPORTED,
            found_version="1.4.0",
            required_version="1.3.0",
        )

        warning_result = ModelVerificationResult(
            model=OpenConfigModel.INTERFACES,
            status=VerificationStatus.VERSION_WARNING,
            found_version="2.9.0",
            required_version="3.0.0",
        )

        error_result = ModelVerificationResult(
            model=OpenConfigModel.SYSTEM,
            status=VerificationStatus.ERROR,
            required_version="0.17.1",
        )

        result = MultiModelVerificationResult(
            overall_status=VerificationStatus.VERSION_WARNING,
            model_results={
                OpenConfigModel.NETWORK_INSTANCE: supported_result,
                OpenConfigModel.INTERFACES: warning_result,
                OpenConfigModel.SYSTEM: error_result,
            },
        )

        supported_models = result.get_supported_models()
        assert len(supported_models) == 2
        assert OpenConfigModel.NETWORK_INSTANCE in supported_models
        assert OpenConfigModel.INTERFACES in supported_models
        assert OpenConfigModel.SYSTEM not in supported_models

    def test_get_unsupported_models(self):
        """Test getting unsupported models."""
        supported_result = ModelVerificationResult(
            model=OpenConfigModel.NETWORK_INSTANCE,
            status=VerificationStatus.SUPPORTED,
            found_version="1.4.0",
            required_version="1.3.0",
        )

        not_found_result = ModelVerificationResult(
            model=OpenConfigModel.INTERFACES,
            status=VerificationStatus.NOT_FOUND,
            required_version="3.0.0",
        )

        error_result = ModelVerificationResult(
            model=OpenConfigModel.SYSTEM,
            status=VerificationStatus.ERROR,
            required_version="0.17.1",
        )

        result = MultiModelVerificationResult(
            overall_status=VerificationStatus.ERROR,
            model_results={
                OpenConfigModel.NETWORK_INSTANCE: supported_result,
                OpenConfigModel.INTERFACES: not_found_result,
                OpenConfigModel.SYSTEM: error_result,
            },
        )

        unsupported_models = result.get_unsupported_models()
        assert len(unsupported_models) == 2
        assert OpenConfigModel.INTERFACES in unsupported_models
        assert OpenConfigModel.SYSTEM in unsupported_models
        assert OpenConfigModel.NETWORK_INSTANCE not in unsupported_models
