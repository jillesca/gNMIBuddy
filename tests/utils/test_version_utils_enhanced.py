#!/usr/bin/env python3
"""
Tests for enhanced version validation functionality.
"""

from src.utils.version_utils import (
    validate_model_version,
    get_model_specific_version_message,
    VersionValidationResult,
)
from src.schemas.openconfig_models import OpenConfigModel
from src.schemas.verification_results import VerificationStatus


class TestVersionValidationResult:
    """Test cases for VersionValidationResult."""

    def test_version_validation_result_creation(self):
        """Test creating a VersionValidationResult."""
        result = VersionValidationResult(
            model=OpenConfigModel.NETWORK_INSTANCE,
            status=VerificationStatus.SUPPORTED,
            found_version="1.4.0",
            required_version="1.3.0",
            message="Version is supported",
        )

        assert result.model == OpenConfigModel.NETWORK_INSTANCE
        assert result.status == VerificationStatus.SUPPORTED
        assert result.found_version == "1.4.0"
        assert result.required_version == "1.3.0"
        assert result.message == "Version is supported"
        assert result.warning_message is None
        assert result.error_message is None


class TestValidateModelVersion:
    """Test cases for validate_model_version function."""

    def test_validate_model_version_supported(self):
        """Test validation with supported version."""
        result = validate_model_version(
            OpenConfigModel.NETWORK_INSTANCE, "1.4.0"
        )

        assert result.model == OpenConfigModel.NETWORK_INSTANCE
        assert result.status == VerificationStatus.SUPPORTED
        assert result.found_version == "1.4.0"
        assert result.required_version == "1.3.0"
        assert "meets minimum requirement" in result.message
        assert result.warning_message is None
        assert result.error_message is None

    def test_validate_model_version_exact_match(self):
        """Test validation with exact required version."""
        result = validate_model_version(
            OpenConfigModel.NETWORK_INSTANCE, "1.3.0"
        )

        assert result.model == OpenConfigModel.NETWORK_INSTANCE
        assert result.status == VerificationStatus.SUPPORTED
        assert result.found_version == "1.3.0"
        assert result.required_version == "1.3.0"
        assert result.warning_message is None
        assert result.error_message is None

    def test_validate_model_version_warning(self):
        """Test validation with older version (warning)."""
        result = validate_model_version(
            OpenConfigModel.NETWORK_INSTANCE, "1.2.0"
        )

        assert result.model == OpenConfigModel.NETWORK_INSTANCE
        assert result.status == VerificationStatus.VERSION_WARNING
        assert result.found_version == "1.2.0"
        assert result.required_version == "1.3.0"
        assert "is older than minimum requirement" in result.message
        assert result.warning_message is not None
        assert "Some features may not work correctly" in result.warning_message
        assert result.error_message is None

    def test_validate_model_version_invalid_found_version(self):
        """Test validation with invalid found version."""
        result = validate_model_version(
            OpenConfigModel.NETWORK_INSTANCE, "invalid.version"
        )

        assert result.model == OpenConfigModel.NETWORK_INSTANCE
        assert result.status == VerificationStatus.ERROR
        assert result.found_version == "invalid.version"
        assert result.required_version == "1.3.0"
        assert result.error_message is not None
        assert "Failed to validate" in result.error_message

    def test_validate_model_version_interfaces(self):
        """Test validation for interfaces model."""
        result = validate_model_version(OpenConfigModel.INTERFACES, "3.1.0")

        assert result.model == OpenConfigModel.INTERFACES
        assert result.status == VerificationStatus.SUPPORTED
        assert result.found_version == "3.1.0"
        assert result.required_version == "3.0.0"
        assert result.warning_message is None
        assert result.error_message is None

    def test_validate_model_version_system(self):
        """Test validation for system model."""
        result = validate_model_version(OpenConfigModel.SYSTEM, "0.17.1")

        assert result.model == OpenConfigModel.SYSTEM
        assert result.status == VerificationStatus.SUPPORTED
        assert result.found_version == "0.17.1"
        assert result.required_version == "0.17.1"
        assert result.warning_message is None
        assert result.error_message is None

    def test_validate_model_version_system_warning(self):
        """Test validation for system model with warning."""
        result = validate_model_version(OpenConfigModel.SYSTEM, "0.16.0")

        assert result.model == OpenConfigModel.SYSTEM
        assert result.status == VerificationStatus.VERSION_WARNING
        assert result.found_version == "0.16.0"
        assert result.required_version == "0.17.1"
        assert result.warning_message is not None


class TestGetModelSpecificVersionMessage:
    """Test cases for get_model_specific_version_message function."""

    def test_get_model_specific_version_message_supported(self):
        """Test getting message for supported version."""
        message = get_model_specific_version_message(
            OpenConfigModel.NETWORK_INSTANCE, "1.4.0", "1.3.0"
        )

        assert "openconfig-network-instance" in message
        assert "v1.4.0 is supported" in message
        assert "minimum required: v1.3.0" in message
        assert "Network instance configuration and state data" in message

    def test_get_model_specific_version_message_warning(self):
        """Test getting message for version warning."""
        message = get_model_specific_version_message(
            OpenConfigModel.INTERFACES, "2.9.0", "3.0.0"
        )

        assert "openconfig-interfaces" in message
        assert "v2.9.0 is older than required v3.0.0" in message
        assert "may cause issues with" in message
        assert "Network interface configuration and state data" in message

    def test_get_model_specific_version_message_system(self):
        """Test getting message for system model."""
        message = get_model_specific_version_message(
            OpenConfigModel.SYSTEM, "0.17.1", "0.17.1"
        )

        assert "openconfig-system" in message
        assert "v0.17.1 is supported" in message
        assert "System-level configuration and state data" in message

    def test_get_model_specific_version_message_invalid_version(self):
        """Test getting message for invalid version."""
        message = get_model_specific_version_message(
            OpenConfigModel.NETWORK_INSTANCE, "invalid.version", "1.3.0"
        )

        assert "Unable to validate" in message
        assert "openconfig-network-instance" in message
        assert "invalid.version" in message
