#!/usr/bin/env python3
"""
Routing information module.
Provides functions for retrieving routing protocol information from network devices using gNMI.
"""

from typing import Optional
from src.gnmi.client import get_gnmi_data
from src.gnmi.parameters import GnmiRequest
from src.schemas.responses import (
    ErrorResponse,
    SuccessResponse,
    OperationStatus,
    NetworkOperationResult,
    FeatureNotFoundResponse,
)
from src.schemas.models import Device
from src.processors.protocols.bgp.config_processor import (
    process_bgp_data,
    generate_bgp_summary,
)
from src.processors.protocols.isis.isis_processor import (
    process_isis_data,
    generate_isis_summary,
)
from src.decorators.smart_capability_verification import verify_required_models
from src.logging.config import get_logger, log_operation

logger = get_logger(__name__)


# Define common requests as constants
def isis_request():
    """
    Create a gNMI request for ISIS routing information.

    Returns:
        GnmiRequest: Request object for ISIS data collection
    """
    logger.debug("Creating ISIS gNMI request")
    request = GnmiRequest(
        path=[
            "openconfig-network-instance:network-instances/network-instance[name=*]/protocols/protocol/isis/interfaces/",
            "openconfig-network-instance:network-instances/network-instance[name=*]/protocols/protocol/isis/global/",
        ],
    )
    logger.debug(
        "ISIS gNMI request created",
        extra={
            "path_count": len(request.path),
            "paths": request.path,
        },
    )
    return request


def bgp_request():
    """
    Create a gNMI request for BGP routing information.

    Returns:
        GnmiRequest: Request object for BGP data collection
    """
    logger.debug("Creating BGP gNMI request")
    request = GnmiRequest(
        path=[
            "openconfig-network-instance:network-instances/network-instance[name=*]/protocols/protocol/bgp"
        ],
    )
    logger.debug(
        "BGP gNMI request created",
        extra={
            "path_count": len(request.path),
            "paths": request.path,
        },
    )
    return request


@verify_required_models()
@log_operation("get_routing_info")
def get_routing_info(
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
    logger.info(
        "Starting routing information collection",
        extra={
            "device_name": device.name,
            "device_ip": device.ip_address,
            "protocol": protocol,
            "include_details": include_details,
        },
    )

    routing_data = {}
    combined_summary = {}
    protocols_to_collect = []

    # Determine which protocols to collect
    if protocol is None:
        protocols_to_collect = ["bgp", "isis"]
        logger.debug(
            "No protocol specified, collecting all protocols",
            extra={
                "device_name": device.name,
                "protocols": protocols_to_collect,
            },
        )
    else:
        if "bgp" in protocol:
            protocols_to_collect.append("bgp")
        if "isis" in protocol:
            protocols_to_collect.append("isis")
        logger.debug(
            "Protocol filter specified",
            extra={
                "device_name": device.name,
                "requested_protocol": protocol,
                "protocols_to_collect": protocols_to_collect,
            },
        )

    # Collect data for requested protocols
    if "bgp" in protocols_to_collect:
        logger.debug(
            "Collecting BGP routing information",
            extra={"device_name": device.name},
        )
        bgp_result = _get_bgp_info(device, include_details)
        if bgp_result.status == OperationStatus.SUCCESS:
            if bgp_result.data:
                routing_data["bgp"] = bgp_result.data.get("routing_data", {})
                combined_summary.update(bgp_result.data.get("summary", {}))
                logger.debug(
                    "BGP data collected successfully",
                    extra={
                        "device_name": device.name,
                        "bgp_data_keys": list(bgp_result.data.keys()),
                    },
                )
        else:
            logger.error(
                "BGP data collection failed",
                extra={
                    "device_name": device.name,
                    "status": bgp_result.status.value,
                },
            )
            # Return early if there's an error
            return bgp_result

    if "isis" in protocols_to_collect:
        logger.debug(
            "Collecting ISIS routing information",
            extra={"device_name": device.name},
        )
        isis_result = _get_isis_info(device, include_details)
        if isis_result.status == OperationStatus.SUCCESS:
            if isis_result.data:
                routing_data["isis"] = isis_result.data.get("routing_data", {})
                combined_summary.update(isis_result.data.get("summary", {}))
                logger.debug(
                    "ISIS data collected successfully",
                    extra={
                        "device_name": device.name,
                        "isis_data_keys": list(isis_result.data.keys()),
                    },
                )
        else:
            logger.error(
                "ISIS data collection failed",
                extra={
                    "device_name": device.name,
                    "status": isis_result.status.value,
                },
            )
            # Return early if there's an error
            return isis_result

    result = NetworkOperationResult(
        device_name=device.name,
        ip_address=device.ip_address,
        nos=device.nos,
        operation_type="routing_info",
        status=OperationStatus.SUCCESS,
        data={"routing_data": routing_data, "summary": combined_summary},
        metadata={"protocol": protocol, "include_details": include_details},
    )

    logger.info(
        "Routing information collection completed",
        extra={
            "device_name": device.name,
            "protocols_collected": list(routing_data.keys()),
            "summary_keys": list(combined_summary.keys()),
            "total_data_points": sum(
                len(data) if isinstance(data, (list, dict)) else 1
                for data in routing_data.values()
            ),
        },
    )

    return result


@log_operation("get_isis_info")
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
    logger.debug(
        "Starting ISIS information collection",
        extra={
            "device_name": device.name,
            "include_details": include_details,
        },
    )

    response = get_gnmi_data(device, isis_request())

    # Handle feature not found responses
    if isinstance(response, FeatureNotFoundResponse):
        logger.info(
            "No ISIS configuration found on device",
            extra={
                "device_name": device.name,
                "feature_name": response.feature_name,
                "response_message": response.message,
            },
        )
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="routing_info",
            status=OperationStatus.FEATURE_NOT_AVAILABLE,
            feature_not_found_response=response,
        )

    if isinstance(response, ErrorResponse):
        logger.error(
            "Error retrieving ISIS information",
            extra={
                "device_name": device.name,
                "error_type": response.type,
                "error_message": response.message,
            },
        )
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="routing_info",
            status=OperationStatus.FAILED,
            error_response=response,
        )

    try:
        # Work directly with response data
        if isinstance(response, SuccessResponse):
            logger.debug(
                "Processing ISIS data from successful response",
                extra={
                    "device_name": device.name,
                    "data_points": len(response.data) if response.data else 0,
                },
            )
            isis_data = process_isis_data(response.data)
        else:
            logger.debug(
                "Processing empty ISIS data",
                extra={"device_name": device.name},
            )
            isis_data = process_isis_data([])

        summary = generate_isis_summary(isis_data)

        logger.debug(
            "ISIS data processing completed",
            extra={
                "device_name": device.name,
                "isis_data_keys": (
                    list(isis_data.keys())
                    if isinstance(isis_data, dict)
                    else None
                ),
                "summary_type": type(summary).__name__,
            },
        )

        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="routing_info",
            status=OperationStatus.SUCCESS,
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
        logger.error(
            "Error parsing ISIS data",
            extra={
                "device_name": device.name,
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
            exc_info=True,
        )
        error_response = ErrorResponse(
            type="PARSING_ERROR",
            message=f"Error parsing ISIS data: {str(e)}",
        )
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="routing_info",
            status=OperationStatus.FAILED,
            error_response=error_response,
        )


