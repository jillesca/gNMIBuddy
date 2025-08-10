#!/usr/bin/env python3
"""
Response schemas for network operations.

Contains structured response objects and data contracts used throughout
the gNMIBuddy application for representing operation results.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Union
from .models import NetworkOS


class RoutingProtocol(Enum):
    """
    Enumeration for routing protocol types.

    Provides type safety and prevents typos when filtering routing protocols.
    """

    BGP = "bgp"
    ISIS = "isis"
    OSPF = "ospf"
    CONNECTED = "connected"
    STATIC = "static"


class OperationStatus(Enum):
    """
    Enumeration for network operation status values.

    Provides type safety and prevents typos when setting or checking
    operation status in NetworkOperationResult objects.
    """

    SUCCESS = "success"
    FAILED = "failed"
    FEATURE_NOT_AVAILABLE = "feature_not_available"
    PARTIAL_SUCCESS = (
        "partial_success"  # New status for multi-protocol operations
    )


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
    nos: NetworkOS
    operation_type: str
    status: OperationStatus
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_response: Optional[ErrorResponse] = None
    feature_not_found_response: Optional[FeatureNotFoundResponse] = None


@dataclass
class BatchOperationSummary:
    """
    Summary metadata for batch operations.

    Contains aggregate information about a batch operation's execution
    and results across multiple devices.

    Attributes:
        total_devices: Total number of devices in the batch operation
        successful: Number of devices that completed successfully
        failed: Number of devices that failed
        execution_time: Total time taken for the batch operation
        operation_type: Type of operation performed on all devices
    """

    total_devices: int
    successful: int
    failed: int
    execution_time: float
    operation_type: str

    @property
    def success_rate(self) -> float:
        """Calculate success rate as a percentage"""
        if self.total_devices == 0:
            return 0.0
        return (self.successful / self.total_devices) * 100


@dataclass
class BatchOperationResult:
    """
    Schema for batch operation results that maintains API consistency.

    This is the standard contract for all batch operations, ensuring
    consistency across the codebase by using NetworkOperationResult
    as the base structure for individual device results.

    Attributes:
        results: List of NetworkOperationResult objects, one per device
        summary: BatchOperationSummary containing aggregate metadata
        metadata: Additional batch operation metadata
    """

    results: List[NetworkOperationResult]
    summary: BatchOperationSummary
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate that summary matches results"""
        if len(self.results) != self.summary.total_devices:
            raise ValueError("Summary total_devices must match results count")

        successful_count = sum(
            1 for r in self.results if r.status == OperationStatus.SUCCESS
        )
        if successful_count != self.summary.successful:
            raise ValueError(
                "Summary successful count must match actual successful results"
            )

    @property
    def successful_results(self) -> List[NetworkOperationResult]:
        """Get only the successful results"""
        return [r for r in self.results if r.status == OperationStatus.SUCCESS]

    @property
    def failed_results(self) -> List[NetworkOperationResult]:
        """Get only the failed results"""
        return [r for r in self.results if r.status != OperationStatus.SUCCESS]

    def get_results_by_device(
        self, device_name: str
    ) -> Optional[NetworkOperationResult]:
        """Get result for a specific device"""
        return next(
            (r for r in self.results if r.device_name == device_name), None
        )


# Validation-related schemas for inventory validation


class ValidationStatus(Enum):
    """Enumeration for validation status values"""

    PASSED = "PASSED"
    FAILED = "FAILED"


@dataclass
class ValidationError:
    """
    Represents an error that occurred during inventory validation.

    Attributes:
        device_name: Name of the device that failed validation (None for file-level errors)
        device_index: Position of the device in the JSON array (None for file-level errors)
        field: The field that failed validation (None for file-level errors)
        error_type: Type of validation error (e.g., "REQUIRED_FIELD", "INVALID_FORMAT")
        message: Human-readable error message
        suggestion: Suggestion for fixing the error
    """

    device_name: Optional[str] = None
    device_index: Optional[int] = None
    field: Optional[str] = None
    error_type: str = ""
    message: str = ""
    suggestion: str = ""

    def __str__(self) -> str:
        """String representation for debugging."""
        if self.device_name:
            return f"ValidationError(device='{self.device_name}', field='{self.field}', type='{self.error_type}')"
        return f"ValidationError(file-level, type='{self.error_type}')"


@dataclass
class ValidationResult:
    """
    Represents the result of inventory validation.

    Attributes:
        status: Overall validation status (PASSED or FAILED)
        total_devices: Total number of devices in the inventory
        valid_devices: Number of devices that passed validation
        invalid_devices: Number of devices that failed validation
        errors: List of validation errors found
        file_path: Path to the inventory file that was validated
    """

    status: ValidationStatus
    total_devices: int
    valid_devices: int
    invalid_devices: int
    errors: List[ValidationError]
    file_path: str

    def __str__(self) -> str:
        """String representation for debugging."""
        return f"ValidationResult(status={self.status.value}, total={self.total_devices}, valid={self.valid_devices}, invalid={self.invalid_devices}, errors={len(self.errors)})"


# Type alias for return types - Go-like error handling pattern
NetworkResponse = Union[
    SuccessResponse, ErrorResponse, FeatureNotFoundResponse
]

# Type alias for batch operations
BatchResponse = BatchOperationResult
