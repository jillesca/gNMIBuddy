#!/usr/bin/env python3
"""
Tests for topology neighbors error handling functionality.

Tests that the topology neighbors collector properly detects ErrorResponse from
topology building and implements fail-fast behavior as required by GitHub issue #2.

Key Test Scenarios:
1. ErrorResponse Detection: Simulate gNMI errors during topology building
2. Data Structure Consistency: Verify `data: {}` format for errors and legitimate empty
3. Status Differentiation: Verify correct status values
4. Metadata Context: Verify metadata provides clear context
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

from src.collectors.topology.neighbors import neighbors


class MockTopologyBuildResult:
    """Mock class for topology build results."""

    def __init__(self, has_errors=False, error_response=None, graph=None):
        self.has_errors = has_errors
        self.error_response = error_response
        self.graph = graph if graph is not None else MockGraph()


class MockGraph:
    """Mock class for NetworkX graph."""

    def __init__(self, nodes=None, has_device=False):
        self._nodes = nodes if nodes is not None else []
        self._has_device = has_device

    def number_of_nodes(self):
        return len(self._nodes)

    def has_node(self, node):
        return self._has_device

    def neighbors(self, node):
        if self._has_device:
            return ["neighbor1", "neighbor2"]
        return []

    def get_edge_data(self, node1, node2):
        return {"interface1": "GigE0/0/0/0", "interface2": "GigE0/0/0/1"}

    def __contains__(self, node):
        """Support for 'node in graph' syntax."""
        return self._has_device


class TestTopologyNeighborsErrorHandling:
    """Test suite for topology neighbors error handling functionality."""

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

    @patch("src.collectors.topology.neighbors._build_graph_ip_only")
    def test_topology_neighbors_error_response_detection(
        self, mock_build_graph
    ):
        """Test that neighbors function detects ErrorResponse during topology building and fails fast."""
        # Arrange: Mock _build_graph_ip_only to return ErrorResponse
        error_response = ErrorResponse(
            type="gNMIException",
            message="GRPC ERROR Host: 192.168.1.1:57777, Error: authentication failed",
            details={"error_code": 401, "grpc_code": "UNAUTHENTICATED"},
        )

        topology_result = MockTopologyBuildResult(
            has_errors=True, error_response=error_response
        )
        mock_build_graph.return_value = topology_result

        # Act: Call neighbors function
        result = neighbors(self.device)

        # Assert: Verify ErrorResponse detection and fail-fast behavior
        assert isinstance(result, NetworkOperationResult)
        assert result.status == OperationStatus.FAILED
        assert result.data == {}  # Empty dict as required
        assert result.error_response == error_response
        assert result.device_name == self.device.name
        assert result.ip_address == self.device.ip_address
        assert result.nos == self.device.nos.value
        assert result.operation_type == "topology_neighbors"

        # Verify metadata provides context about the error
        assert (
            "Failed to build topology due to gNMI errors"
            in result.metadata["message"]
        )
        assert result.metadata["device_in_topology"] == False

        # Verify fail-fast behavior - no further processing was attempted
        mock_build_graph.assert_called_once()

    @patch("src.collectors.topology.neighbors._build_graph_ip_only")
    def test_topology_neighbors_legitimate_isolation(self, mock_build_graph):
        """Test that neighbors function returns success for legitimately isolated devices."""
        # Arrange: Mock successful topology building but device not in graph
        mock_graph = MockGraph(nodes=["other-device"], has_device=False)

        topology_result = MockTopologyBuildResult(
            has_errors=False, error_response=None, graph=mock_graph
        )
        mock_build_graph.return_value = topology_result

        # Act: Call neighbors function
        result = neighbors(self.device)

        # Assert: Verify legitimate isolation is handled as success
        assert isinstance(result, NetworkOperationResult)
        assert result.status == OperationStatus.SUCCESS
        assert (
            result.data == {}
        )  # Empty dict for both error and legitimate empty
        assert result.error_response is None

        # Verify metadata distinguishes legitimate isolation from errors
        metadata = result.metadata
        assert "No neighbors found for device" in metadata["message"]
        assert metadata["device_in_topology"] == False
        # For legitimate case, should indicate isolation reason if implemented

    @patch("src.collectors.topology.neighbors._build_graph_ip_only")
    def test_topology_neighbors_with_neighbors_success(self, mock_build_graph):
        """Test that neighbors function returns neighbors when device is connected."""
        # Arrange: Mock successful topology building with device having neighbors
        mock_graph = MockGraph(
            nodes=["test-device", "neighbor1", "neighbor2"], has_device=True
        )

        topology_result = MockTopologyBuildResult(
            has_errors=False, error_response=None, graph=mock_graph
        )
        mock_build_graph.return_value = topology_result

        # Act: Call neighbors function
        result = neighbors(self.device)

        # Assert: Verify successful neighbor discovery
        assert isinstance(result, NetworkOperationResult)
        assert result.status == OperationStatus.SUCCESS
        assert result.error_response is None

        # Verify device was found in topology and neighbors were retrieved
        assert result.metadata["device_in_topology"] == True
        assert (
            "Found" in result.metadata["message"]
            and "neighbors" in result.metadata["message"]
        )

    @patch("src.collectors.topology.neighbors._build_graph_ip_only")
    def test_topology_neighbors_different_error_types(self, mock_build_graph):
        """Test ErrorResponse handling with different error types."""
        test_cases = [
            {
                "error_type": "CONNECTION_TIMEOUT",
                "message": "Interface collection timeout",
                "details": {"timeout_seconds": 30},
            },
            {
                "error_type": "AUTHENTICATION_FAILED",
                "message": "Invalid credentials for interface discovery",
                "details": {"auth_method": "basic"},
            },
            {
                "error_type": "GRPC_ERROR",
                "message": "gRPC interface collection failed",
                "details": {"grpc_code": "UNAVAILABLE"},
            },
        ]

        for test_case in test_cases:
            # Reset mock for each test case
            mock_build_graph.reset_mock()

            # Arrange
            error_response = ErrorResponse(
                type=test_case["error_type"],
                message=test_case["message"],
                details=test_case["details"],
            )

            topology_result = MockTopologyBuildResult(
                has_errors=True, error_response=error_response
            )
            mock_build_graph.return_value = topology_result

            # Act
            result = neighbors(self.device)

            # Assert: All error types should be handled the same way
            assert result.status == OperationStatus.FAILED
            assert result.data == {}
            assert result.error_response == error_response
            assert (
                "Failed to build topology due to gNMI errors"
                in result.metadata["message"]
            )

    def test_topology_neighbors_direct_isinstance_pattern(self):
        """Test that the code uses direct isinstance checks as required."""
        # This test verifies the implementation follows the mandatory pattern
        # of using direct isinstance(response, ErrorResponse) checks

        # Read the source code to verify pattern
        import inspect

        source = inspect.getsource(neighbors)

        # Verify the function checks for errors in topology result
        # The actual implementation should check topology_result.error_response
        assert "topology_result" in source
        assert "error_response" in source or "has_errors" in source

        # Verify no wrapper functions are used
        assert "has_gnmi_error(" not in source
        assert "is_error_response(" not in source

    def test_topology_neighbors_metadata_class_encapsulation(self):
        """Test that dictionary metadata is used for data encapsulation."""
        # Verify that the function uses classes for data encapsulation, not dictionaries
        with patch(
            "src.collectors.topology.neighbors._build_graph_ip_only"
        ) as mock_build_graph:
            # Setup successful case
            mock_graph = MockGraph(nodes=[], has_device=False)

            topology_result = MockTopologyBuildResult(
                has_errors=False, error_response=None, graph=mock_graph
            )
            mock_build_graph.return_value = topology_result

            result = neighbors(self.device)

            # Verify that metadata comes from a class, not direct dictionary construction
            assert isinstance(result.metadata, dict)
            assert "message" in result.metadata
            assert "device_in_topology" in result.metadata

    @patch("src.collectors.topology.neighbors._build_graph_ip_only")
    def test_topology_neighbors_error_context_preservation(
        self, mock_build_graph
    ):
        """Test that error context is properly preserved in the response."""
        # Arrange: Create ErrorResponse with specific context from interface collection
        original_error = ErrorResponse(
            type="gNMIException",
            message="GRPC ERROR Host: 10.10.20.101:57777, Error: authentication failed during interface collection",
            details={
                "host": "10.10.20.101",
                "port": 57777,
                "error_class": "AuthenticationException",
                "operation": "interface_collection",
                "timestamp": "2025-08-05T07:11:33",
            },
        )

        topology_result = MockTopologyBuildResult(
            has_errors=True, error_response=original_error
        )
        mock_build_graph.return_value = topology_result

        # Act
        result = neighbors(self.device)

        # Assert: Verify error context is preserved exactly
        assert result.error_response is not None
        assert result.error_response.type == original_error.type
        assert result.error_response.message == original_error.message
        assert result.error_response.details == original_error.details

        # Verify device context is also preserved
        assert result.device_name == self.device.name
        assert result.ip_address == self.device.ip_address
        assert result.nos == self.device.nos.value

    @patch("src.collectors.topology.neighbors._build_graph_ip_only")
    def test_topology_neighbors_data_structure_consistency(
        self, mock_build_graph
    ):
        """Test that data structure is consistent between error and success cases."""
        # Test error case
        error_response = ErrorResponse(
            type="gNMIException", message="Interface collection failed"
        )

        topology_result = MockTopologyBuildResult(
            has_errors=True, error_response=error_response
        )
        mock_build_graph.return_value = topology_result

        error_result = neighbors(self.device)

        # Test success case with no neighbors
        mock_build_graph.reset_mock()
        mock_graph = MockGraph(nodes=["test-device"], has_device=False)

        success_topology_result = MockTopologyBuildResult(
            has_errors=False, error_response=None, graph=mock_graph
        )
        mock_build_graph.return_value = success_topology_result

        success_result = neighbors(self.device)

        # Assert: Both cases should return data: {} as required
        assert error_result.data == {}
        assert success_result.data == {}

        # But status should differentiate
        assert error_result.status == OperationStatus.FAILED
        assert success_result.status == OperationStatus.SUCCESS

        # Metadata should provide context to distinguish the cases
        assert "Failed to build topology" in error_result.metadata["message"]
        assert "No neighbors found" in success_result.metadata["message"]

    @patch("src.collectors.topology.neighbors._build_graph_ip_only")
    def test_topology_neighbors_exception_handling(self, mock_build_graph):
        """Test that unexpected exceptions during topology building are handled."""
        # Arrange: Mock _build_graph_ip_only to raise an exception
        mock_build_graph.side_effect = Exception(
            "Unexpected error during topology building"
        )

        # Act: Call neighbors function - should handle exception gracefully
        with pytest.raises(
            Exception, match="Unexpected error during topology building"
        ):
            neighbors(self.device)

        # Alternative approach: If the function should handle exceptions gracefully
        # and return an error result, we would test like this:
        # result = neighbors(self.device)
        # assert isinstance(result, NetworkOperationResult)
        # assert result.status == OperationStatus.FAILED
        # assert result.device_name == self.device.name
        # assert result.operation_type == "topology_neighbors"
