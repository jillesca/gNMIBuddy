#!/usr/bin/env python3
"""
Tests for the GnmiError and GnmiResponse classes in gnmi/responses.py.
Tests the contract for response objects returned from GNMI operations.
"""

import os
import sys
import pytest
import json

# Add the project root to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
)

from src.gnmi.responses import (
    GnmiError,
    GnmiResponse,
    GnmiDataResponse,
    GnmiFeatureNotFoundResponse,
)


class TestGnmiError:
    """Test suite for the GnmiError class."""

    def test_initialization(self):
        """Test basic initialization of the GnmiError class."""
        # Test with minimal parameters
        error = GnmiError(type="TEST_ERROR")
        assert error.type == "TEST_ERROR"
        assert error.message is None
        assert error.details == {}

        # Test with all parameters
        error = GnmiError(
            type="CONNECTION_ERROR",
            message="Failed to connect to device",
            details={"host": "192.168.1.1", "port": 57400},
        )
        assert error.type == "CONNECTION_ERROR"
        assert error.message == "Failed to connect to device"
        assert error.details == {"host": "192.168.1.1", "port": 57400}

    def test_from_dict(self):
        """Test creation from a dictionary."""
        # Test with minimal dictionary
        error_dict = {"type": "TEST_ERROR"}
        error = GnmiError.from_dict(error_dict)
        assert error.type == "TEST_ERROR"
        assert error.message is None
        assert error.details == {}

        # Test with complete dictionary
        error_dict = {
            "type": "CONNECTION_ERROR",
            "message": "Failed to connect to device",
            "host": "192.168.1.1",
            "port": 57400,
            "retry_count": 3,
        }
        error = GnmiError.from_dict(error_dict)
        assert error.type == "CONNECTION_ERROR"
        assert error.message == "Failed to connect to device"
        assert "host" in error.details
        assert "port" in error.details
        assert "retry_count" in error.details
        assert error.details["host"] == "192.168.1.1"
        assert error.details["port"] == 57400
        assert error.details["retry_count"] == 3

    def test_to_dict(self):
        """Test conversion to dictionary."""
        # Test with minimal parameters
        error = GnmiError(type="TEST_ERROR")
        result = error.to_dict()
        assert result["type"] == "TEST_ERROR"
        assert len(result) == 1  # Only type should be present

        # Test with all parameters
        error = GnmiError(
            type="CONNECTION_ERROR",
            message="Failed to connect to device",
            details={"host": "192.168.1.1", "port": 57400},
        )
        result = error.to_dict()
        assert result["type"] == "CONNECTION_ERROR"
        assert result["message"] == "Failed to connect to device"
        assert result["host"] == "192.168.1.1"
        assert result["port"] == 57400


