#!/usr/bin/env python3
"""
Tests for the MPLS functions in collectors/mpls.py.
Uses mocking to test the MPLS functions without making actual GNMI requests.
"""

import os
import sys
import pytest
from unittest.mock import patch

# Add the project root to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
)

from src.collectors.mpls import get_mpls_info, mpls_request
from src.schemas.responses import (
    NetworkOperationResult,
    OperationStatus,
    ErrorResponse,
    SuccessResponse,
)
from src.schemas.models import Device
from src.schemas.models import NetworkOS


class TestMplsInfoFunctions:
    """Test suite for MPLS information functionality."""

    def test_mpls_request(self):
        """Test the mpls_request function generates the correct GNMI request."""
        request = mpls_request()

        # Check the request has the correct path for MPLS data
        assert hasattr(request, "path")
        assert len(request.path) == 1
        assert (
            "openconfig-network-instance:network-instances/network-instance[name=*]/mpls"
            in request.path[0]
        )

    @patch("src.collectors.mpls.get_gnmi_data")
    def test_get_mpls_information_success(self, mock_get_gnmi_data):
        """Test getting MPLS information successfully."""
        # Create a mock device
        mock_device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            nos=NetworkOS.IOSXR,
            username="admin",
            password="password",
        )

        # Create a mock successful GNMI response with the expected data structure
        mock_response = SuccessResponse(
            data=[
                {
                    "openconfig-network-instance:network-instances": {
                        "network-instance": [
                            {
                                "name": "default",
                                "mpls": {
                                    "lsps": {
                                        "static-lsps": {
                                            "static-lsp": [
                                                {
                                                    "name": "lsp1",
                                                    "to": "10.1.1.1",
                                                }
                                            ]
                                        }
                                    },
                                    "global": {"config": {"enabled": True}},
                                },
                            }
                        ]
                    }
                }
            ]
        )

        # Configure the mock to return our response
        mock_get_gnmi_data.return_value = mock_response

        # Mock the MPLS parser functions
        mpls_data = {
            "lsps": [{"name": "lsp1", "to": "10.1.1.1"}],
            "ldp": {"enabled": True, "neighbors": 0},
        }

        summary = {"total_lsps": 1, "ldp_enabled": True, "ldp_neighbors": 0}

        with patch(
            "src.collectors.mpls.process_mpls_data",
            return_value=mpls_data,
        ):
            with patch(
                "src.collectors.mpls.generate_mpls_summary",
                return_value=summary,
            ):
                # Call the function with our mock device
                response = get_mpls_info(mock_device, include_details=True)

                # Verify the response is as expected
                assert isinstance(response, NetworkOperationResult)
                assert response.status == OperationStatus.SUCCESS
                assert response.device_name == "test-device"
                assert response.operation_type == "mpls_info"
                assert response.data["mpls_data"]["lsps"][0]["name"] == "lsp1"
                assert response.data["summary"]["total_lsps"] == 1
                assert response.metadata["include_details"] is True

                # Verify that get_gnmi_data was called with the correct parameters
                mock_get_gnmi_data.assert_called_once()
                args, _ = mock_get_gnmi_data.call_args
                assert args[0] == mock_device

    @patch("src.collectors.mpls.get_gnmi_data")
    def test_get_mpls_information_error(self, mock_get_gnmi_data):
        """Test getting MPLS information with an error."""
        # Create a mock device
        mock_device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            nos=NetworkOS.IOSXR,
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
        response = get_mpls_info(mock_device)

        # Verify the response is an error
        assert isinstance(response, NetworkOperationResult)
        assert response.status == OperationStatus.FAILED
        assert response.error_response is not None
        assert response.error_response.type == "DEVICE_ERROR"

    @patch("src.collectors.mpls.get_gnmi_data")
    def test_get_mpls_information_parsing_error(self, mock_get_gnmi_data):
        """Test getting MPLS information with a parsing error."""
        # Create a mock device
        mock_device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            nos=NetworkOS.IOSXR,
            username="admin",
            password="password",
        )

        # Create a mock successful GNMI response
        mock_response = SuccessResponse(data=[{"some": "data"}])

        # Configure the mock to return our response
        mock_get_gnmi_data.return_value = mock_response

        # Mock the process_mpls_data function to raise an exception
        with patch(
            "src.collectors.mpls.process_mpls_data",
            side_effect=ValueError("Parsing error"),
        ):
            # Call the function with our mock device
            response = get_mpls_info(mock_device)

            # Verify the response is an error
            assert isinstance(response, NetworkOperationResult)
            assert response.status == OperationStatus.FAILED
            assert response.error_response is not None
            assert response.error_response.type == "PARSING_ERROR"
            assert response.error_response.message is not None
            assert "Parsing error" in response.error_response.message
