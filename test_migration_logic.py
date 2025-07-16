#!/usr/bin/env python3
"""Test script to verify the collector migration logic."""

import glob
import os

# Change to the project directory
os.chdir("/Users/jillesca/DevNet/cisco_live/25clus/gNMIBuddy")

collector_files = glob.glob("src/collectors/*.py")
print(f"Found {len(collector_files)} collector files")

migrated_count = 0
for collector_file in collector_files:
    if collector_file.endswith("__init__.py"):
        continue

    print(f"\nChecking {collector_file}...")
    with open(collector_file, "r") as f:
        content = f.read()

    # Check if the file imports and uses the smart verification decorator
    has_import = (
        "from src.decorators.smart_capability_verification import verify_required_models"
        in content
    )
    has_decorator = "@verify_required_models" in content

    print(f"  Has import: {has_import}")
    print(f"  Has decorator: {has_decorator}")

    if has_import and has_decorator:
        migrated_count += 1
        print(f"  ✅ {collector_file} is migrated")
    else:
        print(f"  ❌ {collector_file} is NOT migrated")

print(f"\nMigrated collectors: {migrated_count}")
print(f"Expected at least 5: {'PASS' if migrated_count >= 5 else 'FAIL'}")
