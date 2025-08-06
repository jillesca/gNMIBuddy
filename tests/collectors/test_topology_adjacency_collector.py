#!/usr/bin/env python3
"""
Tests for topology adjacency collector functionality.

Tests the topology adjacency collector that was refactored to follow
the established collector pattern. These tests focus on the collector
logic and proper error handling.
"""

from unittest.mock import patch
from src.schemas.models import Device, NetworkOS, DeviceErrorResult
from src.schemas.responses import (
    ErrorResponse,
    OperationStatus,
    NetworkOperationResult,
)
from src.inventory.manager import InventoryManager

from src.collectors.topology.adjacency import get_topology_adjacency


class MockNetworkTopologyResult:
    """Mock class for network topology results."""

    def __init__(
        self, status=OperationStatus.SUCCESS, error_response=None, data=None
    ):
        self.status = status
        self.error_response = error_response
        self.data = data if data is not None else {"direct_connections": []}


class TestTopologyAdjacencyCollector:
    """Test suite for topology adjacency collector functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        # Reset inventory singleton state before each test
        InventoryManager._instance = None

        self.device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            port=57400,
            username="admin",
            password="admin",
            nos=NetworkOS.IOSXR,
        )

    def teardown_method(self):
        """Clean up after each test."""
        # Reset inventory singleton state after each test
        InventoryManager._instance = None

    @patch("src.collectors.topology.adjacency.get_device")
    def test_topology_adjacency_device_not_found(self, mock_get_device):
        """Test that get_topology_adjacency handles device not found errors."""
        # Arrange: Mock get_device to return DeviceErrorResult
        device_error = DeviceErrorResult(
            msg="Device 'nonexistent' not found in inventory"
        )
        mock_get_device.return_value = device_error

        # Act: Call get_topology_adjacency
        result = get_topology_adjacency("nonexistent")

        # Assert: Verify device not found error handling
        assert isinstance(result, NetworkOperationResult)
        assert result.status == OperationStatus.FAILED
        assert result.device_name == "nonexistent"
        assert result.ip_address == "0.0.0.0"
        assert result.nos == "unknown"
        assert result.operation_type == "topology_adjacency"
        assert result.data == {}

        # Verify metadata provides context
        metadata = result.metadata
        assert metadata["scope"] == "network-wide"
        assert "not found in inventory" in metadata["message"]

        mock_get_device.assert_called_once_with("nonexistent")

    @patch("src.collectors.topology.adjacency.get_device")
    @patch("src.collectors.topology.adjacency.get_network_topology")
    def test_topology_adjacency_error_response_detection(
        self, mock_get_network_topology, mock_get_device
    ):
        """Test that get_topology_adjacency detects ErrorResponse during topology building and fails fast."""
        # Arrange: Mock get_device to return the test device
        mock_get_device.return_value = self.device

        # Mock get_network_topology to return ErrorResponse
        error_response = ErrorResponse(
            type="gNMIException",
            message="GRPC ERROR Host: 192.168.1.1:57777, Error: authentication failed",
            details={"error_code": 401, "grpc_code": "UNAUTHENTICATED"},
        )

        topology_result = MockNetworkTopologyResult(
            status=OperationStatus.FAILED, error_response=error_response
        )
        mock_get_network_topology.return_value = topology_result

        # Act: Call get_topology_adjacency
        result = get_topology_adjacency("test-device")

        # Assert: Verify ErrorResponse detection and fail-fast behavior
        assert isinstance(result, NetworkOperationResult)
        assert result.status == OperationStatus.FAILED
        assert result.data == {}  # Empty dict as required
        assert result.error_response == error_response
        assert result.device_name == self.device.name
        assert result.ip_address == self.device.ip_address
        assert result.nos == self.device.nos.value
        assert result.operation_type == "topology_adjacency"

        # Verify metadata provides context about network-wide scope and error
        metadata = result.metadata
        assert metadata["scope"] == "network-wide"
        assert (
            "Failed to build topology adjacency due to gNMI errors"
            in metadata["message"]
        )

        # Verify fail-fast behavior - functions called once
        mock_get_device.assert_called_once_with("test-device")
        mock_get_network_topology.assert_called_once()

    @patch("src.collectors.topology.adjacency.get_device")
    @patch("src.collectors.topology.adjacency.get_network_topology")
    def test_topology_adjacency_legitimate_empty_network(
        self, mock_get_network_topology, mock_get_device
    ):
        """Test that get_topology_adjacency returns success for legitimate empty network topology."""
        # Arrange: Mock get_device to return the test device
        mock_get_device.return_value = self.device

        # Mock successful topology building but no connections found
        topology_result = MockNetworkTopologyResult(
            status=OperationStatus.SUCCESS,
            error_response=None,
            data={"direct_connections": []},  # No connections in network
        )
        mock_get_network_topology.return_value = topology_result

        # Act: Call get_topology_adjacency
        result = get_topology_adjacency("test-device")

        # Assert: Verify legitimate empty network is handled as success
        assert isinstance(result, NetworkOperationResult)
        assert result.status == OperationStatus.SUCCESS
        assert (
            result.data == {}
        )  # Empty dict for both error and legitimate empty
        assert result.error_response is None

        # Verify metadata distinguishes legitimate empty from errors
        metadata = result.metadata
        assert metadata["scope"] == "network-wide"
        assert metadata["total_connections"] == 0
        assert "No topology connections discovered" in metadata["message"]

    @patch("src.collectors.topology.adjacency.get_device")
    @patch("src.collectors.topology.adjacency.get_network_topology")
    def test_topology_adjacency_with_connections_success(
        self, mock_get_network_topology, mock_get_device
    ):
        """Test that get_topology_adjacency handles successful topology with connections."""
        # Arrange: Mock get_device to return the test device
        mock_get_device.return_value = self.device

        # Mock successful topology building with connections
        mock_connections = [
            {
                "device1": "R1",
                "device2": "R2",
                "interface1": "GigE0/0/0/0",
                "interface2": "GigE0/0/0/1",
            },
            {
                "device1": "R2",
                "device2": "R3",
                "interface1": "GigE0/0/0/2",
                "interface2": "GigE0/0/0/0",
            },
        ]
        topology_result = MockNetworkTopologyResult(
            status=OperationStatus.SUCCESS,
            error_response=None,
            data={"direct_connections": mock_connections},
        )
        mock_get_network_topology.return_value = topology_result

        # Act: Call get_topology_adjacency
        result = get_topology_adjacency("test-device")

        # Assert: Verify successful topology processing
        assert isinstance(result, NetworkOperationResult)
        assert result.status == OperationStatus.SUCCESS
        assert result.data == {}  # Still empty dict as per requirements
        assert result.error_response is None

        # Verify metadata shows connection count
        metadata = result.metadata
        assert metadata["scope"] == "network-wide"
        assert metadata["total_connections"] == 2
        assert (
            "Topology adjacency analysis complete with 2 connections"
            in metadata["message"]
        )

    @patch("src.collectors.topology.adjacency.get_device")
    @patch("src.collectors.topology.adjacency.get_network_topology")
    def test_topology_adjacency_network_topology_failure(
        self, mock_get_network_topology, mock_get_device
    ):
        """Test that get_topology_adjacency handles network topology failures properly."""
        # Arrange: Mock get_device to return the test device
        mock_get_device.return_value = self.device

        # Mock network topology failure without ErrorResponse
        topology_result = MockNetworkTopologyResult(
            status=OperationStatus.FAILED,
            error_response=None,  # No ErrorResponse, just failed status
        )
        mock_get_network_topology.return_value = topology_result

        # Act: Call get_topology_adjacency
        result = get_topology_adjacency("test-device")

        # Assert: Verify failure handling
        assert isinstance(result, NetworkOperationResult)
        assert result.status == OperationStatus.FAILED
        assert result.data == {}

        # Verify metadata provides context
        metadata = result.metadata
        assert metadata["scope"] == "network-wide"
        assert "Topology building failed:" in metadata["message"]

    @patch("src.collectors.topology.adjacency.get_device")
    @patch("src.collectors.topology.adjacency.get_network_topology")
    def test_topology_adjacency_unexpected_exception(
        self, mock_get_network_topology, mock_get_device
    ):
        """Test that get_topology_adjacency handles unexpected exceptions gracefully."""
        # Arrange: Mock get_device to return the test device
        mock_get_device.return_value = self.device

        # Mock get_network_topology to raise an exception
        mock_get_network_topology.side_effect = Exception("Unexpected error")

        # Act: Call get_topology_adjacency
        result = get_topology_adjacency("test-device")

        # Assert: Verify exception handling
        assert isinstance(result, NetworkOperationResult)
        assert result.status == OperationStatus.FAILED
        assert result.data == {}

        # Verify metadata provides context about the exception
        metadata = result.metadata
        assert metadata["scope"] == "network-wide"
        assert (
            "Unexpected error during topology adjacency analysis:"
            in metadata["message"]
        )
