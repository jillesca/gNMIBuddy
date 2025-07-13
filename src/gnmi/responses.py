#!/usr/bin/env python3
"""
Response objects for network operations.
Provides structured objects for representing operation responses.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union


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

    @classmethod
    def from_dict(cls, error_dict: Dict[str, Any]) -> "ErrorResponse":
        """Create an ErrorResponse object from a dictionary."""
        error_type = error_dict.get("type", "UNKNOWN_ERROR")
        message = error_dict.get("message")

        details = {
            k: v for k, v in error_dict.items() if k not in ["type", "message"]
        }

        return cls(type=error_type, message=message, details=details)

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

    @classmethod
    def create(
        cls,
        feature_name: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> "FeatureNotFoundResponse":
        """Create a feature not found response."""
        return cls(
            feature_name=feature_name,
            message=message,
            details=details or {},
        )

    def __str__(self) -> str:
        """String representation for debugging."""
        return f"FeatureNotFoundResponse(feature='{self.feature_name}', message='{self.message}')"


@dataclass
class SuccessResponse:
    """
    Represents a successful response containing network operation data.

    Attributes:
        data: The structured data from the response
        timestamp: Optional timestamp from the notification
        raw_data: The raw data returned by the operation
    """

    data: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

    @classmethod
    def from_raw_response(
        cls, response: Dict[str, Any]
    ) -> Union["SuccessResponse", ErrorResponse]:
        """Create a SuccessResponse from a raw response dictionary."""
        if not response or not isinstance(response, dict):
            return ErrorResponse(
                type="EMPTY_RESPONSE",
                message="No data returned from request",
            )

        if "error" in response:
            return ErrorResponse.from_dict(response["error"])

        updates = response.get("response", [])
        timestamp = response.get("timestamp")

        return cls(raw_data=response, data=updates, timestamp=timestamp)

    def __str__(self) -> str:
        """String representation for debugging."""
        data_count = len(self.data) if self.data else 0
        timestamp_str = (
            f", timestamp='{self.timestamp}'" if self.timestamp else ""
        )
        return f"SuccessResponse(data_count={data_count}{timestamp_str})"


# Type alias for return types - Go-like error handling pattern
NetworkResponse = Union[
    SuccessResponse, ErrorResponse, FeatureNotFoundResponse
]
