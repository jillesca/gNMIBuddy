#!/usr/bin/env python3
"""
Capability verification service for gNMIBuddy.

Provides OpenConfig model capability verification functionality,
specifically for openconfig-network-instance model validation.
"""

from typing import Dict, Any, Optional, Set
from dataclasses import dataclass, field

from ..schemas.models import Device
from ..schemas.capabilities import (
    CapabilityInfo,
    ModelCapability,
    CapabilityVerificationStatus,
    DeviceCapabilities,
)
from ..schemas.responses import ErrorResponse, SuccessResponse
from ..schemas.openconfig_models import OpenConfigModel, get_model_requirement
from ..schemas.verification_results import (
    ModelVerificationResult,
    MultiModelVerificationResult,
    VerificationStatus,
)
from ..gnmi.capabilities import (
    get_device_capabilities,
    extract_capabilities_from_response,
)
from ..utils.version_utils import (
    format_version_comparison_message,
    validate_model_version,
)

# Temporarily use standard logging to avoid circular import
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
        "Starting capability verification",
        extra={
            "device_name": device.name,
            "model_name": model_name,
            "required_version": required_version,
        },
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
        logger.debug(
            "Requesting device capabilities",
            extra={"device_name": device.name},
        )
        capabilities_response = get_device_capabilities(device)

        if isinstance(capabilities_response, ErrorResponse):
            error_msg = f"Failed to retrieve capabilities from device {device.name}: {capabilities_response.message}"
            logger.error(
                "Failed to retrieve capabilities from device",
                extra={
                    "device_name": device.name,
                    "error_type": capabilities_response.type,
                    "error_message": capabilities_response.message,
                },
            )
            result.error_message = error_msg
            result.model_capability.status = (
                CapabilityVerificationStatus.NOT_FOUND
            )
            result.model_capability.error_message = error_msg
            result.metadata["error_type"] = "capability_request_failed"
            return result.to_dict()

        if not isinstance(capabilities_response, SuccessResponse):
            error_msg = f"Unexpected response type from capabilities request: {type(capabilities_response)}"
            logger.error(
                "Unexpected response type from capabilities request",
                extra={
                    "device_name": device.name,
                    "response_type": type(capabilities_response).__name__,
                },
            )
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
            logger.error(
                "No capability data received from device",
                extra={"device_name": device.name},
            )
            result.error_message = error_msg
            result.model_capability.status = (
                CapabilityVerificationStatus.NOT_FOUND
            )
            result.model_capability.error_message = error_msg
            result.metadata["error_type"] = "empty_capabilities"
            return result.to_dict()

        # Extract device capabilities from response
        logger.debug(
            "Extracting capabilities from response",
            extra={
                "device_name": device.name,
                "data_size": len(capabilities_response.data),
            },
        )
        device_capabilities = extract_capabilities_from_response(
            capabilities_response
        )

        if not device_capabilities:
            error_msg = (
                f"Failed to extract capabilities from device {device.name}"
            )
            logger.error(
                "Failed to extract capabilities from device",
                extra={"device_name": device.name},
            )
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

        logger.debug(
            "Capabilities extraction successful",
            extra={
                "device_name": device.name,
                "total_models_found": len(
                    device_capabilities.supported_models
                ),
                "timestamp": device_capabilities.timestamp,
            },
        )

        # Find the openconfig-network-instance model
        logger.debug(
            "Searching for specific model",
            extra={
                "device_name": device.name,
                "model_name": model_name,
                "required_version": required_version,
                "total_models_to_search": len(
                    device_capabilities.supported_models
                ),
            },
        )

        # Log OpenConfig models available for debugging
        openconfig_models = [
            model
            for model in device_capabilities.supported_models
            if "openconfig" in model.name.lower()
        ]

        if openconfig_models:
            logger.debug(
                "Found OpenConfig models",
                extra={
                    "device_name": device.name,
                    "openconfig_model_count": len(openconfig_models),
                    "openconfig_models": [
                        {"name": model.name, "version": model.version}
                        for model in openconfig_models
                    ],
                },
            )
        else:
            logger.debug(
                "No OpenConfig models found in device capabilities",
                extra={"device_name": device.name},
            )

        model_info = device_capabilities.find_model(model_name)

        if not model_info:
            logger.debug(
                "Model not found in available models",
                extra={
                    "device_name": device.name,
                    "model_name": model_name,
                    "available_models": len(
                        device_capabilities.supported_models
                    ),
                },
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


def verify_single_model(
    device: Device, model: OpenConfigModel
) -> ModelVerificationResult:
    """
    Verify that a device supports a specific OpenConfig model.

    Args:
        device: Device object to verify
        model: OpenConfig model to verify

    Returns:
        ModelVerificationResult with verification status and details
    """
    requirement = get_model_requirement(model)
    model_name = requirement.name
    required_version = requirement.min_version

    logger.info(
        "Starting single model verification",
        extra={
            "device_name": device.name,
            "model_name": model_name,
            "required_version": required_version,
        },
    )

    # Get device capabilities
    logger.debug(
        "Requesting device capabilities for single model verification",
        extra={"device_name": device.name, "model_name": model_name},
    )
    capabilities_response = get_device_capabilities(device)

    if isinstance(capabilities_response, ErrorResponse):
        error_msg = f"Failed to retrieve capabilities from device {device.name}: {capabilities_response.message}"
        logger.error(
            "Failed to retrieve capabilities for single model verification",
            extra={
                "device_name": device.name,
                "model_name": model_name,
                "error_type": capabilities_response.type,
                "error_message": capabilities_response.message,
            },
        )
        return ModelVerificationResult(
            model=model,
            status=VerificationStatus.ERROR,
            required_version=required_version,
            error_message=error_msg,
        )

    if not isinstance(capabilities_response, SuccessResponse):
        error_msg = f"Unexpected response type from capabilities request: {type(capabilities_response)}"
        logger.error(
            "Unexpected response type for single model verification",
            extra={
                "device_name": device.name,
                "model_name": model_name,
                "response_type": type(capabilities_response).__name__,
            },
        )
        return ModelVerificationResult(
            model=model,
            status=VerificationStatus.ERROR,
            required_version=required_version,
            error_message=error_msg,
        )

    # Parse capabilities data
    if not capabilities_response.data:
        error_msg = f"No capability data received from device {device.name}"
        logger.error(
            "No capability data received for single model verification",
            extra={
                "device_name": device.name,
                "model_name": model_name,
            },
        )
        return ModelVerificationResult(
            model=model,
            status=VerificationStatus.ERROR,
            required_version=required_version,
            error_message=error_msg,
        )

    try:
        device_capabilities = extract_capabilities_from_response(
            capabilities_response
        )
        if not device_capabilities:
            error_msg = f"Failed to extract capabilities from response for device {device.name}"
            logger.error(error_msg)
            return ModelVerificationResult(
                model=model,
                status=VerificationStatus.ERROR,
                required_version=required_version,
                error_message=error_msg,
            )
    except ValueError as e:
        error_msg = (
            f"Failed to parse capabilities for device {device.name}: {e}"
        )
        logger.error(error_msg)
        return ModelVerificationResult(
            model=model,
            status=VerificationStatus.ERROR,
            required_version=required_version,
            error_message=error_msg,
        )

    # Find the specific model in capabilities
    model_capability = device_capabilities.find_model(model_name)

    if not model_capability:
        error_msg = f"Model {model_name} not found on device {device.name}"
        logger.error(
            "Model not found in device capabilities",
            extra={
                "device_name": device.name,
                "model_name": model_name,
                "available_models": len(device_capabilities.supported_models),
            },
        )
        return ModelVerificationResult(
            model=model,
            status=VerificationStatus.NOT_FOUND,
            required_version=required_version,
            error_message=error_msg,
        )

    # Validate the version
    found_version = model_capability.version
    logger.debug(
        "Validating model version",
        extra={
            "device_name": device.name,
            "model_name": model_name,
            "found_version": found_version,
            "required_version": required_version,
        },
    )
    validation_result = validate_model_version(model, found_version)

    result = ModelVerificationResult(
        model=model,
        status=validation_result.status,
        found_version=found_version,
        required_version=required_version,
        warning_message=validation_result.warning_message,
        error_message=validation_result.error_message,
    )

    # Log the result
    if result.status == VerificationStatus.SUPPORTED:
        logger.info(
            "Single model verification successful",
            extra={
                "device_name": device.name,
                "model_name": model_name,
                "found_version": found_version,
                "required_version": required_version,
            },
        )
    elif result.status == VerificationStatus.VERSION_WARNING:
        logger.warning(
            "Single model verification has version warning",
            extra={
                "device_name": device.name,
                "model_name": model_name,
                "found_version": found_version,
                "required_version": required_version,
                "warning_message": result.warning_message,
            },
        )
    else:
        logger.error(
            "Single model verification failed",
            extra={
                "device_name": device.name,
                "model_name": model_name,
                "status": result.status.value,
                "error_message": result.error_message,
            },
        )

    return result


def verify_models(
    device: Device, models: Set[OpenConfigModel]
) -> MultiModelVerificationResult:
    """
    Verify that a device supports multiple OpenConfig models.

    Args:
        device: Device object to verify
        models: Set of OpenConfig models to verify

    Returns:
        MultiModelVerificationResult with verification status for all models
    """
    logger.info(
        "Starting multi-model verification",
        extra={
            "device_name": device.name,
            "model_count": len(models),
            "models": [model.value for model in models],
        },
    )

    model_results = {}
    supported_count = 0
    warning_count = 0
    error_count = 0

    # Verify each model
    for model in models:
        logger.debug(
            "Verifying individual model",
            extra={
                "device_name": device.name,
                "model": model.value,
            },
        )
        result = verify_single_model(device, model)
        model_results[model] = result

        if result.status == VerificationStatus.SUPPORTED:
            supported_count += 1
        elif result.status == VerificationStatus.VERSION_WARNING:
            warning_count += 1
        else:
            error_count += 1

    logger.debug(
        "Multi-model verification results summary",
        extra={
            "device_name": device.name,
            "supported_count": supported_count,
            "warning_count": warning_count,
            "error_count": error_count,
        },
    )

    # Determine overall status
    if error_count > 0:
        overall_status = VerificationStatus.ERROR
    elif warning_count > 0:
        overall_status = VerificationStatus.VERSION_WARNING
    else:
        overall_status = VerificationStatus.SUPPORTED

    result = MultiModelVerificationResult(
        overall_status=overall_status,
        model_results=model_results,
    )

    logger.info(
        "Multi-model verification completed",
        extra={
            "device_name": device.name,
            "overall_status": overall_status.value,
            "supported_count": supported_count,
            "warning_count": warning_count,
            "error_count": error_count,
        },
    )

    return result
