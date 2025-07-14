#!/usr/bin/env python3
"""
Tests for the inventory manager module.
Focuses on testing the get_device and list_devices functions.
"""

import os
import unittest
from unittest.mock import patch

from src.inventory.manager import InventoryManager
from src.schemas.models import Device


class TestInventoryManager(unittest.TestCase):
    """Test cases for the inventory manager module."""

    def setUp(self):
        """Set up test environment before each test."""
        # Reset the singleton instance and its state
        InventoryManager._instance = None
        InventoryManager._devices = {}
        InventoryManager._initialized = False

    def test_get_device_with_valid_device(self):
        """Test retrieving a valid device by name."""
        # Initialize with test inventory
        test_file = os.path.join(
            os.path.dirname(__file__), "test_devices.json"
        )
        InventoryManager.initialize(test_file)

        # Test getting an existing device
        device, success = InventoryManager.get_device("test-device-1")

        # Assertions
        self.assertTrue(success)
        self.assertIsInstance(device, Device)
        self.assertEqual(device.name, "test-device-1")
        self.assertEqual(device.ip_address, "10.0.0.1")
        self.assertEqual(device.port, 57777)
        self.assertEqual(device.nos, "iosxr")
        self.assertEqual(device.username, "test_user")
        self.assertEqual(device.password, "test_pass")

    def test_get_device_with_invalid_device(self):
        """Test retrieving a non-existent device by name."""
        # Initialize with test inventory
        test_file = os.path.join(
            os.path.dirname(__file__), "test_devices.json"
        )
        InventoryManager.initialize(test_file)

        # Test getting a non-existent device
        result, success = InventoryManager.get_device("non-existent-device")

        # Assertions
        self.assertFalse(success)
        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        self.assertIn("non-existent-device", result["error"])

    def test_list_devices_with_populated_inventory(self):
        """Test listing devices with a populated inventory."""
        # Initialize with test inventory
        test_file = os.path.join(
            os.path.dirname(__file__), "test_devices.json"
        )
        InventoryManager.initialize(test_file)

        # Get the device list
        result = InventoryManager.list_devices()

        # Assertions
        self.assertIsInstance(result, dict)
        self.assertIn("devices", result)
        self.assertEqual(len(result["devices"]), 2)

        # Check specific devices in the list
        devices = {d["name"]: d for d in result["devices"]}
        self.assertIn("test-device-1", devices)
        self.assertIn("test-device-2", devices)

        # Verify device properties
        device1 = devices["test-device-1"]
        self.assertEqual(device1["ip_address"], "10.0.0.1")
        self.assertEqual(device1["port"], 57777)
        self.assertEqual(device1["nos"], "iosxr")

    def test_list_devices_with_empty_inventory(self):
        """Test listing devices with an empty inventory."""
        # Initialize with empty inventory
        empty_file = os.path.join(
            os.path.dirname(__file__), "empty_inventory.json"
        )
        InventoryManager.initialize(empty_file)

        # Get the device list
        result = InventoryManager.list_devices()

        # Assertions
        self.assertIsInstance(result, dict)
        self.assertIn("devices", result)
        self.assertEqual(len(result["devices"]), 0)

    def test_inventory_initialization_with_specific_file(self):
        """Test initializing inventory with a specific file path."""
        # Initialize with test_devices file
        test_file = os.path.join(
            os.path.dirname(__file__), "test_devices.json"
        )
        InventoryManager.initialize(test_file)

        # Verify initialization with test data
        instance = InventoryManager.get_instance()
        self.assertTrue(instance.is_initialized())

        # Check if we can get the first test device
        device, success = InventoryManager.get_device("test-device-1")
        self.assertTrue(success)
        self.assertEqual(device.ip_address, "10.0.0.1")


@patch("src.inventory.manager.InventoryManager.initialize")
class TestAutoInitialization(unittest.TestCase):
    """Tests for auto-initialization with proper mocking."""

    def setUp(self):
        """Set up test environment before each test."""
        # Reset the singleton instance and its state
        InventoryManager._instance = None
        InventoryManager._devices = {}
        InventoryManager._initialized = False

    def test_inventory_initialization_from_sandbox_file(self, mock_initialize):
        """Test initializing inventory without specifying a path."""
        # Setup the mocked devices
        test_device1 = Device(
            name="test-device-1",
            ip_address="10.0.0.1",
            port=57777,
            nos="iosxr",
            username="test_user",
            password="test_pass",
        )
        test_device2 = Device(
            name="test-device-2",
            ip_address="10.0.0.2",
            port=57777,
            nos="iosxr",
            username="test_user",
            password="test_pass",
        )

        # Setup the mock initialization to set our test devices
        def side_effect(*args, **kwargs):
            instance = InventoryManager.get_instance()
            instance._devices = {
                "test-device-1": test_device1,
                "test-device-2": test_device2,
            }
            instance._initialized = True

        mock_initialize.side_effect = side_effect

        # Initialize without specifying a path
        InventoryManager.initialize()

        # Verify mock was called
        mock_initialize.assert_called_once()

        # Verify initialization with our test data
        instance = InventoryManager.get_instance()
        self.assertTrue(instance.is_initialized())

        # We should have exactly 2 devices
        devices = instance.get_devices()
        self.assertEqual(len(devices), 2)
        self.assertIn("test-device-1", devices)
        self.assertIn("test-device-2", devices)

    def test_get_device_auto_initializes(self, mock_initialize):
        """Test that get_device auto-initializes if not already initialized."""
        # Setup the mocked device
        test_device = Device(
            name="test-device-1",
            ip_address="10.0.0.1",
            port=57777,
            nos="iosxr",
            username="test_user",
            password="test_pass",
        )

        # Setup the mock initialization to set our test device
        def side_effect(*args, **kwargs):
            instance = InventoryManager.get_instance()
            instance._devices = {"test-device-1": test_device}
            instance._initialized = True

        mock_initialize.side_effect = side_effect

        # Call get_device without initializing first
        device, success = InventoryManager.get_device("test-device-1")

        # Verify that initialize was called
        mock_initialize.assert_called_once()

        # Should find the device
        self.assertTrue(success)
        self.assertEqual(device.name, "test-device-1")

        # Verify initialization happened
        instance = InventoryManager.get_instance()
        self.assertTrue(instance.is_initialized())

    def test_list_devices_auto_initializes(self, mock_initialize):
        """Test that list_devices auto-initializes if not already initialized."""
        # Setup the mocked device
        test_device = Device(
            name="test-device-1",
            ip_address="10.0.0.1",
            port=57777,
            nos="iosxr",
            username="test_user",
            password="test_pass",
        )

        # Setup the mock initialization to set our test device
        def side_effect(*args, **kwargs):
            instance = InventoryManager.get_instance()
            instance._devices = {"test-device-1": test_device}
            instance._initialized = True

        mock_initialize.side_effect = side_effect

        # Call list_devices without initializing first
        result = InventoryManager.list_devices()

        # Verify that initialize was called
        mock_initialize.assert_called_once()

        # Should list our device
        self.assertEqual(len(result["devices"]), 1)
        self.assertEqual(result["devices"][0]["name"], "test-device-1")

        # Verify initialization happened
        instance = InventoryManager.get_instance()
        self.assertTrue(instance.is_initialized())


if __name__ == "__main__":
    unittest.main()
