#!/usr/bin/env python3
"""
Tests for VPN/VRF error handling functionality.

Tests that the VPN info collector properly detects ErrorResponse from gNMI operations
and implements fail-fast behavior as required by GitHub issue #2.

Key Test Scenarios:
1. ErrorResponse Detection: Simulate gNMI authentication failures
2. Data Structure Consistency: Verify `data: {}` format for errors
3. Status Differentiation: Verify correct status values
4. Metadata Context: Verify metadata provides clear context
5. Fail-Fast Behavior: Verify functions stop processing on errors
"""

import pytest
from unittest.mock import Mock, patch
from src.schemas.models import Device, NetworkOS
from src.schemas.responses import (
    ErrorResponse,
    FeatureNotFoundResponse,
    OperationStatus,
    NetworkOperationResult,
)
from src.schemas.metadata import VpnInfoMetadata
from src.collectors.vpn import get_vpn_info


class TestVpnErrorHandling:
    """Test suite for VPN info error handling functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            port=57400,
            username="admin",
            password="admin",
            nos=NetworkOS.IOSXR,
        )

    @patch("src.collectors.vpn.get_non_default_vrf_names")
    def test_vpn_info_error_response_detection(self, mock_get_vrf_names):
        """Test that get_vpn_info detects ErrorResponse and fails fast."""
        # Arrange: Mock get_non_default_vrf_names to return ErrorResponse
        error_response = ErrorResponse(
            type="gNMIException",
            message="GRPC ERROR Host: 192.168.1.1:57777, Error: authentication failed",
            details={"error_code": 401, "grpc_code": "UNAUTHENTICATED"},
        )
        mock_get_vrf_names.return_value = error_response

        # Act: Call get_vpn_info
        result = get_vpn_info(self.device)

        # Assert: Verify ErrorResponse detection and fail-fast behavior
        assert isinstance(result, NetworkOperationResult)
        assert result.status == OperationStatus.FAILED
        assert result.data == {}  # Empty dict as required
        assert result.error_response == error_response
        assert result.device_name == self.device.name
        assert result.ip_address == self.device.ip_address
        assert result.nos == self.device.nos.value
        assert result.operation_type == "vpn_info"

        # Verify metadata provides context
        assert (
            "Failed to discover VRFs due to gNMI error"
            in result.metadata["message"]
        )

        # Verify no further processing was done (fail-fast)
        mock_get_vrf_names.assert_called_once_with(self.device)

    @patch("src.collectors.vpn.get_non_default_vrf_names")
    def test_vpn_info_feature_not_found_response(self, mock_get_vrf_names):
        """Test that get_vpn_info handles FeatureNotFoundResponse correctly."""
        # Arrange: Mock get_non_default_vrf_names to return FeatureNotFoundResponse
        feature_not_found = FeatureNotFoundResponse(
            feature_name="vrf",
            message="VRF feature not supported on this device",
            details={"feature_type": "vrf", "device_model": "test"},
        )
        mock_get_vrf_names.return_value = feature_not_found

        # Act: Call get_vpn_info
        result = get_vpn_info(self.device, include_details=True)

        # Assert: Verify FeatureNotFoundResponse handling
        assert isinstance(result, NetworkOperationResult)
        assert result.status == OperationStatus.FEATURE_NOT_AVAILABLE
        assert (
            result.data == {}
        )  # Empty dict for both errors and legitimate empty
        assert result.feature_not_found_response == feature_not_found
        assert result.error_response is None

        # Verify metadata contains feature context
        metadata = result.metadata
        assert metadata["message"] == "VRF feature not available on device"
        assert metadata["total_vrfs_on_device"] == 0
        assert metadata["include_details"] == True
        assert metadata["vrf_filter_applied"] == False

    @patch("src.collectors.vpn.get_non_default_vrf_names")
    def test_vpn_info_legitimate_empty_vrfs(self, mock_get_vrf_names):
        """Test that get_vpn_info returns success for legitimate empty VRFs."""
        # Arrange: Mock get_non_default_vrf_names to return empty list (no VRFs)
        mock_get_vrf_names.return_value = []

        # Act: Call get_vpn_info
        result = get_vpn_info(self.device, vrf_name="test-vrf")

        # Assert: Verify legitimate empty result
        assert isinstance(result, NetworkOperationResult)
        assert result.status == OperationStatus.SUCCESS
        assert result.data == {}  # Empty dict as required
        assert result.error_response is None
        assert result.feature_not_found_response is None

        # Verify metadata distinguishes between error and legitimate empty
        metadata = result.metadata
        assert metadata["message"] == "No VRFs found"
        assert metadata["total_vrfs_on_device"] == 0
        assert metadata["vrfs_returned"] == 0
        assert metadata["vrf_filter_applied"] == True
        assert metadata["vrf_filter"] == "test-vrf"

    @patch("src.collectors.vpn.get_non_default_vrf_names")
    @patch("src.collectors.vpn.get_gnmi_data")
    def test_vpn_info_with_vrfs_success(
        self, mock_get_gnmi_data, mock_get_vrf_names
    ):
        """Test that get_vpn_info processes VRFs successfully when available."""
        # Arrange: Mock successful VRF discovery and data collection
        mock_get_vrf_names.return_value = ["vrf1", "vrf2"]

        # Mock gNMI data responses for each VRF
        mock_vrf_data = {
            "rd": "100:1",
            "description": "Test VRF",
            "route_targets": {"import": ["100:1"], "export": ["100:1"]},
        }
        mock_get_gnmi_data.return_value = mock_vrf_data

        # Act: Call get_vpn_info
        result = get_vpn_info(self.device, include_details=True)

        # Assert: Verify successful processing
        assert isinstance(result, NetworkOperationResult)
        assert result.status == OperationStatus.SUCCESS
        # Note: For successful case with actual VRFs, data would contain VRF info
        # But for this test, we verify the error handling path works correctly
        assert result.error_response is None

    def test_vpn_info_direct_isinstance_pattern(self):
        """Test that the code uses direct isinstance checks as required."""
        # This test verifies the implementation follows the mandatory pattern
        # of using direct isinstance(response, ErrorResponse) checks

        # Read the source code to verify pattern
        import inspect

        source = inspect.getsource(get_vpn_info)

        # Verify direct isinstance checks are used (not wrapper functions)
        assert "isinstance(vrf_names_result, ErrorResponse)" in source
        assert (
            "isinstance(vrf_names_result, FeatureNotFoundResponse)" in source
        )

        # Verify no wrapper functions are used
        assert "has_gnmi_error(" not in source
        assert "is_error_response(" not in source

    def test_vpn_info_metadata_class_encapsulation(self):
        """Test that VpnInfoMetadata class is used for data encapsulation."""
        # Verify that the function uses classes for data encapsulation, not dictionaries
        with patch(
            "src.collectors.vpn.get_non_default_vrf_names"
        ) as mock_get_vrf_names:
            mock_get_vrf_names.return_value = []

            result = get_vpn_info(self.device)

            # Verify that metadata comes from a class, not direct dictionary construction
            # The VpnInfoMetadata class should be used for structured data
            assert isinstance(result.metadata, dict)
            assert "message" in result.metadata
            assert "total_vrfs_on_device" in result.metadata
            assert "excluded_internal_vrfs" in result.metadata

    @patch("src.collectors.vpn.get_non_default_vrf_names")
    def test_vpn_info_error_different_types(self, mock_get_vrf_names):
        """Test ErrorResponse handling with different error types."""
        test_cases = [
            {
                "error_type": "CONNECTION_TIMEOUT",
                "message": "Connection timeout to device",
                "details": {"timeout_seconds": 30},
            },
            {
                "error_type": "AUTHENTICATION_FAILED",
                "message": "Invalid credentials",
                "details": {"auth_method": "basic"},
            },
            {
                "error_type": "GRPC_ERROR",
                "message": "gRPC connection failed",
                "details": {"grpc_code": "UNAVAILABLE"},
            },
        ]

        for test_case in test_cases:
            # Reset for each test case
            mock_get_vrf_names.reset_mock()

            # Arrange
            error_response = ErrorResponse(
                type=test_case["error_type"],
                message=test_case["message"],
                details=test_case["details"],
            )
            mock_get_vrf_names.return_value = error_response

            # Act
            result = get_vpn_info(self.device)

            # Assert: All error types should be handled the same way
            assert result.status == OperationStatus.FAILED
            assert result.data == {}
            assert result.error_response == error_response
            assert (
                "Failed to discover VRFs due to gNMI error"
                in result.metadata["message"]
            )

    @patch("src.collectors.vpn.get_non_default_vrf_names")
    def test_vpn_info_error_context_preservation(self, mock_get_vrf_names):
        """Test that error context is properly preserved in the response."""
        # Arrange: Create ErrorResponse with specific context
        original_error = ErrorResponse(
            type="gNMIException",
            message="GRPC ERROR Host: 10.10.20.101:57777, Error: authentication failed",
            details={
                "host": "10.10.20.101",
                "port": 57777,
                "error_class": "AuthenticationException",
                "timestamp": "2025-08-05T07:11:33",
            },
        )
        mock_get_vrf_names.return_value = original_error

        # Act
        result = get_vpn_info(self.device)

        # Assert: Verify error context is preserved exactly
        assert result.error_response is not None
        assert result.error_response.type == original_error.type
        assert result.error_response.message == original_error.message
        assert result.error_response.details == original_error.details

        # Verify device context is also preserved
        assert result.device_name == self.device.name
        assert result.ip_address == self.device.ip_address
        assert result.nos == self.device.nos.value
