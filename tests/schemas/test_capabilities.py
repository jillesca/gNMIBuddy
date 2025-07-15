#!/usr/bin/env python3
"""
Unit tests for capability schemas and models.
"""

import pytest
from src.schemas.capabilities import (
    CapabilityVerificationStatus,
    CapabilityInfo,
    ModelCapability,
    CapabilityError,
    DeviceCapabilities,
)


class TestCapabilityVerificationStatus:
    """Test cases for CapabilityVerificationStatus enum."""

    def test_enum_values(self):
        """Test that all enum values are correct."""
        assert CapabilityVerificationStatus.SUPPORTED.value == "supported"
        assert CapabilityVerificationStatus.UNSUPPORTED.value == "unsupported"
        assert (
            CapabilityVerificationStatus.VERSION_WARNING.value
            == "version_warning"
        )
        assert CapabilityVerificationStatus.NOT_FOUND.value == "not_found"


class TestCapabilityInfo:
    """Test cases for CapabilityInfo dataclass."""

    def test_capability_info_creation(self):
        """Test creating a CapabilityInfo object."""
        info = CapabilityInfo(
            name="openconfig-network-instance",
            version="1.3.0",
            organization="openconfig",
            module="openconfig-network-instance",
            revision="2021-04-01",
            namespace="http://openconfig.net/yang/network-instance",
        )

        assert info.name == "openconfig-network-instance"
        assert info.version == "1.3.0"
        assert info.organization == "openconfig"
        assert info.module == "openconfig-network-instance"
        assert info.revision == "2021-04-01"
        assert info.namespace == "http://openconfig.net/yang/network-instance"

    def test_capability_info_minimal(self):
        """Test creating a minimal CapabilityInfo object."""
        info = CapabilityInfo(
            name="openconfig-interfaces",
            version="2.4.3",
            organization="openconfig",
        )

        assert info.name == "openconfig-interfaces"
        assert info.version == "2.4.3"
        assert info.organization == "openconfig"
        assert info.module is None
        assert info.revision is None
        assert info.namespace is None


class TestModelCapability:
    """Test cases for ModelCapability dataclass."""

    def test_model_capability_creation(self):
        """Test creating a ModelCapability object."""
        capability = ModelCapability(
            model_name="openconfig-network-instance",
            required_version="1.3.0",
            found_version="1.4.0",
            status=CapabilityVerificationStatus.SUPPORTED,
        )

        assert capability.model_name == "openconfig-network-instance"
        assert capability.required_version == "1.3.0"
        assert capability.found_version == "1.4.0"
        assert capability.status == CapabilityVerificationStatus.SUPPORTED
        assert capability.warning_message is None
        assert capability.error_message is None

    def test_model_capability_with_warning(self):
        """Test creating a ModelCapability object with warning."""
        capability = ModelCapability(
            model_name="openconfig-network-instance",
            required_version="1.3.0",
            found_version="1.2.0",
            status=CapabilityVerificationStatus.VERSION_WARNING,
            warning_message="Found version 1.2.0 is older than required 1.3.0",
        )

        assert (
            capability.status == CapabilityVerificationStatus.VERSION_WARNING
        )
        assert (
            capability.warning_message
            == "Found version 1.2.0 is older than required 1.3.0"
        )

    def test_model_capability_with_error(self):
        """Test creating a ModelCapability object with error."""
        capability = ModelCapability(
            model_name="openconfig-network-instance",
            required_version="1.3.0",
            status=CapabilityVerificationStatus.NOT_FOUND,
            error_message="Model not found on device",
        )

        assert capability.status == CapabilityVerificationStatus.NOT_FOUND
        assert capability.found_version is None
        assert capability.error_message == "Model not found on device"

    def test_model_capability_defaults(self):
        """Test ModelCapability with default values."""
        capability = ModelCapability(
            model_name="openconfig-interfaces", required_version="2.4.0"
        )

        assert capability.model_name == "openconfig-interfaces"
        assert capability.required_version == "2.4.0"
        assert capability.found_version is None
        assert capability.status == CapabilityVerificationStatus.NOT_FOUND
        assert capability.warning_message is None
        assert capability.error_message is None


