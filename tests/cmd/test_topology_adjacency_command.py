#!/usr/bin/env python3
"""
Tests for topology adjacency command functionality.

Tests that the command properly delegates to the collector.
"""

from unittest.mock import patch
from src.schemas.models import Device, NetworkOS
from src.schemas.responses import (
    OperationStatus,
    NetworkOperationResult,
)
from src.inventory.manager import InventoryManager

from src.cmd.commands.topology.adjacency import ip_adjacency_dump_cmd


class TestTopologyAdjacencyCommand:
    """Test suite for topology adjacency command functionality."""

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

    @patch("src.collectors.topology.adjacency.get_topology_adjacency")
    def test_command_delegates_to_collector(self, mock_collector):
        """Test that ip_adjacency_dump_cmd delegates to the collector properly."""
        # Arrange: Mock the collector to return a success result
        expected_result = NetworkOperationResult(
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
        mock_collector.return_value = expected_result

        # Act: Call the command function
        result = ip_adjacency_dump_cmd(self.device)

        # Assert: Verify the command delegates to collector with device name
        mock_collector.assert_called_once_with(self.device.name)
        assert result == expected_result
