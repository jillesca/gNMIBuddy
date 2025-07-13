#!/usr/bin/env python3
"""
Routing information module.
Provides functions for retrieving routing protocol information from network devices using gNMI.
"""

import logging
from src.gnmi.client import get_gnmi_data
from src.gnmi.parameters import GnmiRequest
from src.gnmi.responses import (
    ErrorResponse,
    FeatureNotFoundResponse,
)
from src.inventory.models import Device
from src.parsers.system_info_parser import SystemInfoParser
from src.network_tools.responses import SystemInfoResponse


logger = logging.getLogger(__name__)


# Define common requests as constants
def system_request():
    return GnmiRequest(
        path=[
            "openconfig-system:/system",
        ],
    )


def get_system_information(device: Device) -> SystemInfoResponse:
    """
    Get system information from a device.

    Args:
        device: Target device

    Returns:
        SystemInfoResponse: Structured response object for system information
    """

    response = get_gnmi_data(device, system_request())

    # Error/feature-not-found handling
    if isinstance(response, ErrorResponse):
        return SystemInfoResponse(device_name=device.name, error=response)

    if isinstance(response, FeatureNotFoundResponse):
        return SystemInfoResponse(
            device_name=device.name, feature_not_found=response
        )

    response_dict = response.to_dict()
    parser = SystemInfoParser()
    try:
        parsed_data = parser.parse(response_dict)
        return SystemInfoResponse(
            device_name=device.name,
            system_info=parsed_data,
            summary=(
                parsed_data.get("summary", {})
                if isinstance(parsed_data, dict)
                else {}
            ),
        )
    except Exception as e:
        logger.error("Error parsing system info: %s", str(e))
        error_response = ErrorResponse(
            type="PARSING_ERROR",
            message=f"Error parsing system info: {str(e)}",
        )
        return SystemInfoResponse(
            device_name=device.name, error=error_response
        )
