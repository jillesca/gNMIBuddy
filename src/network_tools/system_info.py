#!/usr/bin/env python3
"""
System information module.
Provides functions for retrieving system information from network devices using gNMI.
"""

import logging
from typing import Dict, Any
from src.gnmi.client import get_gnmi_data
from src.gnmi.parameters import GnmiRequest
from src.gnmi.responses import (
    ErrorResponse,
    FeatureNotFoundResponse,
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


def get_system_information(device: Device) -> Dict[str, Any]:
    """
    Get system information from a device.

    Args:
        device: Target device

    Returns:
        Dict[str, Any]: Dictionary containing system information, errors, or feature not found information
    """

    response = get_gnmi_data(device, system_request())

    # Error/feature-not-found handling
    if isinstance(response, ErrorResponse):
        return {"device_name": device.name, "error": response.to_dict()}

    if isinstance(response, FeatureNotFoundResponse):
        return {
            "device_name": device.name,
            "feature_not_found": response.to_dict(),
        }

    response_dict = response.to_dict()
    parser = SystemInfoParser()
    try:
        parsed_data = parser.parse(response_dict)
        return {
            "device_name": device.name,
            "system_info": parsed_data,
            "summary": (
                parsed_data.get("summary", {})
                if isinstance(parsed_data, dict)
                else {}
            ),
        }
    except Exception as e:
        logger.error("Error parsing system info: %s", str(e))
        error_response = ErrorResponse(
            type="PARSING_ERROR",
            message=f"Error parsing system info: {str(e)}",
        )
        return {"device_name": device.name, "error": error_response.to_dict()}
