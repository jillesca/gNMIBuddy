#!/usr/bin/env python3
"""
Response schemas for network operations.

Contains structured response objects and data contracts used throughout
the gNMIBuddy application for representing operation results.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Union


class OperationStatus(Enum):
    """
    Enumeration for network operation status values.

    Provides type safety and prevents typos when setting or checking
    operation status in NetworkOperationResult objects.
    """

    SUCCESS = "success"
    FAILED = "failed"
    FEATURE_NOT_AVAILABLE = "feature_not_available"


@dataclass
class ErrorResponse:
    """
    Represents an error that occurred during a network operation.

    Attributes:
        type: The type of error that occurred
        message: A human-readable error message
        details: Additional error details
    """

    type: str
    message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """String representation for debugging."""
        if self.message:
            return (
                f"ErrorResponse(type='{self.type}', message='{self.message}')"
            )
        return f"ErrorResponse(type='{self.type}')"


@dataclass
class FeatureNotFoundResponse:
    """
    Represents a response for features that are not found on the device.

    This provides a distinction between actual errors and cases where
    a feature is simply not configured or not supported on the device.

    Attributes:
        feature_name: The name of the feature that was not found
        message: A human-readable message explaining the feature not found
        details: Additional details about the feature or the request
    """

    feature_name: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """String representation for debugging."""
        return f"FeatureNotFoundResponse(feature='{self.feature_name}', message='{self.message}')"


@dataclass
class SuccessResponse:
    """
    Represents a successful response containing network operation data.

    Attributes:
        data: The structured data from the response (list of update dictionaries)
        timestamp: Optional timestamp from the notification
    """

    data: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: Optional[str] = None

    def __str__(self) -> str:
        """String representation for debugging."""
        data_count = len(self.data) if self.data else 0
        timestamp_str = (
            f", timestamp='{self.timestamp}'" if self.timestamp else ""
        )
        return f"SuccessResponse(data_count={data_count}{timestamp_str})"


# Unified response object for all network tools
@dataclass
class NetworkOperationResult:
    """
    A clean, simple structure for all network tool responses.

    Attributes:
        device_name: Name of the target device
        ip_address: IP address of the target device
        nos: Network Operating System of the target device
        operation_type: Type of operation performed (interface, system, routing, etc.)
        status: Operation result status (OperationStatus enum)
        data: The parsed/structured data from the operation
        metadata: Additional metadata about the operation and results
                 Common metadata fields include:
                 - capability_verification: Dict containing capability verification results
                   with keys like 'is_supported', 'model_capability', 'warning_message', etc.
                 - device_capabilities: Information about device capabilities
                 - model_versions: Version information for supported models
                 - compatibility_warnings: List of compatibility warnings
        error_response: Optional ErrorResponse object for failed operations
        feature_not_found_response: Optional FeatureNotFoundResponse for unavailable features
    """

    device_name: str
    ip_address: str
    nos: str
    operation_type: str
    status: OperationStatus
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_response: Optional[ErrorResponse] = None
    feature_not_found_response: Optional[FeatureNotFoundResponse] = None


# Type alias for return types - Go-like error handling pattern
NetworkResponse = Union[
    SuccessResponse, ErrorResponse, FeatureNotFoundResponse
]


def add_capability_verification_to_metadata(
    result: NetworkOperationResult, verification_result: Dict[str, Any]
) -> None:
    """
    Add capability verification results to NetworkOperationResult metadata.

    Args:
        result: NetworkOperationResult object to update
        verification_result: Dictionary containing verification results from
                           capability_verification.verify_openconfig_network_instance()
    """
    result.metadata["capability_verification"] = verification_result

    # Add compatibility warnings if present
    if verification_result.get("warning_message"):
        if "compatibility_warnings" not in result.metadata:
            result.metadata["compatibility_warnings"] = []
        result.metadata["compatibility_warnings"].append(
            verification_result["warning_message"]
        )

    # Add model version information
    model_capability = verification_result.get("model_capability", {})
    if model_capability.get("found_version"):
        if "model_versions" not in result.metadata:
            result.metadata["model_versions"] = {}
        result.metadata["model_versions"][model_capability["model_name"]] = {
            "found_version": model_capability["found_version"],
            "required_version": model_capability["required_version"],
            "status": model_capability["status"],
        }


def get_capability_verification_from_metadata(
    result: NetworkOperationResult,
) -> Optional[Dict[str, Any]]:
    """
    Extract capability verification results from NetworkOperationResult metadata.

    Args:
        result: NetworkOperationResult object to extract from

    Returns:
        Dictionary containing verification results or None if not found
    """
    return result.metadata.get("capability_verification")


def has_capability_warnings(result: NetworkOperationResult) -> bool:
    """
    Check if NetworkOperationResult has capability-related warnings.

    Args:
        result: NetworkOperationResult object to check

    Returns:
        True if capability warnings are present, False otherwise
    """
    verification = get_capability_verification_from_metadata(result)
    if not verification:
        return False

    return (
        verification.get("warning_message") is not None
        or verification.get("model_capability", {}).get("warning_message")
        is not None
    )


def get_capability_status_summary(result: NetworkOperationResult) -> str:
    """
    Get a human-readable summary of capability verification status.

    Args:
        result: NetworkOperationResult object to summarize

    Returns:
        String summary of capability status
    """
    verification = get_capability_verification_from_metadata(result)
    if not verification:
        return "No capability verification performed"

    model_capability = verification.get("model_capability", {})
    model_name = model_capability.get("model_name", "unknown")
    status = model_capability.get("status", "unknown")
    found_version = model_capability.get("found_version", "unknown")
    required_version = model_capability.get("required_version", "unknown")

    if verification.get("is_supported"):
        if status == "supported":
            return f"✓ {model_name} v{found_version} is fully supported"
        elif status == "version_warning":
            return f"⚠ {model_name} v{found_version} is supported with warnings (minimum tested: {required_version})"
    else:
        return f"✗ {model_name} is not supported or verification failed"

    return f"? {model_name} capability status unclear"
