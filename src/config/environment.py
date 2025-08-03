#!/usr/bin/env python3
"""
Centralized Environment Management for gNMIBuddy using Pydantic Settings.

This module provides a centralized approach to handle ALL environment variables
used throughout the gNMIBuddy application. It uses Pydantic Settings to provide
type-safe configuration management with proper precedence handling.

Environment Variable Precedence (Pydantic Settings built-in):
1. CLI arguments (highest priority)
2. OS Environment variables
3. .env file values
4. Default values (lowest priority)

This integrates with (does not replace) the existing logging environment
configuration system in src/logging/config/environment.py.
"""

import os
from pathlib import Path
from typing import Optional, Union
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.logging import get_logger

# Setup module logger
logger = get_logger(__name__)


class GNMIBuddySettings(BaseSettings):
    """
    Centralized settings class for gNMIBuddy environment variables.

    Uses Pydantic Settings for type-safe configuration management with
    automatic .env file loading and environment variable precedence.

    All environment variables supported by gNMIBuddy are defined here
    to provide a single source of truth for configuration.
    """

    model_config = SettingsConfigDict(
        env_file=".env",  # Default .env file in project root
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra fields for flexibility
        case_sensitive=False,  # Allow case-insensitive env var names
        validate_default=True,  # Validate default values
    )

    # Network inventory configuration
    network_inventory: Optional[str] = None

    # Logging configuration (delegated to existing logging system)
    gnmibuddy_log_level: Optional[str] = None
    gnmibuddy_module_levels: Optional[str] = None
    gnmibuddy_log_file: Optional[str] = None
    gnmibuddy_structured_logging: Optional[bool] = None
    gnmibuddy_external_suppression_mode: Optional[str] = None

    # MCP configuration
    gnmibuddy_mcp_tool_debug: Optional[bool] = None

    @classmethod
    def from_env_file(
        cls, env_file: Optional[Union[str, Path]] = None
    ) -> "GNMIBuddySettings":
        """
        Load settings from a specific .env file or use default.

        Args:
            env_file: Path to .env file, or None to use default

        Returns:
            GNMIBuddySettings instance loaded from specified or default .env file

        Examples:
            # Use default .env file in project root
            settings = GNMIBuddySettings.from_env_file()

            # Use custom .env file
            settings = GNMIBuddySettings.from_env_file('custom.env')
            settings = GNMIBuddySettings.from_env_file(Path('config/prod.env'))
        """
        if env_file is None:
            logger.debug("Loading settings with default .env file")
            try:
                return cls()
            except Exception as e:
                logger.error("Failed to load default settings: %s", e)
                raise

        # Convert to string if Path object
        env_file_str = (
            str(env_file) if isinstance(env_file, Path) else env_file
        )

        logger.debug(
            "Loading settings from environment file: %s", env_file_str
        )

        # Check if file exists and handle gracefully
        if not os.path.exists(env_file_str):
            # Log warning but don't crash - container-friendly design
            logger.warning(
                "Environment file '%s' not found, using defaults and OS environment variables",
                env_file_str,
            )
            try:
                return cls()
            except Exception as e:
                logger.error(
                    "Failed to load default settings after missing file: %s", e
                )
                raise

        # Create new instance with custom env file
        custom_config = SettingsConfigDict(
            env_file=env_file_str,
            env_file_encoding="utf-8",
            extra="ignore",
            case_sensitive=False,
            validate_default=True,
        )

        class CustomSettings(cls):
            model_config = custom_config

        try:
            logger.info(
                "Successfully loaded settings from environment file: %s",
                env_file_str,
            )
            return CustomSettings()
        except Exception as e:
            logger.error(
                "Failed to load settings from file '%s': %s", env_file_str, e
            )
            raise

    def get_network_inventory(self) -> Optional[str]:
        """
        Get network inventory file path.

        Returns:
            Path to network inventory file or None if not configured
        """
        logger.debug(
            "Retrieving network inventory path: %s", self.network_inventory
        )
        return self.network_inventory

    def get_mcp_tool_debug(self) -> bool:
        """
        Get MCP tool debug mode setting.

        Returns:
            True if MCP tool debug mode is enabled, False otherwise
        """
        debug_enabled = self.gnmibuddy_mcp_tool_debug or False
        logger.debug("MCP tool debug mode: %s", debug_enabled)
        return debug_enabled


# Global instance for application-wide use
# This provides a singleton pattern for configuration access
_settings_instance: Optional[GNMIBuddySettings] = None


def get_settings(
    env_file: Optional[Union[str, Path]] = None, force_reload: bool = False
) -> GNMIBuddySettings:
    """
    Get the global settings instance with optional custom .env file.

    This function provides a singleton pattern for settings access throughout
    the application while allowing for custom .env files when needed.

    Args:
        env_file: Optional path to custom .env file
        force_reload: If True, force reload settings even if already loaded

    Returns:
        GNMIBuddySettings instance

    Examples:
        # Get default settings (uses .env in project root)
        settings = get_settings()

        # Get settings from custom file
        settings = get_settings('custom.env')

        # Force reload settings
        settings = get_settings(force_reload=True)
    """
    global _settings_instance

    try:
        if _settings_instance is None:
            logger.info("Initializing global settings instance")
            _settings_instance = GNMIBuddySettings.from_env_file(env_file)
        elif force_reload:
            logger.info("Force reloading global settings instance")
            _settings_instance = GNMIBuddySettings.from_env_file(env_file)
        elif env_file is not None:
            logger.info(
                "Loading settings with custom environment file: %s", env_file
            )
            _settings_instance = GNMIBuddySettings.from_env_file(env_file)
        else:
            logger.debug("Using cached global settings instance")

        return _settings_instance
    except Exception as e:
        logger.error("Failed to get settings instance: %s", e)
        raise


def reset_settings() -> None:
    """
    Reset the global settings instance.

    This is primarily used for testing to ensure clean state between tests.
    """
    global _settings_instance
    logger.debug("Resetting global settings instance")
    _settings_instance = None
