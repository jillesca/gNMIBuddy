#!/usr/bin/env python3
"""
File handling module for inventory.
Handles parsing JSON inventory files and related file operations.
"""

import json
import os
import sys
from typing import Dict, List, Any, Optional, cast
from pathlib import Path

from src.schemas.models import Device, NetworkOS
from src.logging import get_logger
from src.config.environment import get_settings

# Type alias for device inventory data from JSON
DeviceData = Dict[str, Any]
DeviceInventory = List[DeviceData]

# Setup module logger
logger = get_logger(__name__)


def get_inventory_path(cli_path: Optional[str] = None) -> str:
    """
    Get inventory file path with the following precedence:
    1. Command-line argument (if provided)
    2. Environment variable NETWORK_INVENTORY (via centralized settings)
    3. Raise FileNotFoundError if no inventory path is specified

    Args:
        cli_path: Optional path provided via command-line argument

    Returns:
        Path to the inventory JSON file to use

    Raises:
        FileNotFoundError: If no inventory path is specified
    """
    if cli_path:
        # Get absolute path for clarity in error messages
        abs_path = os.path.abspath(cli_path)
        logger.debug(
            "Using inventory file from command-line argument: %s", abs_path
        )
        return abs_path

    settings = get_settings()
    env_path = settings.get_network_inventory()
    if env_path:
        # Get absolute path for clarity in error messages
        abs_path = os.path.abspath(env_path)
        logger.debug(
            "Using inventory file from NETWORK_INVENTORY environment variable: %s",
            abs_path,
        )
        return abs_path

    # No inventory file path found
    logger.error("No inventory file specified")
    raise FileNotFoundError(
        "No inventory file specified. Please provide a path via command line argument or set the NETWORK_INVENTORY environment variable."
    )


def resolve_inventory_path(file_path: str) -> str:
    """
    Resolve inventory file path with enhanced error reporting.

    This function handles both absolute and relative paths, providing
    clear error messages when files are not found.

    Args:
        file_path: Path to the inventory file (absolute or relative)

    Returns:
        Absolute path to the inventory file

    Raises:
        FileNotFoundError: If the file does not exist with detailed context
    """
    # Convert to absolute path
    abs_path = os.path.abspath(file_path)

    # Check if file exists
    if os.path.exists(abs_path):
        logger.debug("Found inventory file: %s", abs_path)
        return abs_path

    # File doesn't exist - provide helpful error message
    current_dir = os.getcwd()
    is_relative = not os.path.isabs(file_path)

    error_msg = f"File not found: {abs_path}"
    if is_relative:
        error_msg += f"\nNote: '{file_path}' is a relative path, resolved from current directory: {current_dir}"

        # Suggest some common alternatives
        possible_paths = []

        # Check if it exists relative to project root (common mistake)
        try:
            # Try to find project root by looking for pyproject.toml or similar
            project_indicators = ["pyproject.toml", "setup.py", ".git"]
            potential_project_root = Path(current_dir)

            for parent in [potential_project_root] + list(
                potential_project_root.parents
            ):
                if any(
                    (parent / indicator).exists()
                    for indicator in project_indicators
                ):
                    project_relative_path = parent / file_path
                    if project_relative_path.exists():
                        possible_paths.append(str(project_relative_path))
                    break
        except Exception:
            pass  # Ignore errors in suggestion logic

        if possible_paths:
            error_msg += f"\nDid you mean: {possible_paths[0]}?"
        else:
            error_msg += f"\nMake sure you're running from the correct directory or use an absolute path."

    logger.error(error_msg)
    raise FileNotFoundError(error_msg)


def _convert_device_data(device_data: DeviceData) -> DeviceData:
    """
    Convert device data from JSON format to Device-compatible format.

    Handles conversion of string 'nos' field to NetworkOS enum.

    Args:
        device_data: Raw device data from JSON

    Returns:
        Device data with enum conversions applied

    Raises:
        ValueError: If nos value is not supported
    """
    converted_data = device_data.copy()

    # Convert nos string to NetworkOS enum if present
    if "nos" in converted_data and isinstance(converted_data["nos"], str):
        nos_value = converted_data["nos"]
        try:
            converted_data["nos"] = NetworkOS(nos_value)
        except ValueError as e:
            valid_values = [str(nos) for nos in NetworkOS]
            error_msg = f"Invalid network OS '{nos_value}'. Must be one of: {valid_values}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

    return converted_data


def load_inventory(inventory_file: Optional[str] = None) -> Dict[str, Device]:
    """
    Load device inventory from a JSON file and convert to Device objects.

    Args:
        inventory_file: Path to the inventory JSON file (optional)

    Returns:
        Dictionary mapping device names to Device objects

    Raises:
        SystemExit: If the inventory file doesn't exist or is invalid
    """
    if not inventory_file:
        try:
            inventory_file = get_inventory_path()
        except FileNotFoundError as e:
            logger.error("%s", e)
            raise

    try:
        device_inventory = parse_json_file(inventory_file)
        devices: Dict[str, Device] = {}

        for device_data in device_inventory:
            converted_data = _convert_device_data(device_data)
            device = Device(**converted_data)
            devices[device.name] = device

        logger.debug(
            "Successfully loaded %d devices from inventory %s",
            len(devices),
            inventory_file,
        )
        return devices
    except (FileNotFoundError, json.JSONDecodeError, IOError, ValueError) as e:
        error_msg = (
            f"Error loading device inventory from {inventory_file}: {e}"
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg) from e


def parse_json_file(json_file_path: str) -> DeviceInventory:
    """
    Parse a JSON file into a Python list of device dictionaries.

    Args:
        json_file_path: Path to the JSON file (absolute or relative)

    Returns:
        List of dictionaries representing network devices

    Raises:
        FileNotFoundError: If the file does not exist
        json.JSONDecodeError: If the file contains invalid JSON
        IOError: If there's an error reading the file
    """
    try:
        # Resolve path with enhanced error reporting
        abs_path = resolve_inventory_path(json_file_path)

        # Open and parse the JSON file with explicit encoding
        with open(abs_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        logger.debug("Successfully parsed JSON file: %s", abs_path)
        return cast(DeviceInventory, data)
    except json.JSONDecodeError as e:
        # Re-resolve path for error message (in case of symlinks, etc.)
        abs_path = os.path.abspath(json_file_path)
        error_msg = f"Error parsing JSON in {abs_path}: {e}"
        logger.error(error_msg)
        raise json.JSONDecodeError(error_msg, e.doc, e.pos) from e
    except FileNotFoundError:
        # Already logged in resolve_inventory_path
        raise
    except IOError as e:
        abs_path = os.path.abspath(json_file_path)
        error_msg = f"IO error reading file {abs_path}: {e}"
        logger.error(error_msg)
        raise IOError(error_msg) from e
