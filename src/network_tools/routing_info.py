#!/usr/bin/env python3
"""
Routing information module.
Provides functions for retrieving routing protocol information from network devices using gNMI.
"""

import logging
from typing import Optional
from src.gnmi.client import get_gnmi_data
from src.gnmi.parameters import GnmiRequest
from src.schemas.responses import (
    ErrorResponse,
    FeatureNotFoundResponse,
    SuccessResponse,
    NetworkOperationResult,
)
from src.schemas.models import Device
from src.parsers.protocols.bgp.config_parser import (
    parse_bgp_data,
    generate_bgp_summary,
)
from src.parsers.protocols.isis.isis_parser import (
    parse_isis_data,
    generate_isis_summary,
)


logger = logging.getLogger(__name__)


# Define common requests as constants
def isis_request():
    return GnmiRequest(
        path=[
            "openconfig-network-instance:network-instances/network-instance[name=*]/protocols/protocol/isis/interfaces/",
            "openconfig-network-instance:network-instances/network-instance[name=*]/protocols/protocol/isis/global/",
        ],
    )


def bgp_request():
    return GnmiRequest(
        path=[
            "openconfig-network-instance:network-instances/network-instance[name=*]/protocols/protocol/bgp"
        ],
    )


def get_routing_information(
    device: Device,
    protocol: Optional[str] = None,
    include_details: bool = False,
) -> NetworkOperationResult:
    """
    Get routing information from a network device.

    Args:
        device: Device object from inventory
        protocol: Optional protocol filter (bgp, ospf, isis, connected, static)
        include_details: Whether to show detailed information (default: False, returns summary only)

    Returns:
        NetworkOperationResult: Response object containing structured routing information
    """
    routing_data = {}
    combined_summary = {}

    # Collect data for requested protocols
    if protocol is None or "bgp" in protocol:
        bgp_result = _get_bgp_info(device, include_details)
        if bgp_result.status == "success":
            if bgp_result.data:
                routing_data["bgp"] = bgp_result.data.get("routing_data", {})
                combined_summary.update(bgp_result.data.get("summary", {}))
        else:
            # Return early if there's an error
            return bgp_result

    if protocol is None or "isis" in protocol:
        isis_result = _get_isis_info(device, include_details)
        if isis_result.status == "success":
            if isis_result.data:
                routing_data["isis"] = isis_result.data.get("routing_data", {})
                combined_summary.update(isis_result.data.get("summary", {}))
        else:
            # Return early if there's an error
            return isis_result

    return NetworkOperationResult(
        device_name=device.name,
        ip_address=device.ip_address,
        nos=device.nos,
        operation_type="routing_info",
        status="success",
        data={"routing_data": routing_data, "summary": combined_summary},
        metadata={"protocol": protocol, "include_details": include_details},
    )


def _get_isis_info(
    device: Device, include_details: bool = False
) -> NetworkOperationResult:
    """
    Get ISIS routing information from a device.

    Args:
        device: Target device
        include_details: Whether to include detailed information

    Returns:
        NetworkOperationResult: Response object containing ISIS information
    """
    response = get_gnmi_data(device, isis_request())

    # Handle feature not found responses
    if isinstance(response, FeatureNotFoundResponse):
        logger.info("No ISIS configuration found: %s", response)
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="routing_info",
            status="feature_not_available",
            feature_not_found_response=response,
        )

    if isinstance(response, ErrorResponse):
        logger.error("Error retrieving ISIS information: %s", response.message)
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="routing_info",
            status="failed",
            error_response=response,
        )

    try:
        # Work directly with response data
        if isinstance(response, SuccessResponse):
            isis_data = parse_isis_data(response.data)
        else:
            isis_data = parse_isis_data([])
        summary = generate_isis_summary(isis_data)

        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="routing_info",
            status="success",
            data={
                "routing_data": {"isis": isis_data},
                "summary": (
                    summary
                    if isinstance(summary, dict)
                    else {"summary": summary}
                ),
            },
            metadata={"protocol": "isis", "include_details": include_details},
        )
    except (KeyError, ValueError, TypeError) as e:
        logger.error("Error parsing ISIS data: %s", str(e))
        error_response = ErrorResponse(
            type="PARSING_ERROR",
            message=f"Error parsing ISIS data: {str(e)}",
        )
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="routing_info",
            status="failed",
            error_response=error_response,
        )


def _get_bgp_info(
    device: Device, include_details: bool = False
) -> NetworkOperationResult:
    """
    Get BGP routing information from a device.

    Args:
        device: Target device
        include_details: Whether to include detailed information

    Returns:
        NetworkOperationResult: Response object containing BGP information
    """
    response = get_gnmi_data(device, bgp_request())

    # Handle feature not found responses
    if isinstance(response, FeatureNotFoundResponse):
        logger.info("No BGP configuration found: %s", response)
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="routing_info",
            status="feature_not_available",
            feature_not_found_response=response,
        )

    if isinstance(response, ErrorResponse):
        logger.error("Error retrieving BGP information: %s", response.message)
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="routing_info",
            status="failed",
            error_response=response,
        )

    try:
        # Work directly with response data
        data_for_parsing = {}
        if isinstance(response, SuccessResponse):
            if response.data:
                data_for_parsing = {"response": response.data}

        bgp_data = parse_bgp_data(data_for_parsing)
        summary = generate_bgp_summary(bgp_data)

        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="routing_info",
            status="success",
            data={
                "routing_data": {"bgp": bgp_data},
                "summary": (
                    summary
                    if isinstance(summary, dict)
                    else {"summary": summary}
                ),
            },
            metadata={"protocol": "bgp", "include_details": include_details},
        )
    except (KeyError, ValueError, TypeError) as e:
        logger.error("Error parsing BGP data: %s", str(e))
        error_response = ErrorResponse(
            type="PARSING_ERROR",
            message=f"Error parsing BGP data: {str(e)}",
        )
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="routing_info",
            status="failed",
            error_response=error_response,
        )
