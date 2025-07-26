#!/usr/bin/env python3
"""
Tests for the logging functions in network_tools/logging.py.
Uses mocking to test the logging functions without making actual GNMI requests.
"""

import os
import sys
import pytest
from unittest.mock import patch, ANY

# Add the project root to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
)

from src.collectors.logs import get_logs, _validate_and_convert_minutes
from src.schemas.responses import (
    NetworkOperationResult,
    OperationStatus,
    ErrorResponse,
    SuccessResponse,
)
from src.schemas.models import Device


class TestLoggingFunctions:
    """Test suite for logging functionality."""

    @patch("src.collectors.logs.get_gnmi_data")
    def test_get_logging_information_success(self, mock_get_gnmi_data):
        """Test getting logging information successfully."""
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
                    "data": """
            Apr 20 15:32:45 ERROR Test error message
            Apr 20 15:33:12 INFO Test info message
            Apr 20 15:34:01 WARNING Test warning message
            """
                }
            ]
        )

        # Configure the mock to return our response
        mock_get_gnmi_data.return_value = mock_response

        # Mock the filter_logs function to return a structured logs response
        filtered_logs = {
            "logs": [
                {
                    "timestamp": "Apr 20 15:32:45",
                    "severity": "ERROR",
                    "message": "Test error message",
                },
                {
                    "timestamp": "Apr 20 15:33:12",
                    "severity": "INFO",
                    "message": "Test info message",
                },
                {
                    "timestamp": "Apr 20 15:34:01",
                    "severity": "WARNING",
                    "message": "Test warning message",
                },
            ],
            "summary": {
                "total_logs": 3,
                "error_count": 1,
                "info_count": 1,
                "warning_count": 1,
            },
        }

        with patch(
            "src.collectors.logs.filter_logs", return_value=filtered_logs
        ):
            # Call the function with our mock device
            response = get_logs(mock_device, keywords="TEST", minutes=5)

            # Verify the response is as expected
            assert isinstance(response, NetworkOperationResult)
            assert response.status == OperationStatus.SUCCESS
            assert response.device_name == "test-device"
            assert response.operation_type == "logs"
            assert len(response.data["logs"]) == 3
            assert response.data["logs"][0]["severity"] == "ERROR"
            assert (
                response.data["summary"]["filter_info"]["keywords"] == "TEST"
            )
            assert (
                response.data["summary"]["filter_info"]["filter_minutes"] == 5
            )

            # Simply verify get_gnmi_data was called with the device and any request
            mock_get_gnmi_data.assert_called_once_with(
                device=mock_device, request=ANY
            )

    @patch("src.collectors.logs.get_gnmi_data")
    def test_get_logging_information_error(self, mock_get_gnmi_data):
        """Test getting logging information with an error."""
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
        response = get_logs(mock_device)

        # Verify the response is an error
        assert isinstance(response, NetworkOperationResult)
        assert response.status == OperationStatus.FAILED
        assert response.device_name == "test-device"
        assert response.error_response is not None
        assert response.error_response.type == "DEVICE_ERROR"

    @patch("src.collectors.logs.get_gnmi_data")
    def test_get_logging_information_filter_processing_error(
        self, mock_get_gnmi_data
    ):
        """Test getting logging information with a filter processing error."""
        # Create a mock device
        mock_device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            nos="iosxr",
            username="admin",
            password="password",
        )

        # Create a mock successful GNMI response
        mock_response = SuccessResponse(data=[{"data": "Some log data"}])

        # Configure the mock to return our response
        mock_get_gnmi_data.return_value = mock_response

        # Mock the filter_logs function to raise an exception
        with patch(
            "src.collectors.logs.filter_logs",
            side_effect=Exception("Filter processing error"),
        ):
            # Call the function with our mock device
            response = get_logs(mock_device)

            # Verify the response is an error
            assert isinstance(response, NetworkOperationResult)
            assert response.status == OperationStatus.FAILED
            assert response.device_name == "test-device"
            assert response.error_response is not None
            assert response.error_response.type == "LOG_PROCESSING_ERROR"
            assert response.error_response.message is not None
            assert "Filter processing error" in response.error_response.message


