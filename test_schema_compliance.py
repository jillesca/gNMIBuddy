#!/usr/bin/env python3
"""
Test script to verify that the inventory functions return data
that complies with the defined TypedDict schemas.
"""

from src.inventory.models import (
    DeviceListResult,
    DeviceErrorResult,
    DeviceInfo,
)
from src.inventory import list_available_devices, get_device


def test_device_list_result_compliance():
    """Test that list_available_devices returns DeviceListResult-compliant data."""
    result = list_available_devices()

    # Check that result has the correct structure
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "devices" in result, "Result should contain 'devices' key"
    assert isinstance(result["devices"], list), "devices should be a list"

    # Check that each device has the correct DeviceInfo structure
    for device in result["devices"]:
        assert isinstance(device, dict), "Each device should be a dictionary"
        assert "name" in device, "Device should have 'name' field"
        assert "ip_address" in device, "Device should have 'ip_address' field"
        assert "port" in device, "Device should have 'port' field"
        assert "nos" in device, "Device should have 'nos' field"

        assert isinstance(device["name"], str), "name should be a string"
        assert isinstance(
            device["ip_address"], str
        ), "ip_address should be a string"
        assert isinstance(device["port"], int), "port should be an integer"
        assert isinstance(device["nos"], str), "nos should be a string"

    print(
        f"✓ DeviceListResult compliance test passed. Found {len(result['devices'])} devices."
    )


def test_device_error_result_compliance():
    """Test that get_device returns DeviceErrorResult-compliant data for errors."""
    # Try to get a non-existent device
    result, success = get_device("non_existent_device")

    if not success:
        # Check that error result has the correct structure
        assert isinstance(result, dict), "Error result should be a dictionary"
        assert "error" in result, "Error result should contain 'error' key"
        assert isinstance(result["error"], str), "error should be a string"
        print("✓ DeviceErrorResult compliance test passed.")
    else:
        print("⚠ Could not test error case - device was found unexpectedly.")


if __name__ == "__main__":
    print("Testing schema compliance for inventory functions...")

    try:
        test_device_list_result_compliance()
        test_device_error_result_compliance()
        print("\n✅ All schema compliance tests passed!")
    except Exception as e:
        print(f"\n❌ Schema compliance test failed: {e}")
        exit(1)
