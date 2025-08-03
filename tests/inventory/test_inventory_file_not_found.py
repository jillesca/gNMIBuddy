#!/usr/bin/env python3
"""
Tests for inventory file handling, specifically focusing on error cases
such as when an inventory file is not found.
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch

# Ensure the project root is in the Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.inventory.file_handler import (
    get_inventory_path,
    load_inventory,
    parse_json_file,
)


class TestInventoryFileNotFound:
    """Tests for the error handling when inventory files are not found."""

    def test_get_inventory_path_nonexistent(self):
        """Test that get_inventory_path raises FileNotFoundError when no inventory path is specified."""
        # Ensure NETWORK_INVENTORY environment variable is not set and mock settings
        with patch.dict(os.environ, {}, clear=True):
            # Mock the centralized settings to return None for network_inventory
            with patch(
                "src.inventory.file_handler.get_settings"
            ) as mock_get_settings:
                mock_settings = mock_get_settings.return_value
                mock_settings.get_network_inventory.return_value = None

                with pytest.raises(FileNotFoundError) as excinfo:
                    get_inventory_path()

                # Check that the error message is informative
                assert "No inventory file specified" in str(excinfo.value)

    def test_parse_json_file_nonexistent(self):
        """Test that parse_json_file raises FileNotFoundError for a non-existent file."""
        nonexistent_file = "nonexistent_inventory_file.json"

        with pytest.raises(FileNotFoundError) as excinfo:
            parse_json_file(nonexistent_file)

        # Check that the error message includes the filename
        assert f"File not found: {os.path.abspath(nonexistent_file)}" in str(
            excinfo.value
        )

    def test_load_inventory_nonexistent_cli_path(self):
        """Test that load_inventory raises FileNotFoundError when a non-existent CLI path is provided."""
        nonexistent_file = "nonexistent_inventory_file.json"

        # Verify that FileNotFoundError is raised
        with pytest.raises(FileNotFoundError) as exc_info:
            load_inventory(nonexistent_file)

        # Verify error message contains expected content
        assert "Error loading device inventory" in str(exc_info.value)

    def test_load_inventory_nonexistent_env_path(self):
        """Test that load_inventory raises FileNotFoundError when a non-existent environment variable path is used."""
        # Set a non-existent file path in the environment variable
        nonexistent_file = "nonexistent_env_inventory.json"

        with patch.dict(os.environ, {"NETWORK_INVENTORY": nonexistent_file}):
            # Verify that FileNotFoundError is raised
            with pytest.raises(FileNotFoundError) as exc_info:
                # Call without CLI path, so it falls back to env var
                load_inventory()

            # Verify error message contains expected content
            assert "Error loading device inventory" in str(exc_info.value)
