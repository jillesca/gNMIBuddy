#!/usr/bin/env python3
"""
OpenConfig model registry and definitions for gNMIBuddy.

This module provides a centralized registry of OpenConfig models supported
by gNMIBuddy, including their version requirements and descriptions.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class OpenConfigModel(Enum):
    """
    Enumeration of supported OpenConfig models.

    Each model corresponds to a specific OpenConfig schema used by collectors.
    """

    SYSTEM = "openconfig-system"
    INTERFACES = "openconfig-interfaces"
    NETWORK_INSTANCE = "openconfig-network-instance"


@dataclass
class ModelRequirement:
    """
    Represents the requirements for a specific OpenConfig model.

    Attributes:
        name: The OpenConfig model name (e.g., "openconfig-system")
        min_version: Minimum required version for the model
        description: Human-readable description of the model's purpose
    """

    name: str
    min_version: str
    description: str


# Registry mapping OpenConfig models to their requirements
MODEL_REGISTRY: Dict[OpenConfigModel, ModelRequirement] = {
    OpenConfigModel.SYSTEM: ModelRequirement(
        name="openconfig-system",
        min_version="0.17.1",
        description="System-level configuration and state data",
    ),
    OpenConfigModel.INTERFACES: ModelRequirement(
        name="openconfig-interfaces",
        min_version="3.0.0",
        description="Network interface configuration and state data",
    ),
    OpenConfigModel.NETWORK_INSTANCE: ModelRequirement(
        name="openconfig-network-instance",
        min_version="1.3.0",
        description="Network instance configuration and state data (VRFs, routing protocols)",
    ),
}


def get_model_requirement(model: OpenConfigModel) -> ModelRequirement:
    """
    Get the requirement specification for a specific OpenConfig model.

    Args:
        model: The OpenConfig model to get requirements for

    Returns:
        ModelRequirement object containing the model's requirements

    Raises:
        KeyError: If the model is not found in the registry
    """
    return MODEL_REGISTRY[model]


def get_all_models() -> List[OpenConfigModel]:
    """
    Get a list of all supported OpenConfig models.

    Returns:
        List of all OpenConfigModel enum values
    """
    return list(OpenConfigModel)


def get_model_by_name(name: Optional[str]) -> Optional[OpenConfigModel]:
    """
    Get an OpenConfig model by its name string.

    Args:
        name: The model name (e.g., "openconfig-system")

    Returns:
        OpenConfigModel enum value if found, None otherwise
    """
    if not name:
        return None

    for model in OpenConfigModel:
        if model.value == name:
            return model
    return None
