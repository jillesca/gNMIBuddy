#!/usr/bin/env python3
"""
Unit tests for topology utility functions.
Tests logic without making actual gNMI requests.
"""

import pytest
from unittest.mock import MagicMock
import networkx as nx

from src.schemas.responses import NetworkOperationResult, OperationStatus
from src.schemas.models import Device


class TestTopologyFunctions:
    """Test suite for topology functionality."""

    def test_device_creation_for_topology(self):
        """Test Device model creation for topology operations."""
        device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            nos="iosxr",
            username="admin",
            password="password",
        )

        assert device.name == "test-device"
        assert device.ip_address == "192.168.1.1"
        assert device.nos == "iosxr"

    def test_network_operation_result_for_topology(self):
        """Test NetworkOperationResult creation for topology operations."""
        result = NetworkOperationResult(
            device_name="test-device",
            ip_address="192.168.1.1",
            nos="iosxr",
            operation_type="topology",
            status=OperationStatus.SUCCESS,
            data={"topology": {"nodes": ["device1", "device2"]}},
        )

        assert result.device_name == "test-device"
        assert result.operation_type == "topology"
        assert result.status == OperationStatus.SUCCESS
        assert result.data["topology"]["nodes"] == ["device1", "device2"]

    def test_networkx_graph_creation(self):
        """Test NetworkX graph creation for topology operations."""
        graph = nx.Graph()
        graph.add_node("device1")
        graph.add_node("device2")
        graph.add_edge("device1", "device2", network="192.168.1.0/24")

        assert "device1" in graph.nodes
        assert "device2" in graph.nodes
        assert ("device1", "device2") in graph.edges
        assert (
            graph.edges[("device1", "device2")]["network"] == "192.168.1.0/24"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
