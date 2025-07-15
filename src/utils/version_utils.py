#!/usr/bin/env python3
"""
Version comparison utilities for gNMIBuddy.

Provides semantic version comparison and parsing functions for OpenConfig
model version verification.
"""

import re
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class VersionInfo:
    """
    Parsed version information.

    Attributes:
        major: Major version number
        minor: Minor version number
        patch: Patch version number
        pre_release: Pre-release identifier (optional)
        build: Build metadata (optional)
        original: Original version string
    """

    major: int
    minor: int
    patch: int
    pre_release: Optional[str] = None
    build: Optional[str] = None
    original: str = ""


def parse_version_string(
    version: str,
) -> Tuple[int, int, int, Optional[str], Optional[str]]:
    """
    Parse a version string into semantic version components.

    Supports various version formats:
    - Standard semantic: "1.3.0", "2.1.5"
    - With pre-release: "1.3.0-alpha1", "2.0.0-rc.1"
    - With build: "1.3.0+build.1", "2.0.0-alpha+beta"
    - Non-standard: "1.3", "1", "v1.3.0"

    Args:
        version: Version string to parse

    Returns:
        Tuple of (major, minor, patch, pre_release, build)

    Raises:
        ValueError: If version string cannot be parsed
    """
    if not version or not isinstance(version, str):
        raise ValueError(f"Invalid version string: {version}")

    # Remove common prefixes
    clean_version = version.strip()
    if clean_version.lower().startswith("v"):
        clean_version = clean_version[1:]

    # Regex for semantic version parsing
    # Matches: major.minor.patch[-pre-release][+build]
    pattern = r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:-([a-zA-Z0-9.-]+))?(?:\+([a-zA-Z0-9.-]+))?$"

    match = re.match(pattern, clean_version)
    if not match:
        raise ValueError(f"Invalid version format: {version}")

    major_str, minor_str, patch_str, pre_release, build = match.groups()

    # Parse version components
    major = int(major_str)
    minor = int(minor_str) if minor_str else 0
    patch = int(patch_str) if patch_str else 0

    return major, minor, patch, pre_release, build


def compare_versions(version1: str, version2: str) -> int:
    """
    Compare two version strings using semantic versioning rules.

    Args:
        version1: First version string
        version2: Second version string

    Returns:
        -1 if version1 < version2
         0 if version1 == version2
         1 if version1 > version2

    Raises:
        ValueError: If either version string cannot be parsed
    """
    try:
        v1_major, v1_minor, v1_patch, v1_pre, _ = parse_version_string(
            version1
        )
        v2_major, v2_minor, v2_patch, v2_pre, _ = parse_version_string(
            version2
        )
    except ValueError as e:
        raise ValueError(f"Version comparison failed: {e}") from e

    # Compare major.minor.patch
    if v1_major != v2_major:
        return 1 if v1_major > v2_major else -1
    if v1_minor != v2_minor:
        return 1 if v1_minor > v2_minor else -1
    if v1_patch != v2_patch:
        return 1 if v1_patch > v2_patch else -1

    # Handle pre-release versions
    # Per semantic versioning: pre-release < normal version
    if v1_pre and not v2_pre:
        return -1  # version1 is pre-release, version2 is normal
    if not v1_pre and v2_pre:
        return 1  # version1 is normal, version2 is pre-release
    if v1_pre and v2_pre:
        # Both are pre-release, compare pre-release identifiers
        return _compare_pre_release(v1_pre, v2_pre)

    # Both are normal versions and major.minor.patch are equal
    return 0


def _compare_pre_release(pre1: str, pre2: str) -> int:
    """
    Compare pre-release version identifiers.

    Args:
        pre1: First pre-release identifier
        pre2: Second pre-release identifier

    Returns:
        -1 if pre1 < pre2, 0 if equal, 1 if pre1 > pre2
    """
    # Split by dots and compare each part
    parts1 = pre1.split(".")
    parts2 = pre2.split(".")

    for i in range(max(len(parts1), len(parts2))):
        part1 = parts1[i] if i < len(parts1) else ""
        part2 = parts2[i] if i < len(parts2) else ""

        # Try to compare as numbers first
        try:
            num1 = int(part1) if part1 else 0
            num2 = int(part2) if part2 else 0
            if num1 != num2:
                return 1 if num1 > num2 else -1
        except ValueError:
            # Compare as strings
            if part1 != part2:
                return 1 if part1 > part2 else -1

    return 0


def is_version_supported(found_version: str, required_version: str) -> bool:
    """
    Check if a found version meets the minimum required version.

    Args:
        found_version: Version found on device
        required_version: Minimum required version

    Returns:
        True if found_version >= required_version, False otherwise

    Raises:
        ValueError: If either version string cannot be parsed
    """
    try:
        return compare_versions(found_version, required_version) >= 0
    except ValueError:
        return False


def get_version_info(version: str) -> VersionInfo:
    """
    Get detailed version information from a version string.

    Args:
        version: Version string to parse

    Returns:
        VersionInfo object with parsed components

    Raises:
        ValueError: If version string cannot be parsed
    """
    major, minor, patch, pre_release, build = parse_version_string(version)
    return VersionInfo(
        major=major,
        minor=minor,
        patch=patch,
        pre_release=pre_release,
        build=build,
        original=version,
    )


def format_version_comparison_message(
    found_version: str, required_version: str
) -> str:
    """
    Format a human-readable message about version comparison.

    Args:
        found_version: Version found on device
        required_version: Minimum required version

    Returns:
        Formatted comparison message
    """
    try:
        comparison = compare_versions(found_version, required_version)
        if comparison >= 0:
            return f"Version {found_version} meets minimum requirement {required_version}"
        else:
            return f"Version {found_version} is older than minimum requirement {required_version}"
    except ValueError as e:
        return f"Unable to compare versions: {e}"
