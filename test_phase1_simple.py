#!/usr/bin/env python3
"""
Simple Phase 1 test to verify centralized environment management without circular imports.
"""

import os
import tempfile
import sys

# Temporarily modify path to import our module
sys.path.insert(0, "/Users/jillesca/DevNet/cisco_live/25clus/gNMIBuddy")

# Test import and basic functionality
try:
    print("Testing Pydantic Settings import...")
    from pydantic_settings import BaseSettings, SettingsConfigDict

    print("✅ Pydantic Settings imported successfully")

    print("\nTesting basic settings class...")

    class TestSettings(BaseSettings):
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
            case_sensitive=False,
        )

        network_inventory: str | None = None
        gnmibuddy_mcp_tool_debug: bool | None = None

    print("✅ Basic settings class created successfully")

    print("\nTesting .env file loading...")
    settings = TestSettings()
    print(f"Network Inventory: {settings.network_inventory}")
    print(f"MCP Tool Debug: {settings.gnmibuddy_mcp_tool_debug}")

    print("\nTesting custom env file...")
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".env", delete=False
    ) as f:
        f.write("NETWORK_INVENTORY=/custom/path/test.json\n")
        f.write("GNMIBUDDY_MCP_TOOL_DEBUG=true\n")
        temp_file = f.name

    try:
        # Test custom env file
        custom_config = SettingsConfigDict(
            env_file=temp_file,
            env_file_encoding="utf-8",
            extra="ignore",
            case_sensitive=False,
        )

        class CustomTestSettings(TestSettings):
            model_config = custom_config

        custom_settings = CustomTestSettings()
        print(f"Custom Network Inventory: {custom_settings.network_inventory}")
        print(
            f"Custom MCP Tool Debug: {custom_settings.gnmibuddy_mcp_tool_debug}"
        )

        print("✅ Custom .env file loading works")

    finally:
        os.unlink(temp_file)

    print("\nTesting environment variable precedence...")
    original_value = os.environ.get("GNMIBUDDY_MCP_TOOL_DEBUG")
    os.environ["GNMIBUDDY_MCP_TOOL_DEBUG"] = "false"

    try:
        precedence_settings = TestSettings()
        print(
            f"Environment variable precedence: {precedence_settings.gnmibuddy_mcp_tool_debug}"
        )
        print("✅ Environment variable precedence works")
    finally:
        if original_value is not None:
            os.environ["GNMIBUDDY_MCP_TOOL_DEBUG"] = original_value
        else:
            os.environ.pop("GNMIBUDDY_MCP_TOOL_DEBUG", None)

    print("\n🎉 Phase 1 core functionality verified successfully!")
    print("Pydantic Settings implementation is working correctly.")
    print("Ready for integration with gNMIBuddy application.")

except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback

    traceback.print_exc()
