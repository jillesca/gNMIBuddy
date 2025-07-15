#!/usr/bin/env python3
"""
Capability models for gNMIBuddy.

Contains data models for representing device capabilities and capability
verification results used throughout the application.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class CapabilityVerificationStatus(Enum):
    """
    Enumeration for capability verification status values.

    Provides type safety for capability verification results.
    """

    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    VERSION_WARNING = "version_warning"
    NOT_FOUND = "not_found"


@dataclass
class CapabilityInfo:
    """
    Information about a specific capability/model from gNMI capabilities response.

    Attributes:
        name: The name of the capability/model (e.g., "openconfig-network-instance")
        version: The version of the capability/model (e.g., "1.3.0")
        organization: The organization that defined the model (e.g., "openconfig")
        module: The module name (may be different from name)
        revision: The revision date of the model (optional)
        namespace: The namespace URI of the model (optional)
    """

    name: str
    version: str
    organization: str
    module: Optional[str] = None
    revision: Optional[str] = None
    namespace: Optional[str] = None


@dataclass
class ModelCapability:
    """
    Verification result for a specific model requirement.

    Attributes:
        model_name: The name of the model being verified
        required_version: The minimum required version
        found_version: The version found on the device (None if not found)
        status: The verification status
        warning_message: Optional warning message for version issues
        error_message: Optional error message for failures
    """

    model_name: str
    required_version: str
    found_version: Optional[str] = None
    status: CapabilityVerificationStatus = (
        CapabilityVerificationStatus.NOT_FOUND
    )
    warning_message: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class CapabilityError:
    """
    Capability-specific error information.

    Attributes:
        error_type: The type of capability error
        message: Human-readable error message
        model_name: The model that caused the error (optional)
        details: Additional error details
    """

    error_type: str
    message: str
    model_name: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """String representation for debugging."""
        model_str = (
            f" for model '{self.model_name}'" if self.model_name else ""
        )
        return f"CapabilityError({self.error_type}{model_str}: {self.message})"


@dataclass
class DeviceCapabilities:
    """
    Complete capability information for a device.

    Attributes:
        device_name: Name of the device
        gnmi_version: gNMI version supported by the device
        supported_models: List of supported models/capabilities
        supported_encodings: List of supported encodings
        timestamp: When the capabilities were retrieved
        raw_response: Raw capabilities response (for debugging)
    """

    device_name: str
    gnmi_version: str
    supported_models: List[CapabilityInfo] = field(default_factory=list)
    supported_encodings: List[str] = field(default_factory=list)
    timestamp: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def find_model(self, model_name: str) -> Optional[CapabilityInfo]:
        """
        Find a specific model in the supported models list.

        Args:
            model_name: Name of the model to find

        Returns:
            CapabilityInfo object if found, None otherwise
        """
        from ..logging.config import get_logger

        logger = get_logger(__name__)

        logger.debug("Searching for model: '%s'", model_name)
        logger.debug("Total models available: %d", len(self.supported_models))

        # Log first 10 model names for debugging
        if self.supported_models:
            logger.debug("First 10 available models:")
            for i, model in enumerate(self.supported_models[:10]):
                logger.debug(
                    "  %d. '%s' v%s", i + 1, model.name, model.version
                )

        # Search for exact match
        for model in self.supported_models:
            if model.name == model_name:
                logger.debug(
                    "Found matching model: '%s' v%s", model.name, model.version
                )
                return model

        # Enhanced debugging for model not found
        logger.debug(
            "Model '%s' not found in %d available models",
            model_name,
            len(self.supported_models),
        )

        # Check for similar model names (debugging aid)
        similar_models = [
            model
            for model in self.supported_models
            if model_name.lower() in model.name.lower()
            or model.name.lower() in model_name.lower()
        ]

        if similar_models:
            logger.debug(
                "Found %d models with similar names:", len(similar_models)
            )
            for model in similar_models:
                logger.debug("  - '%s' v%s", model.name, model.version)

        return None

    def has_model(self, model_name: str) -> bool:
        """
        Check if a model is supported by the device.

        Args:
            model_name: Name of the model to check

        Returns:
            True if the model is supported, False otherwise
        """
        return self.find_model(model_name) is not None
