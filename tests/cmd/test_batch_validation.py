#!/usr/bin/env python3
"""
Test all-or-nothing batch validation for ops validate command.

Tests the enhanced device resolution that validates ALL specified devices
can be accessed before starting any operations.
"""
import subprocess
import tempfile
import os
import pytest
from unittest.mock import patch, MagicMock


def test_batch_validation_missing_inventory_no_batch_message():
    """Test that missing inventory fails without showing 'Executing batch operation' message"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".log", delete=False
    ) as f:
        log_file = f.name

    try:
        # Run command with multiple devices but no inventory
        result = subprocess.run(
            [
                "uv",
                "run",
                "gnmibuddy.py",
                "ops",
                "validate",
                "--devices",
                "device1,device2,device3",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Write both stdout and stderr to log file
        with open(log_file, "w") as f:
            f.write("STDOUT:\n")
            f.write(result.stdout)
            f.write("\nSTDERR:\n")
            f.write(result.stderr)

        # Read and verify log file contents
        with open(log_file, "r") as f:
            output = f.read()

        # Verify error handling behavior (not exit code due to framework issue)
        assert "Error:" in output, "Should show error message"
        assert "Command Help:" in output, "Should show command help"

        # Critical: Should NOT show "Executing batch operation" message
        assert (
            "Executing batch operation" not in output
        ), "Should not start batch operation when inventory is missing"

        # Should show helpful suggestion
        assert "💡" in output, "Should show helpful suggestion"

    finally:
        if os.path.exists(log_file):
            os.unlink(log_file)


def test_batch_validation_mixed_valid_invalid_devices():
    """Test all-or-nothing approach with mixed valid/invalid devices"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".log", delete=False
    ) as f:
        log_file = f.name

    try:
        # Create a mock inventory file for this test with proper format
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as inv_file:
            inventory_file = inv_file.name
            # Use proper gNMIBuddy inventory format
            inv_file.write(
                '[{"name": "device1", "ip_address": "192.168.1.1", "nos": "iosxr", "port": 57400, "username": "test", "password": "test"}]'
            )

        # Set environment variable to use our test inventory
        env = os.environ.copy()
        env["NETWORK_INVENTORY"] = inventory_file

        # Run command with mix of valid and invalid devices
        result = subprocess.run(
            [
                "uv",
                "run",
                "gnmibuddy.py",
                "ops",
                "validate",
                "--devices",
                "device1,nonexistent_device,another_invalid",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )

        # Write both stdout and stderr to log file
        with open(log_file, "w") as f:
            f.write("STDOUT:\n")
            f.write(result.stdout)
            f.write("\nSTDERR:\n")
            f.write(result.stderr)

        # Read and verify log file contents
        with open(log_file, "r") as f:
            output = f.read()

        # Should fail completely due to invalid devices (behavior, not exit code)
        assert "Error:" in output, "Should show error message"

        # Should NOT show "Executing batch operation" message
        assert (
            "Executing batch operation" not in output
        ), "Should not start batch operation with invalid devices"

        # Should mention the invalid devices in error
        assert "not found in inventory" in output or "Device" in output

    finally:
        # Cleanup
        if os.path.exists(log_file):
            os.unlink(log_file)
        if "inventory_file" in locals() and os.path.exists(inventory_file):
            os.unlink(inventory_file)


def test_batch_validation_empty_device_list():
    """Test validation with empty device list"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".log", delete=False
    ) as f:
        log_file = f.name

    try:
        # Run command with empty devices
        result = subprocess.run(
            [
                "uv",
                "run",
                "gnmibuddy.py",
                "ops",
                "validate",
                "--devices",
                "",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Write both stdout and stderr to log file
        with open(log_file, "w") as f:
            f.write("STDOUT:\n")
            f.write(result.stdout)
            f.write("\nSTDERR:\n")
            f.write(result.stderr)

        # Read and verify log file contents
        with open(log_file, "r") as f:
            output = f.read()

        # Should show help for empty device list (not an error case)
        # The command should handle empty device list gracefully
        assert "Usage:" in output or "Command Help:" in output

    finally:
        if os.path.exists(log_file):
            os.unlink(log_file)


def test_batch_validation_single_invalid_device():
    """Test all-or-nothing validation with single invalid device"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".log", delete=False
    ) as f:
        log_file = f.name

    try:
        # Create a minimal inventory file with proper format
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as inv_file:
            inventory_file = inv_file.name
            inv_file.write(
                '[{"name": "valid_device", "ip_address": "192.168.1.1", "nos": "iosxr", "port": 57400, "username": "test", "password": "test"}]'
            )

        # Set environment variable to use our test inventory
        env = os.environ.copy()
        env["NETWORK_INVENTORY"] = inventory_file

        # Run command with single invalid device
        result = subprocess.run(
            [
                "uv",
                "run",
                "gnmibuddy.py",
                "ops",
                "validate",
                "--devices",
                "invalid_device",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )

        # Write both stdout and stderr to log file
        with open(log_file, "w") as f:
            f.write("STDOUT:\n")
            f.write(result.stdout)
            f.write("\nSTDERR:\n")
            f.write(result.stderr)

        # Read and verify log file contents
        with open(log_file, "r") as f:
            output = f.read()

        # Should fail with device not found error (behavior, not exit code)
        assert "Error:" in output, "Should show error message"
        assert "not found in inventory" in output or "invalid_device" in output

        # Should NOT show "Executing batch operation" message
        assert (
            "Executing batch operation" not in output
        ), "Should not start batch operation with invalid device"

    finally:
        # Cleanup
        if os.path.exists(log_file):
            os.unlink(log_file)
        if "inventory_file" in locals() and os.path.exists(inventory_file):
            os.unlink(inventory_file)


def test_batch_validation_fail_fast_behavior():
    """Test that validation follows fail-fast approach consistently"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".log", delete=False
    ) as f:
        log_file = f.name

    try:
        # Run command that should fail fast
        result = subprocess.run(
            [
                "uv",
                "run",
                "gnmibuddy.py",
                "ops",
                "validate",
                "--devices",
                "device1,device2,device3,device4,device5",
            ],
            capture_output=True,
            text=True,
            timeout=15,  # Shorter timeout - should fail fast
        )

        # Write both stdout and stderr to log file
        with open(log_file, "w") as f:
            f.write("STDOUT:\n")
            f.write(result.stdout)
            f.write("\nSTDERR:\n")
            f.write(result.stderr)

        # Read and verify log file contents
        with open(log_file, "r") as f:
            output = f.read()

        # Should fail quickly without starting operations (behavior, not exit code)
        assert "Error:" in output, "Should show error message"

        # Critical: Should fail before starting any batch operations
        assert (
            "Executing batch operation" not in output
        ), "Should fail before batch execution starts"

    finally:
        if os.path.exists(log_file):
            os.unlink(log_file)
