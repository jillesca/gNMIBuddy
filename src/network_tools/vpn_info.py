#!/usr/bin/env python3
"""
VPN/VRF information module.
Provides functions for retrieving VRF/VPN information from network devices using gNMI.
"""

import logging
from typing import List, Optional, Union
from src.schemas.responses import (
    ErrorResponse,
    SuccessResponse,
    NetworkOperationResult,
)
from src.schemas.models import Device
from src.parsers.protocols.vrf import (
    parse_vrf_data,
    generate_vrf_summary,
    generate_llm_friendly_data,
)
from src.gnmi.client import get_gnmi_data
from src.gnmi.parameters import GnmiRequest


logger = logging.getLogger(__name__)


def get_vpn_information(
    device: Device,
    vrf: Optional[str] = None,
    include_details: bool = False,
) -> NetworkOperationResult:
    """
    Get VRF/VPN information from a network device.

    Args:
        device: Device object from inventory
        vrf: Optional VRF name filter
        include_details: Whether to show detailed information (default: False, returns summary only)

    Returns:
        NetworkOperationResult: Response object containing structured VRF information
    """

    # First get all VRF names from the device
    vrf_names_result = _get_vrfs_name(device)

    if isinstance(vrf_names_result, NetworkOperationResult):
        return vrf_names_result

    vrf_names = vrf_names_result

    if not vrf_names:
        logger.info("No VRFs found on device %s", device.name)
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="vpn_info",
            status="success",
            data={"vrfs": [], "vrf_count": 0},
            metadata={
                "vrf_filter": vrf,
                "include_details": include_details,
                "message": "No VRFs found",
            },
        )

    # If a specific VRF is requested, filter the list
    if isinstance(vrf_names, list) and vrf in vrf_names:
        vrf_names = [vrf]

    # Get detailed information for each VRF
    if isinstance(vrf_names, list):
        return _get_vrf_details(device, vrf_names)
    else:
        # This case should not happen if _get_vrfs_name is working correctly
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="vpn_info",
            status="failed",
            metadata={
                "issue_type": "VRF_NAMES_ERROR",
                "message": "Failed to retrieve VRF names",
            },
        )


DEFAULT_INTERNAL_VRFS = ["default", "**iid"]


def _get_vrfs_name(device: Device) -> Union[List[str], NetworkOperationResult]:
    """
    Get VRF names from a network device, excluding the DEFAULT VRF.

    Returns:
        Either a list of VRF names or a NetworkOperationResult with issue information
    """
    # Create a GnmiRequest for VRF names
    vrf_names_request = GnmiRequest(
        path=[
            "openconfig-network-instance:network-instances/network-instance[name=*]/state/name",
        ],
    )

    response = get_gnmi_data(device, vrf_names_request)

    if isinstance(response, ErrorResponse):
        logger.error("Error retrieving VRF names: %s", response.message)
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="vpn_info",
            status="failed",
            error_response=response,
        )

    # Extract VRF names from the response
    vrf_names = []
    if isinstance(response, SuccessResponse):
        # Work directly with response data
        if response.data:
            response_data = response.data
        else:
            response_data = []

        if isinstance(response_data, list):
            for item in response_data:
                if isinstance(item, dict) and "val" in item:
                    val = item.get("val")
                    if (
                        val
                        and isinstance(val, str)
                        and val.lower()
                        not in [vrf.lower() for vrf in DEFAULT_INTERNAL_VRFS]
                    ):
                        vrf_names.append(val)
    return vrf_names


def _get_vrf_details(
    device: Device,
    vrf_names: List[str],
) -> NetworkOperationResult:
    """
    Get detailed information for specified VRFs.

    Args:
        device: Device object from inventory
        vrf_names: List of VRF names to query
        vrf: Optional VRF name filter
        include_details: Whether to show detailed information (default: False, returns summary only)

    Returns:
        VpnInfoResponse: Response object containing structured VRF information with parsed data and summary
    """
    # If no VRF names, return empty result
    if not vrf_names:
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="vpn_info",
            status="success",
            data={"vpn_data": {}, "summary": {"message": "No VRFs found"}},
        )

    vrf_path_queries = []
    for vrf_name in vrf_names:
        vrf_path_queries.append(
            f"openconfig-network-instance:network-instances/network-instance[name={vrf_name}]"
        )

    # Create a GnmiRequest for VRF details
    vrf_details_request = GnmiRequest(
        path=vrf_path_queries, encoding="json_ietf"
    )

    # Get detailed VRF data
    response = get_gnmi_data(device, vrf_details_request)

    if isinstance(response, ErrorResponse):
        logger.error("Error retrieving VRF details: %s", response.message)
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="vpn_info",
            status="failed",
            error_response=response,
        )

    try:
        # Work directly with response data
        data_for_parsing = {}
        if isinstance(response, SuccessResponse):
            if response.data:
                data_for_parsing = {"response": response.data}

        parsed_data = parse_vrf_data(data_for_parsing)
        llm_data = generate_llm_friendly_data(parsed_data)
        summary = generate_vrf_summary(parsed_data)

        vpn_data = {
            "vrfs": [llm_data] if isinstance(llm_data, dict) else llm_data
        }

        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="vpn_info",
            status="success",
            data={
                "vpn_data": vpn_data,
                "summary": (
                    summary
                    if isinstance(summary, dict)
                    else {"summary": summary}
                ),
            },
        )
    except (KeyError, ValueError, TypeError) as e:
        logger.error("Error parsing VRF data: %s", str(e))
        error_response = ErrorResponse(
            type="PARSING_ERROR",
            message=f"Error parsing VRF data: {str(e)}",
        )
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="vpn_info",
            status="failed",
            error_response=error_response,
        )
