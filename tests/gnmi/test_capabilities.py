#!/usr/bin/env python3
"""
Unit tests for the capability checking functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any
import grpc

from src.gnmi.capabilities import (
    get_device_capabilities,
    _parse_capabilities_response,
    _parse_model_capability,
    extract_capabilities_from_response,
    create_capability_error,
    log_capabilities_summary,
)
from src.schemas.models import Device
from src.schemas.capabilities import (
    CapabilityInfo,
    DeviceCapabilities,
    CapabilityError,
    CapabilityVerificationStatus,
)
from src.schemas.responses import SuccessResponse, ErrorResponse


class TestGetDeviceCapabilities:
    """Test cases for get_device_capabilities function."""

    def test_successful_capabilities_retrieval(self):
        """Test successful capabilities retrieval from device."""
        # Create a test device
        device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            port=9339,
            username="admin",
            password="admin",
            insecure=True,
        )

        # Mock capabilities response
        mock_capabilities = {
            "gNMI_version": "0.7.0",
            "supported_encodings": ["JSON_IETF", "JSON"],
            "supported_models": [
                {
                    "name": "openconfig-network-instance",
                    "version": "1.3.0",
                    "organization": "openconfig",
                    "module": "openconfig-network-instance",
                    "revision": "2021-04-01",
                },
                {
                    "name": "openconfig-interfaces",
                    "version": "2.4.3",
                    "organization": "openconfig",
                },
            ],
        }

        with patch("src.gnmi.capabilities.gNMIclient") as mock_client:
            mock_gc = MagicMock()
            mock_client.return_value.__enter__.return_value = mock_gc
            mock_gc.capabilities.return_value = mock_capabilities

            result = get_device_capabilities(device)

            assert isinstance(result, SuccessResponse)
            assert len(result.data) == 1

            # Verify the device capabilities data
            capabilities_dict = result.data[0]
            assert capabilities_dict["device_name"] == "test-device"
            assert capabilities_dict["gnmi_version"] == "0.7.0"
            assert len(capabilities_dict["supported_models"]) == 2

    def test_timeout_error(self):
        """Test handling of timeout errors."""
        device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            port=9339,
            username="admin",
            password="admin",
            insecure=True,
            gnmi_timeout=5,
        )

        with patch("src.gnmi.capabilities.gNMIclient") as mock_client:
            mock_gc = MagicMock()
            mock_client.return_value.__enter__.return_value = mock_gc
            mock_gc.capabilities.side_effect = grpc.FutureTimeoutError()

            result = get_device_capabilities(device)

            assert isinstance(result, ErrorResponse)
            assert result.type == "CAPABILITIES_TIMEOUT"
            assert (
                result.message is not None and "test-device" in result.message
            )
            assert result.details["timeout"] == 5

    def test_grpc_error(self):
        """Test handling of gRPC errors."""
        device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            port=9339,
            username="admin",
            password="admin",
            insecure=True,
        )

        # Create a proper mock gRPC error
        class MockRpcError(grpc.RpcError):
            def __init__(self):
                super().__init__()
                self._code = Mock()
                self._code.name = "UNAUTHENTICATED"
                self._code.value = 16
                self._details = "Authentication failed"

            def code(self):
                return self._code

            def details(self):
                return self._details

        mock_error = MockRpcError()

        with patch("src.gnmi.capabilities.gNMIclient") as mock_client:
            mock_gc = MagicMock()
            mock_client.return_value.__enter__.return_value = mock_gc
            mock_gc.capabilities.side_effect = mock_error

            result = get_device_capabilities(device)

            assert isinstance(result, ErrorResponse)
            assert result.type == "CAPABILITIES_GRPC_ERROR"
            assert (
                result.message is not None and "test-device" in result.message
            )
            assert result.details["grpc_status"] == "UNAUTHENTICATED"
            assert result.details["grpc_code"] == "16"

    def test_connection_refused(self):
        """Test handling of connection refused errors."""
        device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            port=9339,
            username="admin",
            password="admin",
            insecure=True,
        )

        with patch("src.gnmi.capabilities.gNMIclient") as mock_client:
            mock_gc = MagicMock()
            mock_client.return_value.__enter__.return_value = mock_gc
            mock_gc.capabilities.side_effect = ConnectionRefusedError()

            result = get_device_capabilities(device)

            assert isinstance(result, ErrorResponse)
            assert result.type == "CAPABILITIES_CONNECTION_REFUSED"
            assert (
                result.message is not None and "test-device" in result.message
            )
            assert result.details["address"] == "192.168.1.1:9339"

    def test_unexpected_error(self):
        """Test handling of unexpected errors."""
        device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            port=9339,
            username="admin",
            password="admin",
            insecure=True,
        )

        with patch("src.gnmi.capabilities.gNMIclient") as mock_client:
            mock_gc = MagicMock()
            mock_client.return_value.__enter__.return_value = mock_gc
            mock_gc.capabilities.side_effect = ValueError(
                "Something went wrong"
            )

            result = get_device_capabilities(device)

            assert isinstance(result, ErrorResponse)
            assert result.type == "CAPABILITIES_UNEXPECTED_ERROR"
            assert (
                result.message is not None and "test-device" in result.message
            )
            assert result.details["error_type"] == "ValueError"
            assert result.details["error_str"] == "Something went wrong"


class TestParseCapabilitiesResponse:
    """Test cases for _parse_capabilities_response function."""

    def test_parse_valid_response(self):
        """Test parsing a valid capabilities response."""
        response = {
            "gNMI_version": "0.7.0",
            "supported_encodings": ["JSON_IETF", "JSON"],
            "supported_models": [
                {
                    "name": "openconfig-network-instance",
                    "version": "1.3.0",
                    "organization": "openconfig",
                    "module": "openconfig-network-instance",
                    "revision": "2021-04-01",
                }
            ],
        }

        result = _parse_capabilities_response("test-device", response)

        assert result is not None
        assert result.device_name == "test-device"
        assert result.gnmi_version == "0.7.0"
        assert len(result.supported_models) == 1
        assert result.supported_models[0].name == "openconfig-network-instance"
        assert result.supported_models[0].version == "1.3.0"
        assert result.supported_models[0].organization == "openconfig"

    def test_parse_empty_response(self):
        """Test parsing an empty capabilities response."""
        response = {}

        result = _parse_capabilities_response("test-device", response)

        assert result is not None
        assert result.device_name == "test-device"
        assert result.gnmi_version == "unknown"
        assert len(result.supported_models) == 0
        assert len(result.supported_encodings) == 0

    def test_parse_malformed_response(self):
        """Test parsing a malformed capabilities response."""
        response = {
            "gNMI_version": "0.7.0",
            "supported_models": [
                {
                    "name": "openconfig-network-instance",
                    "version": "1.3.0",
                    # Missing organization
                },
                {
                    # Missing name
                    "version": "1.0.0",
                    "organization": "openconfig",
                },
            ],
        }

        result = _parse_capabilities_response("test-device", response)

        assert result is not None
        assert result.device_name == "test-device"
        assert (
            len(result.supported_models) == 1
        )  # Only the valid model should be included
        assert result.supported_models[0].name == "openconfig-network-instance"


class TestParseModelCapability:
    """Test cases for _parse_model_capability function."""

    def test_parse_complete_model(self):
        """Test parsing a complete model capability."""
        model_data = {
            "name": "openconfig-network-instance",
            "version": "1.3.0",
            "organization": "openconfig",
            "module": "openconfig-network-instance",
            "revision": "2021-04-01",
            "namespace": "http://openconfig.net/yang/network-instance",
        }

        result = _parse_model_capability(model_data)

        assert result is not None
        assert result.name == "openconfig-network-instance"
        assert result.version == "1.3.0"
        assert result.organization == "openconfig"
        assert result.module == "openconfig-network-instance"
        assert result.revision == "2021-04-01"
        assert (
            result.namespace == "http://openconfig.net/yang/network-instance"
        )

    def test_parse_minimal_model(self):
        """Test parsing a minimal model capability."""
        model_data = {
            "name": "openconfig-interfaces",
            "version": "2.4.3",
            "organization": "openconfig",
        }

        result = _parse_model_capability(model_data)

        assert result is not None
        assert result.name == "openconfig-interfaces"
        assert result.version == "2.4.3"
        assert result.organization == "openconfig"
        assert result.module is None
        assert result.revision is None
        assert result.namespace is None

    def test_parse_missing_name(self):
        """Test parsing a model capability without name."""
        model_data = {"version": "1.0.0", "organization": "openconfig"}

        result = _parse_model_capability(model_data)

        assert result is None

    def test_parse_empty_model(self):
        """Test parsing an empty model capability."""
        model_data = {}

        result = _parse_model_capability(model_data)

        assert result is None


class TestExtractCapabilitiesFromResponse:
    """Test cases for extract_capabilities_from_response function."""

    def test_extract_valid_capabilities(self):
        """Test extracting capabilities from a valid SuccessResponse."""
        # Create a response with capabilities data
        capabilities_dict = {
            "device_name": "test-device",
            "gnmi_version": "0.7.0",
            "supported_encodings": ["JSON_IETF"],
            "supported_models": [
                {
                    "name": "openconfig-network-instance",
                    "version": "1.3.0",
                    "organization": "openconfig",
                    "module": None,
                    "revision": None,
                    "namespace": None,
                }
            ],
        }

        response = SuccessResponse(data=[capabilities_dict])

        result = extract_capabilities_from_response(response)

        assert result is not None
        assert result.device_name == "test-device"
        assert result.gnmi_version == "0.7.0"
        assert len(result.supported_models) == 1
        assert result.supported_models[0].name == "openconfig-network-instance"

    def test_extract_empty_response(self):
        """Test extracting capabilities from an empty response."""
        response = SuccessResponse(data=[])

        result = extract_capabilities_from_response(response)

        assert result is None


class TestCreateCapabilityError:
    """Test cases for create_capability_error function."""

    def test_create_basic_error(self):
        """Test creating a basic capability error."""
        error = create_capability_error("MODEL_NOT_FOUND", "Model not found")

        assert error.error_type == "MODEL_NOT_FOUND"
        assert error.message == "Model not found"
        assert error.model_name is None
        assert error.details == {}

    def test_create_error_with_model(self):
        """Test creating a capability error with model name."""
        error = create_capability_error(
            "VERSION_MISMATCH",
            "Version too old",
            model_name="openconfig-network-instance",
        )

        assert error.error_type == "VERSION_MISMATCH"
        assert error.message == "Version too old"
        assert error.model_name == "openconfig-network-instance"

    def test_create_error_with_details(self):
        """Test creating a capability error with additional details."""
        error = create_capability_error(
            "MODEL_NOT_FOUND",
            "Model not found",
            found_version="1.2.0",
            required_version="1.3.0",
        )

        assert error.error_type == "MODEL_NOT_FOUND"
        assert error.message == "Model not found"
        assert error.details["found_version"] == "1.2.0"
        assert error.details["required_version"] == "1.3.0"


class TestLogCapabilitiesSummary:
    """Test cases for log_capabilities_summary function."""

    def test_log_capabilities_summary(self):
        """Test logging capabilities summary."""
        capabilities = DeviceCapabilities(
            device_name="test-device",
            gnmi_version="0.7.0",
            supported_encodings=["JSON_IETF", "JSON"],
            supported_models=[
                CapabilityInfo(
                    name="openconfig-network-instance",
                    version="1.3.0",
                    organization="openconfig",
                ),
                CapabilityInfo(
                    name="openconfig-interfaces",
                    version="2.4.3",
                    organization="openconfig",
                ),
            ],
        )

        # This test mainly checks that the function runs without errors
        # In a real scenario, you might want to capture and verify log messages
        with patch("src.gnmi.capabilities.logger") as mock_logger:
            log_capabilities_summary(capabilities)

            # Verify that info messages were logged
            assert (
                mock_logger.info.call_count >= 4
            )  # At least 4 info messages expected


if __name__ == "__main__":
    pytest.main([__file__])
