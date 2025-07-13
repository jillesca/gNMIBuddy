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
