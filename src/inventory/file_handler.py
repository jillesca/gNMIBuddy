#!/usr/bin/env python3
"""
File handling module for inventory.
Handles parsing JSON inventory files and related file operations.
"""

import json
import os
import sys
import logging
from typing import Dict, List, Any, Optional, cast

from .models import Device

# Type alias for device inventory data from JSON
DeviceData = Dict[str, Any]
DeviceInventory = List[DeviceData]

# Setup module logger
logger = logging.getLogger(__name__)


def get_inventory_path(cli_path: Optional[str] = None) -> str:
    """
    Get inventory file path with the following precedence:
    1. Command-line argument (if provided)
    2. Environment variable NETWORK_INVENTORY
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
            f"Using inventory file from command-line argument: {abs_path}"
        )
        return abs_path

    env_path = os.environ.get("NETWORK_INVENTORY")
    if env_path:
        # Get absolute path for clarity in error messages
        abs_path = os.path.abspath(env_path)
        logger.debug(
            f"Using inventory file from NETWORK_INVENTORY environment variable: {abs_path}"
        )
        return abs_path

    # No inventory file path found
    logger.error("No inventory file specified")
    raise FileNotFoundError(
        "No inventory file specified. Please provide a path via command line argument or set the NETWORK_INVENTORY environment variable."
    )


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
            logger.error(f"{e}")
            sys.exit(1)  # Exit with error code

    try:
        device_inventory = parse_json_file(inventory_file)
        devices: Dict[str, Device] = {
            device["name"]: Device(**device) for device in device_inventory
        }
        logger.debug(
            f"Successfully loaded {len(devices)} devices from inventory {inventory_file}"
        )
        return devices
    except (FileNotFoundError, json.JSONDecodeError, IOError) as e:
        error_msg = (
            f"Error loading device inventory from {inventory_file}: {e}"
        )
        logger.error(error_msg)
        sys.exit(1)  # Exit with error code


def parse_json_file(json_file_path: str) -> DeviceInventory:
    """
    Parse a JSON file into a Python list of device dictionaries.

    Args:
        json_file_path: Path to the JSON file

    Returns:
        List of dictionaries representing network devices

    Raises:
        FileNotFoundError: If the file does not exist
        json.JSONDecodeError: If the file contains invalid JSON
        IOError: If there's an error reading the file
    """
    try:
        # Check if file exists
        abs_path = os.path.abspath(json_file_path)
        if not os.path.exists(abs_path):
            logger.error(f"File not found: {abs_path}")
            raise FileNotFoundError(f"File not found: {abs_path}")

        # Open and parse the JSON file with explicit encoding
        with open(abs_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        return cast(DeviceInventory, data)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON in {abs_path}: {e}")
        raise
    except FileNotFoundError:
        # Already logged in the check above
        raise
    except IOError as e:
        logger.error(f"IO error reading file {abs_path}: {e}")
        raise
