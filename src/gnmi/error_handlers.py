#!/usr/bin/env python3
"""Error handling functions for network operations"""
from typing import Optional, Union
import re
import grpc
from src.inventory.models import Device
from src.gnmi.responses import ErrorResponse, FeatureNotFoundResponse
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def handle_timeout_error(device: Device) -> ErrorResponse:
    """
    Handle connection timeout errors.

    Returns:
        ErrorResponse object with error details
    """
    error_msg = f"Connection timeout when connecting to {device.name} ({device.ip_address}:{device.port})"
    _log_error(device.name, error_msg)

    return ErrorResponse(
        type="CONNECTION_TIMEOUT",
        message=error_msg,
        details={"error_class": "grpc.FutureTimeoutError"},
    )


def handle_rpc_error(
    device: Device, error: grpc.RpcError
) -> Union[ErrorResponse, FeatureNotFoundResponse]:
    """
    Handle gRPC RPC errors from network operations.

    Returns:
        ErrorResponse object with error details or FeatureNotFoundResponse if a feature is not found
    """
    error_type = "GRPC_ERROR"

    # We need to handle these attributes carefully for type checking
    # Using getattr is safer than hasattr+access approach
    try:
        status_code = getattr(error, "code", lambda: None)()
        details = getattr(error, "details", lambda: str(error))()
        code_name = getattr(status_code, "name", "UNKNOWN")
        code_value = getattr(status_code, "value", 0)
    except (AttributeError, TypeError):
        # Fallback values if attributes are missing or have unexpected types
        code_name = "UNKNOWN"
        code_value = 0
        details = str(error)
    feature_name = _extract_feature_name(details)
    error_msg = f"gRPC error when connecting to {device.name}: {code_name} ({code_value}). Details: {details}"

    if feature_name:
        # Return feature not found response instead of error
        _log_error(device.name, error_msg, level="info")
        return FeatureNotFoundResponse.create(
            feature_name=feature_name,
            message=f"Feature '{feature_name}' not found on device {device.name}",
            details={
                "code": code_name,
                "code_value": code_value,
                "device": device.name,
                "device_ip": device.ip_address,
                "full_details": details,
            },
        )

    _log_error(
        device.name,
        error_msg,
    )

    return ErrorResponse(
        type=error_type,
        message=error_msg,
        details={
            "code": code_name,
            "code_value": code_value,
            "details": details,
        },
    )


def handle_connection_refused(device: Device) -> ErrorResponse:
    """
    Handle connection refused errors when connecting to a target.

    Returns:
        ErrorResponse object with error details
    """
    error_msg = f"Connection refused by {device.name} ({device.ip_address}:{device.port}). Ensure the device is running and the port is open."
    _log_error(device.name, error_msg)

    return ErrorResponse(type="CONNECTION_REFUSED", message=error_msg)


def handle_generic_error(
    device: Device, error: Exception
) -> Union[ErrorResponse, FeatureNotFoundResponse]:
    """
    Handle generic exceptions that may occur during network operations.

    Returns:
        ErrorResponse object with error details or FeatureNotFoundResponse if a feature is not found
    """
    error_type = type(error).__name__
    error_message = str(error)
    feature_name = _extract_feature_name(error_message)

    if feature_name or "not found" in error_message.lower():
        # Return feature not found response instead of error
        return FeatureNotFoundResponse.create(
            feature_name=feature_name or "unknown",
            message=f"Feature not found on device {device.name}: {error_message}",
            details={
                "device": device.name,
                "device_ip": device.ip_address,
            },
        )

    error_msg = f"{error_type} - {error_message}"
    _log_error(device.name, error_msg)

    return ErrorResponse(type=error_type, message=error_message)


def _extract_feature_name(details: str) -> Optional[str]:
    not_found_patterns = [
        r"Requested element\(s\) not found: '([^']+)'",  # gRPC error pattern
        r"not found: '([^']+)'",  # Generic error pattern
    ]

    for pattern in not_found_patterns:
        match = re.search(pattern, details, re.IGNORECASE)
        if match:
            return match.group(1)

    return None


def _log_error(device_name: str, message: str, level: str = "error") -> None:
    log_message = f"Error during request to {device_name}: {message}"

    if level == "warning":
        logger.warning(log_message)
    elif level == "info":
        logger.info(log_message)
    else:
        logger.error(log_message)
