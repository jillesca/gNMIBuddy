#!/usr/bin/env python3
"""
Tests for the NetworkToolsResponse class in network_tools/responses.py.
Tests the contract and behavior of the base response class.
"""

import os
import sys
import pytest

# Add the project root to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
)

from src.network_tools.responses import NetworkToolsResponse
from src.gnmi.responses import GnmiResponse, GnmiError


class TestNetworkToolsResponse:
    """Test suite for the NetworkToolsResponse class."""

    def test_initialization(self):
        """Test basic initialization of the NetworkToolsResponse class."""
        # Test with minimal parameters
        response = NetworkToolsResponse()
        assert response.success is True
        assert response.error is None
        assert response.raw_data is None
        assert response.device_name is None

        # Test with all parameters
        error = GnmiError(type="TEST_ERROR", message="Test message")
        response = NetworkToolsResponse(
            success=False,
            error=error,
            raw_data={"data": "test"},
            device_name="test-device",
        )
        assert response.success is False
        assert response.error is error
        assert response.raw_data == {"data": "test"}
        assert response.device_name == "test-device"

    def test_from_gnmi_response(self):
        """Test creating a NetworkToolsResponse from a GnmiResponse."""
        # Test with a successful GnmiResponse
        gnmi_response = GnmiResponse(success=True, raw_data={"data": "test"})
        response = NetworkToolsResponse.from_gnmi_response(
            gnmi_response, "test-device"
        )
        assert response.success is True
        assert response.raw_data == {"data": "test"}
        assert response.device_name == "test-device"

        # Test with an error GnmiResponse
        error = GnmiError(type="TEST_ERROR", message="Test message")
        gnmi_response = GnmiResponse(success=False, error=error)
        response = NetworkToolsResponse.from_gnmi_response(
            gnmi_response, "test-device"
        )
        assert response.success is False
        assert response.error is error
        assert response.device_name == "test-device"

    def test_error_response(self):
        """Test creating an error response."""
        # Test with a GnmiError
        error = GnmiError(type="TEST_ERROR", message="Test message")
        response = NetworkToolsResponse.error_response(error, "test-device")
        assert response.success is False
        assert response.error is error
        assert response.device_name == "test-device"

        # Test with a dictionary
        error_dict = {"type": "DICT_ERROR", "message": "Dict error message"}
        response = NetworkToolsResponse.error_response(
            error_dict, "test-device"
        )
        assert response.success is False
        assert response.error.type == "DICT_ERROR"
        assert response.error.message == "Dict error message"
        assert response.device_name == "test-device"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        # Test successful response
        response = NetworkToolsResponse(device_name="test-device")
        result = response.to_dict()
        assert "device_name" in result
        assert result["device_name"] == "test-device"

        # Test error response
        error = GnmiError(type="TEST_ERROR", message="Test message")
        response = NetworkToolsResponse(
            success=False, error=error, device_name="test-device"
        )
        result = response.to_dict()
        assert "error" in result
        assert result["error"]["type"] == "TEST_ERROR"
        assert result["error"]["message"] == "Test message"

    def test_is_error(self):
        """Test the is_error method."""
        # Test successful response
        response = NetworkToolsResponse()
        assert response.is_error() is False

        # Test error response
        error = GnmiError(type="TEST_ERROR", message="Test message")
        response = NetworkToolsResponse(success=False, error=error)
        assert response.is_error() is True
