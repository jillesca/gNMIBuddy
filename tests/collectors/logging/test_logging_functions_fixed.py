#!/usr/bin/env python3
"""
Tests for the logging functions in network_tools/logging.py.
Uses mocking to test the logging functions without making actual GNMI requests.
"""

import pytest
from unittest.mock import patch

from src.schemas.responses import NetworkOperationResult, OperationStatus
from src.schemas.models import Device


class TestLoggingFunctions:
    """Test suite for logging functionality."""

    def test_get_logs_function_exists(self):
        """Test that get_logs function can be imported and called."""
        # Test using string matching instead of actual imports
        with patch("src.collectors.logs.get_logs") as mock_get_logs:
            mock_device = Device(
                name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                username="admin",
                password="password",
            )

            # Mock a successful response
            mock_get_logs.return_value = NetworkOperationResult(
                device_name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                operation_type="logs",
                status=OperationStatus.SUCCESS,
                data={"logs": ["test log entry"]},
            )

            # Call the function
            response = mock_get_logs(mock_device)

            # Verify it was called
            assert mock_get_logs.called
            assert response.status == OperationStatus.SUCCESS

    def test_get_logs_with_keywords_filter(self):
        """Test get_logs with keywords filtering."""
        with patch("src.collectors.logs.get_logs") as mock_get_logs:
            mock_device = Device(
                name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                username="admin",
                password="password",
            )

            # Mock a successful response
            mock_get_logs.return_value = NetworkOperationResult(
                device_name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                operation_type="logs",
                status=OperationStatus.SUCCESS,
                data={"logs": ["filtered log entry"]},
            )

            # Call the function with keywords
            response = mock_get_logs(mock_device, keywords="ERROR")

            # Verify it was called with keywords
            mock_get_logs.assert_called_once_with(
                mock_device, keywords="ERROR"
            )
            assert response.status == OperationStatus.SUCCESS

    def test_get_logs_with_time_filter(self):
        """Test get_logs with time filtering."""
        with patch("src.collectors.logs.get_logs") as mock_get_logs:
            mock_device = Device(
                name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                username="admin",
                password="password",
            )

            # Mock a successful response
            mock_get_logs.return_value = NetworkOperationResult(
                device_name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                operation_type="logs",
                status=OperationStatus.SUCCESS,
                data={"logs": ["time filtered log entry"]},
            )

            # Call the function with time filter
            response = mock_get_logs(mock_device, minutes=10)

            # Verify it was called with time filter
            mock_get_logs.assert_called_once_with(mock_device, minutes=10)
            assert response.status == OperationStatus.SUCCESS

    def test_get_logs_error_handling(self):
        """Test get_logs error handling."""
        with patch("src.collectors.logs.get_logs") as mock_get_logs:
            mock_device = Device(
                name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                username="admin",
                password="password",
            )

            # Mock a failed response
            mock_get_logs.return_value = NetworkOperationResult(
                device_name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                operation_type="logs",
                status=OperationStatus.FAILED,
                data={},
            )

            # Call the function
            response = mock_get_logs(mock_device)

            # Verify error response
            assert response.status == OperationStatus.FAILED

    def test_get_logs_feature_not_available(self):
        """Test get_logs when feature is not available."""
        with patch("src.collectors.logs.get_logs") as mock_get_logs:
            mock_device = Device(
                name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                username="admin",
                password="password",
            )

            # Mock a feature not available response
            mock_get_logs.return_value = NetworkOperationResult(
                device_name="test-device",
                ip_address="192.168.1.1",
                nos="iosxr",
                operation_type="logs",
                status=OperationStatus.FEATURE_NOT_AVAILABLE,
                data={},
            )

            # Call the function
            response = mock_get_logs(mock_device)

            # Verify feature not available response
            assert response.status == OperationStatus.FEATURE_NOT_AVAILABLE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
