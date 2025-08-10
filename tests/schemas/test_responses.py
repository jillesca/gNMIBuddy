#!/usr/bin/env python3
"""
Tests for response schemas in src/schemas/responses.py.

Tests the response classes and enums to ensure proper validation
and functionality for the new NetworkOperationResult architecture.
"""

import json
from dataclasses import fields
from typing import get_type_hints
from src.schemas.responses import (
    OperationStatus,
    ErrorResponse,
    FeatureNotFoundResponse,
    SuccessResponse,
    NetworkOperationResult,
)
from src.schemas.models import Device
from src.schemas.responses import NetworkOS


class TestOperationStatus:
    """Test suite for OperationStatus enum."""

    def test_operation_status_values(self):
        """Test that OperationStatus has correct values."""
        assert OperationStatus.SUCCESS.value == "success"
        assert OperationStatus.FAILED.value == "failed"
        assert (
            OperationStatus.FEATURE_NOT_AVAILABLE.value
            == "feature_not_available"
        )

    def test_operation_status_membership(self):
        """Test OperationStatus enum membership."""
        assert OperationStatus.SUCCESS in OperationStatus
        assert OperationStatus.FAILED in OperationStatus
        assert OperationStatus.FEATURE_NOT_AVAILABLE in OperationStatus

    def test_operation_status_string_representation(self):
        """Test OperationStatus string representation."""
        assert str(OperationStatus.SUCCESS) == "OperationStatus.SUCCESS"
        assert str(OperationStatus.FAILED) == "OperationStatus.FAILED"
        assert (
            str(OperationStatus.FEATURE_NOT_AVAILABLE)
            == "OperationStatus.FEATURE_NOT_AVAILABLE"
        )

    def test_operation_status_equality(self):
        """Test OperationStatus equality comparisons."""
        status1 = OperationStatus.SUCCESS
        status2 = OperationStatus.SUCCESS
        status3 = OperationStatus.FAILED

        assert status1 == status2
        assert status1 != status3


class TestErrorResponse:
    """Test suite for ErrorResponse class."""

    def test_error_response_creation_minimal(self):
        """Test ErrorResponse creation with minimal fields."""
        error = ErrorResponse(type="CONNECTION_ERROR")

        assert error.type == "CONNECTION_ERROR"
        assert error.message is None
        assert error.details == {}

    def test_error_response_creation_full(self):
        """Test ErrorResponse creation with all fields."""
        details = {"error_code": 500, "timestamp": "2024-01-01T00:00:00Z"}
        error = ErrorResponse(
            type="GRPC_ERROR",
            message="Connection failed to device",
            details=details,
        )

        assert error.type == "GRPC_ERROR"
        assert error.message == "Connection failed to device"
        assert error.details == details

    def test_error_response_default_details(self):
        """Test that ErrorResponse has default empty details."""
        error = ErrorResponse(type="TIMEOUT")

        assert isinstance(error.details, dict)
        assert len(error.details) == 0

    def test_error_response_string_representation(self):
        """Test ErrorResponse string representation."""
        # With message
        error_with_message = ErrorResponse(
            type="CONNECTION_ERROR", message="Failed to connect"
        )
        error_str = str(error_with_message)
        assert "CONNECTION_ERROR" in error_str
        assert "Failed to connect" in error_str

        # Without message
        error_without_message = ErrorResponse(type="GENERIC_ERROR")
        error_str = str(error_without_message)
        assert "GENERIC_ERROR" in error_str

    def test_error_response_field_types(self):
        """Test ErrorResponse field types."""
        type_hints = get_type_hints(ErrorResponse)

        assert type_hints["type"] == str
        # Note: message is Optional[str] which shows as Union or Optional in type hints


class TestFeatureNotFoundResponse:
    """Test suite for FeatureNotFoundResponse class."""

    def test_feature_not_found_creation_minimal(self):
        """Test FeatureNotFoundResponse creation with minimal fields."""
        response = FeatureNotFoundResponse(
            feature_name="bgp", message="BGP not found"
        )

        assert response.feature_name == "bgp"
        assert response.message == "BGP not found"
        assert response.details == {}

    def test_feature_not_found_creation_full(self):
        """Test FeatureNotFoundResponse creation with all fields."""
        details = {"path": "/openconfig-bgp", "device": "router1"}
        response = FeatureNotFoundResponse(
            feature_name="bgp",
            message="BGP not configured on device",
            details=details,
        )

        assert response.feature_name == "bgp"
        assert response.message == "BGP not configured on device"
        assert response.details == details

    def test_feature_not_found_default_details(self):
        """Test that FeatureNotFoundResponse has default empty details."""
        response = FeatureNotFoundResponse(
            feature_name="ospf", message="OSPF not found"
        )

        assert isinstance(response.details, dict)
        assert len(response.details) == 0


