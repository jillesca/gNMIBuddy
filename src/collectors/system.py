#!/usr/bin/env python3
"""
System information module.
Provides functions for retrieving system information from network devices using gNMI.
"""

from src.schemas.responses import (
    ErrorResponse,
    OperationStatus,
    NetworkOperationResult,
    FeatureNotFoundResponse,
)
from src.schemas.models import Device
from src.gnmi.client import get_gnmi_data
from src.gnmi.parameters import GnmiRequest
from src.processors.system_info_processor import SystemInfoProcessor
from src.logging.config import get_logger, log_operation

logger = get_logger(__name__)


# Define common requests as constants
def system_request():
    return GnmiRequest(
        path=[
            "openconfig-system:/system",
        ],
    )


def get_system_info(device: Device) -> NetworkOperationResult:
    """
    Get system information from a device.

    Args:
        device: Target device

    Returns:
        NetworkOperationResult: Response object containing system information or failure details
    """

    response = get_gnmi_data(device, system_request())

    # Error/feature-not-found handling
    if isinstance(response, ErrorResponse):
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="system_info",
            status=OperationStatus.FAILED,
            error_response=response,
        )

    if isinstance(response, FeatureNotFoundResponse):
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="system_info",
            status=OperationStatus.FEATURE_NOT_AVAILABLE,
            feature_not_found_response=response,
            metadata={
                "feature_name": "system information",
                "message": response.message,
            },
        )

    # Work directly with response data
    parser = SystemInfoProcessor()
    try:
        parsed_data = parser.process_data(response.data)
        summary = (
            parsed_data.get("summary", {})
            if isinstance(parsed_data, dict)
            else {}
        )

        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="system_info",
            status=OperationStatus.SUCCESS,
            data={
                "system_data": parsed_data,
                "summary": summary,
            },
        )

    except (KeyError, ValueError, TypeError) as e:
        logger.error("Error parsing system info: %s", str(e))
        error_response = ErrorResponse(
            type="PARSING_ERROR",
            message=f"Error parsing system info: {str(e)}",
        )
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="system_info",
            status=OperationStatus.FAILED,
            error_response=error_response,
        )
