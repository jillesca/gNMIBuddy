#!/usr/bin/env python3
"""
Tests for the inventory manager module using hosts.json.
Provides additional coverage focusing on the real-world hosts.json file.
"""

import os
import pytest
from pathlib import Path

from src.inventory.manager import InventoryManager


@pytest.fixture
def reset_inventory_manager():
    """Reset the InventoryManager singleton between tests."""
    # Reset before test
    InventoryManager._instance = None
    InventoryManager._devices = {}
    InventoryManager._initialized = False

    # Run the test
    yield

    # Reset after test
    InventoryManager._instance = None
    InventoryManager._devices = {}
    InventoryManager._initialized = False


@pytest.fixture
def hosts_file():
    """Return the path to the hosts.json file."""
    project_root = Path(__file__).parent.parent.parent
    return os.path.join(project_root, "hosts.json")


@pytest.fixture
def initialize_hosts(reset_inventory_manager, hosts_file):
    """Initialize inventory manager with hosts.json."""
    InventoryManager.initialize(hosts_file)
    return hosts_file


class TestHostsInventory:
    """Test cases for the inventory manager using the hosts.json file."""

    def test_get_device_from_hosts(self, initialize_hosts):
        """Test retrieving devices from the hosts.json file."""
        # Test getting a device that should exist in hosts.json
        device, success = InventoryManager.get_device("xrd-1")

        # Assertions
        assert success, "Should successfully retrieve xrd-1 device"
        assert device.ip_address == "198.18.158.16"
        assert device.port == 57777
        assert device.nos == "iosxr"
        assert device.username == "admin"
        assert device.password == "C1sco123"

    def test_get_invalid_device_from_hosts(self, initialize_hosts):
        """Test retrieving non-existent device from hosts.json."""
        result, success = InventoryManager.get_device("non-existent-router")

        # Assertions
        assert not success
        assert "error" in result
        assert "non-existent-router" in result["error"]

    def test_list_devices_from_hosts(self, initialize_hosts):
        """Test listing all devices from hosts.json."""
        # Get list of devices
        result = InventoryManager.list_devices()

        # Assertions
        assert "devices" in result
        # hosts.json should have multiple devices
        assert len(result["devices"]) >= 10

        # Check that xrd-1 through xrd-10 exist in the device list
        device_names = [d["name"] for d in result["devices"]]
        for i in range(1, 11):
            assert f"xrd-{i}" in device_names

        # Verify some specific device details
        devices = {d["name"]: d for d in result["devices"]}

        # Check xrd-5
        xrd5 = devices["xrd-5"]
        assert xrd5["ip_address"] == "198.18.158.20"
        assert xrd5["port"] == 57777
        assert xrd5["nos"] == "iosxr"
