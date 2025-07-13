#!/usr/bin/env python3
"""
Routing information module.
Provides functions for retrieving routing protocol information from network devices using gNMI.
"""

import logging
from typing import Optional, List, Dict, Any
from src.gnmi.client import get_gnmi_data
from src.gnmi.parameters import GnmiRequest
from src.gnmi.responses import (
    ErrorResponse,
    FeatureNotFoundResponse,
    SuccessResponse,
)
from src.inventory.models import Device
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
) -> List[Dict[str, Any]]:
    """
    Get routing information from a network device.

    Args:
        device: Device object from inventory
        protocol: Optional protocol filter (bgp, ospf, isis, connected, static)
        include_details: Whether to show detailed information (default: False, returns summary only)

    Returns:
        List of dictionaries containing structured routing information
    """
    result = []

    if protocol is None or "bgp" in protocol:
        result.append(_get_bgp_info(device, include_details))
    if protocol is None or "isis" in protocol:
        result.append(_get_isis_info(device, include_details))

    return result


def _get_isis_info(
    device: Device, include_details: bool = False
) -> Dict[str, Any]:
    """
    Get ISIS routing information from a device.

    Args:
        device: Target device
        include_details: Whether to include detailed information

    Returns:
        Dictionary containing ISIS information
    """
    response = get_gnmi_data(device, isis_request())

    # Handle feature not found responses
    if isinstance(response, FeatureNotFoundResponse):
        logger.info("No ISIS configuration found: %s", response)
        return {
            "device_name": device.name,
            "feature_not_found": response,
        }

    if isinstance(response, ErrorResponse):
        logger.error("Error retrieving ISIS information: %s", response.message)
        return {"device_name": device.name, "error": response}

    try:
        # Work directly with response data
        data_for_parsing = {}
        if isinstance(response, SuccessResponse):
            if response.raw_data:
                data_for_parsing = response.raw_data
            elif response.data:
                data_for_parsing = {"response": response.data}

        isis_data = parse_isis_data(data_for_parsing)
        summary = generate_isis_summary(isis_data)

        return {
            "device_name": device.name,
            "protocols": [{"isis": isis_data}],
            "summary": (
                summary if isinstance(summary, dict) else {"summary": summary}
            ),
            "include_details": include_details,
        }
    except Exception as e:
        logger.error("Error parsing ISIS data: %s", str(e))
        error_response = ErrorResponse(
            type="PARSING_ERROR",
            message=f"Error parsing ISIS data: {str(e)}",
        )
        return {"device_name": device.name, "error": error_response}


def _get_bgp_info(
    device: Device, include_details: bool = False
) -> Dict[str, Any]:
    """
    Get BGP routing information from a device.

    Args:
        device: Target device
        include_details: Whether to include detailed information

    Returns:
        Dictionary containing BGP information
    """
    response = get_gnmi_data(device, bgp_request())

    # Handle feature not found responses
    if isinstance(response, FeatureNotFoundResponse):
        logger.info("No BGP configuration found: %s", response)
        return {
            "device_name": device.name,
            "feature_not_found": response,
        }

    if isinstance(response, ErrorResponse):
        logger.error("Error retrieving BGP information: %s", response.message)
        return {"device_name": device.name, "error": response}

    try:
        # Work directly with response data
        data_for_parsing = {}
        if isinstance(response, SuccessResponse):
            if response.raw_data:
                data_for_parsing = response.raw_data
            elif response.data:
                data_for_parsing = {"response": response.data}

        bgp_data = parse_bgp_data(data_for_parsing)
        summary = generate_bgp_summary(bgp_data)

        return {
            "device_name": device.name,
            "protocols": [{"bgp": bgp_data}],
            "summary": (
                summary if isinstance(summary, dict) else {"summary": summary}
            ),
            "include_details": include_details,
        }
    except Exception as e:
        logger.error("Error parsing BGP data: %s", str(e))
        error_response = ErrorResponse(
            type="PARSING_ERROR",
            message=f"Error parsing BGP data: {str(e)}",
        )
        return {"device_name": device.name, "error": error_response}
