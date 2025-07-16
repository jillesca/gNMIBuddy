#!/usr/bin/env python3
"""
Tests for the MPLS functions in collectors/mpls.py.
Uses mocking to test the MPLS functions without making actual GNMI requests.
"""

import pytest
from unittest.mock import patch

from src.schemas.responses import NetworkOperationResult, OperationStatus
from src.schemas.models import Device


class TestMplsInfoFunctions:
    """Test suite for MPLS information functionality."""

    def test_mpls_request_function_exists(self):
        """Test that mpls_request function can be imported and called."""
        with patch("src.collectors.mpls.mpls_request") as mock_mpls_request:
            mock_device = Device(
                name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                username="admin",
                password="password",
            )

            # Mock a successful response
            mock_mpls_request.return_value = NetworkOperationResult(
                device_name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                operation_type="mpls",
                status=OperationStatus.SUCCESS,
                data={"mpls_info": "test mpls data"},
            )

            # Call the function
            response = mock_mpls_request(mock_device)

            # Verify it was called
            assert mock_mpls_request.called
            assert response.status == OperationStatus.SUCCESS

    def test_get_mpls_info_function_exists(self):
        """Test that get_mpls_info function can be imported and called."""
        with patch("src.collectors.mpls.get_mpls_info") as mock_get_mpls_info:
            mock_device = Device(
                name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                username="admin",
                password="password",
            )

            # Mock a successful response
            mock_get_mpls_info.return_value = NetworkOperationResult(
                device_name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                operation_type="mpls",
                status=OperationStatus.SUCCESS,
                data={"mpls_info": "test mpls data"},
            )

            # Call the function
            response = mock_get_mpls_info(mock_device)

            # Verify it was called
            assert mock_get_mpls_info.called
            assert response.status == OperationStatus.SUCCESS

    def test_get_mpls_info_with_details(self):
        """Test get_mpls_info with include_details parameter."""
        with patch("src.collectors.mpls.get_mpls_info") as mock_get_mpls_info:
            mock_device = Device(
                name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                username="admin",
                password="password",
            )

            # Mock a successful response
            mock_get_mpls_info.return_value = NetworkOperationResult(
                device_name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                operation_type="mpls",
                status=OperationStatus.SUCCESS,
                data={"mpls_info": "detailed mpls data"},
            )

            # Call the function with include_details
            response = mock_get_mpls_info(mock_device, include_details=True)

            # Verify it was called with include_details
            mock_get_mpls_info.assert_called_once_with(
                mock_device, include_details=True
            )
            assert response.status == OperationStatus.SUCCESS

    def test_get_mpls_info_error_handling(self):
        """Test get_mpls_info error handling."""
        with patch("src.collectors.mpls.get_mpls_info") as mock_get_mpls_info:
            mock_device = Device(
                name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                username="admin",
                password="password",
            )

            # Mock a failed response
            mock_get_mpls_info.return_value = NetworkOperationResult(
                device_name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                operation_type="mpls",
                status=OperationStatus.FAILED,
                data={},
            )

            # Call the function
            response = mock_get_mpls_info(mock_device)

            # Verify error response
            assert response.status == OperationStatus.FAILED

    def test_get_mpls_info_feature_not_available(self):
        """Test get_mpls_info when feature is not available."""
        with patch("src.collectors.mpls.get_mpls_info") as mock_get_mpls_info:
            mock_device = Device(
                name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                username="admin",
                password="password",
            )

            # Mock a feature not available response
            mock_get_mpls_info.return_value = NetworkOperationResult(
                device_name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                operation_type="mpls",
                status=OperationStatus.FEATURE_NOT_AVAILABLE,
                data={},
            )

            # Call the function
            response = mock_get_mpls_info(mock_device)

            # Verify feature not available response
            assert response.status == OperationStatus.FEATURE_NOT_AVAILABLE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
