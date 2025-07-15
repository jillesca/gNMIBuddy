#!/usr/bin/env python3
"""
Capability verification service for gNMIBuddy.

Provides OpenConfig model capability verification functionality,
specifically for openconfig-network-instance model validation.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from ..schemas.models import Device
from ..schemas.capabilities import (
    CapabilityInfo,
    ModelCapability,
    CapabilityVerificationStatus,
    DeviceCapabilities,
)
from ..schemas.responses import ErrorResponse, SuccessResponse
from ..gnmi.capabilities import (
    get_device_capabilities,
    extract_capabilities_from_response,
)
from ..utils.version_utils import (
    format_version_comparison_message,
)
from ..logging.config import get_logger

logger = get_logger(__name__)


@dataclass
class VerificationResult:
    """
    Result of capability verification.

    Attributes:
        is_supported: Whether the model is supported
        model_capability: ModelCapability object with verification details
        warning_message: Optional warning message
        error_message: Optional error message
        metadata: Additional metadata for the operation
    """

    is_supported: bool
    model_capability: ModelCapability
    warning_message: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert VerificationResult to dictionary."""
        return {
            "is_supported": self.is_supported,
            "model_capability": {
                "model_name": self.model_capability.model_name,
                "required_version": self.model_capability.required_version,
                "found_version": self.model_capability.found_version,
                "status": self.model_capability.status.value,
                "warning_message": self.model_capability.warning_message,
                "error_message": self.model_capability.error_message,
            },
            "warning_message": self.warning_message,
            "error_message": self.error_message,
            "metadata": self.metadata or {},
        }


