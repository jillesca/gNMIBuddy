#!/usr/bin/env python3
"""
Logging functions module.
Provides functions for retrieving logging information from network devices using gNMI.
"""

import logging
from typing import Optional
from src.schemas.models import Device
from src.gnmi.client import get_gnmi_data
from src.gnmi.parameters import GnmiRequest
from src.parsers.logs.filter import filter_logs
from src.schemas.responses import (
    ErrorResponse,
    SuccessResponse,
    OperationStatus,
    NetworkOperationResult,
)


logger = logging.getLogger(__name__)


def get_logs(
    device: Device,
    keywords: Optional[str] = None,
    minutes: Optional[int] = 5,
    show_all_logs: bool = False,
) -> NetworkOperationResult:
    """
    Get logging information from a network device.

    Args:
        device: Device object containing device information
        keywords: Optional keywords to filter logs
        minutes: Number of minutes to filter logs (default: 5 minutes)
        show_all_logs: If True, return all logs without time filtering (default: False)

    Returns:
        NetworkOperationResult: Response object containing logs or error information
    """
    # Prepare filter information for inclusion in the response
    filter_info = {
        "keywords": keywords,
        "filter_minutes": minutes if not show_all_logs else None,
        "show_all_logs": show_all_logs,
    }

    log_filter = (
        "(-[1-5]-|ISIS|BGP|ADJCHANGE|LINK-3|LINEPROTO|MPLS|VRF|VPN|CONFIG-3)"
    )

    if keywords:
        log_filter = f"(-[1-5]-|{keywords}) | utility egrep -v logged"

    log_query = f"show logging | utility egrep '{log_filter}' | utility egrep -v logged "

    # Create a GnmiRequest with the appropriate parameters for logs
    log_request = GnmiRequest(path=[log_query], encoding="ascii")

    response = get_gnmi_data(device=device, request=log_request)

    # logger.debug(f"Raw log response: {response}")

    if isinstance(response, ErrorResponse):
        logger.error(
            "Failed to get logs from %s: %s", device.name, response.message
        )
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="logs",
            status=OperationStatus.FAILED,
            error_response=response,
        )

    try:
        # Extract gNMI data from response
        gnmi_data = []
        if isinstance(response, SuccessResponse):
            if response.data:
                gnmi_data = response.data

        # Process the logs through the filter
        filtered_logs = filter_logs(
            gnmi_data or [], show_all_logs, minutes or 5
        )

        if "error" in filtered_logs:
            error_response = ErrorResponse(
                type="LOG_PROCESSING_ERROR", message=filtered_logs["error"]
            )
            return NetworkOperationResult(
                device_name=device.name,
                ip_address=device.ip_address,
                nos=device.nos,
                operation_type="logs",
                status=OperationStatus.FAILED,
                error_response=error_response,
            )

        # Create a response with the filtered logs
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="logs",
            status=OperationStatus.SUCCESS,
            data={
                "logs": filtered_logs.get("logs", []),
                "summary": {
                    "count": len(filtered_logs.get("logs", [])),
                    "filter_info": filter_info,
                },
                "filters_applied": filter_info,
            },
        )
    except Exception as e:
        logger.error("Error processing logs from %s: %s", device.name, str(e))
        error_response = ErrorResponse(
            type="LOG_PROCESSING_ERROR",
            message=f"Error processing logs: {str(e)}",
        )
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="logs",
            status=OperationStatus.FAILED,
            error_response=error_response,
        )
