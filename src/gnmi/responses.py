#!/usr/bin/env python3
"""
Response objects for gNMI operations.
Provides structured objects for representing gNMI responses.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
import json


@dataclass
class GnmiError:
    """
    Represents an error that occurred during a gNMI operation.

    Attributes:
        type: The type of error that occurred
        message: A human-readable error message
        details: Additional error details
    """

    type: str
    message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, error_dict: Dict[str, Any]) -> "GnmiError":
        """Create a GnmiError object from a dictionary."""
        error_type = error_dict.get("type", "UNKNOWN_ERROR")
        message = error_dict.get("message")

        details = {
            k: v for k, v in error_dict.items() if k not in ["type", "message"]
        }

        return cls(type=error_type, message=message, details=details)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary representation."""
        result = {"type": self.type}

        if self.message:
            result["message"] = self.message

        result.update(self.details)

        return result


@dataclass
class GnmiResponse:
    """
    Base class for all gNMI responses.

    This provides a common structure for both successful responses and errors.

    Attributes:
        success: Whether the operation was successful
        error: Error information if success is False
        raw_data: The raw data returned by the gNMI operation
    """

    success: bool = True
    error: Optional[GnmiError] = None
    raw_data: Optional[Dict[str, Any]] = None

    @classmethod
    def success_response(cls, data: Dict[str, Any]) -> "GnmiResponse":
        """Create a successful response with the provided data."""
        return cls(success=True, raw_data=data)

    @classmethod
    def error_response(
        cls, error: Union[GnmiError, Dict[str, Any]]
    ) -> "GnmiResponse":
        """Create an error response."""
        if isinstance(error, dict):
            error = GnmiError.from_dict(error)
        return cls(success=False, error=error)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GnmiResponse":
        """Create a GnmiResponse from a dictionary."""
        if "error" in data:
            return cls.error_response(data["error"])
        return cls.success_response(data)

    def is_error(self) -> bool:
        """Check if this response represents an error."""
        return not self.success

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary representation."""
        if self.is_error() and self.error:
            return {"error": self.error.to_dict()}
        return self.raw_data or {}

    def __str__(self) -> str:
        """String representation for debugging."""
        return json.dumps(self.to_dict(), indent=2)

    def to_json(self) -> str:
        """Convert to a JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class GnmiFeatureNotFoundResponse(GnmiResponse):
    """
    Represents a response for features that are not found on the device.

    This provides a distinction between actual errors and cases where
    a feature is simply not configured or not supported on the device.

    Attributes:
        feature_name: The name of the feature that was not found
        feature_message: A human-readable message explaining the feature not found
        feature_details: Additional details about the feature or the request
    """

    feature_name: Optional[str] = None
    feature_message: Optional[str] = None
    feature_details: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        feature_name: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> "GnmiFeatureNotFoundResponse":
        """Create a feature not found response."""
        return cls(
            success=True,  # This is not considered a failure
            feature_name=feature_name,
            feature_message=message,
            feature_details=details or {},
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary representation."""
        result = {
            "feature_not_found": {
                "feature": self.feature_name,
                "message": self.feature_message,
                "details": {},
            }
        }

        if self.feature_details:
            # Copy the details into the result
            for key, value in self.feature_details.items():
                result["feature_not_found"]["details"][key] = value

        return result


@dataclass
class GnmiDataResponse(GnmiResponse):
    """
    Represents a successful response containing gNMI data.

    Attributes:
        data: The structured data from the response
        timestamp: Optional timestamp from the gNMI notification
    """

    data: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: Optional[str] = None

    @classmethod
    def from_raw_response(cls, response: Dict[str, Any]) -> "GnmiResponse":
        """Create a GnmiDataResponse from a raw gNMI response dictionary."""
        if not response or not isinstance(response, dict):
            return cls.error_response(
                GnmiError(
                    type="EMPTY_RESPONSE",
                    message="No data returned from gNMI request",
                )
            )

        if "error" in response:
            return cls.error_response(response["error"])

        updates = response.get("response", [])
        timestamp = response.get("timestamp")

        return cls(
            success=True, raw_data=response, data=updates, timestamp=timestamp
        )

    def to_dict(self) -> Dict[str, Any]:
        """Override to_dict to include data and timestamp."""
        if self.is_error():
            return super().to_dict()

        result = super().to_dict()
        if not result:
            result = {}

        if self.data:
            result["data"] = self.data

        if self.timestamp:
            result["timestamp"] = self.timestamp

        return result
