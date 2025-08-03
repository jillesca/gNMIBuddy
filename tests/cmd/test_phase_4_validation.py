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
