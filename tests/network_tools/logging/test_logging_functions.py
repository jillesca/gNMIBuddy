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

from src.network_tools.logging import get_logging_information
from src.schemas.responses import (
    NetworkOperationResult,
    OperationStatus,
    ErrorResponse,
    SuccessResponse,
)
from src.schemas.models import Device


class TestLoggingFunctions:
    """Test suite for logging functionality."""

    @patch("src.network_tools.logging.get_gnmi_data")
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
            "src.network_tools.logging.filter_logs", return_value=filtered_logs
        ):
            # Call the function with our mock device
            response = get_logging_information(
                mock_device, keywords="TEST", minutes=5
            )

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

    @patch("src.network_tools.logging.get_gnmi_data")
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
        response = get_logging_information(mock_device)

        # Verify the response is an error
        assert isinstance(response, NetworkOperationResult)
        assert response.status == OperationStatus.FAILED
        assert response.device_name == "test-device"
        assert response.error_response is not None
        assert response.error_response.type == "DEVICE_ERROR"

    @patch("src.network_tools.logging.get_gnmi_data")
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
            "src.network_tools.logging.filter_logs",
            side_effect=Exception("Filter processing error"),
        ):
            # Call the function with our mock device
            response = get_logging_information(mock_device)

            # Verify the response is an error
            assert isinstance(response, NetworkOperationResult)
            assert response.status == OperationStatus.FAILED
            assert response.device_name == "test-device"
            assert response.error_response is not None
            assert response.error_response.type == "LOG_PROCESSING_ERROR"
            assert response.error_response.message is not None
            assert "Filter processing error" in response.error_response.message
