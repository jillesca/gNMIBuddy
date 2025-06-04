#!/usr/bin/env python3
"""
Tests for the MPLS functions in network_tools/mpls_info.py.
Uses mocking to test the MPLS functions without making actual GNMI requests.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
)

from src.network_tools.mpls_info import get_mpls_information, mpls_request
from src.network_tools.responses import MplsResponse
from src.gnmi.responses import GnmiResponse, GnmiError


class TestMplsInfoFunctions:
    """Test suite for MPLS information functionality."""

    def test_mpls_request(self):
        """Test the mpls_request function generates the correct GNMI request."""
        request = mpls_request()
        request_dict = request.to_dict()

        # Check the request has the correct XPath for MPLS data
        assert "path" in request_dict
        assert len(request_dict["path"]) == 1
        assert (
            "openconfig-network-instance:network-instances/network-instance[name=*]/mpls"
            in request_dict["path"][0]
        )
        assert request_dict["encoding"] == "json_ietf"
        assert request_dict["datatype"] == "all"

    @patch("src.network_tools.mpls_info.get_gnmi_data")
    def test_get_mpls_information_success(self, mock_get_gnmi_data):
        """Test getting MPLS information successfully."""
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
                        "mpls": {
                            "lsps": {
                                "static-lsps": {
                                    "static-lsp": [
                                        {"name": "lsp1", "to": "10.1.1.1"}
                                    ]
                                }
                            },
                            "global": {"config": {"enabled": True}},
                        },
                    }
                ]
            }
        }

        # Configure the mock to return our response
        mock_get_gnmi_data.return_value = mock_response

        # Mock the MPLS parser functions
        mpls_data = {
            "lsps": [{"name": "lsp1", "to": "10.1.1.1"}],
            "ldp": {"enabled": True, "neighbors": 0},
        }

        summary = {"total_lsps": 1, "ldp_enabled": True, "ldp_neighbors": 0}

        with patch(
            "src.network_tools.mpls_info.parse_mpls_data",
            return_value=mpls_data,
        ):
            with patch(
                "src.network_tools.mpls_info.generate_mpls_summary",
                return_value=summary,
            ):
                # Call the function with our mock device
                response = get_mpls_information(
                    mock_device, include_details=True
                )

                # Verify the response is as expected
                assert isinstance(response, MplsResponse)
                assert response.success is True
                assert response.device_name == "test-device"
                assert response.include_details is True
                assert response.mpls_data["lsps"][0]["name"] == "lsp1"
                assert response.summary["total_lsps"] == 1

                # Verify that get_gnmi_data was called with the correct parameters
                mock_get_gnmi_data.assert_called_once()
                args, _ = mock_get_gnmi_data.call_args
                assert args[0] == mock_device

    @patch("src.network_tools.mpls_info.get_gnmi_data")
    def test_get_mpls_information_error(self, mock_get_gnmi_data):
        """Test getting MPLS information with an error."""
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
        response = get_mpls_information(mock_device)

        # Verify the response is an error
        assert isinstance(response, MplsResponse)
        assert response.success is False
        assert response.error == error

    @patch("src.network_tools.mpls_info.get_gnmi_data")
    def test_get_mpls_information_parsing_error(self, mock_get_gnmi_data):
        """Test getting MPLS information with a parsing error."""
        # Create a mock device
        mock_device = MagicMock()
        mock_device.name = "test-device"

        # Create a mock successful GNMI response
        mock_response = MagicMock(spec=GnmiResponse)
        mock_response.is_error.return_value = False
        mock_response.to_dict.return_value = {"data": "Some MPLS data"}

        # Configure the mock to return our response
        mock_get_gnmi_data.return_value = mock_response

        # Mock the parse_mpls_data function to raise an exception
        with patch(
            "src.network_tools.mpls_info.parse_mpls_data",
            side_effect=Exception("Parsing error"),
        ):
            # Call the function with our mock device
            response = get_mpls_information(mock_device)

            # Verify the response is an error
            assert isinstance(response, MplsResponse)
            assert response.success is False
            assert response.error.type == "PARSING_ERROR"
            assert "Parsing error" in response.error.message
