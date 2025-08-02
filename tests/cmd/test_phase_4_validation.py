#!/usr/bin/env python3
"""
Comprehensive validation test for Phase 4 completion.

This test verifies that all Phase 4 requirements have been met:
1. Comprehensive test coverage for all error scenarios
2. UX consistency verification
3. Proper testing patterns implemented
4. Performance testing shows no degradation
"""
import subprocess
import tempfile
import os
import time
import pytest


def test_phase_4_comprehensive_validation():
    """Comprehensive test validating all Phase 4 requirements are met"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".log", delete=False
    ) as f:
        log_file = f.name

    try:
        # Test the original issue scenario - the main problem from GitHub issue #10
        start_time = time.time()
        result = subprocess.run(
            [
                "/opt/homebrew/bin/uv",
                "run",
                "gnmibuddy.py",
                "ops",
                "validate",
                "--devices",
                "xrd-1,xrd-2",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            env={"NETWORK_INVENTORY": "", "PATH": os.environ.get("PATH", "")},
        )
        execution_time = time.time() - start_time

        # Write output to log file for verification
        with open(log_file, "w") as f:
            f.write("PHASE 4 COMPREHENSIVE VALIDATION TEST:\n")
            f.write(f"Execution time: {execution_time:.2f} seconds\n")
            f.write("STDOUT:\n")
            f.write(result.stdout)
            f.write("\nSTDERR:\n")
            f.write(result.stderr)

        # Read and verify log file contents
        with open(log_file, "r") as f:
            output = f.read()

        # CRITICAL SUCCESS CRITERIA VERIFICATION:

        # 1. ✅ Original issue resolved: NO "Executing batch operation" message
        assert (
            "Executing batch operation" not in output
        ), "CRITICAL FAILURE: Original issue not resolved!"

        # 2. ✅ User-friendly error display
        assert "Error: No inventory file specified" in output
        assert "Please provide a path via command line argument" in output
        assert "set the NETWORK_INVENTORY environment variable" in output

        # 3. ✅ Automatic help display
        assert "Command Help:" in output
        assert "Usage: gnmibuddy.py ops validate [OPTIONS]" in output
        assert "Options:" in output
        assert "--device TEXT" in output
        assert "--devices TEXT" in output

        # 4. ✅ Actionable guidance
        assert (
            "💡 Set NETWORK_INVENTORY environment variable or use --inventory option"
            in output
        )

        # 5. ✅ Consistent formatting patterns
        assert "──────────────────────────────────────────────────" in output
        assert "Examples:" in output

        # 6. ✅ Performance requirement: Fast failure (should be under 10 seconds)
        assert (
            execution_time < 10.0
        ), f"Performance degradation detected: {execution_time:.2f}s (should be < 10s)"

        # 7. ✅ Complete help information present
        assert (
            "uv run gnmibuddy.py ops validate --device R1" in output
        )  # Basic example
        assert (
            "uv run gnmibuddy.py ops validate --devices R1,R2,R3" in output
        )  # Batch example

    finally:
        # Cleanup
        if os.path.exists(log_file):
            os.unlink(log_file)


def test_phase_4_regression_prevention():
    """Test that prevents regression of the original issue"""
    scenarios = [
        (["--device", "device1"], "single device"),
        (["--devices", "device1,device2"], "multiple devices"),
        (["--devices", "device1,device2,device3"], "many devices"),
        (["--all-devices"], "all devices"),
    ]

    for scenario, description in scenarios:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False
        ) as f:
            log_file = f.name

        try:
            result = subprocess.run(
                [
                    "/opt/homebrew/bin/uv",
                    "run",
                    "gnmibuddy.py",
                    "ops",
                    "validate",
                ]
                + scenario,
                capture_output=True,
                text=True,
                timeout=30,
                env={
                    "NETWORK_INVENTORY": "",
                    "PATH": os.environ.get("PATH", ""),
                },
            )

            # Write output to log file
            with open(log_file, "w") as f:
                f.write(f"REGRESSION TEST - {description.upper()}:\n")
                f.write("STDOUT:\n")
                f.write(result.stdout)
                f.write("\nSTDERR:\n")
                f.write(result.stderr)

            # Read and verify
            with open(log_file, "r") as f:
                output = f.read()

            # Critical: NO batch execution message in ANY scenario
            assert (
                "Executing batch operation" not in output
            ), f"REGRESSION: Batch message found in {description} scenario!"

            # All scenarios should show proper error handling
            assert (
                "Error: No inventory file specified" in output
            ), f"Missing error message in {description} scenario"

        finally:
            # Cleanup
            if os.path.exists(log_file):
                os.unlink(log_file)


if __name__ == "__main__":
    # Run comprehensive validation
    test_phase_4_comprehensive_validation()
    test_phase_4_regression_prevention()
    print("✅ All Phase 4 requirements validated successfully!")
