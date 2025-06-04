#!/usr/bin/env python3
"""
Tests for the LogResponse class in network_tools/responses.py.
Tests the contract and behavior of log-specific response classes.
"""

import os
import sys
import pytest

# Add the project root to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
)

from src.network_tools.responses import LogResponse
from src.gnmi.responses import GnmiError


class TestLogResponse:
    """Test suite for the LogResponse class."""

    def test_initialization(self):
        """Test basic initialization of the LogResponse class."""
        # Test with minimal parameters
        response = LogResponse()
        assert response.success is True
        assert response.logs == []
        assert response.summary is None
        assert response.filter_info == {}

        # Test with logs, summary, and filter_info
        logs = [
            {
                "timestamp": "2024-04-20",
                "severity": "ERROR",
                "message": "Test error",
            }
        ]
        summary = {"total_logs": 1, "error_count": 1}
        filter_info = {
            "keywords": "ERROR",
            "filter_minutes": 5,
            "show_all_logs": False,
        }

        response = LogResponse(
            logs=logs,
            summary=summary,
            filter_info=filter_info,
            device_name="test-device",
        )

        assert response.success is True
        assert response.logs == logs
        assert response.summary == summary
        assert response.filter_info == filter_info
        assert response.device_name == "test-device"

    def test_from_logs(self):
        """Test creation from logs data."""
        # Test with valid logs data
        logs_data = {
            "logs": [
                {
                    "timestamp": "2024-04-20",
                    "severity": "ERROR",
                    "message": "Test error",
                },
                {
                    "timestamp": "2024-04-20",
                    "severity": "WARNING",
                    "message": "Test warning",
                },
            ],
            "summary": {"total_logs": 2, "error_count": 1, "warning_count": 1},
        }

        filter_info = {
            "keywords": "ERROR",
            "filter_minutes": 5,
            "show_all_logs": False,
        }

        response = LogResponse.from_logs(logs_data, "test-device", filter_info)
        assert response.success is True
        assert len(response.logs) == 2
        assert response.summary["total_logs"] == 2
        assert response.device_name == "test-device"
        assert response.filter_info == filter_info

        # Test with error data
        error_data = {
            "error": {"type": "PARSE_ERROR", "message": "Failed to parse logs"}
        }
        response = LogResponse.from_logs(error_data, "test-device")
        assert response.success is False
        assert response.error is not None
        assert response.error.type == "PARSE_ERROR"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        # Test with logs and summary
        logs = [
            {
                "timestamp": "2024-04-20",
                "severity": "ERROR",
                "message": "Test error",
            },
            {
                "timestamp": "2024-04-20",
                "severity": "WARNING",
                "message": "Test warning",
            },
        ]
        summary = {"total_logs": 2, "error_count": 1, "warning_count": 1}
        filter_info = {
            "keywords": "ERROR",
            "filter_minutes": 5,
            "show_all_logs": False,
        }

        response = LogResponse(
            logs=logs, summary=summary, filter_info=filter_info
        )

        result = response.to_dict()
        assert "logs" in result
        assert "summary" in result
        assert "filter_info" in result
        assert result["logs"] == logs
        assert result["summary"] == summary
        assert result["filter_info"] == filter_info

        # Test error response
        error = GnmiError(type="TEST_ERROR", message="Test message")
        response = LogResponse(success=False, error=error)
        result = response.to_dict()
        assert "error" in result
        assert result["error"]["type"] == "TEST_ERROR"
