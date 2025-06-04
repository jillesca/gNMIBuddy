#!/usr/bin/env python3
"""
VPN/VRF information module.
Provides functions for retrieving VRF/VPN information from network devices using XPath.
"""

import logging
from typing import List, Optional
from src.gnmi.client import get_gnmi_data
from src.gnmi.parameters import GnmiRequest
from src.gnmi.responses import GnmiError
from src.inventory.models import Device
from src.network_tools.responses import VpnResponse
from src.parsers.protocols.vrf import (
    parse_vrf_data,
    generate_vrf_summary,
    generate_llm_friendly_data,
)


logger = logging.getLogger(__name__)


def get_vpn_information(
    device: Device,
    vrf: Optional[str] = None,
    include_details: bool = False,
) -> VpnResponse:
    """
    Get VRF/VPN information from a network device.

    Args:
        device: Device object from inventory
        vrf: Optional VRF name filter
        include_details: Whether to show detailed information (default: False, returns summary only)

    Returns:
        VpnResponse object containing structured VRF information
    """

    # First get all VRF names from the device
    vrf_names_result = _get_vrfs_name(device)

    if (
        isinstance(vrf_names_result, VpnResponse)
        and vrf_names_result.is_error()
    ):
        return vrf_names_result

    vrf_names = vrf_names_result

    if not vrf_names:
        logger.info(f"No VRFs found on device {device.name}")
        return VpnResponse(
            success=True,
            device_name=device.name,
            vrfs=[],
            summary={"message": "No VRFs found"},
        )

    # If a specific VRF is requested, filter the list
    if vrf in vrf_names:
        vrf_names = [vrf]

    # Get detailed information for each VRF
    return _get_vrf_details(device, vrf_names, include_details)


DEFAULT_INTERNAL_VRFS = ["default", "**iid"]


def _get_vrfs_name(device: Device) -> List[str] | VpnResponse:
    """
    Get VRF names from a network device, excluding the DEFAULT VRF.

    Returns:
        Either a list of VRF names or a VpnResponse with error information
    """
    # Create a GnmiRequest for VRF names
    vrf_names_request = GnmiRequest(
        xpath=[
            "openconfig-network-instance:network-instances/network-instance[name=*]/state/name",
        ],
    )

    response = get_gnmi_data(device, vrf_names_request)

    if response.is_error():
        logger.error(f"Error retrieving VRF names: {response.error}")
        return VpnResponse.error_response(response.error)

    # Extract VRF names from the response
    vrf_names = []
    if response.data:
        for item in response.data:
            if "val" in item:
                if item["val"].lower() not in [
                    vrf.lower() for vrf in DEFAULT_INTERNAL_VRFS
                ]:
                    vrf_names.append(item["val"])
    return vrf_names


def _get_vrf_details(
    device: Device, vrf_names: List[str], include_details: bool = False
) -> VpnResponse:
    """
    Get detailed information for specified VRFs.

    Args:
        device: Device object from inventory
        vrf_names: List of VRF names to query
        include_details: Whether to show detailed information (default: False, returns summary only)

    Returns:
        VpnResponse containing structured VRF information with parsed data and summary
    """
    # If no VRF names, return empty result
    if not vrf_names:
        return VpnResponse(
            success=True,
            device_name=device.name,
            vrfs=[],
            summary={"message": "No VRFs found"},
        )

    vrf_xpath_queries = []
    for vrf_name in vrf_names:
        vrf_xpath_queries.append(
            f"openconfig-network-instance:network-instances/network-instance[name={vrf_name}]"
        )

    # Create a GnmiRequest for VRF details
    vrf_details_request = GnmiRequest(
        xpath=vrf_xpath_queries, encoding="json_ietf"
    )

    # Get detailed VRF data
    response = get_gnmi_data(device, vrf_details_request)

    if response.is_error():
        logger.error(f"Error retrieving VRF details: {response.error}")
        return VpnResponse.error_response(response.error)

    try:
        parsed_data = parse_vrf_data(response.to_dict())
        llm_data = generate_llm_friendly_data(parsed_data)
        summary = generate_vrf_summary(parsed_data)

        vpn_response = VpnResponse(
            success=True,
            device_name=device.name,
            vrfs=llm_data,
            summary=summary,
            include_details=include_details,
            raw_data=response.raw_data,
        )

        return vpn_response
    except Exception as e:
        logger.error(f"Error parsing VRF data: {str(e)}")
        return VpnResponse.error_response(
            GnmiError(
                type="PARSING_ERROR",
                message=f"Error parsing VRF data: {str(e)}",
            )
        )
