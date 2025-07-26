#!/usr/bin/env python3
"""
VPN/VRF information module.
Provides functions for retrieving VRF/VPN information from network devices using gNMI.
"""

from typing import List, Optional, Union
from src.schemas.responses import (
    ErrorResponse,
    SuccessResponse,
    OperationStatus,
    NetworkOperationResult,
)
from src.schemas.models import Device
from src.processors.protocols.vrf import (
    process_vrf_data,
    generate_individual_vrf_summary,
    generate_llm_friendly_data,
)
from src.gnmi.client import get_gnmi_data
from src.gnmi.parameters import GnmiRequest
from src.logging.config import get_logger, log_operation
from src.utils.vrf_utils import (
    get_non_default_vrf_names,
    DEFAULT_INTERNAL_VRFS,
)

logger = get_logger(__name__)


def get_vpn_info(
    device: Device,
    vrf_name: Optional[str] = None,
    include_details: bool = False,
) -> NetworkOperationResult:
    """
    Get VRF/VPN information from a network device.

    Args:
        device: Device object from inventory
        vrf_name: Optional VRF name filter
        include_details: Whether to show detailed information (default: False, returns summary only)

    Returns:
        NetworkOperationResult: Response object containing structured VRF information
    """

    # Get all VRF names from the device
    vrf_names_result = get_non_default_vrf_names(device)
    logger.debug(
        "VRF names discovery result for device %s: %s",
        device.name,
        str(vrf_names_result),
    )

    if not vrf_names_result:
        logger.info("No VRFs found on device %s", device.name)
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="vpn_info",
            status=OperationStatus.SUCCESS,
            data={"vrfs": []},
            metadata={
                "total_vrfs_on_device": 0,
                "vrfs_returned": 0,
                "vrf_filter_applied": vrf_name is not None,
                "vrf_filter": vrf_name,
                "include_details": include_details,
                "excluded_internal_vrfs": DEFAULT_INTERNAL_VRFS,
                "message": "No VRFs found",
            },
        )

    total_vrfs_found = len(vrf_names_result)
    logger.info(
        "Discovered %d VRFs on device %s", total_vrfs_found, device.name
    )

    # If a specific VRF is requested, filter the list
    if vrf_name:
        logger.debug(
            "Applying VRF filter '%s' to found VRFs: %s",
            vrf_name,
            vrf_names_result,
        )
        if vrf_name in vrf_names_result:
            vrf_names_result = [vrf_name]
        else:
            # VRF not found, return empty result
            logger.warning(
                "Requested VRF '%s' not found on device %s (available VRFs: %s)",
                vrf_name,
                device.name,
                str(vrf_names_result),
            )
            vrf_names_result = []
        logger.debug("VRFs after filtering: %s", str(vrf_names_result))

    # Get detailed information for each VRF
    return _get_vrf_details(
        device, vrf_names_result, include_details, total_vrfs_found, vrf_name
    )


def _get_vrf_details(
    device: Device,
    vrf_names: List[str],
    include_details: bool = False,
    total_vrfs_found: int = 0,
    vrf_name_filter: Optional[str] = None,
) -> NetworkOperationResult:
    """
    Get detailed information for specified VRFs.

    Args:
        device: Device object from inventory
        vrf_names: List of VRF names to query
        include_details: Whether to include detailed data in the response
        total_vrfs_found: Total number of VRFs found on the device
        vrf_name_filter: The VRF name filter applied, if any

    Returns:
        NetworkOperationResult: Response object containing structured VRF information with parsed data and summary
    """
    # If no VRF names, return empty result
    if not vrf_names:
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="vpn_info",
            status=OperationStatus.SUCCESS,
            data={"vrfs": []},
            metadata={
                "total_vrfs_on_device": total_vrfs_found,
                "vrfs_returned": 0,
                "vrf_filter_applied": vrf_name_filter is not None,
                "vrf_filter": vrf_name_filter,
                "include_details": include_details,
                "excluded_internal_vrfs": DEFAULT_INTERNAL_VRFS,
                "message": (
                    "No VRFs found matching filter"
                    if vrf_name_filter
                    else "No VRFs found"
                ),
            },
        )

    # Build path queries for each VRF
    vrf_path_queries = [
        f"openconfig-network-instance:network-instances/network-instance[name={vrf_name}]"
        for vrf_name in vrf_names
    ]
    logger.debug(
        "Building gNMI paths for VRFs %s: %s",
        str(vrf_names),
        str(vrf_path_queries),
    )

    vrf_details_request = GnmiRequest(
        path=vrf_path_queries, encoding="json_ietf"
    )

    response = get_gnmi_data(device, vrf_details_request)
    logger.debug(
        "gNMI response type: %s, status: %s",
        type(response).__name__,
        getattr(response, "status", "N/A"),
    )

    if isinstance(response, ErrorResponse):
        logger.debug(
            "ErrorResponse details - type: %s, message: %s",
            response.type,
            response.message,
        )
        logger.error("Error retrieving VRF details: %s", response.message)
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="vpn_info",
            status=OperationStatus.FAILED,
            error_response=response,
        )

    try:
        # Extract gNMI data from response
        gnmi_data = (
            response.data if isinstance(response, SuccessResponse) else []
        )
        logger.debug(
            "Extracted gNMI data length: %d",
            len(gnmi_data) if gnmi_data else 0,
        )

        processed_data = process_vrf_data(gnmi_data or [])
        logger.debug(
            "Processed VRF data keys: %s",
            str(list(processed_data.keys()) if processed_data else []),
        )

        llm_data = generate_llm_friendly_data(processed_data)
        logger.debug(
            "LLM-friendly data - VRF count: %d, keys: %s",
            len(llm_data.get("vrfs", [])),
            str(list(llm_data.keys())),
        )

        # Get timestamp for summaries
        timestamp = llm_data.get("timestamp", "Unknown")

        # Build the new data structure
        result_data = []

        # Process each VRF individually
        for vrf in llm_data.get("vrfs", []):
            vrf_entry = {}

            if include_details:
                vrf_entry["detailed_data"] = {
                    "timestamp": timestamp,
                    **vrf,
                }
            else:
                vrf_entry["detailed_data"] = {}

            vrf_entry["summary"] = generate_individual_vrf_summary(
                vrf, timestamp
            )

            result_data.append(vrf_entry)

        final_result = NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="vpn_info",
            status=OperationStatus.SUCCESS,
            data={"vrfs": result_data},
            metadata={
                "total_vrfs_on_device": total_vrfs_found,
                "vrfs_returned": len(result_data),
                "vrf_filter_applied": vrf_name_filter is not None,
                "vrf_filter": vrf_name_filter,
                "include_details": include_details,
                "excluded_internal_vrfs": DEFAULT_INTERNAL_VRFS,
                "message": "VRF information retrieved",
            },
        )

        logger.info(
            "VRF processing complete for %s: %d VRFs processed",
            device.name,
            len(result_data),
        )

        logger.debug(
            "Final NetworkOperationResult - status: %s, data entries: %d, metadata keys: %s",
            final_result.status,
            len(final_result.data),
            str(list(final_result.metadata.keys())),
        )

        return final_result

    except (KeyError, ValueError, TypeError) as e:
        logger.error("Error processing VRF data: %s", str(e))
        logger.debug("Exception details: %s", str(e), exc_info=True)
        error_response = ErrorResponse(
            type="PROCESSING_ERROR",
            message=f"Error processing VRF data: {str(e)}",
        )
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="vpn_info",
            status=OperationStatus.FAILED,
            error_response=error_response,
        )
