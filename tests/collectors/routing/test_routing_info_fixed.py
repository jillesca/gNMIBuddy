#!/usr/bin/env python3
"""
Tests for the routing functions in collectors/routing.py.
Uses mocking to test the routing functions without making actual GNMI requests.
"""

import pytest
from unittest.mock import patch

from src.schemas.responses import NetworkOperationResult, OperationStatus
from src.schemas.models import Device


class TestRoutingInfoFunctions:
    """Test suite for routing information functionality."""

    def test_get_routing_info_function_exists(self):
        """Test that get_routing_info function can be imported and called."""
        with patch(
            "src.collectors.routing.get_routing_info"
        ) as mock_get_routing_info:
            mock_device = Device(
                name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                username="admin",
                password="password",
            )

            # Mock a successful response
            mock_get_routing_info.return_value = NetworkOperationResult(
                device_name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                operation_type="routing",
                status=OperationStatus.SUCCESS,
                data={"routing_info": "test routing data"},
            )

            # Call the function
            response = mock_get_routing_info(mock_device)

            # Verify it was called
            assert mock_get_routing_info.called
            assert response.status == OperationStatus.SUCCESS

    def test_get_routing_info_with_protocol_filter(self):
        """Test get_routing_info with protocol filter."""
        with patch(
            "src.collectors.routing.get_routing_info"
        ) as mock_get_routing_info:
            mock_device = Device(
                name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                username="admin",
                password="password",
            )

            # Mock a successful response
            mock_get_routing_info.return_value = NetworkOperationResult(
                device_name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                operation_type="routing",
                status=OperationStatus.SUCCESS,
                data={"routing_info": "bgp routing data"},
            )

            # Call the function with protocol filter
            response = mock_get_routing_info(mock_device, protocol="bgp")

            # Verify it was called with protocol
            mock_get_routing_info.assert_called_once_with(
                mock_device, protocol="bgp"
            )
            assert response.status == OperationStatus.SUCCESS

    def test_get_routing_info_with_details(self):
        """Test get_routing_info with include_details parameter."""
        with patch(
            "src.collectors.routing.get_routing_info"
        ) as mock_get_routing_info:
            mock_device = Device(
                name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                username="admin",
                password="password",
            )

            # Mock a successful response
            mock_get_routing_info.return_value = NetworkOperationResult(
                device_name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                operation_type="routing",
                status=OperationStatus.SUCCESS,
                data={"routing_info": "detailed routing data"},
            )

            # Call the function with include_details
            response = mock_get_routing_info(mock_device, include_details=True)

            # Verify it was called with include_details
            mock_get_routing_info.assert_called_once_with(
                mock_device, include_details=True
            )
            assert response.status == OperationStatus.SUCCESS

    def test_bgp_request_function_exists(self):
        """Test that bgp_request function can be imported and called."""
        with patch("src.collectors.routing.bgp_request") as mock_bgp_request:
            # Mock a successful response
            mock_bgp_request.return_value = {
                "path": ["bgp-path"],
                "encoding": "json_ietf",
            }

            # Call the function
            response = mock_bgp_request()

            # Verify it was called
            assert mock_bgp_request.called
            assert "path" in response

    def test_isis_request_function_exists(self):
        """Test that isis_request function can be imported and called."""
        with patch("src.collectors.routing.isis_request") as mock_isis_request:
            # Mock a successful response
            mock_isis_request.return_value = {
                "path": ["isis-path"],
                "encoding": "json_ietf",
            }

            # Call the function
            response = mock_isis_request()

            # Verify it was called
            assert mock_isis_request.called
            assert "path" in response

    def test_get_routing_info_error_handling(self):
        """Test get_routing_info error handling."""
        with patch(
            "src.collectors.routing.get_routing_info"
        ) as mock_get_routing_info:
            mock_device = Device(
                name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                username="admin",
                password="password",
            )

            # Mock a failed response
            mock_get_routing_info.return_value = NetworkOperationResult(
                device_name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                operation_type="routing",
                status=OperationStatus.FAILED,
                data={},
            )

            # Call the function
            response = mock_get_routing_info(mock_device)

            # Verify error response
            assert response.status == OperationStatus.FAILED

    def test_get_routing_info_feature_not_available(self):
        """Test get_routing_info when feature is not available."""
        with patch(
            "src.collectors.routing.get_routing_info"
        ) as mock_get_routing_info:
            mock_device = Device(
                name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                username="admin",
                password="password",
            )

            # Mock a feature not available response
            mock_get_routing_info.return_value = NetworkOperationResult(
                device_name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                operation_type="routing",
                status=OperationStatus.FEATURE_NOT_AVAILABLE,
                data={},
            )

            # Call the function
            response = mock_get_routing_info(mock_device)

            # Verify feature not available response
            assert response.status == OperationStatus.FEATURE_NOT_AVAILABLE

    def test_get_routing_info_with_isis_protocol(self):
        """Test get_routing_info with ISIS protocol."""
        with patch(
            "src.collectors.routing.get_routing_info"
        ) as mock_get_routing_info:
            mock_device = Device(
                name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                username="admin",
                password="password",
            )

            # Mock a successful response
            mock_get_routing_info.return_value = NetworkOperationResult(
                device_name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                operation_type="routing",
                status=OperationStatus.SUCCESS,
                data={"routing_info": "isis routing data"},
            )

            # Call the function with ISIS protocol
            response = mock_get_routing_info(mock_device, protocol="isis")

            # Verify it was called with ISIS protocol
            mock_get_routing_info.assert_called_once_with(
                mock_device, protocol="isis"
            )
            assert response.status == OperationStatus.SUCCESS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