class TestGnmiResponse:
    """Test suite for the GnmiResponse class."""

    def test_initialization(self):
        """Test basic initialization of the GnmiResponse class."""
        # Test with default parameters
        response = GnmiResponse()
        assert response.success is True
        assert response.error is None
        assert response.raw_data is None

        # Test with success=False and error
        error = GnmiError(type="TEST_ERROR", message="Test error message")
        response = GnmiResponse(success=False, error=error)
        assert response.success is False
        assert response.error is error
        assert response.raw_data is None

        # Test with success=True and raw_data
        raw_data = {"path": "/interfaces", "val": {"status": "up"}}
        response = GnmiResponse(success=True, raw_data=raw_data)
        assert response.success is True
        assert response.error is None
        assert response.raw_data == raw_data

    def test_success_response(self):
        """Test creating a success response."""
        data = {"path": "/interfaces", "val": {"status": "up"}}
        response = GnmiResponse.success_response(data)
        assert response.success is True
        assert response.error is None
        assert response.raw_data == data

    def test_error_response(self):
        """Test creating an error response."""
        # Test with GnmiError object
        error = GnmiError(type="CONNECTION_ERROR", message="Connection failed")
        response = GnmiResponse.error_response(error)
        assert response.success is False
        assert response.error is error
        assert response.raw_data is None

        # Test with error dictionary
        error_dict = {
            "type": "TIMEOUT_ERROR",
            "message": "Request timed out",
            "timeout": 30,
        }
        response = GnmiResponse.error_response(error_dict)
        assert response.success is False
        assert response.error.type == "TIMEOUT_ERROR"
        assert response.error.message == "Request timed out"
        assert response.error.details["timeout"] == 30

    def test_from_dict(self):
        """Test creation from a dictionary."""
        # Test with success data
        data_dict = {"data": {"path": "/interfaces", "val": {"status": "up"}}}
        response = GnmiResponse.from_dict(data_dict)
        assert response.success is True
        assert response.raw_data == data_dict

        # Test with error data
        error_dict = {
            "error": {"type": "PARSE_ERROR", "message": "Invalid JSON"}
        }
        response = GnmiResponse.from_dict(error_dict)
        assert response.success is False
        assert response.error.type == "PARSE_ERROR"
        assert response.error.message == "Invalid JSON"

    def test_is_error(self):
        """Test the is_error method."""
        # Test success response
        response = GnmiResponse()
        assert response.is_error() is False

        # Test error response
        error = GnmiError(type="TEST_ERROR")
        response = GnmiResponse(success=False, error=error)
        assert response.is_error() is True

    def test_to_dict(self):
        """Test conversion to dictionary."""
        # Test success response
        raw_data = {"path": "/interfaces", "val": {"status": "up"}}
        response = GnmiResponse(success=True, raw_data=raw_data)
        result = response.to_dict()
        assert result == raw_data

        # Test error response
        error = GnmiError(type="TEST_ERROR", message="Test error message")
        response = GnmiResponse(success=False, error=error)
        result = response.to_dict()
        assert "error" in result
        assert result["error"]["type"] == "TEST_ERROR"
        assert result["error"]["message"] == "Test error message"

        # Test with empty response
        response = GnmiResponse()
        result = response.to_dict()
        assert result == {}

    def test_to_json(self):
        """Test conversion to JSON string."""
        # Test success response
        raw_data = {"path": "/interfaces", "val": {"status": "up"}}
        response = GnmiResponse(success=True, raw_data=raw_data)
        json_str = response.to_json()
        assert isinstance(json_str, str)
        assert json.loads(json_str) == raw_data

        # Test error response
        error = GnmiError(type="TEST_ERROR", message="Test error message")
        response = GnmiResponse(success=False, error=error)
        json_str = response.to_json()
        assert isinstance(json_str, str)
        error_dict = json.loads(json_str)
        assert "error" in error_dict
        assert error_dict["error"]["type"] == "TEST_ERROR"