def verify_openconfig_network_instance(device: Device) -> Dict[str, Any]:
    """
    Verify that a device supports the openconfig-network-instance model.

    This function checks if the device supports the openconfig-network-instance
    model with minimum version 1.3.0. It returns a verification result with
    appropriate status, messages, and metadata.

    Args:
        device: Device object to verify

    Returns:
        Dictionary containing verification result with keys:
        - is_supported: bool - Whether the model is supported
        - model_capability: ModelCapability object
        - warning_message: Optional warning message
        - error_message: Optional error message
        - metadata: Additional metadata about the verification

    Raises:
        None - All errors are captured in the result
    """
    model_name = "openconfig-network-instance"
    required_version = "1.3.0"

    logger.info(
        "Verifying %s capability for device %s", model_name, device.name
    )

    # Initialize result structure
    result = VerificationResult(
        is_supported=False,
        model_capability=ModelCapability(
            model_name=model_name, required_version=required_version
        ),
        metadata={
            "device_name": device.name,
            "verification_model": model_name,
            "required_version": required_version,
            "verification_timestamp": None,
        },
    )

    try:
        # Get device capabilities
        capabilities_response = get_device_capabilities(device)

        if isinstance(capabilities_response, ErrorResponse):
            error_msg = f"Failed to retrieve capabilities from device {device.name}: {capabilities_response.message}"
            logger.error(error_msg)
            result.error_message = error_msg
            result.model_capability.status = (
                CapabilityVerificationStatus.NOT_FOUND
            )
            result.model_capability.error_message = error_msg
            result.metadata["error_type"] = "capability_request_failed"
            return result.to_dict()

        if not isinstance(capabilities_response, SuccessResponse):
            error_msg = f"Unexpected response type from capabilities request: {type(capabilities_response)}"
            logger.error(error_msg)
            result.error_message = error_msg
            result.model_capability.status = (
                CapabilityVerificationStatus.NOT_FOUND
            )
            result.model_capability.error_message = error_msg
            result.metadata["error_type"] = "unexpected_response_type"
            return result.to_dict()

        # Parse capabilities data
        if not capabilities_response.data:
            error_msg = (
                f"No capability data received from device {device.name}"
            )
            logger.error(error_msg)
            result.error_message = error_msg
            result.model_capability.status = (
                CapabilityVerificationStatus.NOT_FOUND
            )
            result.model_capability.error_message = error_msg
            result.metadata["error_type"] = "empty_capabilities"
            return result.to_dict()

        # Extract device capabilities from response
        device_capabilities = extract_capabilities_from_response(
            capabilities_response
        )

        if not device_capabilities:
            error_msg = (
                f"Failed to extract capabilities from device {device.name}"
            )
            logger.error(error_msg)
            result.error_message = error_msg
            result.model_capability.status = (
                CapabilityVerificationStatus.NOT_FOUND
            )
            result.model_capability.error_message = error_msg
            result.metadata["error_type"] = "capability_extraction_failed"
            return result.to_dict()

        result.metadata["total_models_found"] = len(
            device_capabilities.supported_models
        )
        result.metadata["verification_timestamp"] = (
            device_capabilities.timestamp
        )

        # Find the openconfig-network-instance model
        logger.debug("Searching for model: %s", model_name)
        logger.debug("Required version: %s", required_version)
        logger.debug(
            "Total models to search: %d",
            len(device_capabilities.supported_models),
        )

        # Log OpenConfig models available for debugging
        openconfig_models = [
            model
            for model in device_capabilities.supported_models
            if "openconfig" in model.name.lower()
        ]

        if openconfig_models:
            logger.debug("Found %d OpenConfig models:", len(openconfig_models))
            for model in openconfig_models:
                logger.debug("  - %s v%s", model.name, model.version)
        else:
            logger.debug("No OpenConfig models found in device capabilities")

        model_info = device_capabilities.find_model(model_name)

        if not model_info:
            logger.debug(
                "Model not found in %d available models",
                len(device_capabilities.supported_models),
            )
            # Log first few model names for debugging
            if device_capabilities.supported_models:
                logger.debug("First 5 available models:")
                for i, model in enumerate(
                    device_capabilities.supported_models[:5]
                ):
                    logger.debug(
                        "  %d. %s v%s", i + 1, model.name, model.version
                    )

            # Additional debugging - check for case sensitivity issues
            logger.debug("Checking for case-insensitive matches...")
            case_insensitive_matches = [
                model
                for model in device_capabilities.supported_models
                if model.name.lower() == model_name.lower()
            ]

            if case_insensitive_matches:
                logger.debug("Found case-insensitive matches:")
                for model in case_insensitive_matches:
                    logger.debug(
                        "  - %s (actual case: '%s')", model.name, model.name
                    )
            else:
                logger.debug("No case-insensitive matches found")

            error_msg = (
                f"Model '{model_name}' not found on device {device.name}"
            )
            logger.error(error_msg)
            result.error_message = error_msg
            result.model_capability.status = (
                CapabilityVerificationStatus.NOT_FOUND
            )
            result.model_capability.error_message = error_msg
            result.metadata["error_type"] = "model_not_found"
            result.metadata["available_models"] = [
                model.name for model in device_capabilities.supported_models
            ]
            return result.to_dict()

        logger.debug(
            "Found model: %s v%s", model_info.name, model_info.version
        )

        # Model found, check version
        result.model_capability.found_version = model_info.version
        result.metadata["found_version"] = model_info.version
        result.metadata["model_organization"] = model_info.organization

        if not model_info.version:
            warning_msg = f"Model '{model_name}' found on device {device.name} but version information is missing"
            logger.warning(warning_msg)
            result.warning_message = warning_msg
            result.model_capability.status = (
                CapabilityVerificationStatus.VERSION_WARNING
            )
            result.model_capability.warning_message = warning_msg
            result.metadata["warning_type"] = "missing_version"
            # Allow usage but with warning
            result.is_supported = True
            return result.to_dict()

        # Compare versions
        logger.debug(
            "Comparing found version %s with required version %s",
            model_info.version,
            required_version,
        )
        try:
            from src.utils.version_utils import compare_versions

            version_comparison = compare_versions(
                model_info.version, required_version
            )
            if version_comparison >= 0:
                success_msg = f"Model '{model_name}' version {model_info.version} meets minimum requirement {required_version}"
                logger.info(success_msg)
                result.is_supported = True
                result.model_capability.status = (
                    CapabilityVerificationStatus.SUPPORTED
                )
                result.metadata["version_check"] = "passed"
                result.metadata["version_comparison"] = (
                    format_version_comparison_message(
                        model_info.version, required_version
                    )
                )
            else:
                warning_msg = f"Model '{model_name}' version {model_info.version} is older than tested version {required_version}. Functionality may be limited."
                logger.warning(warning_msg)
                result.warning_message = warning_msg
                result.model_capability.status = (
                    CapabilityVerificationStatus.VERSION_WARNING
                )
                result.model_capability.warning_message = warning_msg
                result.metadata["warning_type"] = "version_older_than_tested"
                result.metadata["version_check"] = "warning"
                result.metadata["version_comparison"] = (
                    format_version_comparison_message(
                        model_info.version, required_version
                    )
                )
                # Allow usage but with warning
                result.is_supported = True

        except ValueError as e:
            warning_msg = f"Unable to compare version {model_info.version} with required {required_version}: {e}"
            logger.warning(warning_msg)
            result.warning_message = warning_msg
            result.model_capability.status = (
                CapabilityVerificationStatus.VERSION_WARNING
            )
            result.model_capability.warning_message = warning_msg
            result.metadata["warning_type"] = "version_comparison_failed"
            result.metadata["version_check"] = "warning"
            # Allow usage but with warning
            result.is_supported = True

        return result.to_dict()

    except (ValueError, TypeError, AttributeError) as e:
        error_msg = f"Unexpected error during capability verification for device {device.name}: {str(e)}"
        logger.exception(error_msg)
        result.error_message = error_msg
        result.model_capability.status = CapabilityVerificationStatus.NOT_FOUND
        result.model_capability.error_message = error_msg
        result.metadata["error_type"] = "unexpected_error"
        result.metadata["exception_type"] = type(e).__name__
        return result.to_dict()


