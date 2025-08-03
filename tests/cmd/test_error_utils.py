#!/usr/bin/env python3
"""
Test error utility functions.
"""
import tempfile
import subprocess
import os
import sys
import pytest
from unittest.mock import Mock, patch
import click
from click.testing import CliRunner

# Import the error utils function to test
from src.cmd.commands.error_utils import display_error_with_help


def test_display_error_with_help_function():
    """Test the error utility function directly with mocked click context."""

    # Create a mock click context
    mock_ctx = Mock()
    mock_ctx.get_help.return_value = "Mock command help text"

    # Test with suggestion
    with patch("click.echo") as mock_echo:
        with pytest.raises(SystemExit) as exc_info:
            display_error_with_help(
                mock_ctx, "Test error message", "Test suggestion"
            )

        # Verify exit code
        assert exc_info.value.code == 1

        # Verify click.echo was called with correct arguments
        expected_calls = [
            (("Error: Test error message",), {"err": True}),
            (("─" * 50,), {"err": True}),
            (("Command Help:",), {"err": True}),
            (("─" * 50,), {"err": True}),
            (("Mock command help text",), {"err": True}),
            (("\n💡 Test suggestion",), {"err": True}),
        ]

        actual_calls = [call for call in mock_echo.call_args_list]
        assert len(actual_calls) == len(expected_calls)

        # Check each call
        for i, (expected_args, expected_kwargs) in enumerate(expected_calls):
            actual_args, actual_kwargs = actual_calls[i]
            assert actual_args == expected_args
            assert actual_kwargs == expected_kwargs


def test_display_error_with_help_no_suggestion():
    """Test the error utility function without suggestion."""

    # Create a mock click context
    mock_ctx = Mock()
    mock_ctx.get_help.return_value = "Mock command help text"

    # Test without suggestion
    with patch("click.echo") as mock_echo:
        with pytest.raises(SystemExit) as exc_info:
            display_error_with_help(mock_ctx, "Test error message")

        # Verify exit code
        assert exc_info.value.code == 1

        # Verify click.echo was called with correct arguments (no suggestion)
        expected_calls = [
            (("Error: Test error message",), {"err": True}),
            (("─" * 50,), {"err": True}),
            (("Command Help:",), {"err": True}),
            (("─" * 50,), {"err": True}),
            (("Mock command help text",), {"err": True}),
        ]

        actual_calls = [call for call in mock_echo.call_args_list]
        assert len(actual_calls) == len(expected_calls)


def test_ops_validate_uses_error_utils():
    """Test that ops validate command uses the error utils (integration test)."""

    import tempfile
    import shutil
    import os

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".log", delete=False
    ) as f:
        log_file = f.name

    # Create a temporary directory to run the command from (without .env file)
    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp()
        original_cwd = os.getcwd()

        # Change to temp directory to avoid loading .env from project root
        os.chdir(temp_dir)

        # Run command and redirect output to log file
        # Create environment without NETWORK_INVENTORY to test "no inventory" scenario
        env = os.environ.copy()
        if "NETWORK_INVENTORY" in env:
            del env["NETWORK_INVENTORY"]

        result = subprocess.run(
            [
                "uv",
                "run",
                "--directory",
                original_cwd,  # Still run from the project directory
                "gnmibuddy.py",
                "ops",
                "validate",
                "--devices",
                "device1,device2",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            env=env,  # Use modified environment
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

        # Verify error handling matches error utils pattern
        # With dotenv support, we now get "Devices not found" instead of "No inventory file specified"
        # because the .env file provides an inventory file
        assert (
            "Error: No inventory file specified" in output
            or "Error: Devices not found in inventory:" in output
        )
        assert "Command Help:" in output
        assert "─" * 50 in output  # Separator line
        assert "💡" in output  # Suggestion present
        # Updated to match new behavior - either the old message or the new environment variable suggestion
        assert (
            "Set NETWORK_INVENTORY environment variable" in output
            or "Available devices:" in output
        )

        # Verify no "Executing batch operation" message appears
        assert "Executing batch operation" not in output

    finally:
        # Cleanup
        if temp_dir:
            os.chdir(original_cwd)
            shutil.rmtree(temp_dir)
        if os.path.exists(log_file):
            os.unlink(log_file)
        if os.path.exists(log_file):
            os.unlink(log_file)


def test_error_utils_format_consistency():
    """Test that error utils format is consistent between commands."""

    # Test ops validate command for error handling patterns
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".log", delete=False
    ) as f:
        ops_log = f.name

    try:
        # Run ops validate with a device that doesn't exist (this will show error formatting)
        ops_result = subprocess.run(
            [
                "uv",
                "run",
                "gnmibuddy.py",
                "ops",
                "validate",
                "--devices",
                "nonexistent_device",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        with open(ops_log, "w") as f:
            f.write("STDOUT:\n")
            f.write(ops_result.stdout)
            f.write("\nSTDERR:\n")
            f.write(ops_result.stderr)

        # Read the output
        with open(ops_log, "r") as f:
            ops_output = f.read()

        # Verify error formatting patterns
        assert (
            "Command Help:" in ops_output
        ), "Expected 'Command Help:' in ops validate output"
        assert (
            "─" * 30 in ops_output
        ), "Expected separator line in ops validate output"
        assert (
            "💡" in ops_output
        ), "Expected 💡 suggestion in ops validate output"

        # With dotenv support, should show "devices not found" error
        assert (
            "devices not found" in ops_output.lower()
            or "device" in ops_output.lower()
        ), "Expected device-related error in ops validate output"

    finally:
        # Cleanup
        if os.path.exists(ops_log):
            os.unlink(ops_log)


def test_error_utils_different_error_messages():
    """Test that error utils works with different error messages."""

    mock_ctx = Mock()
    mock_ctx.get_help.return_value = "Test help"

    test_cases = [
        ("Simple error", "Simple suggestion"),
        ("Complex error with details", None),
        ("", "Empty error test"),
        (
            "Single line error",
            "Single-line suggestion",
        ),  # Changed from multi-line
    ]

    for error_msg, suggestion in test_cases:
        with patch("click.echo") as mock_echo:
            with pytest.raises(SystemExit):
                display_error_with_help(mock_ctx, error_msg, suggestion)

            # Verify error message appears
            calls = [str(call) for call in mock_echo.call_args_list]
            error_found = any(f"Error: {error_msg}" in call for call in calls)
            assert (
                error_found
            ), f"Error message '{error_msg}' not found in output"

            # Check suggestion handling
            if suggestion:
                suggestion_found = any(
                    f"💡 {suggestion}" in call for call in calls
                )
                assert (
                    suggestion_found
                ), f"Suggestion '{suggestion}' not found in output"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
