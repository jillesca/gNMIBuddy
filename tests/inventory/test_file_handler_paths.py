#!/usr/bin/env python3
"""
Tests for inventory file handler path handling.
Tests both absolute and relative path functionality.
"""

import os
import sys
import json
import tempfile
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
    resolve_inventory_path,  # Add the new function
)


class TestFileHandlerPaths:
    """Tests for path handling in file_handler module."""

    @pytest.fixture
    def sample_inventory_data(self):
        """Sample inventory data for testing."""
        return [
            {
                "ip_address": "10.0.0.1",
                "nos": "iosxr",
                "port": 57777,
                "username": "test_user",
                "password": "test_pass",
                "name": "test-device-1",
            },
            {
                "ip_address": "10.0.0.2",
                "nos": "iosxr",
                "port": 57777,
                "username": "test_user",
                "password": "test_pass",
                "name": "test-device-2",
            },
        ]

    @pytest.fixture
    def temp_inventory_file(self, sample_inventory_data):
        """Create a temporary inventory file for testing."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(sample_inventory_data, f, indent=2)
            temp_file_path = f.name

        yield temp_file_path

        # Cleanup
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

    def test_parse_json_file_absolute_path(self, temp_inventory_file):
        """Test parsing JSON file with absolute path."""
        absolute_path = os.path.abspath(temp_inventory_file)

        result = parse_json_file(absolute_path)

        assert len(result) == 2
        assert result[0]["name"] == "test-device-1"
        assert result[1]["name"] == "test-device-2"

    def test_parse_json_file_relative_path(self, temp_inventory_file):
        """Test parsing JSON file with relative path."""
        # Get the directory containing the temp file
        temp_dir = os.path.dirname(temp_inventory_file)
        temp_filename = os.path.basename(temp_inventory_file)

        # Change to the temp directory and use relative path
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            # Use just the filename as a relative path
            result = parse_json_file(temp_filename)

            assert len(result) == 2
            assert result[0]["name"] == "test-device-1"
            assert result[1]["name"] == "test-device-2"
        finally:
            os.chdir(original_cwd)

    def test_parse_json_file_relative_path_with_subdirs(
        self, temp_inventory_file, sample_inventory_data
    ):
        """Test parsing JSON file with relative path including subdirectories."""
        # Create a subdirectory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            sub_dir = os.path.join(temp_dir, "config", "inventory")
            os.makedirs(sub_dir, exist_ok=True)

            # Create inventory file in subdirectory
            inventory_file = os.path.join(sub_dir, "devices.json")
            with open(inventory_file, "w") as f:
                json.dump(sample_inventory_data, f, indent=2)

            # Change to temp_dir and use relative path
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                relative_path = os.path.join(
                    "config", "inventory", "devices.json"
                )

                result = parse_json_file(relative_path)

                assert len(result) == 2
                assert result[0]["name"] == "test-device-1"
                assert result[1]["name"] == "test-device-2"
            finally:
                os.chdir(original_cwd)

    def test_get_inventory_path_cli_absolute(self, temp_inventory_file):
        """Test get_inventory_path with absolute CLI path."""
        absolute_path = os.path.abspath(temp_inventory_file)

        result = get_inventory_path(cli_path=absolute_path)

        assert result == absolute_path

    def test_get_inventory_path_cli_relative(self, temp_inventory_file):
        """Test get_inventory_path with relative CLI path."""
        # Get relative path from current directory
        relative_path = os.path.relpath(temp_inventory_file)

        result = get_inventory_path(cli_path=relative_path)

        # get_inventory_path should convert to absolute path
        expected_absolute = os.path.abspath(relative_path)
        assert result == expected_absolute

    def test_get_inventory_path_env_absolute(self, temp_inventory_file):
        """Test get_inventory_path with absolute path from environment variable."""
        absolute_path = os.path.abspath(temp_inventory_file)

        with patch.dict(os.environ, {"NETWORK_INVENTORY": absolute_path}):
            result = get_inventory_path()

            assert result == absolute_path

    def test_get_inventory_path_env_relative(self, sample_inventory_data):
        """Test get_inventory_path with relative path from environment variable."""
        # Create a temporary file that we control
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(sample_inventory_data, f, indent=2)
            temp_file_path = f.name

        try:
            # Create relative path from the same temp file
            relative_path = os.path.relpath(temp_file_path)

            # Mock the settings to return our relative path
            with patch(
                "src.inventory.file_handler.get_settings"
            ) as mock_get_settings:
                mock_settings = mock_get_settings.return_value
                mock_settings.get_network_inventory.return_value = (
                    relative_path
                )

                result = get_inventory_path()

                # Should convert to absolute path - verify it's the same resolved path
                expected_absolute = os.path.abspath(relative_path)
                assert result == expected_absolute

                # Also verify the result points to the same file as the original
                assert os.path.samefile(result, temp_file_path)
        finally:
            # Cleanup
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_load_inventory_absolute_path(self, temp_inventory_file):
        """Test load_inventory with absolute path."""
        absolute_path = os.path.abspath(temp_inventory_file)

        devices = load_inventory(inventory_file=absolute_path)

        assert len(devices) == 2
        assert "test-device-1" in devices
        assert "test-device-2" in devices
        assert devices["test-device-1"].ip_address == "10.0.0.1"

    def test_load_inventory_relative_path(self, temp_inventory_file):
        """Test load_inventory with relative path."""
        # Get the directory containing the temp file
        temp_dir = os.path.dirname(temp_inventory_file)
        temp_filename = os.path.basename(temp_inventory_file)

        # Change to the temp directory and use relative path
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)

            devices = load_inventory(inventory_file=temp_filename)

            assert len(devices) == 2
            assert "test-device-1" in devices
            assert "test-device-2" in devices
            assert devices["test-device-1"].ip_address == "10.0.0.1"
        finally:
            os.chdir(original_cwd)

    def test_nonexistent_relative_path(self):
        """Test that nonexistent relative paths are handled correctly."""
        nonexistent_relative = "nonexistent/path/to/inventory.json"

        with pytest.raises(FileNotFoundError) as excinfo:
            parse_json_file(nonexistent_relative)

        # Error message should include the absolute path that was attempted
        expected_abs_path = os.path.abspath(nonexistent_relative)
        assert f"File not found: {expected_abs_path}" in str(excinfo.value)

    def test_current_directory_relative_path(self, sample_inventory_data):
        """Test relative path in current directory (./filename)."""
        # Create a temporary file in current directory
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, dir="."
        ) as f:
            json.dump(sample_inventory_data, f, indent=2)
            temp_filename = os.path.basename(f.name)

        try:
            # Test with './filename' format
            dot_relative_path = f"./{temp_filename}"
            result = parse_json_file(dot_relative_path)

            assert len(result) == 2
            assert result[0]["name"] == "test-device-1"

            # Test with just 'filename' format
            result2 = parse_json_file(temp_filename)

            assert len(result2) == 2
            assert result2[0]["name"] == "test-device-1"

        finally:
            # Cleanup
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

    def test_path_normalization(self, sample_inventory_data):
        """Test that paths with .. and . are normalized correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create nested directory structure
            sub_dir = os.path.join(temp_dir, "sub")
            os.makedirs(sub_dir, exist_ok=True)

            # Create inventory file
            inventory_file = os.path.join(temp_dir, "inventory.json")
            with open(inventory_file, "w") as f:
                json.dump(sample_inventory_data, f, indent=2)

            # Change to subdirectory
            original_cwd = os.getcwd()
            try:
                os.chdir(sub_dir)

                # Use path with .. to go up and access the file
                relative_path_with_parent = "../inventory.json"

                result = parse_json_file(relative_path_with_parent)

                assert len(result) == 2
                assert result[0]["name"] == "test-device-1"

            finally:
                os.chdir(original_cwd)

    def test_resolve_inventory_path_absolute(self, temp_inventory_file):
        """Test resolve_inventory_path with absolute path."""
        absolute_path = os.path.abspath(temp_inventory_file)

        result = resolve_inventory_path(absolute_path)

        assert result == absolute_path

    def test_resolve_inventory_path_relative(self, temp_inventory_file):
        """Test resolve_inventory_path with relative path."""
        # Get the directory containing the temp file
        temp_dir = os.path.dirname(temp_inventory_file)
        temp_filename = os.path.basename(temp_inventory_file)

        # Change to the temp directory and use relative path
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)

            result = resolve_inventory_path(temp_filename)

            # Should return absolute path
            expected_absolute = os.path.abspath(temp_filename)
            assert result == expected_absolute
        finally:
            os.chdir(original_cwd)

    def test_resolve_inventory_path_nonexistent_with_helpful_error(self):
        """Test that resolve_inventory_path provides helpful error messages for nonexistent files."""
        nonexistent_file = "nonexistent_inventory.json"

        with pytest.raises(FileNotFoundError) as excinfo:
            resolve_inventory_path(nonexistent_file)

        error_msg = str(excinfo.value)
        # Should include absolute path that was attempted
        expected_abs_path = os.path.abspath(nonexistent_file)
        assert f"File not found: {expected_abs_path}" in error_msg

        # Should mention it's a relative path and current directory
        assert "relative path" in error_msg
        assert "current directory" in error_msg

    def test_resolve_inventory_path_suggests_alternatives(
        self, sample_inventory_data
    ):
        """Test that resolve_inventory_path suggests alternatives when file is not found."""
        # Create a file in project root to simulate the scenario
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock project structure
            project_dir = os.path.join(temp_dir, "project")
            os.makedirs(project_dir)

            # Create pyproject.toml to mark it as project root
            pyproject_file = os.path.join(project_dir, "pyproject.toml")
            with open(pyproject_file, "w") as f:
                f.write("[tool.poetry]\nname = 'test'\n")

            # Create inventory file in project root
            inventory_file = os.path.join(project_dir, "inventory.json")
            with open(inventory_file, "w") as f:
                json.dump(sample_inventory_data, f)

            # Create subdirectory and try to access inventory from there
            sub_dir = os.path.join(project_dir, "subdir")
            os.makedirs(sub_dir)

            original_cwd = os.getcwd()
            try:
                os.chdir(sub_dir)

                with pytest.raises(FileNotFoundError) as excinfo:
                    resolve_inventory_path("inventory.json")

                error_msg = str(excinfo.value)
                # Should suggest the correct path
                assert (
                    "Did you mean:" in error_msg
                    or "Make sure you're running from the correct directory"
                    in error_msg
                )

            finally:
                os.chdir(original_cwd)
