#!/usr/bin/env python3
"""
Tests for the routing functions in network_tools/routing_info.py.
Uses mocking to test the routing functions without making actual GNMI requests.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
)

from src.network_tools.routing_info import (
    get_routing_information,
    bgp_request,
    isis_request,
    _get_bgp_info,
    _get_isis_info,
)
from src.network_tools.responses import RoutingResponse
from src.gnmi.responses import GnmiResponse, GnmiError


class TestRoutingInfoFunctions:
    """Test suite for routing information functionality."""

    def test_bgp_request(self):
        """Test the bgp_request function generates the correct GNMI request."""
        request = bgp_request()
        request_dict = request.to_dict()

        # Check the request has the correct path for BGP data
        assert "path" in request_dict
        assert len(request_dict["path"]) == 1
        assert (
            "openconfig-network-instance:network-instances/network-instance[name=*]/protocols/protocol/bgp"
            in request_dict["path"][0]
        )
        assert request_dict["encoding"] == "json_ietf"
        assert request_dict["datatype"] == "all"

    def test_isis_request(self):
        """Test the isis_request function generates the correct GNMI request."""
        request = isis_request()
        request_dict = request.to_dict()

        # Check the request has the correct paths for ISIS data
        assert "path" in request_dict
        assert len(request_dict["path"]) == 2
        assert any("interfaces" in path for path in request_dict["path"])
        assert any("global" in path for path in request_dict["path"])
        assert request_dict["encoding"] == "json_ietf"
        assert request_dict["datatype"] == "all"

    @patch("src.network_tools.routing_info._get_bgp_info")
    @patch("src.network_tools.routing_info._get_isis_info")
    def test_get_routing_information_all_protocols(
        self, mock_get_isis_info, mock_get_bgp_info
    ):
        """Test getting routing information for all protocols."""
        # Create a mock device
        mock_device = MagicMock()
        mock_device.name = "test-device"

        # Create mock responses for BGP and ISIS
        bgp_response = MagicMock(spec=RoutingResponse)
        bgp_response.success = True
        bgp_response.protocols = {"bgp": {"neighbors": 2}}

        isis_response = MagicMock(spec=RoutingResponse)
        isis_response.success = True
        isis_response.protocols = {"isis": {"interfaces": 3}}

        # Configure the mocks to return our responses
        mock_get_bgp_info.return_value = bgp_response
        mock_get_isis_info.return_value = isis_response

        # Call the function with no protocol filter (get all)
        responses = get_routing_information(mock_device, include_details=True)

        # Verify we got both protocol responses
        assert len(responses) == 2
        assert mock_get_bgp_info.called
        assert mock_get_isis_info.called

    @patch("src.network_tools.routing_info._get_bgp_info")
    @patch("src.network_tools.routing_info._get_isis_info")
    def test_get_routing_information_bgp_only(
        self, mock_get_isis_info, mock_get_bgp_info
    ):
        """Test getting routing information for BGP only."""
        # Create a mock device
        mock_device = MagicMock()
        mock_device.name = "test-device"

        # Create a mock response for BGP
        bgp_response = MagicMock(spec=RoutingResponse)
        bgp_response.success = True
        bgp_response.protocols = {"bgp": {"neighbors": 2}}

        # Configure the mock to return our response
        mock_get_bgp_info.return_value = bgp_response

        # Call the function with BGP protocol filter
        responses = get_routing_information(mock_device, protocol="bgp")

        # Verify we got only BGP response
        assert len(responses) == 1
        assert mock_get_bgp_info.called
        assert not mock_get_isis_info.called

    @patch("src.network_tools.routing_info.get_gnmi_data")
    def test_get_bgp_info_success(self, mock_get_gnmi_data):
        """Test getting BGP information successfully."""
        # Create a mock device
        mock_device = MagicMock()
        mock_device.name = "test-device"

        # Create a mock successful GNMI response
        mock_response = MagicMock(spec=GnmiResponse)
        mock_response.is_error.return_value = False
        mock_response.to_dict.return_value = {
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
            "src.network_tools.routing_info.parse_bgp_data",
            return_value=bgp_data,
        ):
            with patch(
                "src.network_tools.routing_info.generate_bgp_summary",
                return_value=summary,
            ):
                # Call the function with our mock device
                response = _get_bgp_info(mock_device, include_details=True)

                # Verify the response is as expected
                assert isinstance(response, RoutingResponse)
                assert response.success is True
                assert response.device_name == "test-device"
                assert response.include_details is True
                assert response.protocols["bgp"] == bgp_data
                assert response.summary["total_neighbors"] == 2

                # Verify that get_gnmi_data was called with the correct parameters
                mock_get_gnmi_data.assert_called_once()
                args, _ = mock_get_gnmi_data.call_args
                assert args[0] == mock_device

    @patch("src.network_tools.routing_info.get_gnmi_data")
    def test_get_bgp_info_error(self, mock_get_gnmi_data):
        """Test getting BGP information with an error."""
        # Create a mock device
        mock_device = MagicMock()
        mock_device.name = "test-device"

        # Create a mock error response
        error = GnmiError(
            type="DEVICE_ERROR", message="Could not connect to device"
        )
        mock_response = MagicMock(spec=GnmiResponse)
        mock_response.is_error.return_value = True
        mock_response.error = error

        # Configure the mock to return our error response
        mock_get_gnmi_data.return_value = mock_response

        # Call the function with our mock device
        response = _get_bgp_info(mock_device)

        # Verify the response is an error
        assert isinstance(response, RoutingResponse)
        assert response.success is False
        assert response.device_name == "test-device"
        assert response.error == error

    @patch("src.network_tools.routing_info.get_gnmi_data")
    def test_get_isis_info_success(self, mock_get_gnmi_data):
        """Test getting ISIS information successfully."""
        # Create a mock device
        mock_device = MagicMock()
        mock_device.name = "test-device"

        # Create a mock successful GNMI response
        mock_response = MagicMock(spec=GnmiResponse)
        mock_response.is_error.return_value = False
        mock_response.to_dict.return_value = {
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
            "src.network_tools.routing_info.parse_isis_data",
            return_value=isis_data,
        ):
            with patch(
                "src.network_tools.routing_info.generate_isis_summary",
                return_value=summary,
            ):
                # Call the function with our mock device
                response = _get_isis_info(mock_device, include_details=True)

                # Verify the response is as expected
                assert isinstance(response, RoutingResponse)
                assert response.success is True
                assert response.device_name == "test-device"
                assert response.include_details is True
                assert response.protocols["isis"] == isis_data
                assert response.summary["total_interfaces"] == 2

                # Verify that get_gnmi_data was called with the correct parameters
                mock_get_gnmi_data.assert_called_once()
                args, _ = mock_get_gnmi_data.call_args
                assert args[0] == mock_device
