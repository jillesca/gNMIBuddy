#!/usr/bin/env python3
"""
Log file path generation utilities.

This module handles log file path generation, including sequential
numbering and project root detection, following the Single Responsibility Principle.
"""

import os
import glob
import re
from pathlib import Path
from typing import Optional


class LogFilePathGenerator:
    """
    Generates log file paths with sequential numbering.

    Handles the creation of numbered log files like:
    - gnmibuddy_001.log
    - gnmibuddy_002.log
    - gnmibuddy_003.log

    Encapsulates all file path logic in one place for better maintainability.
    """

    DEFAULT_BASE_NAME = "gnmibuddy"
    DEFAULT_LOG_DIR = "logs"

    @classmethod
    def get_next_log_file_path(
        cls, log_dir: Optional[Path] = None, base_name: str = DEFAULT_BASE_NAME
    ) -> Path:
        """
        Generate the next sequential log file path.

        Args:
            log_dir: Directory where log files are stored (defaults to project_root/logs)
            base_name: Base name for the log files

        Returns:
            Path to the next sequential log file
        """
        if log_dir is None:
            project_root = cls._get_project_root()
            log_dir = project_root / cls.DEFAULT_LOG_DIR

        # Ensure log directory exists
        log_dir.mkdir(parents=True, exist_ok=True)

        # Find the next sequential number
        next_number = cls._find_next_sequence_number(log_dir, base_name)

        # Generate the new filename with zero-padded number
        new_filename = f"{base_name}_{next_number:03d}.log"
        return log_dir / new_filename

    @classmethod
    def _find_next_sequence_number(cls, log_dir: Path, base_name: str) -> int:
        """
        Find the next sequential number for log files.

        Args:
            log_dir: Directory to search for existing log files
            base_name: Base name pattern to match

        Returns:
            Next sequential number to use
        """
        # Pattern to match existing log files
        pattern = str(log_dir / f"{base_name}_*.log")
        existing_files = glob.glob(pattern)

        # Extract numbers from existing files
        numbers = []
        number_pattern = re.compile(rf"{re.escape(base_name)}_(\d+)\.log$")

        for file_path in existing_files:
            filename = os.path.basename(file_path)
            match = number_pattern.match(filename)
            if match:
                numbers.append(int(match.group(1)))

        # Find the next number
        return max(numbers) + 1 if numbers else 1

    @classmethod
    def _get_project_root(cls) -> Path:
        """
        Get the project root directory reliably.

        Walks up from this file's location to find the project root,
        identified by the presence of key project files.

        Returns:
            Path to the project root directory
        """
        # Start from this file's location
        current_path = Path(__file__).resolve()

        # Walk up the directory tree looking for project indicators
        for parent in current_path.parents:
            # Look for common project root indicators
            indicators = [
                parent / "pyproject.toml",
                parent / "setup.py",
                parent / "requirements.txt",
                parent / ".git",
                parent / "gnmibuddy.py",  # Our main script
            ]

            if any(indicator.exists() for indicator in indicators):
                return parent

        # Fallback: go up three levels from src/logging/config/file_utils.py
        # This matches the original behavior
        return current_path.parent.parent.parent.parent

    @classmethod
    def get_log_directory(cls, custom_log_dir: Optional[str] = None) -> Path:
        """
        Get the log directory path.

        Args:
            custom_log_dir: Custom log directory override

        Returns:
            Path to the log directory
        """
        if custom_log_dir:
            return Path(custom_log_dir)

        project_root = cls._get_project_root()
        return project_root / cls.DEFAULT_LOG_DIR

    @classmethod
    def list_existing_log_files(
        cls, log_dir: Optional[Path] = None, base_name: str = DEFAULT_BASE_NAME
    ) -> list[Path]:
        """
        List existing log files in chronological order.

        Args:
            log_dir: Directory to search (defaults to project logs directory)
            base_name: Base name pattern to match

        Returns:
            List of log file paths, sorted by sequence number
        """
        if log_dir is None:
            log_dir = cls.get_log_directory()

        if not log_dir.exists():
            return []

        # Find matching log files
        pattern = f"{base_name}_*.log"
        log_files = list(log_dir.glob(pattern))

        # Sort by sequence number
        number_pattern = re.compile(rf"{re.escape(base_name)}_(\d+)\.log$")

        def extract_number(file_path: Path) -> int:
            match = number_pattern.match(file_path.name)
            return int(match.group(1)) if match else 0

        return sorted(log_files, key=extract_number)

    @classmethod
    def get_latest_log_file(
        cls, log_dir: Optional[Path] = None, base_name: str = DEFAULT_BASE_NAME
    ) -> Optional[Path]:
        """
        Get the most recent log file.

        Args:
            log_dir: Directory to search (defaults to project logs directory)
            base_name: Base name pattern to match

        Returns:
            Path to the latest log file, or None if no log files exist
        """
        log_files = cls.list_existing_log_files(log_dir, base_name)
        return log_files[-1] if log_files else None
