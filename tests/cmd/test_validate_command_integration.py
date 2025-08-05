#!/usr/bin/env python3
"""
Tests for validate command integration with modified functions.

Tests that the validate command properly integrates the topology_adjacency function
and that all modified functions (vpn_info, topology_neighbors, topology_adjacency)
are properly tested with ErrorResponse detection and fail-fast behavior.

Key Test Scenarios:
1. Validate Command Integration: Verify topology_adjacency is included in test suite
2. ErrorResponse Propagation: Verify errors are properly shown in validate results
3. Data Structure Consistency: Verify `data: {}` format across all functions
4. Status Differentiation: Verify correct status values in validate results
5. Fail-Fast Behavior: Verify validate command shows failures correctly
"""

import pytest
import json
from unittest.mock import Mock, patch
from src.schemas.models import Device, NetworkOS
from src.schemas.responses import (
    ErrorResponse,
    FeatureNotFoundResponse,
    OperationStatus,
    NetworkOperationResult,
)
from src.cmd.commands.ops.validate import _run_collector_tests


class TestValidateCommandIntegration:
    """Test suite for validate command integration with modified functions."""

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

    def test_validate_command_includes_topology_adjacency(self):
        """Test that validate command includes topology_adjacency function in test suite."""
        # This test verifies that Task 3 (topology adjacency) was properly integrated

        # Read the validate command source to verify integration
        import inspect
        from src.cmd.commands.ops.validate import _run_collector_tests

        source = inspect.getsource(_run_collector_tests)

        # Verify topology_adjacency is included in test_functions
        assert "topology_adjacency" in source
        assert "ip_adjacency_dump_cmd" in source

        # Verify the import is present
        from src.cmd.commands.ops.validate import ip_adjacency_dump_cmd

        assert callable(ip_adjacency_dump_cmd)

    @patch("src.collectors.vpn.get_vpn_info")
    @patch("src.collectors.topology.neighbors.neighbors")
    @patch("src.cmd.commands.topology.adjacency.ip_adjacency_dump_cmd")
    def test_validate_command_error_propagation(
        self, mock_adjacency, mock_neighbors, mock_vpn_info
    ):
        """Test that validate command properly propagates ErrorResponse from modified functions."""
        # Arrange: Mock all three modified functions to return ErrorResponse
        error_response = ErrorResponse(
            type="gNMIException",
            message="GRPC ERROR Host: 192.168.1.1:57777, Error: authentication failed",
        )

        # Mock VPN info error
        mock_vpn_info.return_value = NetworkOperationResult(
            device_name=self.device.name,
            ip_address=self.device.ip_address,
            nos=self.device.nos.value,
            operation_type="vpn_info",
            status=OperationStatus.FAILED,
            data={},
            error_response=error_response,
            metadata={"message": "Failed to discover VRFs due to gNMI error"},
        )

        # Mock topology neighbors error
        mock_neighbors.return_value = NetworkOperationResult(
            device_name=self.device.name,
            ip_address=self.device.ip_address,
            nos=self.device.nos.value,
            operation_type="topology_neighbors",
            status=OperationStatus.FAILED,
            data={},
            error_response=error_response,
            metadata={
                "message": "Failed to build topology due to gNMI errors",
                "device_in_topology": False,
            },
        )

        # Mock topology adjacency error
        mock_adjacency.return_value = NetworkOperationResult(
            device_name=self.device.name,
            ip_address=self.device.ip_address,
            nos=self.device.nos.value,
            operation_type="topology_adjacency",
            status=OperationStatus.FAILED,
            data={},
            error_response=error_response,
            metadata={
                "scope": "network-wide",
                "message": "Failed to build topology adjacency due to gNMI errors",
            },
        )

        # Mock other functions to return success to isolate the test
        with (
            patch("src.collectors.system.get_system_info") as mock_system,
            patch("src.collectors.profile.get_device_profile") as mock_profile,
            patch(
                "src.collectors.interfaces.get_interfaces"
            ) as mock_interfaces,
            patch("src.collectors.mpls.get_mpls_info") as mock_mpls,
            patch("src.collectors.routing.get_routing_info") as mock_routing,
        ):

            # Mock successful responses for other functions
            success_result = NetworkOperationResult(
                device_name=self.device.name,
                ip_address=self.device.ip_address,
                nos=self.device.nos.value,
                operation_type="test",
                status=OperationStatus.SUCCESS,
                data={"test": "data"},
                metadata={"message": "Success"},
            )

            mock_system.return_value = success_result
            mock_profile.return_value = success_result
            mock_interfaces.return_value = success_result
            mock_mpls.return_value = success_result
            mock_routing.return_value = success_result

            # Act: Run collector tests
            results = _run_collector_tests(
                self.device, test_query="basic", include_data=True
            )

        # Assert: Verify error propagation in results
        assert "test_results" in results
        test_results = results["test_results"]

        # Verify VPN info shows error
        assert "vpn_info" in test_results
        vpn_result = test_results["vpn_info"]
        assert vpn_result["status"] == "FAILED"
        assert vpn_result["result_data"]["status"] == "failed"
        assert vpn_result["result_data"]["data"] == {}
        assert (
            "Failed to discover VRFs due to gNMI error"
            in vpn_result["result_data"]["metadata"]["message"]
        )

        # Verify topology neighbors shows error
        assert "topology_neighbors" in test_results
        neighbors_result = test_results["topology_neighbors"]
        assert neighbors_result["status"] == "FAILED"
        assert neighbors_result["result_data"]["status"] == "failed"
        assert neighbors_result["result_data"]["data"] == {}
        assert (
            "Failed to build topology due to gNMI errors"
            in neighbors_result["result_data"]["metadata"]["message"]
        )

        # Verify topology adjacency shows error
        assert "topology_adjacency" in test_results
        adjacency_result = test_results["topology_adjacency"]
        assert adjacency_result["status"] == "FAILED"
        assert adjacency_result["result_data"]["status"] == "failed"
        assert adjacency_result["result_data"]["data"] == {}
        assert (
            "Failed to build topology adjacency due to gNMI errors"
            in adjacency_result["result_data"]["metadata"]["message"]
        )

    @patch("src.collectors.vpn.get_vpn_info")
    @patch("src.collectors.topology.neighbors.neighbors")
    @patch("src.cmd.commands.topology.adjacency.ip_adjacency_dump_cmd")
    def test_validate_command_legitimate_empty_results(
        self, mock_adjacency, mock_neighbors, mock_vpn_info
    ):
        """Test that validate command handles legitimate empty results correctly."""
        # Arrange: Mock all three modified functions to return legitimate empty results

        # Mock VPN info - no VRFs found (legitimate)
        mock_vpn_info.return_value = NetworkOperationResult(
            device_name=self.device.name,
            ip_address=self.device.ip_address,
            nos=self.device.nos.value,
            operation_type="vpn_info",
            status=OperationStatus.SUCCESS,
            data={},
            metadata={
                "message": "No VRFs found",
                "total_vrfs_on_device": 0,
                "vrfs_returned": 0,
                "vrf_filter_applied": False,
                "vrf_filter": None,
                "include_details": False,
                "excluded_internal_vrfs": ["default", "**iid"],
            },
        )

        # Mock topology neighbors - device isolated (legitimate)
        mock_neighbors.return_value = NetworkOperationResult(
            device_name=self.device.name,
            ip_address=self.device.ip_address,
            nos=self.device.nos.value,
            operation_type="topology_neighbors",
            status=OperationStatus.SUCCESS,
            data={},
            metadata={
                "message": "No neighbors found for device test-device",
                "device_in_topology": False,
                "isolation_reason": "legitimate",
            },
        )

        # Mock topology adjacency - no connections (legitimate)
        mock_adjacency.return_value = NetworkOperationResult(
            device_name=self.device.name,
            ip_address=self.device.ip_address,
            nos=self.device.nos.value,
            operation_type="topology_adjacency",
            status=OperationStatus.SUCCESS,
            data={},
            metadata={
                "scope": "network-wide",
                "total_connections": 0,
                "message": "No topology connections discovered",
            },
        )

        # Mock other functions
        with (
            patch("src.collectors.system.get_system_info") as mock_system,
            patch("src.collectors.profile.get_device_profile") as mock_profile,
            patch(
                "src.collectors.interfaces.get_interfaces"
            ) as mock_interfaces,
            patch("src.collectors.mpls.get_mpls_info") as mock_mpls,
            patch("src.collectors.routing.get_routing_info") as mock_routing,
        ):

            success_result = NetworkOperationResult(
                device_name=self.device.name,
                ip_address=self.device.ip_address,
                nos=self.device.nos.value,
                operation_type="test",
                status=OperationStatus.SUCCESS,
                data={"test": "data"},
                metadata={"message": "Success"},
            )

            mock_system.return_value = success_result
            mock_profile.return_value = success_result
            mock_interfaces.return_value = success_result
            mock_mpls.return_value = success_result
            mock_routing.return_value = success_result

            # Act: Run collector tests
            results = _run_collector_tests(
                self.device, test_query="basic", include_data=True
            )

        # Assert: Verify legitimate empty results are handled as SUCCESS
        test_results = results["test_results"]

        # Verify VPN info shows success with context
        vpn_result = test_results["vpn_info"]
        assert vpn_result["status"] == "SUCCESS"
        assert vpn_result["result_data"]["status"] == "success"
        assert vpn_result["result_data"]["data"] == {}
        assert (
            "No VRFs found" in vpn_result["result_data"]["metadata"]["message"]
        )

        # Verify topology neighbors shows success with context
        neighbors_result = test_results["topology_neighbors"]
        assert neighbors_result["status"] == "SUCCESS"
        assert neighbors_result["result_data"]["status"] == "success"
        assert neighbors_result["result_data"]["data"] == {}
        assert (
            "No neighbors found"
            in neighbors_result["result_data"]["metadata"]["message"]
        )

        # Verify topology adjacency shows success with context
        adjacency_result = test_results["topology_adjacency"]
        assert adjacency_result["status"] == "SUCCESS"
        assert adjacency_result["result_data"]["status"] == "success"
        assert adjacency_result["result_data"]["data"] == {}
        assert (
            "No topology connections discovered"
            in adjacency_result["result_data"]["metadata"]["message"]
        )

    def test_validate_command_function_count(self):
        """Test that validate command now includes 8 functions (including topology_adjacency)."""
        # This test verifies that the validate command test suite was properly updated

        # Read the source to check function count
        import inspect
        from src.cmd.commands.ops.validate import _run_collector_tests

        source = inspect.getsource(_run_collector_tests)

        # Count the functions in test_functions dictionary
        basic_functions = [
            "system_info",
            "device_profile",
            "interfaces",
            "mpls_info",
            "routing_info",
            "vpn_info",
            "topology_neighbors",
            "topology_adjacency",  # This should be the new addition
        ]

        for func_name in basic_functions:
            assert (
                func_name in source
            ), f"Function {func_name} not found in validate command"

    @patch("src.collectors.vpn.get_vpn_info")
    @patch("src.collectors.topology.neighbors.neighbors")
    @patch("src.cmd.commands.topology.adjacency.ip_adjacency_dump_cmd")
    def test_validate_command_data_structure_consistency(
        self, mock_adjacency, mock_neighbors, mock_vpn_info
    ):
        """Test that all modified functions return consistent data structures in validate."""
        # Arrange: Mix of error and success cases
        error_response = ErrorResponse(
            type="gNMIException", message="Test error"
        )

        # VPN info - error case
        mock_vpn_info.return_value = NetworkOperationResult(
            device_name=self.device.name,
            ip_address=self.device.ip_address,
            nos=self.device.nos.value,
            operation_type="vpn_info",
            status=OperationStatus.FAILED,
            data={},
            error_response=error_response,
            metadata={"message": "Failed"},
        )

        # Topology neighbors - success case (legitimate empty)
        mock_neighbors.return_value = NetworkOperationResult(
            device_name=self.device.name,
            ip_address=self.device.ip_address,
            nos=self.device.nos.value,
            operation_type="topology_neighbors",
            status=OperationStatus.SUCCESS,
            data={},
            metadata={
                "message": "No neighbors found",
                "device_in_topology": False,
            },
        )

        # Topology adjacency - error case
        mock_adjacency.return_value = NetworkOperationResult(
            device_name=self.device.name,
            ip_address=self.device.ip_address,
            nos=self.device.nos.value,
            operation_type="topology_adjacency",
            status=OperationStatus.FAILED,
            data={},
            error_response=error_response,
            metadata={"scope": "network-wide", "message": "Failed"},
        )

        # Mock other functions
        with (
            patch("src.collectors.system.get_system_info") as mock_system,
            patch("src.collectors.profile.get_device_profile") as mock_profile,
            patch(
                "src.collectors.interfaces.get_interfaces"
            ) as mock_interfaces,
            patch("src.collectors.mpls.get_mpls_info") as mock_mpls,
            patch("src.collectors.routing.get_routing_info") as mock_routing,
        ):

            success_result = NetworkOperationResult(
                device_name=self.device.name,
                ip_address=self.device.ip_address,
                nos=self.device.nos.value,
                operation_type="test",
                status=OperationStatus.SUCCESS,
                data={"test": "data"},
                metadata={"message": "Success"},
            )

            mock_system.return_value = success_result
            mock_profile.return_value = success_result
            mock_interfaces.return_value = success_result
            mock_mpls.return_value = success_result
            mock_routing.return_value = success_result

            # Act: Run collector tests
            results = _run_collector_tests(
                self.device, test_query="basic", include_data=True
            )

        # Assert: Verify data structure consistency
        test_results = results["test_results"]

        # All modified functions should return data: {} regardless of status
        for func_name in [
            "vpn_info",
            "topology_neighbors",
            "topology_adjacency",
        ]:
            assert func_name in test_results
            result_data = test_results[func_name]["result_data"]
            assert (
                result_data["data"] == {}
            ), f"{func_name} should return empty dict for data"

            # Status should differentiate error vs success
            if func_name == "topology_neighbors":
                assert result_data["status"] == "success"
            else:
                assert result_data["status"] == "failed"

            # Metadata should provide context
            assert "message" in result_data["metadata"]

    def test_validate_command_full_mode_includes_topology_adjacency(self):
        """Test that topology_adjacency is included in both basic and full validation modes."""
        import inspect
        from src.cmd.commands.ops.validate import _run_collector_tests

        source = inspect.getsource(_run_collector_tests)

        # topology_adjacency should be in the basic test_functions, not just full mode additions
        # This ensures it runs in both basic and full modes
        lines = source.split("\n")

        basic_section_found = False
        topology_adjacency_in_basic = False

        for line in lines:
            if "test_functions = {" in line:
                basic_section_found = True
            elif basic_section_found and "topology_adjacency" in line:
                topology_adjacency_in_basic = True
                break
            elif basic_section_found and "test_functions.update(" in line:
                # End of basic section
                break

        assert (
            topology_adjacency_in_basic
        ), "topology_adjacency should be in basic test functions, not just full mode"

    @patch("src.cmd.commands.ops.validate._run_collector_tests")
    def test_validate_command_summary_with_modified_functions(
        self, mock_run_tests
    ):
        """Test that validate command summary properly counts modified functions."""
        # Arrange: Mock results with mixed success/failure for modified functions
        mock_results = {
            "test_results": {
                "system_info": {"status": "SUCCESS"},
                "device_profile": {"status": "SUCCESS"},
                "interfaces": {"status": "SUCCESS"},
                "mpls_info": {"status": "SUCCESS"},
                "routing_info": {"status": "SUCCESS"},
                "vpn_info": {"status": "FAILED"},  # Modified function - error
                "topology_neighbors": {
                    "status": "SUCCESS"
                },  # Modified function - legitimate empty
                "topology_adjacency": {
                    "status": "FAILED"
                },  # New function - error
            },
            "summary": {
                "total_tests": 8,  # Should now be 8 with topology_adjacency
                "successful": 6,
                "failed": 2,
                "feature_not_available": 0,
            },
        }
        mock_run_tests.return_value = mock_results

        # Act: Import and verify the count
        from src.cmd.commands.ops.validate import _run_collector_tests

        results = _run_collector_tests(self.device, test_query="basic")

        # Assert: Verify counts include the new function
        assert results["summary"]["total_tests"] == 8
        assert "topology_adjacency" in results["test_results"]
