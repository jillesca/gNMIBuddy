#!/usr/bin/env python3
"""
Phase 5 - Final Integration and Documentation Tests

Comprehensive testing to ensure all phases work together seamlessly
and no breaking changes have been introduced.
"""

import subprocess
import tempfile
import os


class TestPhase5RegressionPrevention:
    """Tests to prevent regression of original issue and ensure all fixes persist."""

    def test_original_issue_completely_resolved(self):
        """Verify the exact original issue scenario is completely fixed."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False
        ) as f:
            log_file = f.name

        try:
            # Run the exact command from the original issue report
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "gnmibuddy.py",
                    "ops",
                    "validate",
                    "--devices",
                    "test-device-1,test-device-2",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            with open(log_file, "w") as f:
                f.write("REPRODUCTION TEST OF ORIGINAL ISSUE:\n")
                f.write(
                    "Command: uv run gnmibuddy.py ops validate --devices test-device-1,test-device-2\n\n"
                )
                f.write("STDOUT:\n")
                f.write(result.stdout)
                f.write("\nSTDERR:\n")
                f.write(result.stderr)

            with open(log_file, "r") as f:
                output = f.read()

            # Original problematic behaviors should be completely eliminated
            assert (
                "Executing batch operation on 2 devices..." not in output
            ), "Original problematic batch message should be eliminated"
            assert (
                "Failed to process device test-device-1" not in output
            ), "Original device processing errors should be prevented"
            assert (
                "Failed to process device test-device-2" not in output
            ), "Original device processing errors should be prevented"
            assert (
                '"results": [' not in output
            ), "Original JSON error output should be prevented"

            # New improved behaviors should be present
            assert (
                "No inventory file specified" in output
                or "Devices not found in inventory:" in output
            ), "Should show clear error message"
            assert (
                "Command Help:" in output
            ), "Should show helpful command help"
            assert "💡" in output, "Should provide actionable suggestions"

        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)
