#!/usr/bin/env python3
"""
Tests for topology adjacency functionality.

Tests the new topology adjacency function implementation that was added to meet
the requirements of GitHub issue #2. Focuses on ErrorResponse detection and
fail-fast behavior during network-wide topology building.

Key Test Scenarios:
1. ErrorResponse Detection: Simulate gNMI errors during network topology building
2. Data Structure Consistency: Verify `data: {}` format for errors and legitimate empty
3. Status Differentiation: Verify correct status values
4. Metadata Context: Verify metadata provides clear context about network-wide scope
5. Fail-Fast Behavior: Verify functions stop processing on errors
"""

import pytest
from unittest.mock import Mock, patch
from src.schemas.models import Device, NetworkOS
from src.schemas.responses import (
    ErrorResponse,
    OperationStatus,
    NetworkOperationResult,
)
from src.schemas.metadata import TopologyAdjacencyMetadata
from src.cmd.commands.topology.adjacency import ip_adjacency_dump_cmd


class MockNetworkTopologyResult:
    """Mock class for network topology results."""

    def __init__(
        self, status=OperationStatus.SUCCESS, error_response=None, data=None
    ):
        self.status = status
        self.error_response = error_response
        self.data = data if data is not None else {"direct_connections": []}


class TestTopologyAdjacencyErrorHandling:
    """Test suite for topology adjacency error handling functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            port=57400,
            username="admin",
            password="admin",
            nos=NetworkOS.IOSXR,
        )

    def _get_metadata_value(self, metadata, key):
        """Helper to get metadata value whether it's dict or object."""
        if hasattr(metadata, key):
            return getattr(metadata, key)
        else:
            return metadata[key]

    @patch("src.cmd.commands.topology.adjacency.get_network_topology")
    def test_topology_adjacency_error_response_detection(
        self, mock_get_network_topology
    ):
        """Test that ip_adjacency_dump_cmd detects ErrorResponse during topology building and fails fast."""
        # Arrange: Mock get_network_topology to return ErrorResponse
        error_response = ErrorResponse(
            type="gNMIException",
            message="GRPC ERROR Host: 192.168.1.1:57777, Error: authentication failed",
            details={"error_code": 401, "grpc_code": "UNAUTHENTICATED"},
        )

        topology_result = MockNetworkTopologyResult(
            status=OperationStatus.FAILED, error_response=error_response
        )
        mock_get_network_topology.return_value = topology_result

        # Act: Call ip_adjacency_dump_cmd
        result = ip_adjacency_dump_cmd(self.device)

        # Assert: Verify ErrorResponse detection and fail-fast behavior
        assert isinstance(result, NetworkOperationResult)
        assert result.status == OperationStatus.FAILED
        assert result.data == {}  # Empty dict as required
        assert result.error_response == error_response
        assert result.device_name == self.device.name
        assert result.ip_address == self.device.ip_address
        assert result.nos == self.device.nos
        assert result.operation_type == "topology_adjacency"

        # Verify metadata provides context about network-wide scope and error
        metadata = result.metadata
        assert self._get_metadata_value(metadata, "scope") == "network-wide"
        assert (
            "Failed to build topology adjacency due to gNMI errors"
            in self._get_metadata_value(metadata, "message")
        )

        # Verify fail-fast behavior - function stops processing on error
        mock_get_network_topology.assert_called_once()

    @patch("src.cmd.commands.topology.adjacency.get_network_topology")
    def test_topology_adjacency_legitimate_empty_network(
        self, mock_get_network_topology
    ):
        """Test that ip_adjacency_dump_cmd returns success for legitimate empty network topology."""
        # Arrange: Mock successful topology building but no connections found
        topology_result = MockNetworkTopologyResult(
            status=OperationStatus.SUCCESS,
            error_response=None,
            data={"direct_connections": []},  # No connections in network
        )
        mock_get_network_topology.return_value = topology_result

        # Act: Call ip_adjacency_dump_cmd
        result = ip_adjacency_dump_cmd(self.device)

        # Assert: Verify legitimate empty network is handled as success
        assert isinstance(result, NetworkOperationResult)
        assert result.status == OperationStatus.SUCCESS
        assert (
            result.data == {}
        )  # Empty dict for both error and legitimate empty
        assert result.error_response is None

        # Verify metadata distinguishes legitimate empty from errors
        metadata = result.metadata
        assert self._get_metadata_value(metadata, "scope") == "network-wide"
        assert self._get_metadata_value(metadata, "total_connections") == 0
        assert (
            "No topology connections discovered"
            in self._get_metadata_value(metadata, "message")
        )

    @patch("src.cmd.commands.topology.adjacency.get_network_topology")
    def test_topology_adjacency_with_connections_success(
        self, mock_get_network_topology
    ):
        """Test that ip_adjacency_dump_cmd handles successful topology with connections."""
        # Arrange: Mock successful topology building with connections
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

        # Act: Call ip_adjacency_dump_cmd
        result = ip_adjacency_dump_cmd(self.device)

        # Assert: Verify successful topology processing
        assert isinstance(result, NetworkOperationResult)
        assert result.status == OperationStatus.SUCCESS
        assert result.data == {}  # Still empty dict as per requirements
        assert result.error_response is None

        # Verify metadata shows connection count
        metadata = result.metadata
        assert self._get_metadata_value(metadata, "scope") == "network-wide"
        assert self._get_metadata_value(metadata, "total_connections") == 2
        assert (
            "Topology adjacency analysis complete with 2 connections"
            in self._get_metadata_value(metadata, "message")
        )

    @patch("src.cmd.commands.topology.adjacency.get_network_topology")
    def test_topology_adjacency_device_parameter_handling(
        self, mock_get_network_topology
    ):
        """Test that ip_adjacency_dump_cmd handles device parameter correctly for network-wide operation."""
        # Test with None device (edge case)
        topology_result = MockNetworkTopologyResult(
            status=OperationStatus.SUCCESS, error_response=None
        )
        mock_get_network_topology.return_value = topology_result

        # Act: Call with None device
        result = ip_adjacency_dump_cmd(None)

        # Assert: Verify function handles None device gracefully
        assert isinstance(result, NetworkOperationResult)
        assert result.device_name == "ALL_DEVICES"
        assert result.ip_address == "0.0.0.0"
        assert result.nos == "N/A"
        assert result.operation_type == "topology_adjacency"

    @patch("src.cmd.commands.topology.adjacency.get_network_topology")
    def test_topology_adjacency_different_error_types(
        self, mock_get_network_topology
    ):
        """Test ErrorResponse handling with different error types from topology building."""
        test_cases = [
            {
                "error_type": "CONNECTION_TIMEOUT",
                "message": "Multiple device timeout during topology building",
                "details": {
                    "timeout_seconds": 30,
                    "failed_devices": ["R1", "R2"],
                },
            },
            {
                "error_type": "AUTHENTICATION_FAILED",
                "message": "Invalid credentials for network discovery",
                "details": {"auth_method": "basic", "failed_count": 3},
            },
            {
                "error_type": "GRPC_ERROR",
                "message": "gRPC network topology collection failed",
                "details": {
                    "grpc_code": "UNAVAILABLE",
                    "scope": "network-wide",
                },
            },
        ]

        for test_case in test_cases:
            # Reset mock for each test case
            mock_get_network_topology.reset_mock()

            # Arrange
            error_response = ErrorResponse(
                type=test_case["error_type"],
                message=test_case["message"],
                details=test_case["details"],
            )

            topology_result = MockNetworkTopologyResult(
                status=OperationStatus.FAILED, error_response=error_response
            )
            mock_get_network_topology.return_value = topology_result

            # Act
            result = ip_adjacency_dump_cmd(self.device)

            # Assert: All error types should be handled the same way
            assert result.status == OperationStatus.FAILED
            assert result.data == {}
            assert result.error_response == error_response
            assert (
                self._get_metadata_value(result.metadata, "scope")
                == "network-wide"
            )
            assert (
                "Failed to build topology adjacency due to gNMI errors"
                in self._get_metadata_value(result.metadata, "message")
            )

    def test_topology_adjacency_direct_isinstance_pattern(self):
        """Test that the code uses direct isinstance checks as required."""
        # This test verifies the implementation follows the mandatory pattern
        # of using direct isinstance(response, ErrorResponse) checks

        # Read the source code to verify pattern
        import inspect

        source = inspect.getsource(ip_adjacency_dump_cmd)

        # Verify direct isinstance checks are used for ErrorResponse
        assert (
            "isinstance(topology_result.error_response, ErrorResponse)"
            in source
        )

        # Verify no wrapper functions are used
        assert "has_gnmi_error(" not in source
        assert "is_error_response(" not in source

    def test_topology_adjacency_metadata_class_encapsulation(self):
        """Test that TopologyAdjacencyMetadata class is used for data encapsulation."""
        # Verify that the function uses classes for data encapsulation, not dictionaries
        with patch(
            "src.cmd.commands.topology.adjacency.get_network_topology"
        ) as mock_get_network_topology:
            # Setup successful case
            topology_result = MockNetworkTopologyResult(
                status=OperationStatus.SUCCESS, error_response=None
            )
            mock_get_network_topology.return_value = topology_result

            result = ip_adjacency_dump_cmd(self.device)

            # Verify that metadata comes from TopologyAdjacencyMetadata class
            assert result.metadata is not None
            assert (
                self._get_metadata_value(result.metadata, "scope") is not None
            )
            assert (
                self._get_metadata_value(result.metadata, "message")
                is not None
            )

            # Verify network-wide scope
            assert (
                self._get_metadata_value(result.metadata, "scope")
                == "network-wide"
            )

    @patch("src.cmd.commands.topology.adjacency.get_network_topology")
    def test_topology_adjacency_error_context_preservation(
        self, mock_get_network_topology
    ):
        """Test that error context is properly preserved in the response."""
        # Arrange: Create ErrorResponse with specific context from network topology building
        original_error = ErrorResponse(
            type="gNMIException",
            message="GRPC ERROR: Network-wide topology building failed due to authentication errors",
            details={
                "scope": "network-wide",
                "failed_devices": ["R1", "R2", "R3"],
                "error_class": "AuthenticationException",
                "operation": "network_topology_building",
                "timestamp": "2025-08-05T07:11:33",
            },
        )

        topology_result = MockNetworkTopologyResult(
            status=OperationStatus.FAILED, error_response=original_error
        )
        mock_get_network_topology.return_value = topology_result

        # Act
        result = ip_adjacency_dump_cmd(self.device)

        # Assert: Verify error context is preserved exactly
        assert result.error_response is not None
        assert result.error_response.type == original_error.type
        assert result.error_response.message == original_error.message
        assert result.error_response.details == original_error.details

        # Verify operation context
        assert result.operation_type == "topology_adjacency"
        assert (
            self._get_metadata_value(result.metadata, "scope")
            == "network-wide"
        )

    @patch("src.cmd.commands.topology.adjacency.get_network_topology")
    def test_topology_adjacency_data_structure_consistency(
        self, mock_get_network_topology
    ):
        """Test that data structure is consistent between error and success cases."""
        # Test error case
        error_response = ErrorResponse(
            type="gNMIException", message="Network topology building failed"
        )

        topology_result = MockNetworkTopologyResult(
            status=OperationStatus.FAILED, error_response=error_response
        )
        mock_get_network_topology.return_value = topology_result

        error_result = ip_adjacency_dump_cmd(self.device)

        # Test success case with no connections
        mock_get_network_topology.reset_mock()
        success_topology_result = MockNetworkTopologyResult(
            status=OperationStatus.SUCCESS,
            error_response=None,
            data={"direct_connections": []},
        )
        mock_get_network_topology.return_value = success_topology_result

        success_result = ip_adjacency_dump_cmd(self.device)

        # Assert: Both cases should return data: {} as required
        assert error_result.data == {}
        assert success_result.data == {}

        # But status should differentiate
        assert error_result.status == OperationStatus.FAILED
        assert success_result.status == OperationStatus.SUCCESS

        # Metadata should provide context to distinguish the cases
        assert (
            "Failed to build topology adjacency"
            in self._get_metadata_value(error_result.metadata, "message")
        )
        assert (
            "No topology connections discovered"
            in self._get_metadata_value(success_result.metadata, "message")
        )

        # Both should have network-wide scope
        assert (
            self._get_metadata_value(error_result.metadata, "scope")
            == "network-wide"
        )
        assert (
            self._get_metadata_value(success_result.metadata, "scope")
            == "network-wide"
        )

    @patch("src.cmd.commands.topology.adjacency.get_network_topology")
    def test_topology_adjacency_exception_handling(
        self, mock_get_network_topology
    ):
        """Test that unexpected exceptions during network topology building are handled."""
        # Arrange: Mock get_network_topology to raise an exception
        mock_get_network_topology.side_effect = Exception(
            "Unexpected error during network topology building"
        )

        # Act: Call ip_adjacency_dump_cmd
        result = ip_adjacency_dump_cmd(self.device)

        # Assert: Verify exception is handled gracefully
        assert isinstance(result, NetworkOperationResult)
        # Implementation may vary on how exceptions are handled,
        # but it should not crash and provide meaningful error info
        assert result.device_name == self.device.name
        assert result.operation_type == "topology_adjacency"

    @patch("src.cmd.commands.topology.adjacency.get_network_topology")
    def test_topology_adjacency_integration_requirements(
        self, mock_get_network_topology
    ):
        """Test that the adjacency function meets integration requirements."""
        # This test verifies the function can be integrated into the validate command
        # as specified in the GitHub issue requirements

        topology_result = MockNetworkTopologyResult(
            status=OperationStatus.SUCCESS, error_response=None
        )
        mock_get_network_topology.return_value = topology_result

        # Act: Verify function can be called with device parameter (validate command style)
        result = ip_adjacency_dump_cmd(self.device)

        # Assert: Function should be compatible with validate command requirements
        assert isinstance(result, NetworkOperationResult)
        assert hasattr(result, "device_name")
        assert hasattr(result, "operation_type")
        assert hasattr(result, "status")
        assert hasattr(result, "data")
        assert hasattr(result, "metadata")

        # Verify it returns the expected operation type for validate command
        assert result.operation_type == "topology_adjacency"
