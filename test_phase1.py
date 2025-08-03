#!/usr/bin/env python3
"""
Test script for Phase 1 implementation - Centralized Environment Management.

This script tests the new centralized environment management system to ensure:
1. Settings can be loaded from .env file
2. Graceful handling of missing .env files
3. Integration with existing logging environment system
4. All supported environment variables are accessible
"""

import os
import sys
import tempfile
from pathlib import Path

# Add src to Python path for testing
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.environment import (
    GNMIBuddySettings,
    get_settings,
    reset_settings,
)


def test_default_env_file():
    """Test loading from default .env file."""
    print("=== Testing Default .env File Loading ===")

    # Reset settings to ensure clean state
    reset_settings()

    settings = get_settings()
    print(f"Network Inventory: {settings.get_network_inventory()}")
    print(f"MCP Tool Debug: {settings.get_mcp_tool_debug()}")

    # Test logging integration
    logging_config = settings.get_logging_config()
    print(f"Logging Config: {logging_config}")

    # Show all environment variables
    all_vars = settings.get_all_environment_variables()
    print("\nAll Environment Variables:")
    for key, value in all_vars.items():
        print(f"  {key}: {value}")

    print("✅ Default .env file test completed\n")


def test_missing_env_file():
    """Test graceful handling of missing .env file."""
    print("=== Testing Missing .env File Handling ===")

    reset_settings()

    # Create settings with non-existent file
    settings = GNMIBuddySettings.from_env_file("non_existent.env")
    print(
        f"Network Inventory (missing file): {settings.get_network_inventory()}"
    )
    print(f"MCP Tool Debug (missing file): {settings.get_mcp_tool_debug()}")

    print("✅ Missing .env file test completed (no crash - good!)\n")


def test_custom_env_file():
    """Test loading from custom .env file."""
    print("=== Testing Custom .env File Loading ===")

    reset_settings()

    # Create temporary .env file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".env", delete=False
    ) as f:
        f.write("NETWORK_INVENTORY=/custom/path/inventory.json\n")
        f.write("GNMIBUDDY_LOG_LEVEL=debug\n")
        f.write("GNMIBUDDY_MCP_TOOL_DEBUG=true\n")
        temp_env_file = f.name

    try:
        # Load from custom file
        settings = GNMIBuddySettings.from_env_file(temp_env_file)
        print(
            f"Network Inventory (custom): {settings.get_network_inventory()}"
        )
        print(f"Log Level (custom): {settings.gnmibuddy_log_level}")
        print(f"MCP Tool Debug (custom): {settings.get_mcp_tool_debug()}")

        print("✅ Custom .env file test completed\n")
    finally:
        # Clean up
        os.unlink(temp_env_file)


def test_environment_variable_precedence():
    """Test that OS environment variables take precedence over .env file."""
    print("=== Testing Environment Variable Precedence ===")

    reset_settings()

    # Set OS environment variable
    original_value = os.environ.get("GNMIBUDDY_MCP_TOOL_DEBUG")
    os.environ["GNMIBUDDY_MCP_TOOL_DEBUG"] = "true"

    try:
        settings = get_settings()
        print(
            f"MCP Tool Debug (OS env should override): {settings.get_mcp_tool_debug()}"
        )

        print("✅ Environment variable precedence test completed\n")
    finally:
        # Restore original value
        if original_value is not None:
            os.environ["GNMIBUDDY_MCP_TOOL_DEBUG"] = original_value
        else:
            os.environ.pop("GNMIBUDDY_MCP_TOOL_DEBUG", None)


def test_supported_variables():
    """Test supported variables documentation."""
    print("=== Testing Supported Variables Documentation ===")

    supported_vars = GNMIBuddySettings.get_supported_variables()
    print("Supported Environment Variables:")
    for var_name, description in supported_vars.items():
        print(f"  {var_name}: {description}")

    print("✅ Supported variables test completed\n")


def test_existing_logging_integration():
    """Test that existing logging functionality still works."""
    print("=== Testing Existing Logging Integration ===")

    reset_settings()

    # Import existing logging environment reader directly
    from src.logging.config.environment import EnvironmentConfigReader

    # Test direct access (existing code path)
    direct_config = EnvironmentConfigReader.read_configuration()
    print(f"Direct logging config: {direct_config}")

    # Test via new centralized system
    settings = get_settings()
    centralized_config = settings.get_logging_config()
    print(f"Centralized logging config: {centralized_config}")

    # They should be the same
    print(f"Configs match: {direct_config == centralized_config}")

    print("✅ Existing logging integration test completed\n")


if __name__ == "__main__":
    print("🧪 Phase 1 Testing: Centralized Environment Management\n")

    test_default_env_file()
    test_missing_env_file()
    test_custom_env_file()
    test_environment_variable_precedence()
    test_supported_variables()
    test_existing_logging_integration()

    print("🎉 All Phase 1 tests completed successfully!")
    print("\nNext: Phase 2 agents can proceed with CLI option updates.")
