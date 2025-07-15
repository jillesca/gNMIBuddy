#!/usr/bin/env python3
"""
Tests for version_utils module.

Tests version comparison and parsing functionality for OpenConfig
model version verification.
"""

import pytest
from src.utils.version_utils import (
    parse_version_string,
    compare_versions,
    is_version_supported,
    get_version_info,
    format_version_comparison_message,
    VersionInfo,
)


class TestParseVersionString:
    """Test version string parsing functionality."""

    def test_parse_standard_version(self):
        """Test parsing standard semantic versions."""
        major, minor, patch, pre, build = parse_version_string("1.3.0")
        assert major == 1
        assert minor == 3
        assert patch == 0
        assert pre is None
        assert build is None

    def test_parse_version_with_prefix(self):
        """Test parsing versions with 'v' prefix."""
        major, minor, patch, pre, build = parse_version_string("v1.3.0")
        assert major == 1
        assert minor == 3
        assert patch == 0
        assert pre is None
        assert build is None

    def test_parse_version_with_prerelease(self):
        """Test parsing versions with pre-release identifiers."""
        major, minor, patch, pre, build = parse_version_string("1.3.0-alpha1")
        assert major == 1
        assert minor == 3
        assert patch == 0
        assert pre == "alpha1"
        assert build is None

    def test_parse_version_with_build(self):
        """Test parsing versions with build metadata."""
        major, minor, patch, pre, build = parse_version_string("1.3.0+build.1")
        assert major == 1
        assert minor == 3
        assert patch == 0
        assert pre is None
        assert build == "build.1"

    def test_parse_version_with_prerelease_and_build(self):
        """Test parsing versions with both pre-release and build."""
        major, minor, patch, pre, build = parse_version_string(
            "1.3.0-alpha+beta"
        )
        assert major == 1
        assert minor == 3
        assert patch == 0
        assert pre == "alpha"
        assert build == "beta"

    def test_parse_version_missing_patch(self):
        """Test parsing versions without patch number."""
        major, minor, patch, pre, build = parse_version_string("1.3")
        assert major == 1
        assert minor == 3
        assert patch == 0
        assert pre is None
        assert build is None

    def test_parse_version_missing_minor_and_patch(self):
        """Test parsing versions with only major number."""
        major, minor, patch, pre, build = parse_version_string("1")
        assert major == 1
        assert minor == 0
        assert patch == 0
        assert pre is None
        assert build is None

    def test_parse_invalid_version(self):
        """Test parsing invalid version strings."""
        with pytest.raises(ValueError):
            parse_version_string("invalid")

        with pytest.raises(ValueError):
            parse_version_string("")

    def test_parse_version_complex_prerelease(self):
        """Test parsing complex pre-release versions."""
        major, minor, patch, pre, build = parse_version_string("2.0.0-rc.1.2")
        assert major == 2
        assert minor == 0
        assert patch == 0
        assert pre == "rc.1.2"
        assert build is None


class TestCompareVersions:
    """Test version comparison functionality."""

    def test_compare_equal_versions(self):
        """Test comparing equal versions."""
        assert compare_versions("1.3.0", "1.3.0") == 0
        assert compare_versions("1.3", "1.3.0") == 0
        assert compare_versions("1", "1.0.0") == 0

    def test_compare_different_major(self):
        """Test comparing versions with different major numbers."""
        assert compare_versions("2.0.0", "1.9.9") == 1
        assert compare_versions("1.9.9", "2.0.0") == -1

    def test_compare_different_minor(self):
        """Test comparing versions with different minor numbers."""
        assert compare_versions("1.4.0", "1.3.9") == 1
        assert compare_versions("1.3.9", "1.4.0") == -1

    def test_compare_different_patch(self):
        """Test comparing versions with different patch numbers."""
        assert compare_versions("1.3.1", "1.3.0") == 1
        assert compare_versions("1.3.0", "1.3.1") == -1

    def test_compare_prerelease_versions(self):
        """Test comparing pre-release versions."""
        # Pre-release < normal version
        assert compare_versions("1.3.0-alpha", "1.3.0") == -1
        assert compare_versions("1.3.0", "1.3.0-alpha") == 1

        # Pre-release vs pre-release
        assert compare_versions("1.3.0-alpha", "1.3.0-beta") == -1
        assert compare_versions("1.3.0-beta", "1.3.0-alpha") == 1
        assert compare_versions("1.3.0-alpha", "1.3.0-alpha") == 0

    def test_compare_with_build_metadata(self):
        """Test comparing versions with build metadata."""
        # Build metadata should be ignored in comparison
        assert compare_versions("1.3.0+build1", "1.3.0+build2") == 0
        assert compare_versions("1.3.0+build1", "1.3.0") == 0

    def test_compare_invalid_versions(self):
        """Test comparing invalid version strings."""
        with pytest.raises(ValueError):
            compare_versions("invalid", "1.3.0")

        with pytest.raises(ValueError):
            compare_versions("1.3.0", "invalid")

    def test_compare_complex_prerelease(self):
        """Test comparing complex pre-release versions."""
        assert compare_versions("1.3.0-alpha.1", "1.3.0-alpha.2") == -1
        assert compare_versions("1.3.0-alpha.2", "1.3.0-alpha.1") == 1
        assert compare_versions("1.3.0-alpha.1", "1.3.0-alpha.1") == 0


