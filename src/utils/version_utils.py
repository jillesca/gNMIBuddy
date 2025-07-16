#!/usr/bin/env python3
"""
Version comparison utilities for gNMIBuddy.

Provides semantic version comparison and parsing functions for OpenConfig
model version verification.
"""

import re
from typing import Tuple, Optional
from dataclasses import dataclass
from ..schemas.openconfig_models import OpenConfigModel, get_model_requirement
from ..schemas.verification_results import VerificationStatus


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


@dataclass
class VersionValidationResult:
    """
    Result of validating a model version against requirements.

    Attributes:
        model: The OpenConfig model being validated
        status: The validation status
        found_version: The version found on the device
        required_version: The minimum required version
        message: Human-readable validation message
        warning_message: Optional warning message for version issues
        error_message: Optional error message for failures
    """

    model: OpenConfigModel
    status: VerificationStatus
    found_version: Optional[str] = None
    required_version: str = ""
    message: str = ""
    warning_message: Optional[str] = None
    error_message: Optional[str] = None


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


def validate_model_version(
    model: OpenConfigModel, found_version: str
) -> VersionValidationResult:
    """
    Validate a found model version against the required version for the model.

    Args:
        model: The OpenConfig model to validate
        found_version: The version found on the device

    Returns:
        VersionValidationResult with validation status and messages

    Raises:
        ValueError: If the model is not supported or version cannot be parsed
    """
    try:
        # Get the model requirement from the registry
        requirement = get_model_requirement(model)
        required_version = requirement.min_version

        # Parse both versions to ensure they're valid
        parse_version_string(found_version)
        parse_version_string(required_version)

        # Compare versions
        comparison = compare_versions(found_version, required_version)

        warning_message = None
        if comparison >= 0:
            # Version meets or exceeds requirement
            status = VerificationStatus.SUPPORTED
            message = f"Model {model.value} version {found_version} meets minimum requirement {required_version}"
        else:
            # Version is older than requirement
            status = VerificationStatus.VERSION_WARNING
            message = f"Model {model.value} version {found_version} is older than minimum requirement {required_version}"
            warning_message = (
                f"Device has {model.value} v{found_version} but minimum required is v{required_version}. "
                f"Some features may not work correctly."
            )

        return VersionValidationResult(
            model=model,
            status=status,
            found_version=found_version,
            required_version=required_version,
            message=message,
            warning_message=warning_message,
        )

    except ValueError as e:
        # Version parsing failed
        error_message = (
            f"Failed to validate {model.value} version {found_version}: {e}"
        )
        return VersionValidationResult(
            model=model,
            status=VerificationStatus.ERROR,
            found_version=found_version,
            required_version=get_model_requirement(model).min_version,
            message=error_message,
            error_message=error_message,
        )
    except KeyError:
        # Model not found in registry
        error_message = f"Model {model.value} is not supported by this version of gNMIBuddy"
        return VersionValidationResult(
            model=model,
            status=VerificationStatus.ERROR,
            found_version=found_version,
            message=error_message,
            error_message=error_message,
        )


def get_model_specific_version_message(
    model: OpenConfigModel, found_version: str, required_version: str
) -> str:
    """
    Get a model-specific version comparison message with context.

    Args:
        model: The OpenConfig model
        found_version: Version found on device
        required_version: Minimum required version

    Returns:
        Formatted comparison message with model context
    """
    try:
        requirement = get_model_requirement(model)
        comparison = compare_versions(found_version, required_version)

        if comparison >= 0:
            return (
                f"{model.value} v{found_version} is supported "
                f"(minimum required: v{required_version}). "
                f"Used for: {requirement.description}"
            )
        else:
            return (
                f"{model.value} v{found_version} is older than required v{required_version}. "
                f"This may cause issues with: {requirement.description}"
            )
    except (ValueError, KeyError) as e:
        return f"Unable to validate {model.value} version {found_version}: {e}"
