#!/usr/bin/env python3
"""
Path analyzer utility for extracting OpenConfig models from gNMI paths.

This module provides functionality to analyze gNMI paths and determine
which OpenConfig models are required for a given request.
"""

import re
from typing import Optional, Set, List

from ..schemas.openconfig_models import OpenConfigModel


def extract_model_from_path(path: Optional[str]) -> Optional[OpenConfigModel]:
    """
    Extract the OpenConfig model from a gNMI path string.

    This function analyzes various gNMI path formats and identifies the
    OpenConfig model being referenced. It handles:
    - Prefixed paths: "openconfig-system:/system"
    - Colon-separated paths: "openconfig-interfaces:interfaces"
    - Wildcards and array indices: "openconfig-network-instance:network-instances/network-instance[name=*]"
    - Various path formats used by collectors

    Args:
        path: The gNMI path string to analyze

    Returns:
        OpenConfigModel enum if model can be determined, None otherwise
    """
    if not path or not isinstance(path, str):
        return None

    # Clean the path by removing leading/trailing whitespace
    path = path.strip()

    # Pattern to match OpenConfig model names at the beginning of paths
    # Handles formats like:
    # - "openconfig-system:/system"
    # - "openconfig-interfaces:interfaces"
    # - "openconfig-interfaces@interfaces"
    # - "openconfig-network-instance:network-instances/..."
    openconfig_pattern = r"^(openconfig-[a-zA-Z-]+)(?::|/|@|#)"

    match = re.match(openconfig_pattern, path)
    if match:
        model_name = match.group(1)

        # Map model names to enum values
        model_mapping = {
            "openconfig-system": OpenConfigModel.SYSTEM,
            "openconfig-interfaces": OpenConfigModel.INTERFACES,
            "openconfig-network-instance": OpenConfigModel.NETWORK_INSTANCE,
        }

        return model_mapping.get(model_name)

    # If no explicit model prefix, try to infer from path structure
    # This handles cases where paths might not have explicit prefixes
    if "/system" in path or path.startswith("system"):
        return OpenConfigModel.SYSTEM
    elif "/interfaces" in path or path.startswith("interfaces"):
        return OpenConfigModel.INTERFACES
    elif "/network-instances" in path or "network-instance" in path:
        return OpenConfigModel.NETWORK_INSTANCE

    # Could not determine model from path
    return None


def extract_models_from_paths(paths: List[str]) -> Set[OpenConfigModel]:
    """
    Extract OpenConfig models from a list of gNMI paths.

    Args:
        paths: List of gNMI path strings to analyze

    Returns:
        Set of OpenConfigModel enums found in the paths
    """
    models = set()

    for path in paths:
        model = extract_model_from_path(path)
        if model:
            models.add(model)

    return models


def is_openconfig_path(path: Optional[str]) -> bool:
    """
    Check if a path is an OpenConfig path.

    Args:
        path: The gNMI path string to check

    Returns:
        True if the path appears to be an OpenConfig path, False otherwise
    """
    if not path or not isinstance(path, str):
        return False

    # Check for explicit OpenConfig model prefix
    if re.match(r"^openconfig-[a-zA-Z-]+(?::|/)", path):
        return True

    # Check for common OpenConfig path patterns
    openconfig_patterns = [
        "/system",
        "/interfaces",
        "/network-instances",
        "network-instance",
        "/protocols/protocol",
        "/afi-safis/afi-safi",
    ]

    return any(pattern in path for pattern in openconfig_patterns)


def get_model_name_from_path(path: Optional[str]) -> Optional[str]:
    """
    Extract the model name string from a gNMI path.

    Args:
        path: The gNMI path string to analyze

    Returns:
        Model name string if found, None otherwise
    """
    model = extract_model_from_path(path)
    return model.value if model else None
