#!/usr/bin/env python3
"""
MPLS functions module.
Provides functions for retrieving MPLS information from network devices using gNMI.
"""

import logging
from src.gnmi.client import get_gnmi_data
from src.gnmi.parameters import GnmiRequest
from src.gnmi.responses import GnmiError
from src.inventory.models import Device
from src.network_tools.responses import MplsResponse
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
) -> MplsResponse:
    """
    Get MPLS information from a network device.

    Args:
        device: Device object from inventory
        include_details: Whether to show detailed information (default: False, returns summary only)

    Returns:
        MplsResponse object containing structured MPLS information
    """
    response = get_gnmi_data(device, mpls_request())

    if response.is_error():
        logger.error(f"Error retrieving MPLS information: {response.error}")
        return MplsResponse.error_response(response.error)

    try:
        mpls_data = parse_mpls_data(response.to_dict())
        summary = generate_mpls_summary(mpls_data)

        # Add summary to the mpls_data for consistent return format
        mpls_data["summary"] = summary

        mpls_response = MplsResponse(
            success=True,
            device_name=device.name,
            mpls_data=mpls_data,
            summary=summary,
            include_details=include_details,
            raw_data=response.raw_data,
        )

        return mpls_response
    except Exception as e:
        logger.error(f"Error parsing MPLS data: {str(e)}")
        return MplsResponse.error_response(
            GnmiError(
                type="PARSING_ERROR",
                message=f"Error parsing MPLS data: {str(e)}",
            )
        )
