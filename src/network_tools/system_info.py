#!/usr/bin/env python3
"""
System information module.
Provides functions for retrieving system information from network devices using gNMI.
"""

import logging
from src.gnmi.client import get_gnmi_data
from src.gnmi.parameters import GnmiRequest
from src.gnmi.responses import (
    ErrorResponse,
    FeatureNotFoundResponse,
    NetworkOperationResult,
)
from src.inventory.models import Device
from src.parsers.system_info_parser import SystemInfoParser


logger = logging.getLogger(__name__)


# Define common requests as constants
def system_request():
    return GnmiRequest(
        path=[
            "openconfig-system:/system",
        ],
    )


def get_system_information(device: Device) -> NetworkOperationResult:
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
            status="failed",
            error_response=response,
        )

    if isinstance(response, FeatureNotFoundResponse):
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="system_info",
            status="feature_not_available",
            feature_not_found_response=response,
            metadata={
                "feature_name": "system information",
                "message": response.message,
            },
        )

    # Work directly with response data
    parser = SystemInfoParser()
    try:
        parsed_data = parser.parse(response.data)
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
            status="success",
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
            status="failed",
            error_response=error_response,
        )