def _parse_device_capabilities(
    capabilities_data: Dict[str, Any], device_name: str
) -> DeviceCapabilities:
    """
    Parse capability data into DeviceCapabilities object.

    .. deprecated::
        This function is deprecated. Use extract_capabilities_from_response() instead.
        This function expects raw gNMI capability data, but capability verification
        now uses DeviceCapabilities objects from get_device_capabilities().

    Args:
        capabilities_data: Raw capability data from gNMI response
        device_name: Name of the device

    Returns:
        DeviceCapabilities object
    """
    logger.warning(
        "_parse_device_capabilities is deprecated. Use extract_capabilities_from_response() instead."
    )

    # Extract basic capability information
    gnmi_version = capabilities_data.get("gNMI_version", "unknown")
    supported_encodings = capabilities_data.get("supported_encodings", [])

    # Parse supported models
    supported_models = []
    supported_models_data = capabilities_data.get("supported_models", [])

    for model_data in supported_models_data:
        if isinstance(model_data, dict):
            model_info = CapabilityInfo(
                name=model_data.get("name", ""),
                version=model_data.get("version", ""),
                organization=model_data.get("organization", ""),
                module=model_data.get("module"),
                revision=model_data.get("revision"),
                namespace=model_data.get("namespace"),
            )
            supported_models.append(model_info)

    return DeviceCapabilities(
        device_name=device_name,
        gnmi_version=gnmi_version,
        supported_models=supported_models,
        supported_encodings=supported_encodings,
        raw_response=capabilities_data,
    )


def get_verification_summary(verification_result: Dict[str, Any]) -> str:
    """
    Get a human-readable summary of the verification result.

    Args:
        verification_result: Result dictionary from verify_openconfig_network_instance

    Returns:
        Formatted summary string
    """
    model_capability = verification_result.get("model_capability", {})
    model_name = model_capability.get("model_name", "unknown")
    required_version = model_capability.get("required_version", "unknown")
    found_version = model_capability.get("found_version", "not found")
    status = model_capability.get("status", "unknown")

    if verification_result.get("is_supported"):
        if status == "supported":
            return f"✓ {model_name} v{found_version} is supported (minimum required: {required_version})"
        elif status == "version_warning":
            return f"⚠ {model_name} v{found_version} is supported but may have limited functionality (minimum tested: {required_version})"
    else:
        if status == "not_found":
            return f"✗ {model_name} is not supported on this device"
        else:
            return f"✗ {model_name} verification failed"

    return f"? {model_name} verification status unknown"
