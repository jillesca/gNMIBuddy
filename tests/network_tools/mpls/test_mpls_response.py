#!/usr/bin/env python3
"""
Tests for the MplsResponse class in network_tools/responses.py.
Tests the contract and behavior of MPLS-specific response classes.
"""

import os
import sys
import pytest

# Add the project root to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
)

from src.network_tools.responses import MplsResponse
from src.gnmi.responses import GnmiError


class TestMplsResponse:
    """Test suite for the MplsResponse class."""

    def test_initialization(self):
        """Test basic initialization of the MplsResponse class."""
        # Test with minimal parameters
        response = MplsResponse()
        assert response.success is True
        assert response.mpls_data == {}
        assert response.summary is None
        assert response.include_details is False

        # Test with MPLS data and summary
        mpls_data = {
            "lsps": [{"name": "lsp1", "to": "10.1.1.1"}],
            "ldp": {"neighbors": 2},
            "summary": {"total_lsps": 1, "ldp_neighbors": 2},
        }
        summary = {"total_lsps": 1, "ldp_neighbors": 2}

        response = MplsResponse(
            mpls_data=mpls_data,
            summary=summary,
            device_name="test-device",
            include_details=True,
        )

        assert response.success is True
        assert response.mpls_data == mpls_data
        assert response.summary == summary
        assert response.device_name == "test-device"
        assert response.include_details is True

    def test_from_dict(self):
        """Test creation from a dictionary."""
        # Test with valid MPLS data
        mpls_data = {
            "lsps": [
                {"name": "lsp1", "to": "10.1.1.1"},
                {"name": "lsp2", "to": "10.1.1.2"},
            ],
            "ldp": {"neighbors": 2},
            "summary": {"total_lsps": 2, "ldp_neighbors": 2},
        }

        response = MplsResponse.from_dict(mpls_data, "test-device", True)
        assert response.success is True
        assert response.mpls_data == mpls_data
        assert response.summary == mpls_data.get("summary")
        assert response.device_name == "test-device"
        assert response.include_details is True

        # Test with error data
        error_data = {
            "error": {
                "type": "PARSE_ERROR",
                "message": "Failed to parse MPLS data",
            }
        }
        response = MplsResponse.from_dict(error_data, "test-device")
        assert response.success is False
        assert response.error is not None
        assert response.error.type == "PARSE_ERROR"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        # Test with include_details=True
        mpls_data = {
            "lsps": [{"name": "lsp1", "to": "10.1.1.1"}],
            "ldp": {"neighbors": 2},
        }
        summary = {"total_lsps": 1, "ldp_neighbors": 2}

        response = MplsResponse(
            mpls_data=mpls_data, summary=summary, include_details=True
        )

        result = response.to_dict()
        assert "data" in result
        assert result["data"] == mpls_data

        # Test with include_details=False
        response = MplsResponse(
            mpls_data=mpls_data, summary=summary, include_details=False
        )

        result = response.to_dict()
        assert "data" not in result
        assert "summary" in result
        assert result["summary"] == summary

        # Test error response
        error = GnmiError(type="TEST_ERROR", message="Test message")
        response = MplsResponse(success=False, error=error)
        result = response.to_dict()
        assert "error" in result
        assert result["error"]["type"] == "TEST_ERROR"
