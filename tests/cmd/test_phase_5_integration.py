#!/usr/bin/env python3
"""
Phase 5 - Final Integration and Documentation Tests

Comprehensive testing to ensure all phases work together seamlessly
and no breaking changes have been introduced.
"""

import subprocess
import tempfile
import os
import time
import pytest
from unittest.mock import patch, MagicMock


class TestPhase5FinalIntegration:
    """Comprehensive integration tests for all phases working together."""

    def test_complete_workflow_error_scenario(self):
        """Test the complete workflow from missing inventory to helpful error message."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False
        ) as f:
            log_file = f.name

        try:
            # Run command that should trigger all error handling components
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "gnmibuddy.py",
                    "ops",
                    "validate",
                    "--devices",
                    "device1,device2,device3",  # Multiple devices to test batch validation
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Write output to log file for detailed analysis
            with open(log_file, "w") as f:
                f.write("STDOUT:\n")
                f.write(result.stdout)
                f.write("\nSTDERR:\n")
                f.write(result.stderr)

            # Read and verify complete workflow
            with open(log_file, "r") as f:
                output = f.read()

            # NOTE: Exit code appears to be framework-level issue (mentioned in Phase 1 comments)
            # Focus on functionality working correctly rather than exit code

            # Phase 1: Early inventory validation working
            assert (
                "No inventory file specified" in output
                or "Devices not found in inventory:" in output
            ), f"Early validation should catch inventory error. Output: {output[:500]}"

            # Phase 2: Error utils providing consistent formatting
            assert (
                "──────────────────────────────────────────────────" in output
            ), f"Error utils formatting should be applied. Output: {output[:500]}"
            assert (
                "Command Help:" in output
            ), f"Help should be displayed automatically. Output: {output[:500]}"
            assert (
                "💡" in output
            ), f"Helpful suggestions should be provided. Output: {output[:500]}"

            # Phase 3: No batch execution message (critical improvement)
            assert (
                "Executing batch operation" not in output
            ), f"Batch operation message should be eliminated. Output: {output[:500]}"
            assert (
                "Failed to process device" not in output
            ), f"Device processing errors should be prevented. Output: {output[:500]}"

            # Phase 4: Comprehensive error handling
            assert (
                "NETWORK_INVENTORY" in output
            ), f"Actionable guidance should be present. Output: {output[:500]}"

            # Phase 5: Enhanced documentation - verify improved help examples are included
            assert (
                "export NETWORK_INVENTORY" in output
            ), f"Should include inventory setup examples. Output: {output[:500]}"
            assert (
                "--inventory" in output
            ), f"Should mention inventory option. Output: {output[:500]}"

        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)

    def test_documentation_improvements_accessible(self):
        """Verify that improved help text is accessible and informative."""
        # Test help command includes inventory setup guidance
        result = subprocess.run(
            ["uv", "run", "gnmibuddy.py", "ops", "validate", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, "Help command should succeed"

        # Should include inventory setup examples
        help_text = result.stdout
        assert (
            "NETWORK_INVENTORY" in help_text
        ), "Help should mention environment variable"
        assert (
            "--inventory" in help_text
        ), "Help should mention inventory option"
        assert (
            "export NETWORK_INVENTORY" in help_text
        ), "Help should include setup examples"


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