class TestGnmiDataResponse:
    """Test suite for the GnmiDataResponse class."""

    def test_initialization(self):
        """Test basic initialization of the GnmiDataResponse class."""
        # Test with default parameters
        response = GnmiDataResponse()
        assert response.success is True
        assert response.error is None
        assert response.raw_data is None
        assert response.data == []
        assert response.timestamp is None

        # Test with data and timestamp
        data = [{"path": "/interfaces", "val": {"status": "up"}}]
        timestamp = "12345678"
        response = GnmiDataResponse(
            success=True,
            raw_data={"response": data, "timestamp": timestamp},
            data=data,
            timestamp=timestamp,
        )
        assert response.success is True
        assert response.data == data
        assert response.timestamp == timestamp

    def test_from_raw_response(self):
        """Test creation from a raw GNMI response."""
        # Test with valid response
        raw_response = {
            "response": [
                {
                    "path": "/interfaces/interface[name=GigabitEthernet0/0/0/0]",
                    "val": {"state": "up"},
                },
                {
                    "path": "/interfaces/interface[name=GigabitEthernet0/0/0/1]",
                    "val": {"state": "down"},
                },
            ],
            "timestamp": "12345678",
        }
        response = GnmiDataResponse.from_raw_response(raw_response)
        assert response.success is True
        assert len(response.data) == 2
        assert response.timestamp == "12345678"

        # Test with empty response
        response = GnmiDataResponse.from_raw_response({})
        assert response.success is False
        assert response.error.type == "EMPTY_RESPONSE"

        # Test with error response
        error_response = {
            "error": {"type": "ACCESS_DENIED", "message": "Permission denied"}
        }
        response = GnmiDataResponse.from_raw_response(error_response)
        assert response.success is False
        assert response.error.type == "ACCESS_DENIED"
        assert response.error.message == "Permission denied"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        # Test success response with data
        data = [{"path": "/interfaces", "val": {"status": "up"}}]
        timestamp = "12345678"
        raw_data = {"response": data, "timestamp": timestamp}
        response = GnmiDataResponse(
            success=True, raw_data=raw_data, data=data, timestamp=timestamp
        )
        result = response.to_dict()
        assert "data" in result
        assert result["data"] == data
        assert result["timestamp"] == timestamp

        # Test error response
        error = GnmiError(type="TEST_ERROR", message="Test error message")
        response = GnmiDataResponse(success=False, error=error)
        result = response.to_dict()
        assert "error" in result
        assert result["error"]["type"] == "TEST_ERROR"

        # Test with empty values
        response = GnmiDataResponse(success=True)
        result = response.to_dict()
        assert isinstance(result, dict)
        # Result should be an empty dict or have empty lists/values


class TestGnmiFeatureNotFoundResponse:
    """Test suite for the GnmiFeatureNotFoundResponse class."""

    def test_initialization(self):
        """Test basic initialization of the GnmiFeatureNotFoundResponse class."""
        # Test with default parameters
        response = GnmiFeatureNotFoundResponse()
        assert response.success is True
        assert response.error is None
        assert response.raw_data is None
        assert response.feature_name is None
        assert response.feature_message is None
        assert response.feature_details == {}

        # Test with feature parameters
        feature_name = "ospf"
        feature_message = "OSPF is not configured on device"
        feature_details = {"device": "router1", "path": "/ospf/neighbors"}
        response = GnmiFeatureNotFoundResponse(
            feature_name=feature_name,
            feature_message=feature_message,
            feature_details=feature_details,
        )
        assert (
            response.success is True
        )  # Feature not found should not be an error
        assert response.feature_name == feature_name
        assert response.feature_message == feature_message
        assert response.feature_details == feature_details

    def test_create_method(self):
        """Test the create class method."""
        feature_name = "bgp"
        message = "BGP is not configured on device router1"
        details = {"device": "router1", "path": "/bgp"}

        response = GnmiFeatureNotFoundResponse.create(
            feature_name=feature_name, message=message, details=details
        )

        assert response.success is True
        assert response.feature_name == feature_name
        assert response.feature_message == message
        assert response.feature_details == details

    def test_to_dict(self):
        """Test conversion to dictionary."""
        # Test with minimal parameters
        response = GnmiFeatureNotFoundResponse(
            feature_name="ospf", feature_message="OSPF not found"
        )
        result = response.to_dict()
        assert "feature_not_found" in result
        assert result["feature_not_found"]["feature"] == "ospf"
        assert result["feature_not_found"]["message"] == "OSPF not found"

        # Test with details
        response = GnmiFeatureNotFoundResponse(
            feature_name="bgp",
            feature_message="BGP not configured",
            feature_details={"device": "router1", "code": "NOT_FOUND"},
        )
        result = response.to_dict()
        assert "feature_not_found" in result
        assert result["feature_not_found"]["feature"] == "bgp"
        assert result["feature_not_found"]["message"] == "BGP not configured"
        assert "details" in result["feature_not_found"]
        assert result["feature_not_found"]["details"]["device"] == "router1"
        assert result["feature_not_found"]["details"]["code"] == "NOT_FOUND"