class TestSuccessResponse:
    """Test suite for SuccessResponse class."""

    def test_success_response_creation_minimal(self):
        """Test SuccessResponse creation with minimal fields."""
        response = SuccessResponse(data=[])

        assert response.data == []
        assert response.timestamp is None

    def test_success_response_creation_full(self):
        """Test SuccessResponse creation with all fields."""
        data = [{"interface": "GigE0/0/0"}, {"interface": "GigE0/0/1"}]
        timestamp = "2024-01-01T00:00:00Z"

        response = SuccessResponse(data=data, timestamp=timestamp)

        assert response.data == data
        assert response.timestamp == timestamp

    def test_success_response_default_timestamp(self):
        """Test that SuccessResponse has default None timestamp."""
        response = SuccessResponse(data=[{"test": "value"}])

        assert response.timestamp is None


class TestNetworkOperationResult:
    """Test suite for NetworkOperationResult class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.device = Device(
            name="test-device", ip_address="192.168.1.1", nos="iosxr"
        )

    def test_network_operation_result_creation_minimal(self):
        """Test NetworkOperationResult creation with minimal required fields."""
        result = NetworkOperationResult(
            device_name="test-device",
            ip_address="192.168.1.1",
            nos="iosxr",
            operation_type="system_info",
            status=OperationStatus.SUCCESS,
        )

        assert result.device_name == "test-device"
        assert result.ip_address == "192.168.1.1"
        assert result.nos == "iosxr"
        assert result.operation_type == "system_info"
        assert result.status == OperationStatus.SUCCESS
        assert result.data == {}
        assert result.metadata == {}
        assert result.error_response is None
        assert result.feature_not_found_response is None

    def test_network_operation_result_success_creation(self):
        """Test NetworkOperationResult creation for successful operation."""
        data = {"hostname": "router1", "version": "7.3.1"}
        metadata = {"collection_time": "2024-01-01T00:00:00Z"}

        result = NetworkOperationResult(
            device_name=self.device.name,
            ip_address=self.device.ip_address,
            nos=self.device.nos,
            operation_type="system_info",
            status=OperationStatus.SUCCESS,
            data=data,
            metadata=metadata,
        )

        assert result.status == OperationStatus.SUCCESS
        assert result.data == data
        assert result.metadata == metadata
        assert result.error_response is None
        assert result.feature_not_found_response is None

    def test_network_operation_result_error_creation(self):
        """Test NetworkOperationResult creation for error scenario."""
        error_response = ErrorResponse(
            type="CONNECTION_ERROR", message="Failed to connect to device"
        )

        result = NetworkOperationResult(
            device_name=self.device.name,
            ip_address=self.device.ip_address,
            nos=self.device.nos,
            operation_type="system_info",
            status=OperationStatus.FAILED,
            error_response=error_response,
        )

        assert result.status == OperationStatus.FAILED
        assert result.data == {}
        assert result.metadata == {}
        assert result.error_response == error_response
        assert result.feature_not_found_response is None

    def test_network_operation_result_feature_not_found_creation(self):
        """Test NetworkOperationResult creation for feature not found scenario."""
        feature_response = FeatureNotFoundResponse(
            feature_name="bgp", message="BGP not configured on device"
        )

        result = NetworkOperationResult(
            device_name=self.device.name,
            ip_address=self.device.ip_address,
            nos=self.device.nos,
            operation_type="routing_info",
            status=OperationStatus.FEATURE_NOT_AVAILABLE,
            feature_not_found_response=feature_response,
        )

        assert result.status == OperationStatus.FEATURE_NOT_AVAILABLE
        assert result.data == {}
        assert result.metadata == {}
        assert result.error_response is None
        assert result.feature_not_found_response == feature_response

    def test_network_operation_result_default_values(self):
        """Test NetworkOperationResult default values."""
        result = NetworkOperationResult(
            device_name="test",
            ip_address="1.1.1.1",
            nos="iosxr",
            operation_type="test",
            status=OperationStatus.SUCCESS,
        )

        assert result.data == {}
        assert result.metadata == {}
        assert result.error_response is None
        assert result.feature_not_found_response is None

    def test_network_operation_result_field_types(self):
        """Test NetworkOperationResult field types."""
        type_hints = get_type_hints(NetworkOperationResult)

        assert type_hints["device_name"] == str
        assert type_hints["ip_address"] == str
        assert type_hints["nos"] == NetworkOS
        assert type_hints["operation_type"] == str
        assert type_hints["status"] == OperationStatus

    def test_network_operation_result_required_fields(self):
        """Test that NetworkOperationResult has all required fields."""
        result_fields = [f.name for f in fields(NetworkOperationResult)]

        required_fields = [
            "device_name",
            "ip_address",
            "nos",
            "operation_type",
            "status",
            "data",
            "metadata",
            "error_response",
            "feature_not_found_response",
        ]

        for field_name in required_fields:
            assert field_name in result_fields, f"Missing field: {field_name}"


class TestResponseSerializationIntegration:
    """Integration tests for response serialization and data handling."""

    def setup_method(self):
        """Setup test fixtures."""
        self.device = Device(
            name="test-device", ip_address="192.168.1.1", nos="iosxr"
        )

    def test_successful_operation_serialization(self):
        """Test serialization of successful NetworkOperationResult."""
        data = {
            "hostname": "router1",
            "version": "7.3.1",
            "interfaces": ["GigE0/0/0", "GigE0/0/1"],
        }
        metadata = {
            "collection_time": "2024-01-01T00:00:00Z",
            "response_time_ms": 150,
        }

        result = NetworkOperationResult(
            device_name=self.device.name,
            ip_address=self.device.ip_address,
            nos=self.device.nos,
            operation_type="system_info",
            status=OperationStatus.SUCCESS,
            data=data,
            metadata=metadata,
        )

        # Should be JSON serializable
        result_dict = {
            "device_name": result.device_name,
            "ip_address": result.ip_address,
            "nos": result.nos,
            "operation_type": result.operation_type,
            "status": result.status.value,
            "data": result.data,
            "metadata": result.metadata,
        }

        json_str = json.dumps(result_dict)
        deserialized = json.loads(json_str)

        assert deserialized["device_name"] == self.device.name
        assert deserialized["status"] == "success"
        assert deserialized["data"]["hostname"] == "router1"

    def test_error_operation_handling(self):
        """Test error handling in NetworkOperationResult."""
        error_response = ErrorResponse(
            type="TIMEOUT_ERROR",
            message="Request timed out after 30 seconds",
            details={"timeout_value": 30, "error_code": "E001"},
        )

        result = NetworkOperationResult(
            device_name=self.device.name,
            ip_address=self.device.ip_address,
            nos=self.device.nos,
            operation_type="interface_info",
            status=OperationStatus.FAILED,
            error_response=error_response,
        )

        assert result.status == OperationStatus.FAILED
        assert result.error_response is not None
        assert result.error_response.type == "TIMEOUT_ERROR"
        assert result.error_response.message is not None
        assert "timed out" in result.error_response.message
        assert result.error_response.details["timeout_value"] == 30

    def test_feature_not_found_handling(self):
        """Test feature not found handling in NetworkOperationResult."""
        feature_response = FeatureNotFoundResponse(
            feature_name="mpls",
            message="MPLS not configured on this device",
            details={
                "path": "/openconfig-mpls",
                "suggestion": "Enable MPLS first",
            },
        )

        result = NetworkOperationResult(
            device_name=self.device.name,
            ip_address=self.device.ip_address,
            nos=self.device.nos,
            operation_type="mpls_info",
            status=OperationStatus.FEATURE_NOT_AVAILABLE,
            feature_not_found_response=feature_response,
        )

        assert result.status == OperationStatus.FEATURE_NOT_AVAILABLE
        assert result.feature_not_found_response is not None
        assert result.feature_not_found_response.feature_name == "mpls"
        assert "not configured" in result.feature_not_found_response.message
        assert (
            result.feature_not_found_response.details["suggestion"]
            == "Enable MPLS first"
        )

    def test_response_consistency_across_operations(self):
        """Test that different operation types maintain consistent response structure."""
        operations = [
            ("system_info", {"hostname": "router1"}),
            ("interface_info", {"interfaces": ["GigE0/0/0"]}),
            ("mpls_info", {"mpls_status": "enabled"}),
            ("routing_info", {"bgp_peers": 5}),
        ]

        for op_type, test_data in operations:
            result = NetworkOperationResult(
                device_name=self.device.name,
                ip_address=self.device.ip_address,
                nos=self.device.nos,
                operation_type=op_type,
                status=OperationStatus.SUCCESS,
                data=test_data,
            )

            # All results should have consistent structure
            assert result.device_name == self.device.name
            assert result.ip_address == self.device.ip_address
            assert result.nos == self.device.nos
            assert result.operation_type == op_type
            assert result.status == OperationStatus.SUCCESS
            assert result.data == test_data
            assert isinstance(result.metadata, dict)
            assert result.error_response is None
            assert result.feature_not_found_response is None