class TestCapabilityError:
    """Test cases for CapabilityError dataclass."""

    def test_capability_error_creation(self):
        """Test creating a CapabilityError object."""
        error = CapabilityError(
            error_type="MODEL_NOT_FOUND",
            message="The required model is not supported by the device",
            model_name="openconfig-network-instance",
            details={"required_version": "1.3.0"},
        )

        assert error.error_type == "MODEL_NOT_FOUND"
        assert (
            error.message
            == "The required model is not supported by the device"
        )
        assert error.model_name == "openconfig-network-instance"
        assert error.details == {"required_version": "1.3.0"}

    def test_capability_error_minimal(self):
        """Test creating a minimal CapabilityError object."""
        error = CapabilityError(
            error_type="GENERIC_ERROR", message="Something went wrong"
        )

        assert error.error_type == "GENERIC_ERROR"
        assert error.message == "Something went wrong"
        assert error.model_name is None
        assert error.details == {}

    def test_capability_error_string_representation(self):
        """Test string representation of CapabilityError."""
        error = CapabilityError(
            error_type="MODEL_NOT_FOUND",
            message="Model not found",
            model_name="openconfig-network-instance",
        )

        str_repr = str(error)
        assert "CapabilityError" in str_repr
        assert "MODEL_NOT_FOUND" in str_repr
        assert "openconfig-network-instance" in str_repr
        assert "Model not found" in str_repr

    def test_capability_error_string_representation_no_model(self):
        """Test string representation of CapabilityError without model name."""
        error = CapabilityError(
            error_type="GENERIC_ERROR", message="Something went wrong"
        )

        str_repr = str(error)
        assert "CapabilityError" in str_repr
        assert "GENERIC_ERROR" in str_repr
        assert "Something went wrong" in str_repr
        assert "for model" not in str_repr


class TestDeviceCapabilities:
    """Test cases for DeviceCapabilities dataclass."""

    def test_device_capabilities_creation(self):
        """Test creating a DeviceCapabilities object."""
        model1 = CapabilityInfo(
            name="openconfig-network-instance",
            version="1.3.0",
            organization="openconfig",
        )
        model2 = CapabilityInfo(
            name="openconfig-interfaces",
            version="2.4.3",
            organization="openconfig",
        )

        capabilities = DeviceCapabilities(
            device_name="test-device",
            gnmi_version="0.7.0",
            supported_models=[model1, model2],
            supported_encodings=["JSON_IETF", "JSON"],
            timestamp="2023-01-01T12:00:00Z",
            raw_response={"test": "data"},
        )

        assert capabilities.device_name == "test-device"
        assert capabilities.gnmi_version == "0.7.0"
        assert len(capabilities.supported_models) == 2
        assert len(capabilities.supported_encodings) == 2
        assert capabilities.timestamp == "2023-01-01T12:00:00Z"
        assert capabilities.raw_response == {"test": "data"}

    def test_device_capabilities_defaults(self):
        """Test DeviceCapabilities with default values."""
        capabilities = DeviceCapabilities(
            device_name="test-device", gnmi_version="0.7.0"
        )

        assert capabilities.device_name == "test-device"
        assert capabilities.gnmi_version == "0.7.0"
        assert capabilities.supported_models == []
        assert capabilities.supported_encodings == []
        assert capabilities.timestamp is None
        assert capabilities.raw_response is None

    def test_find_model_success(self):
        """Test finding a model in supported models."""
        model1 = CapabilityInfo(
            name="openconfig-network-instance",
            version="1.3.0",
            organization="openconfig",
        )
        model2 = CapabilityInfo(
            name="openconfig-interfaces",
            version="2.4.3",
            organization="openconfig",
        )

        capabilities = DeviceCapabilities(
            device_name="test-device",
            gnmi_version="0.7.0",
            supported_models=[model1, model2],
        )

        found_model = capabilities.find_model("openconfig-network-instance")
        assert found_model is not None
        assert found_model.name == "openconfig-network-instance"
        assert found_model.version == "1.3.0"

    def test_find_model_not_found(self):
        """Test finding a model that doesn't exist."""
        model1 = CapabilityInfo(
            name="openconfig-interfaces",
            version="2.4.3",
            organization="openconfig",
        )

        capabilities = DeviceCapabilities(
            device_name="test-device",
            gnmi_version="0.7.0",
            supported_models=[model1],
        )

        found_model = capabilities.find_model("openconfig-network-instance")
        assert found_model is None

    def test_has_model_true(self):
        """Test has_model method when model exists."""
        model1 = CapabilityInfo(
            name="openconfig-network-instance",
            version="1.3.0",
            organization="openconfig",
        )

        capabilities = DeviceCapabilities(
            device_name="test-device",
            gnmi_version="0.7.0",
            supported_models=[model1],
        )

        assert capabilities.has_model("openconfig-network-instance") is True

    def test_has_model_false(self):
        """Test has_model method when model doesn't exist."""
        model1 = CapabilityInfo(
            name="openconfig-interfaces",
            version="2.4.3",
            organization="openconfig",
        )

        capabilities = DeviceCapabilities(
            device_name="test-device",
            gnmi_version="0.7.0",
            supported_models=[model1],
        )

        assert capabilities.has_model("openconfig-network-instance") is False

    def test_has_model_empty_list(self):
        """Test has_model method with empty supported models list."""
        capabilities = DeviceCapabilities(
            device_name="test-device",
            gnmi_version="0.7.0",
            supported_models=[],
        )

        assert capabilities.has_model("openconfig-network-instance") is False


if __name__ == "__main__":
    pytest.main([__file__])
