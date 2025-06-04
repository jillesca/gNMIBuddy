#!/usr/bin/env python3
"""
Tests for the RoutingResponse class in network_tools/responses.py.
Tests the contract and behavior of routing-specific response classes.
"""

import os
import sys
import pytest

# Add the project root to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
)

from src.network_tools.responses import RoutingResponse
from src.gnmi.responses import GnmiError


class TestRoutingResponse:
    """Test suite for the RoutingResponse class."""

    def test_initialization(self):
        """Test basic initialization of the RoutingResponse class."""
        # Test with minimal parameters
        response = RoutingResponse()
        assert response.success is True
        assert response.routes == []
        assert response.protocols == {}
        assert response.summary is None
        assert response.include_details is False

        # Test with routing data, protocols, and summary
        routes = [
            {
                "prefix": "10.0.0.0/24",
                "next_hop": "10.1.1.1",
                "protocol": "bgp",
            },
            {
                "prefix": "10.0.1.0/24",
                "next_hop": "10.1.1.2",
                "protocol": "isis",
            },
        ]
        protocols = {
            "bgp": {"neighbors": 2, "routes": 1},
            "isis": {"neighbors": 3, "routes": 1},
        }
        summary = {"total_routes": 2, "bgp_routes": 1, "isis_routes": 1}

        response = RoutingResponse(
            routes=routes,
            protocols=protocols,
            summary=summary,
            device_name="test-device",
            include_details=True,
        )

        assert response.success is True
        assert response.routes == routes
        assert response.protocols == protocols
        assert response.summary == summary
        assert response.device_name == "test-device"
        assert response.include_details is True

    def test_from_dict(self):
        """Test creation from a dictionary."""
        # Test with valid routing data
        routing_data = {
            "routes": [
                {
                    "prefix": "10.0.0.0/24",
                    "next_hop": "10.1.1.1",
                    "protocol": "bgp",
                },
                {
                    "prefix": "10.0.1.0/24",
                    "next_hop": "10.1.1.2",
                    "protocol": "isis",
                },
            ],
            "protocols": {
                "bgp": {"neighbors": 2, "routes": 1},
                "isis": {"neighbors": 3, "routes": 1},
            },
            "summary": {"total_routes": 2, "bgp_routes": 1, "isis_routes": 1},
        }

        response = RoutingResponse.from_dict(routing_data, "test-device", True)
        assert response.success is True
        assert response.routes == routing_data.get("routes")
        assert response.protocols == routing_data.get("protocols")
        assert response.summary == routing_data.get("summary")
        assert response.device_name == "test-device"
        assert response.include_details is True

        # Test with error data
        error_data = {
            "error": {
                "type": "PARSE_ERROR",
                "message": "Failed to parse routing data",
            }
        }
        response = RoutingResponse.from_dict(error_data, "test-device")
        assert response.success is False
        assert response.error is not None
        assert response.error.type == "PARSE_ERROR"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        # Test with include_details=True
        routes = [
            {
                "prefix": "10.0.0.0/24",
                "next_hop": "10.1.1.1",
                "protocol": "bgp",
            },
            {
                "prefix": "10.0.1.0/24",
                "next_hop": "10.1.1.2",
                "protocol": "isis",
            },
        ]
        protocols = {
            "bgp": {"neighbors": 2, "routes": 1},
            "isis": {"neighbors": 3, "routes": 1},
        }
        summary = {"total_routes": 2, "bgp_routes": 1, "isis_routes": 1}

        response = RoutingResponse(
            routes=routes,
            protocols=protocols,
            summary=summary,
            include_details=True,
        )

        result = response.to_dict()
        assert "data" in result
        assert "summary" in result
        assert result["data"]["routes"] == routes
        assert result["data"]["protocols"] == protocols
        assert result["summary"] == summary

        # Test with include_details=False
        response = RoutingResponse(
            routes=routes,
            protocols=protocols,
            summary=summary,
            include_details=False,
        )

        result = response.to_dict()
        assert "data" not in result
        assert "summary" in result
        assert result["summary"] == summary

        # Test error response
        error = GnmiError(type="TEST_ERROR", message="Test message")
        response = RoutingResponse(success=False, error=error)
        result = response.to_dict()
        assert "error" in result
        assert result["error"]["type"] == "TEST_ERROR"
