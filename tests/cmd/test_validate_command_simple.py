#!/usr/bin/env python3
"""
Tests for validate command integration.

Tests that the validate command includes topology_adjacency function properly.
"""

from src.schemas.models import Device, NetworkOS
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
