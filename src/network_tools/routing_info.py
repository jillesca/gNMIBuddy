#!/usr/bin/env python3
"""
Routing information module.
Provides functions for retrieving routing protocol information from network devices using gNMI.
"""

import logging
from typing import Optional, List, cast
from src.gnmi.client import get_gnmi_data
from src.gnmi.parameters import GnmiRequest
from src.gnmi.responses import GnmiError, GnmiFeatureNotFoundResponse
from src.inventory.models import Device
from src.network_tools.responses import RoutingResponse
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
        xpath=[
            "openconfig-network-instance:network-instances/network-instance[name=*]/protocols/protocol/isis/interfaces/",
            "openconfig-network-instance:network-instances/network-instance[name=*]/protocols/protocol/isis/global/",
        ],
    )


def bgp_request():
    return GnmiRequest(
        xpath=[
            "openconfig-network-instance:network-instances/network-instance[name=*]/protocols/protocol/bgp"
        ],
    )


def get_routing_information(
    device: Device,
    protocol: Optional[str] = None,
    include_details: bool = False,
) -> List[RoutingResponse]:
    """
    Get routing information from a network device.

    Args:
        device: Device object from inventory
        protocol: Optional protocol filter (bgp, ospf, isis, connected, static)
        include_details: Whether to show detailed information (default: False, returns summary only)

    Returns:
        List of RoutingResponse objects containing structured routing information
    """
    result = []

    if protocol is None or "bgp" in protocol:
        result.append(_get_bgp_info(device, include_details))
    if protocol is None or "isis" in protocol:
        result.append(_get_isis_info(device, include_details))

    return result


def _get_isis_info(
    device: Device, include_details: bool = False
) -> RoutingResponse:
    """
    Get ISIS routing information from a device.

    Args:
        device: Target device
        include_details: Whether to include detailed information

    Returns:
        RoutingResponse containing ISIS information
    """
    response = get_gnmi_data(device, isis_request())

    # Special handling for GnmiFeatureNotFoundResponse
    if isinstance(response, GnmiFeatureNotFoundResponse):
        logger.error(
            f"Error retrieving ISIS information: {response.to_dict()}"
        )

        # Instead of creating a RoutingResponse directly, pass the feature_not_found data through the error_response
        # but set success=True so it doesn't get wrapped in an "error" object
        response_dict = response.to_dict()
        return cast(
            RoutingResponse,
            RoutingResponse(
                success=True, device_name=device.name, raw_data=response_dict
            ),
        )

    if response.is_error():
        logger.error(f"Error retrieving ISIS information: {response.error}")
        return RoutingResponse.error_response(
            response.error, device_name=device.name
        )

    try:
        isis_data = parse_isis_data(response.to_dict())
        summary = generate_isis_summary(isis_data)

        # Create structured response data
        routing_data = {
            "protocol": "isis",
            "routes": isis_data.get("routes", []),
            "protocols": {"isis": isis_data},
            "summary": summary,
        }

        return RoutingResponse(
            success=True,
            device_name=device.name,
            routes=routing_data.get("routes", []),
            protocols=routing_data.get("protocols", {}),
            summary=summary,
            include_details=include_details,
            raw_data=response.raw_data,
        )
    except Exception as e:
        logger.error(f"Error parsing ISIS data: {str(e)}")
        return RoutingResponse.error_response(
            GnmiError(
                type="PARSING_ERROR",
                message=f"Error parsing ISIS data: {str(e)}",
            ),
            device_name=device.name,
        )


def _get_bgp_info(
    device: Device, include_details: bool = False
) -> RoutingResponse:
    """
    Get BGP routing information from a device.

    Args:
        device: Target device
        include_details: Whether to include detailed information

    Returns:
        RoutingResponse containing BGP information
    """
    response = get_gnmi_data(device, bgp_request())

    # Special handling for feature not found responses
    if isinstance(response, GnmiFeatureNotFoundResponse):
        logger.error(f"Error retrieving BGP information: {response.to_dict()}")
        # Create a RoutingResponse that will pass through the feature_not_found data
        result = RoutingResponse(
            success=True, device_name=device.name, raw_data=response.to_dict()
        )
        return result

    if response.is_error():
        logger.error(f"Error retrieving BGP information: {response.error}")
        return RoutingResponse.error_response(
            response.error, device_name=device.name
        )

    try:
        bgp_data = parse_bgp_data(response.to_dict())
        summary = generate_bgp_summary(bgp_data)

        # Create structured response data
        routing_data = {
            "protocol": "bgp",
            "routes": bgp_data.get("routes", []),
            "protocols": {"bgp": bgp_data},
            "summary": summary,
        }

        return RoutingResponse(
            success=True,
            device_name=device.name,
            routes=routing_data.get("routes", []),
            protocols=routing_data.get("protocols", {}),
            summary=summary,
            include_details=include_details,
            raw_data=response.raw_data,
        )
    except Exception as e:
        logger.error(f"Error parsing BGP data: {str(e)}")
        return RoutingResponse.error_response(
            GnmiError(
                type="PARSING_ERROR",
                message=f"Error parsing BGP data: {str(e)}",
            ),
            device_name=device.name,
        )
