#!/usr/bin/env python3
"""
Tests for validate command integration.

Tests that the validate command includes topology_adjacency function properly.
"""

from src.schemas.models import Device, NetworkOS
from src.cmd.commands.ops.validate import _run_collector_tests
from src.inventory.manager import InventoryManager


class TestValidateCommandIntegration:
    """Test suite for validate command integration."""

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

    def test_validate_command_includes_topology_adjacency(self):
        """Test that validate command includes topology_adjacency in test functions."""
        # This is a simple validation that the function is imported and available
        from src.cmd.commands.ops.validate import ip_adjacency_dump_cmd

        # Verify the function is callable
        assert callable(ip_adjacency_dump_cmd)

        # Verify it appears in the source code
        import inspect

        source = inspect.getsource(_run_collector_tests)
        assert "topology_adjacency" in source
        assert "ip_adjacency_dump_cmd" in source
