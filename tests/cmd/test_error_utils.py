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

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".log", delete=False
    ) as f:
        log_file = f.name

    try:
        # Run command and redirect output to log file
        result = subprocess.run(
            [
                "uv",
                "run",
                "gnmibuddy.py",
                "ops",
                "validate",
                "--devices",
                "device1,device2",
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

        # Verify error handling matches error utils pattern
        assert "Error: No inventory file specified" in output
        assert "Command Help:" in output
        assert "─" * 50 in output  # Separator line
        assert "💡" in output  # Suggestion present
        assert "Set NETWORK_INVENTORY environment variable" in output

        # Verify no "Executing batch operation" message appears
        assert "Executing batch operation" not in output

    finally:
        # Cleanup
        if os.path.exists(log_file):
            os.unlink(log_file)


def test_error_utils_format_consistency():
    """Test that error utils format matches inventory validate pattern."""

    # Test inventory validate command for comparison
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".log", delete=False
    ) as f:
        inventory_log = f.name

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".log", delete=False
    ) as f:
        ops_log = f.name

    try:
        # Run inventory validate (reference pattern)
        inventory_result = subprocess.run(
            ["uv", "run", "gnmibuddy.py", "inventory", "validate"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        with open(inventory_log, "w") as f:
            f.write("STDOUT:\n")
            f.write(inventory_result.stdout)
            f.write("\nSTDERR:\n")
            f.write(inventory_result.stderr)

        # Run ops validate (our implementation)
        ops_result = subprocess.run(
            [
                "uv",
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
        )

        with open(ops_log, "w") as f:
            f.write("STDOUT:\n")
            f.write(ops_result.stdout)
            f.write("\nSTDERR:\n")
            f.write(ops_result.stderr)

        # Read both outputs
        with open(inventory_log, "r") as f:
            inventory_output = f.read()

        with open(ops_log, "r") as f:
            ops_output = f.read()

        # Both should have similar error patterns
        common_patterns = [
            "Error: No inventory file specified",
            "Command Help:",
            "─" * 30,  # At least 30 separator chars
        ]

        for pattern in common_patterns:
            assert (
                pattern in inventory_output
            ), f"Pattern '{pattern}' missing from inventory validate"
            assert (
                pattern in ops_output
            ), f"Pattern '{pattern}' missing from ops validate"

        # Ops validate should have the suggestion that inventory validate doesn't
        assert (
            "💡" in ops_output
        ), "Expected 💡 suggestion in ops validate output"

    finally:
        # Cleanup
        for log_file in [inventory_log, ops_log]:
            if os.path.exists(log_file):
                os.unlink(log_file)


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
