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
    """Return the path to the test_devices.json file."""
    return os.path.join(Path(__file__).parent, "test_devices.json")


@pytest.fixture
def initialize_hosts(reset_inventory_manager, hosts_file):
    """Initialize inventory manager with test_devices.json."""
    InventoryManager.initialize(hosts_file)
    return hosts_file


class TestHostsInventory:
    """Test cases for the inventory manager using the test_devices.json file."""

    def test_get_device_from_hosts(self, initialize_hosts):
        """Test retrieving devices from the test_devices.json file."""
        # Test getting a device that should exist in test_devices.json
        device, success = InventoryManager.get_device("test-device-1")

        # Assertions
        assert success, "Should successfully retrieve test-device-1 device"
        assert device.ip_address == "10.0.0.1"
        assert device.port == 57777
        assert device.nos == "iosxr"
        assert device.username == "test_user"
        assert device.password == "test_pass"

    def test_get_invalid_device_from_hosts(self, initialize_hosts):
        """Test retrieving non-existent device from test_devices.json."""
        result, success = InventoryManager.get_device("non-existent-router")

        # Assertions
        assert not success
        assert "error" in result
        assert "non-existent-router" in result["error"]

    def test_list_devices_from_hosts(self, initialize_hosts):
        """Test listing all devices from test_devices.json."""
        # Get list of devices
        result = InventoryManager.list_devices()

        # Assertions
        assert "devices" in result
        # test_devices.json should have 2 devices
        assert len(result["devices"]) == 2

        # Check that test-device-1 and test-device-2 exist in the device list
        device_names = [d["name"] for d in result["devices"]]
        assert "test-device-1" in device_names
        assert "test-device-2" in device_names

        # Verify some specific device details
        devices = {d["name"]: d for d in result["devices"]}

        # Check test-device-2
        test_device_2 = devices["test-device-2"]
        assert test_device_2["ip_address"] == "10.0.0.2"
        assert test_device_2["port"] == 57777
        assert test_device_2["nos"] == "iosxr"
