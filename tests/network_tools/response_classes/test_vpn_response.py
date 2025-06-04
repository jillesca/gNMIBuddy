#!/usr/bin/env python3
"""
Tests for the VpnResponse class in network_tools/responses.py.
Tests the contract and behavior of VPN-specific response classes.
"""

import os
import sys
import pytest

# Add the project root to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
)

from src.network_tools.responses import VpnResponse
from src.gnmi.responses import GnmiError


class TestVpnResponse:
    """Test suite for the VpnResponse class."""

    def test_initialization(self):
        """Test basic initialization of the VpnResponse class."""
        # Test with minimal parameters
        response = VpnResponse()
        assert response.success is True
        assert response.vrfs == []
        assert response.summary is None
        assert response.include_details is False

        # Test with VRFs and summary
        vrfs = [
            {
                "name": "VRF1",
                "rd": "1:1",
                "interfaces": ["GigabitEthernet0/0/0/0"],
            }
        ]
        summary = {"total_vrfs": 1, "total_interfaces": 1}
        response = VpnResponse(
            vrfs=vrfs,
            summary=summary,
            device_name="test-device",
            include_details=True,
        )
        assert response.success is True
        assert response.vrfs == vrfs
        assert response.summary == summary
        assert response.device_name == "test-device"
        assert response.include_details is True

    def test_from_dict(self):
        """Test creation from a dictionary."""
        # Test with valid VRF data
        vrf_data = {
            "vrfs": [
                {
                    "name": "VRF1",
                    "rd": "1:1",
                    "interfaces": ["GigabitEthernet0/0/0/0"],
                },
                {
                    "name": "VRF2",
                    "rd": "2:2",
                    "interfaces": ["GigabitEthernet0/0/0/1"],
                },
            ],
            "summary": {"total_vrfs": 2, "total_interfaces": 2},
        }
        response = VpnResponse.from_dict(vrf_data, "test-device", True)
        assert response.success is True
        assert len(response.vrfs) == 2
        assert response.summary["total_vrfs"] == 2
        assert response.device_name == "test-device"
        assert response.include_details is True

        # Test with error data
        error_data = {
            "error": {
                "type": "FETCH_ERROR",
                "message": "Failed to fetch VPN data",
            }
        }
        response = VpnResponse.from_dict(error_data, "test-device")
        assert response.success is False
        assert response.error is not None
        assert response.error.type == "FETCH_ERROR"

    def test_vrf_count(self):
        """Test the vrf_count method."""
        # Test with empty VRFs
        response = VpnResponse()
        assert response.vrf_count() == 0

        # Test with multiple VRFs
        response = VpnResponse(
            vrfs=[{"name": "VRF1", "rd": "1:1"}, {"name": "VRF2", "rd": "2:2"}]
        )
        assert response.vrf_count() == 2

    def test_to_dict(self):
        """Test conversion to dictionary."""
        # Test with details
        vrfs = [
            {
                "name": "VRF1",
                "rd": "1:1",
                "interfaces": ["GigabitEthernet0/0/0/0"],
            },
            {
                "name": "VRF2",
                "rd": "2:2",
                "interfaces": ["GigabitEthernet0/0/0/1"],
            },
        ]
        summary = {"total_vrfs": 2, "total_interfaces": 2}
        response = VpnResponse(
            vrfs=vrfs, summary=summary, include_details=True
        )
        result = response.to_dict()
        assert "data" in result
        assert "summary" in result
        assert result["data"] == vrfs
        assert result["summary"] == summary

        # Test without details
        response = VpnResponse(
            vrfs=vrfs, summary=summary, include_details=False
        )
        result = response.to_dict()
        assert "data" not in result
        assert "summary" in result
        assert result["summary"] == summary

        # Test error response
        error = GnmiError(type="TEST_ERROR", message="Test message")
        response = VpnResponse(success=False, error=error)
        result = response.to_dict()
        assert "error" in result
        assert result["error"]["type"] == "TEST_ERROR"
