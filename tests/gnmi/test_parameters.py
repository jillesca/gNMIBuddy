#!/usr/bin/env python3
"""
Tests for the GnmiRequest parameter class in gnmi/parameters.py.
Tests the contract for parameter objects used in GNMI requests.
"""

import os
import sys
import pytest

# Add the project root to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
)

from src.gnmi.parameters import GnmiRequest


class TestGnmiRequest:
    """Test suite for the GnmiRequest parameter class."""

    def test_initialization(self):
        """Test basic initialization of the GnmiRequest class."""
        # Test with minimal parameters
        request = GnmiRequest(path=["/interfaces"])
        assert request.path == ["/interfaces"]
        assert request.prefix is None
        assert request.encoding == "json_ietf"
        assert request.datatype == "all"
        assert request.extended_params == {}

        # Test with all parameters
        request = GnmiRequest(
            path=["/interfaces", "/network-instances"],
            prefix="/openconfig",
            encoding="json",
            datatype="config",
            extended_params={"timeout": 30},
        )
        assert request.path == ["/interfaces", "/network-instances"]
        assert request.prefix == "/openconfig"
        assert request.encoding == "json"
        assert request.datatype == "config"
        assert request.extended_params == {"timeout": 30}

    def test_mapping_functionality(self):
        """Test mapping functionality of the GnmiRequest class."""
        # Test minimal parameters
        request = GnmiRequest(path=["/interfaces"])
        assert request["path"] == ["/interfaces"]
        assert request["encoding"] == "json_ietf"
        assert request["datatype"] == "all"
        # prefix should not be in keys when None
        assert "prefix" not in list(request.keys())

        # Test with all parameters including extended parameters
        request = GnmiRequest(
            path=["/interfaces", "/network-instances"],
            prefix="/openconfig",
            encoding="json",
            datatype="config",
            extended_params={"timeout": 30, "labels": ["test"]},
        )
        assert request["path"] == ["/interfaces", "/network-instances"]
        assert request["prefix"] == "/openconfig"
        assert request["encoding"] == "json"
        assert request["datatype"] == "config"
        assert request["timeout"] == 30
        assert request["labels"] == ["test"]

        # Test that it can be unpacked with **
        def mock_function(**kwargs):
            return kwargs

        result = mock_function(**request)
        assert result["path"] == ["/interfaces", "/network-instances"]
        assert result["timeout"] == 30

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
