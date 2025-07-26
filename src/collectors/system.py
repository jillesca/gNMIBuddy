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
from src.logging import get_logger, log_operation

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
    logger.debug("Getting system info for device %s", device.name)

    response = get_gnmi_data(device, system_request())
    logger.debug(
        "System gNMI response type: %s, status: %s",
        type(response).__name__,
        getattr(response, "status", "N/A"),
    )

    # Error/feature-not-found handling
    if isinstance(response, ErrorResponse):
        logger.debug(
            "ErrorResponse details - type: %s, message: %s",
            response.type,
            response.message,
        )
        logger.error(
            "Error retrieving system information from %s: %s",
            device.name,
            response.message,
        )
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="system_info",
            status=OperationStatus.FAILED,
            error_response=response,
        )

    if isinstance(response, FeatureNotFoundResponse):
        logger.debug(
            "FeatureNotFoundResponse - feature: %s, message: %s",
            response.feature_name,
            response.message,
        )
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
        logger.debug(
            "Processing system data with length: %d",
            len(response.data) if response.data else 0,
        )

        parsed_data = parser.process_data(response.data)
        logger.debug(
            "Parsed system data keys: %s",
            str(list(parsed_data.keys()) if parsed_data else []),
        )

        summary = (
            parsed_data.get("summary", {})
            if isinstance(parsed_data, dict)
            else {}
        )
        logger.debug("System summary available: %s", bool(summary))

        logger.info(
            "System information successfully collected for %s", device.name
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
        logger.debug("Exception details: %s", str(e), exc_info=True)
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
