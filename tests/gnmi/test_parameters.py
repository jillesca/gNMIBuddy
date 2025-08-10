#!/usr/bin/env python3
"""
Tests for the GnmiRequest parameter class in gnmi/parameters.py.
Tests the contract for parameter objects used in GNMI requests.
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
)

from src.gnmi.parameters import GnmiRequest
from src.gnmi.capabilities.encoding import GnmiEncoding


class TestGnmiRequest:
    """Test suite for the GnmiRequest parameter class."""

    def test_initialization(self):
        """Test basic initialization of the GnmiRequest class."""
        # Test with minimal parameters
        request = GnmiRequest(path=["/interfaces"])
        assert request.path == ["/interfaces"]
        assert request.prefix is None
        assert request.encoding == GnmiEncoding.JSON_IETF
        assert request.datatype == "all"

        # Test with all core parameters plus some gNMI specific ones
        request = GnmiRequest(
            path=["/interfaces", "/network-instances"],
            prefix="/openconfig",
            encoding=GnmiEncoding.JSON,
            datatype="config",
        )
        assert request.path == ["/interfaces", "/network-instances"]
        assert request.prefix == "/openconfig"
        assert request.encoding == GnmiEncoding.JSON
        assert request.datatype == "config"

    def test_mapping_functionality(self):
        """Test mapping functionality of the GnmiRequest class."""
        # Test minimal parameters
        request = GnmiRequest(path=["/interfaces"])
        assert request["path"] == ["/interfaces"]
        assert request["encoding"] == GnmiEncoding.JSON_IETF
        assert request["datatype"] == "all"
        # prefix is included even when None (simplified behavior)
        assert request["prefix"] is None

        # Test with all parameters including gNMI specific parameters
        request = GnmiRequest(
            path=["/interfaces", "/network-instances"],
            prefix="/openconfig",
            encoding=GnmiEncoding.JSON,
            datatype="config",
        )
        assert request["path"] == ["/interfaces", "/network-instances"]
        assert request["prefix"] == "/openconfig"
        assert request["encoding"] == GnmiEncoding.JSON
        assert request["datatype"] == "config"

        # Test that it can be unpacked with **
        def mock_function(**kwargs):
            return kwargs

        result = mock_function(**request)
        assert result["path"] == ["/interfaces", "/network-instances"]

    def test_multiple_paths(self):
        """Test handling of multiple path expressions."""
        request = GnmiRequest(
            path=[
                "/interfaces/interface[name=GigabitEthernet0/0/0/0]",
                "/interfaces/interface[name=GigabitEthernet0/0/0/1]",
            ]
        )
        assert len(request["path"]) == 2
        assert (
            request["path"][0]
            == "/interfaces/interface[name=GigabitEthernet0/0/0/0]"
        )
        assert (
            request["path"][1]
            == "/interfaces/interface[name=GigabitEthernet0/0/0/1]"
        )
