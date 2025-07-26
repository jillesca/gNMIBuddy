import platform
from importlib.metadata import version, PackageNotFoundError


def get_python_version() -> str:
    """Get the current Python version."""
    return platform.python_version()


def load_gnmibuddy_version() -> str:
    """Load the gNMIBuddy version from the installed package metadata."""
    try:
        return version("gnmibuddy")
    except PackageNotFoundError:
        # Fallback for development environment
        import os
        import tomllib
        from typing import Any

        pyproject_path: str = os.path.join(
            os.path.dirname(__file__), "../../pyproject.toml"
        )
        try:
            with open(pyproject_path, "rb") as f:
                pyproject_data: Any = tomllib.load(f)
                return pyproject_data["project"]["version"]
        except FileNotFoundError:
            return "unknown"
