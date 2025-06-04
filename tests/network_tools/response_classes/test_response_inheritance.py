#!/usr/bin/env python3
"""
Tests for the inheritance hierarchy of response classes.
Verifies that base class methods work properly when inherited by specialized classes.
"""

import os
import sys
import pytest

# Add the project root to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
)

from src.network_tools.responses import (
    NetworkToolsResponse,
    InterfaceResponse,
    MplsResponse,
    RoutingResponse,
    VpnResponse,
    LogResponse,
)
from src.gnmi.responses import GnmiError


class TestResponseInheritance:
    """Test suite for response class inheritance."""

    def test_error_propagation(self):
        """Test that error state and method propagate properly to child classes."""
        error = GnmiError(type="TEST_ERROR", message="Test message")

        # Create instances of each response class with an error
        base_response = NetworkToolsResponse(success=False, error=error)
        interface_response = InterfaceResponse(success=False, error=error)
        mpls_response = MplsResponse(success=False, error=error)
        routing_response = RoutingResponse(success=False, error=error)
        vpn_response = VpnResponse(success=False, error=error)
        log_response = LogResponse(success=False, error=error)

        # Verify that is_error() works for all classes
        assert base_response.is_error() is True
        assert interface_response.is_error() is True
        assert mpls_response.is_error() is True
        assert routing_response.is_error() is True
        assert vpn_response.is_error() is True
        assert log_response.is_error() is True

        # Verify that to_dict() handles errors properly for all classes
        for response in [
            base_response,
            interface_response,
            mpls_response,
            routing_response,
            vpn_response,
            log_response,
        ]:
            result = response.to_dict()
            assert "error" in result
            assert result["error"]["type"] == "TEST_ERROR"
            assert result["error"]["message"] == "Test message"

    def test_device_name_propagation(self):
        """Test that device_name is handled properly in all response classes."""
        device_name = "test-device"

        # Test with successful responses
        responses = [
            NetworkToolsResponse(device_name=device_name),
            InterfaceResponse(device_name=device_name),
            MplsResponse(device_name=device_name),
            RoutingResponse(device_name=device_name),
            VpnResponse(device_name=device_name),
            LogResponse(device_name=device_name),
        ]

        # Verify each response has the right device_name
        for response in responses:
            assert response.device_name == device_name

    def test_from_gnmi_response_inheritance(self):
        """Test that from_gnmi_response works for all child classes."""
        device_name = "test-device"

        # Create a base response
        base_response = NetworkToolsResponse(device_name="original")

        # Test that each child class can create from the base response
        interface_response = InterfaceResponse.from_gnmi_response(
            base_response, device_name
        )
        mpls_response = MplsResponse.from_gnmi_response(
            base_response, device_name
        )
        routing_response = RoutingResponse.from_gnmi_response(
            base_response, device_name
        )
        vpn_response = VpnResponse.from_gnmi_response(
            base_response, device_name
        )
        log_response = LogResponse.from_gnmi_response(
            base_response, device_name
        )

        # Verify each response has the right device_name
        for response in [
            interface_response,
            mpls_response,
            routing_response,
            vpn_response,
            log_response,
        ]:
            assert response.device_name == device_name
            assert response.success is True
