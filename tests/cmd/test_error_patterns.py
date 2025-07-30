#!/usr/bin/env python3
"""
Test UX consistency patterns for ops validate command.

This test suite ensures that error handling patterns are consistent
and comprehensive, focusing on critical UX validation.
"""
import subprocess
import tempfile
import os
import pytest


def test_ops_validate_error_consistency_basic():
    """Test that ops validate error format is consistent across different scenarios"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".log", delete=False
    ) as f:
        log_file = f.name

    try:
        # Test single device scenario
        result = subprocess.run(
            [
                "/opt/homebrew/bin/uv",
                "run",
                "gnmibuddy.py",
                "ops",
                "validate",
                "--device",
                "device1",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            env={"NETWORK_INVENTORY": "", "PATH": os.environ.get("PATH", "")},
        )

        # Write output to log file
        with open(log_file, "w") as f:
            f.write("SINGLE DEVICE TEST:\n")
            f.write("STDOUT:\n")
            f.write(result.stdout)
            f.write("\nSTDERR:\n")
            f.write(result.stderr)

        # Read and verify log file contents
        with open(log_file, "r") as f:
            output = f.read()

        # Critical UX consistency checks
        assert "Error: No inventory file specified" in output
        assert "Command Help:" in output
        assert "💡 Set NETWORK_INVENTORY environment variable" in output
        # Critical: NO batch execution message should appear
        assert "Executing batch operation" not in output

    finally:
        # Cleanup
        if os.path.exists(log_file):
            os.unlink(log_file)


def test_ops_validate_no_batch_message_critical():
    """Critical test: ensure NO batch execution message appears in error scenarios"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".log", delete=False
    ) as f:
        log_file = f.name

    try:
        # Test scenario most likely to show batch message (multiple devices)
        result = subprocess.run(
            [
                "/opt/homebrew/bin/uv",
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
            env={"NETWORK_INVENTORY": "", "PATH": os.environ.get("PATH", "")},
        )

        # Write output to log file
        with open(log_file, "w") as f:
            f.write("MULTIPLE DEVICES TEST:\n")
            f.write("STDOUT:\n")
            f.write(result.stdout)
            f.write("\nSTDERR:\n")
            f.write(result.stderr)

        # Read and verify log file contents
        with open(log_file, "r") as f:
            output = f.read()

        # This is the MOST CRITICAL test - the original issue was seeing this message
        assert (
            "Executing batch operation" not in output
        ), "CRITICAL FAILURE: 'Executing batch operation' message appeared - this is the main issue from the GitHub issue"

        # Should show proper error instead
        assert "Error: No inventory file specified" in output

    finally:
        # Cleanup
        if os.path.exists(log_file):
            os.unlink(log_file)


def test_error_message_actionable_guidance():
    """Test that error messages provide actionable guidance"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".log", delete=False
    ) as f:
        log_file = f.name

    try:
        # Test actionable guidance
        result = subprocess.run(
            [
                "/opt/homebrew/bin/uv",
                "run",
                "gnmibuddy.py",
                "ops",
                "validate",
                "--all-devices",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            env={"NETWORK_INVENTORY": "", "PATH": os.environ.get("PATH", "")},
        )

        # Write output to log file
        with open(log_file, "w") as f:
            f.write("ALL DEVICES TEST:\n")
            f.write("STDOUT:\n")
            f.write(result.stdout)
            f.write("\nSTDERR:\n")
            f.write(result.stderr)

        # Read and verify log file contents
        with open(log_file, "r") as f:
            output = f.read()

        # Verify actionable guidance is present
        assert (
            "💡 Set NETWORK_INVENTORY environment variable or use --inventory option"
            in output
        )
        assert "Error: No inventory file specified" in output
        assert "Please provide a path via command line argument" in output

    finally:
        # Cleanup
        if os.path.exists(log_file):
            os.unlink(log_file)


def test_help_display_completeness():
    """Test that command help displayed on error is complete"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".log", delete=False
    ) as f:
        log_file = f.name

    try:
        # Test help completeness
        result = subprocess.run(
            [
                "/opt/homebrew/bin/uv",
                "run",
                "gnmibuddy.py",
                "ops",
                "validate",
                "--devices",
                "device1",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            env={"NETWORK_INVENTORY": "", "PATH": os.environ.get("PATH", "")},
        )

        # Write output to log file
        with open(log_file, "w") as f:
            f.write("HELP COMPLETENESS TEST:\n")
            f.write("STDOUT:\n")
            f.write(result.stdout)
            f.write("\nSTDERR:\n")
            f.write(result.stderr)

        # Read and verify log file contents
        with open(log_file, "r") as f:
            output = f.read()

        # Verify help contains essential information
        assert "Usage: gnmibuddy.py ops validate [OPTIONS]" in output
        assert "--device TEXT" in output  # Device option
        assert "--devices TEXT" in output  # Devices option
        assert "--all-devices" in output  # All devices option
        assert "Examples:" in output  # Examples section

    finally:
        # Cleanup
        if os.path.exists(log_file):
            os.unlink(log_file)


def test_error_display_formatting():
    """Test that error display formatting follows consistent patterns"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".log", delete=False
    ) as f:
        log_file = f.name

    try:
        # Test formatting
        result = subprocess.run(
            [
                "/opt/homebrew/bin/uv",
                "run",
                "gnmibuddy.py",
                "ops",
                "validate",
                "--device",
                "testdevice",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            env={"NETWORK_INVENTORY": "", "PATH": os.environ.get("PATH", "")},
        )

        # Write output to log file
        with open(log_file, "w") as f:
            f.write("FORMATTING TEST:\n")
            f.write("STDOUT:\n")
            f.write(result.stdout)
            f.write("\nSTDERR:\n")
            f.write(result.stderr)

        # Read and verify log file contents
        with open(log_file, "r") as f:
            output = f.read()

        # Test critical formatting elements
        assert "Error:" in output  # Error prefix
        assert "Command Help:" in output  # Help header
        assert "─" in output  # Separator lines
        assert "💡" in output  # Suggestion indicator

    finally:
        # Cleanup
        if os.path.exists(log_file):
            os.unlink(log_file)


if __name__ == "__main__":
    # Run a simple test manually
    test_ops_validate_error_consistency_basic()
    print("Basic consistency test passed!")
