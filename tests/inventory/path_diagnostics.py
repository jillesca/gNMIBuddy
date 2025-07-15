#!/usr/bin/env python3
"""
Diagnostic script to help debug path issues in file_handler.
This script helps identify current working directory issues that might affect relative path resolution.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def diagnose_path_issues():
    """Diagnose common path-related issues."""
    print("=== Path Diagnostics ===")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script location: {os.path.dirname(os.path.abspath(__file__))}")
    print(f"Project root: {project_root}")
    print()

    # Check if sample files exist
    sample_files = [
        "xrd_sandbox.json",
        "./xrd_sandbox.json",
        "tests/inventory/test_devices.json",
        "./tests/inventory/test_devices.json",
    ]

    print("=== File Existence Check ===")
    for file_path in sample_files:
        abs_path = os.path.abspath(file_path)
        exists = os.path.exists(file_path)
        abs_exists = os.path.exists(abs_path)
        print(f"Relative path '{file_path}': exists={exists}")
        print(f"  Absolute equivalent '{abs_path}': exists={abs_exists}")
        print()

    # Test relative path resolution
    print("=== Relative Path Resolution Test ===")
    test_relative_paths = [
        "xrd_sandbox.json",
        "./xrd_sandbox.json",
        "../xrd_sandbox.json",
        "tests/inventory/test_devices.json",
    ]

    for rel_path in test_relative_paths:
        try:
            abs_path = os.path.abspath(rel_path)
            exists = os.path.exists(abs_path)
            print(f"'{rel_path}' -> '{abs_path}' (exists: {exists})")
        except OSError as e:
            print(f"'{rel_path}' -> ERROR: {e}")

    print()
    print("=== Environment Variables ===")
    network_inv = os.environ.get("NETWORK_INVENTORY")
    print(f"NETWORK_INVENTORY: {network_inv}")

    if network_inv:
        abs_env_path = os.path.abspath(network_inv)
        exists = os.path.exists(abs_env_path)
        print(f"  Resolves to: {abs_env_path} (exists: {exists})")


if __name__ == "__main__":
    diagnose_path_issues()
