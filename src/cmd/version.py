#!/usr/bin/env python3
"""Version information utilities for gNMIBuddy CLI"""
import sys
import platform
import importlib.metadata
from typing import Dict, Any, Optional
from src.utils.version_utils import load_gnmibuddy_version, get_python_version
from src.logging.config import get_logger

logger = get_logger(__name__)


# Version output templates - separated from logic for better readability
SIMPLE_VERSION_TEMPLATE = (
    "gNMIBuddy {gnmibuddy_version} (Python {python_version})"
)

DETAILED_VERSION_TEMPLATE = """gNMIBuddy {gnmibuddy_version}

Python:
  Version: {python_version}
  Implementation: {python_implementation}
  Compiler: {python_compiler}

Platform:
  System: {system} {release}
  Machine: {machine}
  Architecture: {architecture}

{dependencies_section}

{build_section}"""

DEPENDENCIES_SECTION_TEMPLATE = """Dependencies:
{dependency_list}"""

BUILD_SECTION_TEMPLATE = """Build Information:
{build_list}"""


class VersionInfo:
    """Centralized version information manager"""

    def __init__(self):
        self._gnmibuddy_version = None
        self._python_info = None
        self._platform_info = None
        self._dependencies = None

    def get_gnmibuddy_version(self) -> str:
        """Get gNMIBuddy version"""
        if self._gnmibuddy_version is None:
            self._gnmibuddy_version = load_gnmibuddy_version()
        return self._gnmibuddy_version

    def get_python_version(self) -> Dict[str, str]:
        """Get Python version information"""
        if self._python_info is None:
            self._python_info = get_python_version()
        return self._python_info

    def get_platform_info(self) -> Dict[str, str]:
        """Get platform information"""
        if self._platform_info is None:
            uname = platform.uname()
            self._platform_info = {
                "system": uname.system,
                "release": uname.release,
                "version": uname.version,
                "machine": uname.machine,
                "processor": uname.processor,
                "architecture": platform.architecture()[0],
            }
        return self._platform_info

    def get_dependency_versions(self) -> Dict[str, str]:
        """Get versions of key dependencies"""
        if self._dependencies is None:
            dependencies = [
                "click",
                "pyyaml",
                "grpcio",
                "protobuf",
                "cryptography",
            ]

            versions = {}
            for dep in dependencies:
                version = self._get_package_version(dep)
                if version:
                    versions[dep] = version

            self._dependencies = versions

        return self._dependencies

    def _get_package_version(self, package_name: str) -> Optional[str]:
        """Get version of a specific package"""
        try:
            return importlib.metadata.version(package_name)
        except importlib.metadata.PackageNotFoundError:
            try:
                # Try alternative import method
                module = importlib.import_module(package_name)
                if hasattr(module, "__version__"):
                    return str(module.__version__)
                elif hasattr(module, "version"):
                    return str(module.version)
            except ImportError:
                pass
        except Exception as e:
            logger.debug("Error getting version for %s: %s", package_name, e)
        return None

    def get_build_info(self) -> Dict[str, Any]:
        """Get build information (git info, etc.)"""
        try:
            import subprocess

            build_info = {}

            # Try to get git information
            try:
                # Git commit hash
                result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    build_info["git_commit"] = result.stdout.strip()[:8]

                # Git branch
                result = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    build_info["git_branch"] = result.stdout.strip()

                # Git dirty status
                result = subprocess.run(
                    ["git", "diff", "--quiet"],
                    capture_output=True,
                    timeout=5,
                )
                build_info["git_dirty"] = result.returncode != 0

                # Git tag
                result = subprocess.run(
                    ["git", "describe", "--tags", "--exact-match"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    build_info["git_tag"] = result.stdout.strip()

            except (subprocess.TimeoutExpired, FileNotFoundError):
                # Git not available or timeout
                pass

            # Add Python executable path
            build_info["python_executable"] = sys.executable

            return build_info

        except Exception as e:
            logger.debug("Error getting build info: %s", e)
            return {}

    def get_comprehensive_version_info(self) -> Dict[str, Any]:
        """Get all version information as a structured dictionary"""
        return {
            "gnmibuddy": {
                "version": self.get_gnmibuddy_version(),
            },
            "python": self.get_python_version(),
            "platform": self.get_platform_info(),
            "dependencies": self.get_dependency_versions(),
            "build": self.get_build_info(),
        }

    def _format_dependency_list(self, dependencies: Dict[str, str]) -> str:
        """Format dependencies as an indented list."""
        if not dependencies:
            return ""

        dep_lines = []
        for name, version in sorted(dependencies.items()):
            dep_lines.append(f"  {name}: {version}")

        return "\n".join(dep_lines)

    def _format_build_list(self, build_info: Dict[str, Any]) -> str:
        """Format build information as an indented list."""
        if not build_info:
            return ""

        build_lines = []
        for key, value in build_info.items():
            if key.startswith("git_"):
                key_display = key.replace("git_", "Git ")
                if key == "git_dirty":
                    value = "Yes" if value else "No"
                    key_display = "Git dirty"
            else:
                key_display = key.replace("_", " ").title()
            build_lines.append(f"  {key_display}: {value}")

        return "\n".join(build_lines)

    def format_version_output(self, detailed: bool = False) -> str:
        """Format version information for display"""
        gnmibuddy_version = self.get_gnmibuddy_version()
        python_info = self.get_python_version()

        if not detailed:
            # Simple version output
            return SIMPLE_VERSION_TEMPLATE.format(
                gnmibuddy_version=gnmibuddy_version,
                python_version=python_info["version"],
            )

        # Detailed version output
        platform_info = self.get_platform_info()
        dependencies = self.get_dependency_versions()
        build_info = self.get_build_info()

        # Build dependencies section
        dependencies_section = ""
        if dependencies:
            dependency_list = self._format_dependency_list(dependencies)
            dependencies_section = DEPENDENCIES_SECTION_TEMPLATE.format(
                dependency_list=dependency_list
            )

        # Build build information section
        build_section = ""
        if build_info:
            build_list = self._format_build_list(build_info)
            build_section = BUILD_SECTION_TEMPLATE.format(
                build_list=build_list
            )

        return DETAILED_VERSION_TEMPLATE.format(
            gnmibuddy_version=gnmibuddy_version,
            python_version=python_info["version"],
            python_implementation=python_info["implementation"],
            python_compiler=python_info["compiler"],
            system=platform_info["system"],
            release=platform_info["release"],
            machine=platform_info["machine"],
            architecture=platform_info["architecture"],
            dependencies_section=dependencies_section,
            build_section=build_section,
        ).strip()


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
    version_output = get_version_info(detailed=detailed)
    print(version_output)
