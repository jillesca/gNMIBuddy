import os
import tomllib
from typing import Any


def load_gnmibuddy_version() -> str:
    """Load the gNMIBuddy version from the pyproject.toml file."""
    pyproject_path: str = os.path.join(
        os.path.dirname(__file__), "../../pyproject.toml"
    )
    with open(pyproject_path, "rb") as f:
        pyproject_data: Any = tomllib.load(f)
        return pyproject_data["project"]["version"]
