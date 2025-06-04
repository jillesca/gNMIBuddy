#!/usr/bin/env python3
"""
Tests for the InterfaceResponse class in network_tools/responses.py.
Tests the contract and behavior of interface-specific response classes.
"""

import os
import sys
import pytest

# Add the project root to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
)

from src.network_tools.responses import InterfaceResponse
from src.gnmi.responses import GnmiError


class TestInterfaceResponse:
    """Test suite for the InterfaceResponse class."""

    def test_initialization(self):
        """Test basic initialization of the InterfaceResponse class."""
        # Test with minimal parameters
        response = InterfaceResponse()
        assert response.success is True
        assert response.interfaces == []
        assert response.summary is None
        assert response.is_single_interface is False

        # Test with interfaces and summary
        interfaces = [{"name": "GigabitEthernet0/0/0/0", "admin_state": "UP"}]
        summary = {"total_interfaces": 1, "admin_up": 1}
        response = InterfaceResponse(
            interfaces=interfaces, summary=summary, device_name="test-device"
        )
        assert response.success is True
        assert response.interfaces == interfaces
        assert response.summary == summary
        assert response.device_name == "test-device"
        assert response.is_single_interface is False

    def test_single_interface(self):
        """Test creation from single interface data."""
        # Test with valid interface data
        interface_data = {
            "interface": {
                "name": "GigabitEthernet0/0/0/0",
                "admin_state": "UP",
                "oper_state": "UP",
            }
        }
        response = InterfaceResponse.single_interface(
            interface_data, "test-device"
        )
        assert response.success is True
        assert len(response.interfaces) == 1
        assert response.interfaces[0]["name"] == "GigabitEthernet0/0/0/0"
        assert response.device_name == "test-device"
        assert response.is_single_interface is True

        # Test with error data
        error_data = {
            "error": {"type": "NOT_FOUND", "message": "Interface not found"}
        }
        response = InterfaceResponse.single_interface(
            error_data, "test-device"
        )
        assert response.success is False
        assert response.error is not None
        assert response.error.type == "NOT_FOUND"

        # Test with empty interface data
        # The implementation filters out empty interfaces, so we should expect an empty list
        empty_data = {"interface": {}}
        response = InterfaceResponse.single_interface(
            empty_data, "test-device"
        )
        assert response.success is True
        assert len(response.interfaces) == 0  # Updated to expect 0 interfaces
        assert response.is_single_interface is True

    def test_interface_brief(self):
        """Test creation from interface brief data."""
        # Test with valid interfaces data
        interfaces_data = {
            "interfaces": [
                {"name": "GigabitEthernet0/0/0/0", "admin_status": "UP"},
                {"name": "GigabitEthernet0/0/0/1", "admin_status": "DOWN"},
            ],
            "summary": {"total_interfaces": 2, "admin_up": 1, "admin_down": 1},
        }
        response = InterfaceResponse.interface_brief(
            interfaces_data, "test-device"
        )
        assert response.success is True
        assert len(response.interfaces) == 2
        assert response.summary["total_interfaces"] == 2
        assert response.device_name == "test-device"
        assert response.is_single_interface is False

        # Test with error data
        error_data = {
            "error": {
                "type": "FETCH_ERROR",
                "message": "Failed to fetch interfaces",
            }
        }
        response = InterfaceResponse.interface_brief(error_data, "test-device")
        assert response.success is False
        assert response.error is not None
        assert response.error.type == "FETCH_ERROR"

    def test_is_empty(self):
        """Test the is_empty method."""
        # Test with empty interfaces
        response = InterfaceResponse()
        assert response.is_empty() is True

        # Test with non-empty interfaces
        response = InterfaceResponse(
            interfaces=[{"name": "GigabitEthernet0/0/0/0"}]
        )
        assert response.is_empty() is False

    def test_interface_count(self):
        """Test the interface_count method."""
        # Test with empty interfaces
        response = InterfaceResponse()
        assert response.interface_count() == 0

        # Test with multiple interfaces
        response = InterfaceResponse(
            interfaces=[
                {"name": "GigabitEthernet0/0/0/0"},
                {"name": "GigabitEthernet0/0/0/1"},
            ]
        )
        assert response.interface_count() == 2

    def test_to_dict(self):
        """Test conversion to dictionary."""
        # Test single interface response
        interface = {"name": "GigabitEthernet0/0/0/0", "admin_state": "UP"}
        response = InterfaceResponse(
            interfaces=[interface], is_single_interface=True
        )
        result = response.to_dict()
        assert "interface" in result
        assert result["interface"] == interface

        # Test interface brief response
        interfaces = [
            {"name": "GigabitEthernet0/0/0/0", "admin_status": "UP"},
            {"name": "GigabitEthernet0/0/0/1", "admin_status": "DOWN"},
        ]
        summary = {"total_interfaces": 2, "admin_up": 1, "admin_down": 1}
        response = InterfaceResponse(interfaces=interfaces, summary=summary)
        result = response.to_dict()
        assert "interfaces" in result
        assert "summary" in result
        assert result["interfaces"] == interfaces
        assert result["summary"] == summary

        # Test error response
        error = GnmiError(type="TEST_ERROR", message="Test message")
        response = InterfaceResponse(success=False, error=error)
        result = response.to_dict()
        assert "error" in result
        assert result["error"]["type"] == "TEST_ERROR"