class TestMinutesValidation:
    """Test suite for minutes parameter validation functionality."""

    def test_validate_and_convert_minutes_valid_int(self):
        """Test validation with valid integer input."""
        result = _validate_and_convert_minutes(5)
        assert result == 5
        assert isinstance(result, int)

    def test_validate_and_convert_minutes_valid_string(self):
        """Test validation with valid string input."""
        result = _validate_and_convert_minutes("10")
        assert result == 10
        assert isinstance(result, int)

    def test_validate_and_convert_minutes_zero(self):
        """Test validation with zero (should be valid)."""
        result = _validate_and_convert_minutes(0)
        assert result == 0
        assert isinstance(result, int)

        result = _validate_and_convert_minutes("0")
        assert result == 0
        assert isinstance(result, int)

    def test_validate_and_convert_minutes_none(self):
        """Test validation with None input (should be valid)."""
        result = _validate_and_convert_minutes(None)
        assert result is None

    def test_validate_and_convert_minutes_negative_int(self):
        """Test validation with negative integer input."""
        with pytest.raises(ValueError) as exc_info:
            _validate_and_convert_minutes(-5)

        error_message = str(exc_info.value)
        assert "Minutes must be a positive integer, got: -5" in error_message
        assert (
            "Please provide a positive number (e.g., 5, 10, 30)"
            in error_message
        )

    def test_validate_and_convert_minutes_negative_string(self):
        """Test validation with negative string input."""
        with pytest.raises(ValueError) as exc_info:
            _validate_and_convert_minutes("-10")

        error_message = str(exc_info.value)
        assert (
            "Minutes must be a positive integer, got: '-10'" in error_message
        )
        assert (
            "Please provide a positive number as string (e.g., '5', '10', '30')"
            in error_message
        )

    def test_validate_and_convert_minutes_invalid_string(self):
        """Test validation with invalid string input."""
        with pytest.raises(ValueError) as exc_info:
            _validate_and_convert_minutes("abc")

        error_message = str(exc_info.value)
        assert "Minutes must be a valid number, got: 'abc'" in error_message
        assert (
            "Please provide either an integer (e.g., 5) or a string representing a number (e.g., '5')"
            in error_message
        )

    def test_validate_and_convert_minutes_float_string(self):
        """Test validation with float string input."""
        with pytest.raises(ValueError) as exc_info:
            _validate_and_convert_minutes("5.5")

        error_message = str(exc_info.value)
        assert "Minutes must be a valid number, got: '5.5'" in error_message

    def test_validate_and_convert_minutes_wrong_type_list(self):
        """Test validation with wrong type input (list)."""
        with pytest.raises(ValueError) as exc_info:
            _validate_and_convert_minutes([5])  # type: ignore

        error_message = str(exc_info.value)
        assert (
            "Minutes must be an integer or string representing a number, got: list '[5]'"
            in error_message
        )
        assert (
            "Please provide either an integer (e.g., 5) or a string representing a number (e.g., '5')"
            in error_message
        )

    def test_validate_and_convert_minutes_wrong_type_dict(self):
        """Test validation with wrong type input (dict)."""
        with pytest.raises(ValueError) as exc_info:
            _validate_and_convert_minutes({"minutes": 5})  # type: ignore

        error_message = str(exc_info.value)
        assert (
            "Minutes must be an integer or string representing a number, got: dict"
            in error_message
        )

    def test_validate_and_convert_minutes_wrong_type_float(self):
        """Test validation with wrong type input (float)."""
        with pytest.raises(ValueError) as exc_info:
            _validate_and_convert_minutes(5.5)  # type: ignore

        error_message = str(exc_info.value)
        assert (
            "Minutes must be an integer or string representing a number, got: float '5.5'"
            in error_message
        )

    @patch("src.collectors.logs.get_gnmi_data")
    def test_get_logs_with_string_minutes_success(self, mock_get_gnmi_data):
        """Test get_logs function with valid string minutes parameter."""
        # Create a mock device
        mock_device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            nos="iosxr",
            username="admin",
            password="password",
        )

        # Create a mock successful GNMI response
        mock_response = SuccessResponse(data=[{"data": "Some log data"}])
        mock_get_gnmi_data.return_value = mock_response

        # Mock the filter_logs function
        filtered_logs = {"logs": [], "summary": {"total_logs": 0}}

        with patch(
            "src.collectors.logs.filter_logs", return_value=filtered_logs
        ):
            # Call the function with string minutes
            response = get_logs(mock_device, minutes="15")

            # Verify the response is successful
            assert isinstance(response, NetworkOperationResult)
            assert response.status == OperationStatus.SUCCESS
            assert (
                response.data["summary"]["filter_info"]["filter_minutes"] == 15
            )

    @patch("src.collectors.logs.get_gnmi_data")
    def test_get_logs_with_invalid_minutes_parameter(self, mock_get_gnmi_data):
        """Test get_logs function with invalid minutes parameter."""
        # Create a mock device
        mock_device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            nos="iosxr",
            username="admin",
            password="password",
        )

        # Call the function with invalid minutes
        response = get_logs(mock_device, minutes="invalid")

        # Verify the response is an error
        assert isinstance(response, NetworkOperationResult)
        assert response.status == OperationStatus.FAILED
        assert response.error_response is not None
        assert response.error_response.type == "INVALID_PARAMETER"
        assert (
            "Minutes must be a valid number, got: 'invalid'"
            in response.error_response.message
        )

        # Verify gNMI was not called due to early validation failure
        mock_get_gnmi_data.assert_not_called()

    @patch("src.collectors.logs.get_gnmi_data")
    def test_get_logs_with_negative_minutes_parameter(
        self, mock_get_gnmi_data
    ):
        """Test get_logs function with negative minutes parameter."""
        # Create a mock device
        mock_device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            nos="iosxr",
            username="admin",
            password="password",
        )

        # Call the function with negative minutes
        response = get_logs(mock_device, minutes=-5)

        # Verify the response is an error
        assert isinstance(response, NetworkOperationResult)
        assert response.status == OperationStatus.FAILED
        assert response.error_response is not None
        assert response.error_response.type == "INVALID_PARAMETER"
        assert (
            "Minutes must be a positive integer, got: -5"
            in response.error_response.message
        )

        # Verify gNMI was not called due to early validation failure
        mock_get_gnmi_data.assert_not_called()
