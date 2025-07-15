#!/usr/bin/env python3
"""
Tests for the inventory manager module, focusing on get_device and list_devices functions.
These tests use the actual inventory files to ensure functionality works as expected.
"""

import os
import pytest
from pathlib import Path

from src.inventory.manager import InventoryManager
from src.schemas.models import Device


@pytest.fixture
def inventory_paths():
    """Provide paths to the inventory files used in tests."""
    # Test data paths
    return {
        "test_devices": os.path.join(
            Path(__file__).parent, "test_devices.json"
        ),
        "sandbox": os.path.join(Path(__file__).parent, "test_devices.json"),
        "hosts": os.path.join(Path(__file__).parent, "test_devices.json"),
        "empty": os.path.join(Path(__file__).parent, "empty_inventory.json"),
    }


class TestGetDevice:
    """Tests for the get_device function."""

    def test_get_device_from_test_devices(self, inventory_paths):
        """Test retrieving a device using a test inventory file."""
        # Reset before test
        InventoryManager._instance = None
        InventoryManager._devices = {}
        InventoryManager._initialized = False

        # Initialize with test data
        InventoryManager.initialize(inventory_paths["test_devices"])

        # Get a device that should exist
        device, success = InventoryManager.get_device("test-device-1")

        # Assertions for successful retrieval
        assert success
        assert isinstance(device, Device)
        assert device.name == "test-device-1"
        assert device.ip_address == "10.0.0.1"

        # Test getting a non-existent device
        error_result, error_success = InventoryManager.get_device(
            "non-existent"
        )

        # Assertions for error case
        assert not error_success
        assert isinstance(error_result, dict)
        assert "error" in error_result

    def test_get_device_from_sandbox(self, inventory_paths):
        """Test retrieving a device from the test_devices.json file."""
        # Reset before test
        InventoryManager._instance = None
        InventoryManager._devices = {}
        InventoryManager._initialized = False

        # Initialize with sandbox data
        InventoryManager.initialize(inventory_paths["sandbox"])

        # Get the test device
        device, success = InventoryManager.get_device("test-device-1")

        # Assertions
        assert success
        assert isinstance(device, Device)
        assert device.name == "test-device-1"
        assert device.ip_address == "10.0.0.1"
        assert device.port == 57777

    def test_get_device_from_hosts(self, inventory_paths):
        """Test retrieving a device from the test_devices.json file."""
        # Reset before test
        InventoryManager._instance = None
        InventoryManager._devices = {}
        InventoryManager._initialized = False

        # Initialize with hosts data
        InventoryManager.initialize(inventory_paths["hosts"])

        # Get one of the devices from test_devices.json
        device, success = InventoryManager.get_device("test-device-2")

        # Assertions
        assert success
        assert isinstance(device, Device)
        assert device.name == "test-device-2"
        assert device.ip_address == "10.0.0.2"
        assert device.port == 57777
        assert device.username == "test_user"


class TestListDevices:
    """Tests for the list_devices function."""

    def test_list_devices_from_test_devices(self, inventory_paths):
        """Test listing devices from the test inventory file."""
        # Reset before test
        InventoryManager._instance = None
        InventoryManager._devices = {}
        InventoryManager._initialized = False

        # Initialize with test data
        InventoryManager.initialize(inventory_paths["test_devices"])

        # Get the device list
        result = InventoryManager.list_devices()

        # Assertions
        assert isinstance(result, dict)
        assert "devices" in result
        assert len(result["devices"]) == 2

        # Check specific devices in the list
        device_names = [d["name"] for d in result["devices"]]
        assert "test-device-1" in device_names
        assert "test-device-2" in device_names

    def test_list_devices_from_sandbox(self, inventory_paths):
        """Test listing devices from the test_devices.json file."""
        # Reset before test
        InventoryManager._instance = None
        InventoryManager._devices = {}
        InventoryManager._initialized = False

        InventoryManager.initialize(inventory_paths["sandbox"])

        # Get the device list
        result = InventoryManager.list_devices()

        # Assertions
        assert isinstance(result, dict)
        assert "devices" in result
        assert len(result["devices"]) == 2

        # Check that test devices are in the list
        device_names = [d["name"] for d in result["devices"]]
        assert "test-device-1" in device_names
        assert "test-device-2" in device_names

    def test_list_devices_from_hosts(self, inventory_paths):
        """Test listing devices from the test_devices.json file."""
        # Reset before test
        InventoryManager._instance = None
        InventoryManager._devices = {}
        InventoryManager._initialized = False

        # Initialize with hosts data
        InventoryManager.initialize(inventory_paths["hosts"])

        # Get the device list
        result = InventoryManager.list_devices()

        # Assertions
        assert isinstance(result, dict)
        assert "devices" in result
        assert len(result["devices"]) == 2

        # Check that expected devices are in the list
        device_names = [d["name"] for d in result["devices"]]
        assert "test-device-1" in device_names
        assert "test-device-2" in device_names

    def test_list_devices_from_empty_inventory(self, inventory_paths):
        """Test listing devices from an empty inventory file."""
        # Reset before test
        InventoryManager._instance = None
        InventoryManager._devices = {}
        InventoryManager._initialized = False

        # Initialize with empty inventory
        InventoryManager.initialize(inventory_paths["empty"])

        # Get the device list
        result = InventoryManager.list_devices()

        # Assertions
        assert isinstance(result, dict)
        assert "devices" in result
        assert len(result["devices"]) == 0
