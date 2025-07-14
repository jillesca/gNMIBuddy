#!/usr/bin/env python3
"""
Tests for the routing functions in collectors/routing.py.
Uses mocking to test the routing functions without making actual GNMI requests.
"""

import os
import sys
import pytest
from unittest.mock import patch

# Add the project root to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
)

from src.collectors.routing import (
    get_routing_info,
    bgp_request,
    isis_request,
    _get_bgp_info,
    _get_isis_info,
)
from src.schemas.responses import (
    NetworkOperationResult,
    OperationStatus,
    ErrorResponse,
    SuccessResponse,
)
from src.schemas.models import Device


class TestRoutingInfoFunctions:
    """Test suite for routing information functionality."""

    def test_bgp_request(self):
        """Test the bgp_request function generates the correct GNMI request."""
        request = bgp_request()

        # Check the request has the correct path for BGP data
        assert hasattr(request, "path")
        assert len(request.path) == 1
        assert (
            "openconfig-network-instance:network-instances/network-instance[name=*]/protocols/protocol/bgp"
            in request.path[0]
        )
        assert request.encoding == "json_ietf"
        assert request.datatype == "all"

    def test_isis_request(self):
        """Test the isis_request function generates the correct GNMI request."""
        request = isis_request()

        # Check the request has the correct paths for ISIS data
        assert hasattr(request, "path")
        assert len(request.path) == 2
        assert any("interfaces" in path for path in request.path)
        assert any("global" in path for path in request.path)
        assert request.encoding == "json_ietf"
        assert request.datatype == "all"

    @patch("src.collectors.routing._get_bgp_info")
    @patch("src.collectors.routing._get_isis_info")
    def test_get_routing_information_all_protocols(
        self, mock_get_isis_info, mock_get_bgp_info
    ):
        """Test getting routing information for all protocols."""
        # Create a mock device
        mock_device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            nos="iosxr",
            username="admin",
            password="password",
        )

        # Create mock responses for BGP and ISIS
        bgp_response = NetworkOperationResult(
            device_name="test-device",
            ip_address="192.168.1.1",
            nos="iosxr",
            operation_type="routing_info",
            status=OperationStatus.SUCCESS,
            data={
                "routing_data": {"bgp": {"neighbors": 2}},
                "summary": {"bgp_neighbors": 2},
            },
            metadata={"protocol": "bgp", "include_details": True},
        )

        isis_response = NetworkOperationResult(
            device_name="test-device",
            ip_address="192.168.1.1",
            nos="iosxr",
            operation_type="routing_info",
            status=OperationStatus.SUCCESS,
            data={
                "routing_data": {"isis": {"interfaces": 3}},
                "summary": {"isis_interfaces": 3},
            },
            metadata={"protocol": "isis", "include_details": True},
        )

        # Configure the mocks to return our responses
        mock_get_bgp_info.return_value = bgp_response
        mock_get_isis_info.return_value = isis_response

        # Call the function with no protocol filter (get all)
        response = get_routing_info(mock_device, include_details=True)

        # Verify we got the combined response
        assert isinstance(response, NetworkOperationResult)
        assert response.status == OperationStatus.SUCCESS
        assert response.device_name == "test-device"
        assert "bgp" in response.data["routing_data"]
        assert "isis" in response.data["routing_data"]
        assert mock_get_bgp_info.called
        assert mock_get_isis_info.called

    @patch("src.collectors.routing._get_bgp_info")
    @patch("src.collectors.routing._get_isis_info")
    def test_get_routing_information_bgp_only(
        self, mock_get_isis_info, mock_get_bgp_info
    ):
        """Test getting routing information for BGP only."""
        # Create a mock device
        mock_device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            nos="iosxr",
            username="admin",
            password="password",
        )

        # Create a mock response for BGP
        bgp_response = NetworkOperationResult(
            device_name="test-device",
            ip_address="192.168.1.1",
            nos="iosxr",
            operation_type="routing_info",
            status=OperationStatus.SUCCESS,
            data={
                "routing_data": {"bgp": {"neighbors": 2}},
                "summary": {"bgp_neighbors": 2},
            },
            metadata={"protocol": "bgp", "include_details": False},
        )

        # Configure the mock to return our response
        mock_get_bgp_info.return_value = bgp_response

        # Call the function with BGP protocol filter
        response = get_routing_info(mock_device, protocol="bgp")

        # Verify we got only BGP response
        assert isinstance(response, NetworkOperationResult)
        assert response.status == OperationStatus.SUCCESS
        assert "bgp" in response.data["routing_data"]
        assert "isis" not in response.data["routing_data"]
        assert mock_get_bgp_info.called
        assert not mock_get_isis_info.called

    @patch("src.collectors.routing.get_gnmi_data")
    def test_get_bgp_info_success(self, mock_get_gnmi_data):
        """Test getting BGP information successfully."""
        # Create a mock device
        mock_device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            nos="iosxr",
            username="admin",
            password="password",
        )

        # Create a mock successful GNMI response
        mock_response = SuccessResponse(
            data=[
                {
                    "openconfig-network-instance:network-instances": {
                        "network-instance": [
                            {
                                "name": "default",
                                "protocols": {
                                    "protocol": [
                                        {
                                            "identifier": "BGP",
                                            "name": "bgp",
                                            "bgp": {
                                                "neighbors": {
                                                    "neighbor": [
                                                        {
                                                            "neighbor-address": "10.1.1.1"
                                                        },
                                                        {
                                                            "neighbor-address": "10.1.1.2"
                                                        },
                                                    ]
                                                }
                                            },
                                        }
                                    ]
                                },
                            }
                        ]
                    }
                }
            ]
        )

        # Configure the mock to return our response
        mock_get_gnmi_data.return_value = mock_response

        # Mock the BGP parser functions
        bgp_data = {
            "neighbors": [
                {"address": "10.1.1.1", "state": "ESTABLISHED"},
                {"address": "10.1.1.2", "state": "ESTABLISHED"},
            ],
            "routes": [{"prefix": "192.168.1.0/24", "next-hop": "10.1.1.1"}],
        }

        summary = {
            "total_neighbors": 2,
            "established_neighbors": 2,
            "total_routes": 1,
        }

        with patch(
            "src.collectors.routing.parse_bgp_data",
            return_value=bgp_data,
        ):
            with patch(
                "src.collectors.routing.generate_bgp_summary",
                return_value=summary,
            ):
                # Call the function with our mock device
                response = _get_bgp_info(mock_device, include_details=True)

                # Verify the response is as expected
                assert isinstance(response, NetworkOperationResult)
                assert response.status == OperationStatus.SUCCESS
                assert response.device_name == "test-device"
                assert response.operation_type == "routing_info"
                assert response.data["routing_data"]["bgp"] == bgp_data
                assert response.data["summary"]["total_neighbors"] == 2
                assert response.metadata["include_details"] is True

                # Verify that get_gnmi_data was called with the correct parameters
                mock_get_gnmi_data.assert_called_once()
                args, _ = mock_get_gnmi_data.call_args
                assert args[0] == mock_device

    @patch("src.collectors.routing.get_gnmi_data")
    def test_get_bgp_info_error(self, mock_get_gnmi_data):
        """Test getting BGP information with an error."""
        # Create a mock device
        mock_device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            nos="iosxr",
            username="admin",
            password="password",
        )

        # Create a mock error response
        error_response = ErrorResponse(
            type="DEVICE_ERROR", message="Could not connect to device"
        )

        # Configure the mock to return our error response
        mock_get_gnmi_data.return_value = error_response

        # Call the function with our mock device
        response = _get_bgp_info(mock_device)

        # Verify the response is an error
        assert isinstance(response, NetworkOperationResult)
        assert response.status == OperationStatus.FAILED
        assert response.device_name == "test-device"
        assert response.error_response is not None
        assert response.error_response.type == "DEVICE_ERROR"

    @patch("src.collectors.routing.get_gnmi_data")
    def test_get_isis_info_success(self, mock_get_gnmi_data):
        """Test getting ISIS information successfully."""
        # Create a mock device
        mock_device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            nos="iosxr",
            username="admin",
            password="password",
        )

        # Create a mock successful GNMI response
        mock_response = SuccessResponse(
            data=[
                {
                    "openconfig-network-instance:network-instances": {
                        "network-instance": [
                            {
                                "name": "default",
                                "protocols": {
                                    "protocol": [
                                        {
                                            "identifier": "ISIS",
                                            "name": "isis",
                                            "isis": {
                                                "interfaces": {
                                                    "interface": [
                                                        {
                                                            "interface-id": "GigabitEthernet0/0/0/0"
                                                        },
                                                        {
                                                            "interface-id": "GigabitEthernet0/0/0/1"
                                                        },
                                                    ]
                                                },
                                                "global": {
                                                    "config": {
                                                        "level-capability": "LEVEL_2"
                                                    }
                                                },
                                            },
                                        }
                                    ]
                                },
                            }
                        ]
                    }
                }
            ]
        )

        # Configure the mock to return our response
        mock_get_gnmi_data.return_value = mock_response

        # Mock the ISIS parser functions
        isis_data = {
            "interfaces": [
                {"name": "GigabitEthernet0/0/0/0", "level": 2},
                {"name": "GigabitEthernet0/0/0/1", "level": 2},
            ],
            "neighbors": [
                {
                    "system-id": "0000.0000.0001",
                    "interface": "GigabitEthernet0/0/0/0",
                }
            ],
        }

        summary = {
            "total_interfaces": 2,
            "active_interfaces": 2,
            "total_neighbors": 1,
        }

        with patch(
            "src.collectors.routing.parse_isis_data",
            return_value=isis_data,
        ):
            with patch(
                "src.collectors.routing.generate_isis_summary",
                return_value=summary,
            ):
                # Call the function with our mock device
                response = _get_isis_info(mock_device, include_details=True)

                # Verify the response is as expected
                assert isinstance(response, NetworkOperationResult)
                assert response.status == OperationStatus.SUCCESS
                assert response.device_name == "test-device"
                assert response.operation_type == "routing_info"
                assert response.data["routing_data"]["isis"] == isis_data
                assert response.data["summary"]["total_interfaces"] == 2
                assert response.metadata["include_details"] is True

                # Verify that get_gnmi_data was called with the correct parameters
                mock_get_gnmi_data.assert_called_once()
                args, _ = mock_get_gnmi_data.call_args
                assert args[0] == mock_device
