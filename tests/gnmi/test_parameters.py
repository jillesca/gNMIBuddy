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
from src.schemas.openconfig_models import OpenConfigModel


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

        # Test with all core parameters plus some gNMI specific ones
        request = GnmiRequest(
            path=["/interfaces", "/network-instances"],
            prefix="/openconfig",
            encoding="json",
            datatype="config",
        )
        assert request.path == ["/interfaces", "/network-instances"]
        assert request.prefix == "/openconfig"
        assert request.encoding == "json"
        assert request.datatype == "config"

    def test_mapping_functionality(self):
        """Test mapping functionality of the GnmiRequest class."""
        # Test minimal parameters
        request = GnmiRequest(path=["/interfaces"])
        assert request["path"] == ["/interfaces"]
        assert request["encoding"] == "json_ietf"
        assert request["datatype"] == "all"
        # prefix is included even when None (simplified behavior)
        assert request["prefix"] is None

        # Test with all parameters including gNMI specific parameters
        request = GnmiRequest(
            path=["/interfaces", "/network-instances"],
            prefix="/openconfig",
            encoding="json",
            datatype="config",
        )
        assert request["path"] == ["/interfaces", "/network-instances"]
        assert request["prefix"] == "/openconfig"
        assert request["encoding"] == "json"
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

    def test_single_model_detection(self):
        """Test detection of single OpenConfig model."""
        # System model
        system_request = GnmiRequest(path=["openconfig-system:/system"])
        models = system_request.get_required_models()
        assert models == {OpenConfigModel.SYSTEM}

        # Interfaces model
        interfaces_request = GnmiRequest(
            path=["openconfig-interfaces:interfaces"]
        )
        models = interfaces_request.get_required_models()
        assert models == {OpenConfigModel.INTERFACES}

        # Network instance model
        network_instance_request = GnmiRequest(
            path=[
                "openconfig-network-instance:network-instances/network-instance[name=*]"
            ]
        )
        models = network_instance_request.get_required_models()
        assert models == {OpenConfigModel.NETWORK_INSTANCE}

    def test_multiple_model_detection(self):
        """Test detection of multiple OpenConfig models in single request."""
        multi_model_request = GnmiRequest(
            path=[
                "openconfig-system:/system",
                "openconfig-interfaces:interfaces",
                "openconfig-network-instance:network-instances/network-instance[name=*]",
            ]
        )

        models = multi_model_request.get_required_models()
        expected_models = {
            OpenConfigModel.SYSTEM,
            OpenConfigModel.INTERFACES,
            OpenConfigModel.NETWORK_INSTANCE,
        }
        assert models == expected_models

    def test_requires_model(self):
        """Test requires_model method."""
        request = GnmiRequest(
            path=[
                "openconfig-system:/system",
                "openconfig-interfaces:interfaces",
            ]
        )

        assert request.requires_model(OpenConfigModel.SYSTEM)
        assert request.requires_model(OpenConfigModel.INTERFACES)
        assert not request.requires_model(OpenConfigModel.NETWORK_INSTANCE)

    def test_get_model_names(self):
        """Test get_model_names method."""
        request = GnmiRequest(
            path=[
                "openconfig-system:/system",
                "openconfig-interfaces:interfaces",
            ]
        )

        model_names = request.get_model_names()
        expected_names = {"openconfig-system", "openconfig-interfaces"}
        assert model_names == expected_names

    def test_real_collector_paths(self):
        """Test model detection with real collector paths."""
        # System collector path
        system_request = GnmiRequest(path=["openconfig-system:/system"])
        assert system_request.get_required_models() == {OpenConfigModel.SYSTEM}

        # Interfaces collector path
        interfaces_request = GnmiRequest(
            path=["openconfig-interfaces:interfaces"]
        )
        assert interfaces_request.get_required_models() == {
            OpenConfigModel.INTERFACES
        }

        # Routing collector paths
        routing_request = GnmiRequest(
            path=[
                "openconfig-network-instance:network-instances/network-instance[name=*]/protocols/protocol/isis/interfaces/",
                "openconfig-network-instance:network-instances/network-instance[name=*]/protocols/protocol/bgp",
            ]
        )
        assert routing_request.get_required_models() == {
            OpenConfigModel.NETWORK_INSTANCE
        }

    def test_no_models_detected(self):
        """Test request with no detectable OpenConfig models."""
        non_openconfig_request = GnmiRequest(
            path=[
                "invalid-path",
                "not-openconfig:/path",
                "random-string",
            ]
        )

        models = non_openconfig_request.get_required_models()
        assert models == set()

        model_names = non_openconfig_request.get_model_names()
        assert model_names == set()

    def test_backward_compatibility_with_model_detection(self):
        """Test that existing GnmiRequest functionality is preserved with new model detection."""
        request = GnmiRequest(
            path=["openconfig-system:/system"],
            prefix="some-prefix",
            encoding="json_ietf",
            datatype="state",
        )

        # Test existing functionality
        assert request.path == ["openconfig-system:/system"]
        assert request.prefix == "some-prefix"
        assert request.encoding == "json_ietf"
        assert request.datatype == "state"

        # Test mapping interface
        assert request.path == ["openconfig-system:/system"]
        assert request.prefix == "some-prefix"

        # Test that it can be unpacked
        keys = list(request.keys())
        assert "path" in keys
        assert request["path"] == ["openconfig-system:/system"]

        # Test new functionality
        models = request.get_required_models()
        assert models == {OpenConfigModel.SYSTEM}
