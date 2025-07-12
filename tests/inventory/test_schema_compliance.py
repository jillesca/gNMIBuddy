#!/usr/bin/env python3
"""
Test script to verify that the inventory functions return data
with the expected structure and behavior.
"""

from src.inventory import list_available_devices, get_device


def test_device_list_result_compliance():
    """Test that list_available_devices returns properly structured data."""
    result = list_available_devices()

    # Check that result has the correct structure
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "devices" in result, "Result should contain 'devices' key"
    assert isinstance(result["devices"], list), "devices should be a list"

    # Check that each device has the correct structure (non-sensitive fields only)
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

        # Verify no sensitive information is exposed
        assert (
            "username" not in device
        ), "Device list should not contain sensitive 'username'"
        assert (
            "password" not in device
        ), "Device list should not contain sensitive 'password'"

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
        assert (
            "device_info" in result
        ), "Error result should contain 'device_info' key"
        assert isinstance(result["error"], str), "error should be a string"
        assert result["device_info"] is None or isinstance(
            result["device_info"], dict
        ), "device_info should be None or a dictionary"

        # If device_info is provided, check its structure
        if result["device_info"] is not None:
            device_info = result["device_info"]
            assert (
                "name" in device_info
            ), "Device info should have 'name' field"
            assert (
                "ip_address" in device_info
            ), "Device info should have 'ip_address' field"
            assert (
                "port" in device_info
            ), "Device info should have 'port' field"
            assert "nos" in device_info, "Device info should have 'nos' field"

            assert isinstance(
                device_info["name"], str
            ), "name should be a string"
            assert isinstance(
                device_info["ip_address"], str
            ), "ip_address should be a string"
            assert isinstance(
                device_info["port"], int
            ), "port should be an integer"
            assert isinstance(
                device_info["nos"], str
            ), "nos should be a string"

        print("✓ DeviceErrorResult compliance test passed.")
    else:
        print("⚠ Could not test error case - device was found unexpectedly.")


def test_device_to_device_info_method():
    """Test that Device objects can be converted to device info using to_device_info method."""
    # Get the first available device
    device_list_result = list_available_devices()

    if device_list_result["devices"]:
        first_device_info = device_list_result["devices"][0]
        device_name = first_device_info["name"]

        # Get the full device object
        result, success = get_device(device_name)

        if success:
            # At this point, result should be a Device object
            from src.inventory.models import Device

            assert isinstance(
                result, Device
            ), "Result should be a Device instance when success is True"

            # Check that the device has the to_device_info method
            assert hasattr(
                result, "to_device_info"
            ), "Device should have to_device_info method"

            # Convert to device info and verify structure
            device_info = result.to_device_info()

            assert isinstance(
                device_info, dict
            ), "Device info should be a dictionary"
            assert (
                "name" in device_info
            ), "Device info should have 'name' field"
            assert (
                "ip_address" in device_info
            ), "Device info should have 'ip_address' field"
            assert (
                "port" in device_info
            ), "Device info should have 'port' field"
            assert "nos" in device_info, "Device info should have 'nos' field"

            assert isinstance(
                device_info["name"], str
            ), "name should be a string"
            assert isinstance(
                device_info["ip_address"], str
            ), "ip_address should be a string"
            assert isinstance(
                device_info["port"], int
            ), "port should be an integer"
            assert isinstance(
                device_info["nos"], str
            ), "nos should be a string"

            # Verify that sensitive information is not included
            assert (
                "username" not in device_info
            ), "Device info should not contain sensitive 'username'"
            assert (
                "password" not in device_info
            ), "Device info should not contain sensitive 'password'"

            print("✓ Device.to_device_info() method compliance test passed.")
        else:
            print("⚠ Could not test device conversion - device lookup failed.")
    else:
        print("⚠ Could not test device conversion - no devices available.")


if __name__ == "__main__":
    print("Testing schema compliance for inventory functions...")

    try:
        test_device_list_result_compliance()
        test_device_error_result_compliance()
        test_device_to_device_info_method()
        print("\n✅ All schema compliance tests passed!")
    except AssertionError as e:
        print(f"\n❌ Schema compliance test failed: {e}")
        exit(1)
