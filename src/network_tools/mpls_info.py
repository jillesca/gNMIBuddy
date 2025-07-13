#!/usr/bin/env python3
"""
MPLS functions module.
Provides functions for retrieving MPLS information from network devices using gNMI.
"""

import logging
from typing import Dict, Any
from src.gnmi.client import get_gnmi_data
from src.gnmi.parameters import GnmiRequest
from src.gnmi.responses import ErrorResponse, SuccessResponse
from src.inventory.models import Device
from src.parsers.protocols.mpls.mpls_parser import (
    parse_mpls_data,
    generate_mpls_summary,
)

logger = logging.getLogger(__name__)


def mpls_request():
    return GnmiRequest(
        path=[
            "openconfig-network-instance:network-instances/network-instance[name=*]/mpls",
        ],
    )


def get_mpls_information(
    device: Device,
    include_details: bool = False,
) -> Dict[str, Any]:
    """
    Get MPLS information from a network device.

    Args:
        device: Device object from inventory
        include_details: Whether to show detailed information (default: False, returns summary only)

    Returns:
        Dict[str, Any]: Dictionary containing structured MPLS information
    """
    response = get_gnmi_data(device, mpls_request())

    if isinstance(response, ErrorResponse):
        logger.error("Error retrieving MPLS information: %s", response.message)
        return {"device_name": device.name, "error": response}

    try:
        # Work directly with response data
        data_for_parsing = {}
        if isinstance(response, SuccessResponse):
            if response.raw_data:
                data_for_parsing = response.raw_data
            elif response.data:
                data_for_parsing = {"response": response.data}

        mpls_data = parse_mpls_data(data_for_parsing)
        summary = generate_mpls_summary(mpls_data)

        # Add summary to the mpls_data for consistent return format
        mpls_data["summary"] = summary

        return {
            "device_name": device.name,
            "mpls_data": mpls_data,
            "summary": (
                summary if isinstance(summary, dict) else {"summary": summary}
            ),
            "include_details": include_details,
        }
    except Exception as e:
        logger.error("Error parsing MPLS data: %s", str(e))
        error_response = ErrorResponse(
            type="PARSING_ERROR",
            message=f"Error parsing MPLS data: {str(e)}",
        )
        return {"device_name": device.name, "error": error_response}
