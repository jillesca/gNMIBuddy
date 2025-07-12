#!/usr/bin/env python3
"""
Routing information module.
Provides functions for retrieving routing protocol information from network devices using gNMI.
"""

import logging
from typing import cast
from src.gnmi.client import get_gnmi_data
from src.gnmi.parameters import GnmiRequest
from src.gnmi.responses import (
    GnmiError,
    GnmiFeatureNotFoundResponse,
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
    if isinstance(response, GnmiError):
        return cast(
            SystemInfoResponse,
            SystemInfoResponse.error_response(
                response, device_name=device.name
            ),
        )
    if isinstance(response, GnmiFeatureNotFoundResponse):
        return cast(
            SystemInfoResponse,
            SystemInfoResponse.error_response(
                response, device_name=device.name
            ),
        )

    response_dict = response.to_dict()
    parser = SystemInfoParser()
    try:
        parsed_data = parser.parse(response_dict)
        return SystemInfoResponse.from_dict(
            parsed_data, device_name=device.name
        )
    except Exception as e:
        logger.error(f"Error parsing system info: {str(e)}")
        return cast(
            SystemInfoResponse,
            SystemInfoResponse.error_response(
                GnmiError(
                    type="PARSING_ERROR",
                    message=f"Error parsing system info: {str(e)}",
                ),
                device_name=device.name,
            ),
        )