class TestIsVersionSupported:
    """Test version support checking functionality."""

    def test_version_supported(self):
        """Test checking if version is supported."""
        assert is_version_supported("1.3.0", "1.3.0") is True
        assert is_version_supported("1.3.1", "1.3.0") is True
        assert is_version_supported("1.4.0", "1.3.0") is True
        assert is_version_supported("2.0.0", "1.3.0") is True

    def test_version_not_supported(self):
        """Test checking if version is not supported."""
        assert is_version_supported("1.2.9", "1.3.0") is False
        assert is_version_supported("1.3.0-alpha", "1.3.0") is False
        assert is_version_supported("0.9.0", "1.3.0") is False

    def test_version_supported_with_invalid_version(self):
        """Test checking support with invalid version strings."""
        assert is_version_supported("invalid", "1.3.0") is False
        assert is_version_supported("1.3.0", "invalid") is False


class TestGetVersionInfo:
    """Test version info extraction functionality."""

    def test_get_version_info_standard(self):
        """Test getting version info for standard version."""
        info = get_version_info("1.3.0")
        assert info.major == 1
        assert info.minor == 3
        assert info.patch == 0
        assert info.pre_release is None
        assert info.build is None
        assert info.original == "1.3.0"

    def test_get_version_info_with_prerelease(self):
        """Test getting version info with pre-release."""
        info = get_version_info("1.3.0-alpha1")
        assert info.major == 1
        assert info.minor == 3
        assert info.patch == 0
        assert info.pre_release == "alpha1"
        assert info.build is None
        assert info.original == "1.3.0-alpha1"

    def test_get_version_info_invalid(self):
        """Test getting version info for invalid version."""
        with pytest.raises(ValueError):
            get_version_info("invalid")


class TestFormatVersionComparisonMessage:
    """Test version comparison message formatting."""

    def test_format_supported_version(self):
        """Test formatting message for supported version."""
        message = format_version_comparison_message("1.3.1", "1.3.0")
        assert "1.3.1" in message
        assert "1.3.0" in message
        assert "meets minimum requirement" in message

    def test_format_unsupported_version(self):
        """Test formatting message for unsupported version."""
        message = format_version_comparison_message("1.2.9", "1.3.0")
        assert "1.2.9" in message
        assert "1.3.0" in message
        assert "older than minimum requirement" in message

    def test_format_invalid_version(self):
        """Test formatting message for invalid version."""
        message = format_version_comparison_message("invalid", "1.3.0")
        assert "Unable to compare versions" in message


class TestVersionInfo:
    """Test VersionInfo dataclass."""

    def test_version_info_creation(self):
        """Test creating VersionInfo objects."""
        info = VersionInfo(
            major=1,
            minor=3,
            patch=0,
            pre_release="alpha",
            build="build1",
            original="1.3.0-alpha+build1",
        )
        assert info.major == 1
        assert info.minor == 3
        assert info.patch == 0
        assert info.pre_release == "alpha"
        assert info.build == "build1"
        assert info.original == "1.3.0-alpha+build1"

    def test_version_info_defaults(self):
        """Test VersionInfo with default values."""
        info = VersionInfo(major=1, minor=3, patch=0)
        assert info.major == 1
        assert info.minor == 3
        assert info.patch == 0
        assert info.pre_release is None
        assert info.build is None
        assert info.original == ""
