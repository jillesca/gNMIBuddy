#!/usr/bin/env python3
"""Enhanced version information for gNMIBuddy CLI"""
import sys
import platform
import importlib.metadata
from typing import Dict, Optional, Any
from src.utils.version_utils import load_gnmibuddy_version
from src.logging.config import get_logger

logger = get_logger(__name__)


class VersionInfo:
    """Comprehensive version information provider"""

    def __init__(self):
        self._version_cache = {}
        self._build_info_cache = {}

    def get_gnmibuddy_version(self) -> str:
        """Get gNMIBuddy version"""
        if "gnmibuddy" not in self._version_cache:
            try:
                self._version_cache["gnmibuddy"] = load_gnmibuddy_version()
            except Exception as e:
                logger.warning("Could not load gNMIBuddy version: %s", e)
                self._version_cache["gnmibuddy"] = "unknown"
        return self._version_cache["gnmibuddy"]

    def get_python_version(self) -> Dict[str, str]:
        """Get detailed Python version information"""
        return {
            "version": sys.version.split()[0],
            "full_version": sys.version,
            "implementation": platform.python_implementation(),
            "compiler": platform.python_compiler(),
        }

    def get_platform_info(self) -> Dict[str, str]:
        """Get platform information"""
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "architecture": " ".join(platform.architecture()),
        }

    def get_dependency_versions(self) -> Dict[str, str]:
        """Get versions of key dependencies"""
        dependencies = {
            "click": self._get_package_version("click"),
            "pygnmi": self._get_package_version("pygnmi"),
            "networkx": self._get_package_version("networkx"),
            "pyyaml": self._get_package_version("pyyaml"),
            "mcp": self._get_package_version("mcp"),
        }

        # Filter out None values
        return {k: v for k, v in dependencies.items() if v is not None}

    def _get_package_version(self, package_name: str) -> Optional[str]:
        """Get version of a specific package"""
        try:
            return importlib.metadata.version(package_name)
        except importlib.metadata.PackageNotFoundError:
            try:
                # Try alternative package names
                alt_names = {
                    "pyyaml": "PyYAML",
                    "mcp": "mcp",
                }
                if package_name in alt_names:
                    return importlib.metadata.version(alt_names[package_name])
            except importlib.metadata.PackageNotFoundError:
                pass
        except Exception as e:
            logger.debug("Error getting version for %s: %s", package_name, e)
        return None

    def get_build_info(self) -> Dict[str, Any]:
        """Get build information if available"""
        if not self._build_info_cache:
            try:
                # Try to get build information from various sources
                build_info = {
                    "python_executable": sys.executable,
                    "python_path": sys.path[0] if sys.path else "unknown",
                }

                # Add Git information if available
                try:
                    import subprocess
                    import os

                    # Check if we're in a git repository
                    if os.path.exists(".git"):
                        try:
                            # Get Git commit hash
                            result = subprocess.run(
                                ["git", "rev-parse", "HEAD"],
                                capture_output=True,
                                text=True,
                                check=True,
                                timeout=5,
                            )
                            build_info["git_commit"] = result.stdout.strip()[
                                :8
                            ]
                        except (
                            subprocess.CalledProcessError,
                            subprocess.TimeoutExpired,
                            FileNotFoundError,
                        ):
                            pass

                        try:
                            # Get Git branch
                            result = subprocess.run(
                                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                                capture_output=True,
                                text=True,
                                check=True,
                                timeout=5,
                            )
                            build_info["git_branch"] = result.stdout.strip()
                        except (
                            subprocess.CalledProcessError,
                            subprocess.TimeoutExpired,
                            FileNotFoundError,
                        ):
                            pass

                        try:
                            # Check if there are uncommitted changes
                            result = subprocess.run(
                                ["git", "status", "--porcelain"],
                                capture_output=True,
                                text=True,
                                check=True,
                                timeout=5,
                            )
                            build_info["git_dirty"] = bool(
                                result.stdout.strip()
                            )
                        except (
                            subprocess.CalledProcessError,
                            subprocess.TimeoutExpired,
                            FileNotFoundError,
                        ):
                            pass

                except Exception as e:
                    logger.debug("Could not get Git information: %s", e)

                self._build_info_cache = build_info
            except Exception as e:
                logger.debug("Error getting build info: %s", e)
                self._build_info_cache = {}

        return self._build_info_cache

    def get_comprehensive_version_info(self) -> Dict[str, Any]:
        """Get all version information in a structured format"""
        return {
            "gnmibuddy": {
                "version": self.get_gnmibuddy_version(),
                "build": self.get_build_info(),
            },
            "python": self.get_python_version(),
            "platform": self.get_platform_info(),
            "dependencies": self.get_dependency_versions(),
        }

    def format_version_output(self, detailed: bool = False) -> str:
        """Format version information for display"""
        gnmibuddy_version = self.get_gnmibuddy_version()
        python_info = self.get_python_version()

        if not detailed:
            # Simple version output
            return f"gNMIBuddy {gnmibuddy_version} (Python {python_info['version']})"

        # Detailed version output
        lines = []
        lines.append(f"gNMIBuddy {gnmibuddy_version}")
        lines.append("")

        # Python information
        lines.append("Python:")
        lines.append(f"  Version: {python_info['version']}")
        lines.append(f"  Implementation: {python_info['implementation']}")
        lines.append(f"  Compiler: {python_info['compiler']}")
        lines.append("")

        # Platform information
        platform_info = self.get_platform_info()
        lines.append("Platform:")
        lines.append(
            f"  System: {platform_info['system']} {platform_info['release']}"
        )
        lines.append(f"  Machine: {platform_info['machine']}")
        lines.append(f"  Architecture: {platform_info['architecture']}")
        lines.append("")

        # Dependencies
        deps = self.get_dependency_versions()
        if deps:
            lines.append("Dependencies:")
            for name, version in sorted(deps.items()):
                lines.append(f"  {name}: {version}")
            lines.append("")

        # Build information
        build_info = self.get_build_info()
        if build_info:
            lines.append("Build Information:")
            for key, value in build_info.items():
                if key.startswith("git_"):
                    key_display = key.replace("git_", "Git ")
                    if key == "git_dirty":
                        value = "Yes" if value else "No"
                        key_display = "Git dirty"
                else:
                    key_display = key.replace("_", " ").title()
                lines.append(f"  {key_display}: {value}")

        return "\n".join(lines)


# Global version info instance
version_info = VersionInfo()


def get_version_info(detailed: bool = False) -> str:
    """
    Get formatted version information

    Args:
        detailed: Whether to include detailed information

    Returns:
        Formatted version string
    """
    return version_info.format_version_output(detailed=detailed)


def get_version_dict() -> Dict[str, Any]:
    """
    Get version information as a dictionary

    Returns:
        Dictionary containing comprehensive version information
    """
    return version_info.get_comprehensive_version_info()


def print_version(detailed: bool = False):
    """
    Print version information to stdout

    Args:
        detailed: Whether to include detailed information
    """
    print(get_version_info(detailed=detailed))
