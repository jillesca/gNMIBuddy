#!/usr/bin/env python3
"""
Provides functions for retrieving MPLS information from network devices using gNMI.
"""

import logging
from src.schemas.responses import (
    ErrorResponse,
    SuccessResponse,
    NetworkOperationResult,
)
from src.schemas.models import Device
from src.parsers.protocols.mpls.mpls_parser import (
    parse_mpls_data,
    generate_mpls_summary,
)
from src.gnmi.client import get_gnmi_data
from src.gnmi.parameters import GnmiRequest

logger = logging.getLogger(__name__)


def mpls_request():
    return GnmiRequest(
        path=[
            "openconfig-network-instance:network-instances/network-instance[name=*]/mpls",
        ],
    )


def get_mpls_information(device: Device) -> NetworkOperationResult:
    """
    Get MPLS information from a network device.

    Args:
        device: Device object from inventory

    Returns:
        NetworkOperationResult: Response object containing structured MPLS information
    """
    response = get_gnmi_data(device, mpls_request())

    if isinstance(response, ErrorResponse):
        logger.error("Error retrieving MPLS information: %s", response.message)
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="mpls_info",
            status="failed",
            error_response=response,
        )

    try:
        # Work directly with response data
        if isinstance(response, SuccessResponse):
            mpls_data = parse_mpls_data(response.data)
        else:
            mpls_data = parse_mpls_data([])
        summary = generate_mpls_summary(mpls_data)

        # Add summary to the mpls_data for consistent return format
        mpls_data["summary"] = summary

        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="mpls_info",
            status="success",
            data={
                "mpls_data": mpls_data,
                "summary": (
                    summary
                    if isinstance(summary, dict)
                    else {"summary": summary}
                ),
            },
        )
    except (KeyError, ValueError, TypeError) as e:
        logger.error("Error parsing MPLS data: %s", str(e))
        error_response = ErrorResponse(
            type="PARSING_ERROR",
            message=f"Error parsing MPLS data: {str(e)}",
        )
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="mpls_info",
            status="failed",
            error_response=error_response,
        )