@log_operation("get_bgp_info")
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
    logger.debug(
        "Starting BGP information collection",
        extra={
            "device_name": device.name,
            "include_details": include_details,
        },
    )

    response = get_gnmi_data(device, bgp_request())

    # Handle feature not found responses
    if isinstance(response, FeatureNotFoundResponse):
        logger.info(
            "No BGP configuration found on device",
            extra={
                "device_name": device.name,
                "feature_name": response.feature_name,
                "response_message": response.message,
            },
        )
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="routing_info",
            status=OperationStatus.FEATURE_NOT_AVAILABLE,
            feature_not_found_response=response,
        )

    if isinstance(response, ErrorResponse):
        logger.error(
            "Error retrieving BGP information",
            extra={
                "device_name": device.name,
                "error_type": response.type,
                "error_message": response.message,
            },
        )
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="routing_info",
            status=OperationStatus.FAILED,
            error_response=response,
        )

    try:
        # Extract gNMI data from response
        gnmi_data = []
        if isinstance(response, SuccessResponse):
            if response.data:
                gnmi_data = response.data
                logger.debug(
                    "Processing BGP data from successful response",
                    extra={
                        "device_name": device.name,
                        "data_points": len(response.data),
                    },
                )
            else:
                logger.debug(
                    "No BGP data in successful response",
                    extra={"device_name": device.name},
                )
        else:
            logger.debug(
                "Processing empty BGP data",
                extra={"device_name": device.name},
            )

        bgp_data = process_bgp_data(gnmi_data or [])
        summary = generate_bgp_summary(bgp_data)

        logger.debug(
            "BGP data processing completed",
            extra={
                "device_name": device.name,
                "bgp_data_keys": (
                    list(bgp_data.keys())
                    if isinstance(bgp_data, dict)
                    else None
                ),
                "summary_type": type(summary).__name__,
            },
        )

        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="routing_info",
            status=OperationStatus.SUCCESS,
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
        logger.error(
            "Error parsing BGP data",
            extra={
                "device_name": device.name,
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
            exc_info=True,
        )
        error_response = ErrorResponse(
            type="PARSING_ERROR",
            message=f"Error parsing BGP data: {str(e)}",
        )
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="routing_info",
            status=OperationStatus.FAILED,
            error_response=error_response,
        )
