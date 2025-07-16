#!/usr/bin/env python3
"""
Routing information module.
Provides functions for retrieving routing protocol information from network devices using gNMI.
"""

from typing import Optional, List, Union, Dict
from src.gnmi.client import get_gnmi_data
from src.gnmi.parameters import GnmiRequest
from src.schemas.responses import (
    ErrorResponse,
    SuccessResponse,
    OperationStatus,
    NetworkOperationResult,
    FeatureNotFoundResponse,
    RoutingProtocol,
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
from src.logging.config import get_logger

logger = get_logger(__name__)


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


def get_routing_info(
    device: Device,
    protocol: Optional[
        Union[str, List[str], RoutingProtocol, List[RoutingProtocol]]
    ] = None,
    include_details: bool = False,
) -> NetworkOperationResult:
    """
    Get routing information from a network device.

    Args:
        device: Device object from inventory
        protocol: Optional protocol filter. Can be:
            - A single protocol string or RoutingProtocol enum value
            - A list of protocol strings or RoutingProtocol enum values
            - None to get all available protocols
        include_details: Whether to show detailed information (default: False, returns summary only)

    Returns:
        NetworkOperationResult: Response object containing structured routing information
    """
    routing_protocols = []
    protocols_to_query = _normalize_protocol_parameter(protocol)

    # Track protocol statuses and errors in metadata
    protocol_statuses = {}
    protocol_errors = {}

    for protocol_enum in protocols_to_query:
        protocol_name = protocol_enum.value

        if protocol_enum == RoutingProtocol.BGP:
            bgp_result = _get_bgp_info(device, include_details)
            protocol_statuses[protocol_name] = bgp_result.status.value

            if bgp_result.status == OperationStatus.SUCCESS:
                # Add successful protocol data to routing_protocols
                if bgp_result.data:
                    routing_protocols.append(
                        {
                            "protocol": protocol_name,
                            "detailed_data": bgp_result.data.get(
                                "detailed_data", {}
                            ),
                            "summary": bgp_result.data.get("summary", {}),
                        }
                    )
            elif bgp_result.status == OperationStatus.FEATURE_NOT_AVAILABLE:
                protocol_errors[protocol_name] = {
                    "type": "feature_not_found",
                    "message": (
                        bgp_result.feature_not_found_response.message
                        if bgp_result.feature_not_found_response
                        else ""
                    ),
                }
            else:
                protocol_errors[protocol_name] = {
                    "type": "error",
                    "message": (
                        bgp_result.error_response.message
                        if bgp_result.error_response
                        else ""
                    ),
                }

        elif protocol_enum == RoutingProtocol.ISIS:
            isis_result = _get_isis_info(device, include_details)
            protocol_statuses[protocol_name] = isis_result.status.value

            if isis_result.status == OperationStatus.SUCCESS:
                # Add successful protocol data to routing_protocols
                if isis_result.data:
                    routing_protocols.append(
                        {
                            "protocol": protocol_name,
                            "detailed_data": isis_result.data.get(
                                "detailed_data", {}
                            ),
                            "summary": isis_result.data.get("summary", {}),
                        }
                    )
            elif isis_result.status == OperationStatus.FEATURE_NOT_AVAILABLE:
                protocol_errors[protocol_name] = {
                    "type": "feature_not_found",
                    "message": (
                        isis_result.feature_not_found_response.message
                        if isis_result.feature_not_found_response
                        else ""
                    ),
                }
            else:
                protocol_errors[protocol_name] = {
                    "type": "error",
                    "message": (
                        isis_result.error_response.message
                        if isis_result.error_response
                        else ""
                    ),
                }

    # Calculate statistics
    successful_protocols = len(
        [
            s
            for s in protocol_statuses.values()
            if s == OperationStatus.SUCCESS.value
        ]
    )
    failed_protocols = len(
        [
            s
            for s in protocol_statuses.values()
            if s == OperationStatus.FAILED.value
        ]
    )
    feature_not_found_protocols = len(
        [
            s
            for s in protocol_statuses.values()
            if s == OperationStatus.FEATURE_NOT_AVAILABLE.value
        ]
    )
    total_protocols = len(protocols_to_query)

    # Determine overall status
    if successful_protocols == total_protocols:
        overall_status = OperationStatus.SUCCESS
    elif successful_protocols > 0:
        overall_status = OperationStatus.PARTIAL_SUCCESS
    elif feature_not_found_protocols == total_protocols:
        overall_status = OperationStatus.FEATURE_NOT_AVAILABLE
    else:
        overall_status = OperationStatus.FAILED

    protocol_str = ", ".join([p.value for p in protocols_to_query])

    metadata = {
        "protocol": protocol_str,
        "include_details": include_details,
        "successful_protocols": successful_protocols,
        "failed_protocols": failed_protocols,
        "feature_not_found_protocols": feature_not_found_protocols,
        "total_protocols": total_protocols,
        "protocol_statuses": protocol_statuses,
    }

    # Add error information to metadata if any protocols failed
    if protocol_errors:
        metadata["protocol_errors"] = protocol_errors

    return NetworkOperationResult(
        device_name=device.name,
        ip_address=device.ip_address,
        nos=device.nos,
        operation_type="routing_info",
        status=overall_status,
        data={"routing_protocols": routing_protocols},
        metadata=metadata,
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
            status=OperationStatus.FEATURE_NOT_AVAILABLE,
            feature_not_found_response=response,
        )

    if isinstance(response, ErrorResponse):
        logger.error("Error retrieving ISIS information: %s", response.message)
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="routing_info",
            status=OperationStatus.FAILED,
            error_response=response,
        )

    try:
        if isinstance(response, SuccessResponse):
            isis_data = process_isis_data(response.data)
        else:
            isis_data = process_isis_data([])
        summary = generate_isis_summary(isis_data)

        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="routing_info",
            status=OperationStatus.SUCCESS,
            data={
                "detailed_data": isis_data if include_details else {},
                "summary": summary,
            },
            metadata={
                "protocol": RoutingProtocol.ISIS.value,
                "include_details": include_details,
            },
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
            status=OperationStatus.FAILED,
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

    if isinstance(response, FeatureNotFoundResponse):
        logger.info("No BGP configuration found: %s", response)
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="routing_info",
            status=OperationStatus.FEATURE_NOT_AVAILABLE,
            feature_not_found_response=response,
        )

    if isinstance(response, ErrorResponse):
        logger.error("Error retrieving BGP information: %s", response.message)
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="routing_info",
            status=OperationStatus.FAILED,
            error_response=response,
        )

    try:
        gnmi_data = []
        if isinstance(response, SuccessResponse):
            if response.data:
                gnmi_data = response.data

        bgp_data = process_bgp_data(gnmi_data or [])
        summary = generate_bgp_summary(bgp_data)

        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="routing_info",
            status=OperationStatus.SUCCESS,
            data={
                "detailed_data": bgp_data if include_details else {},
                "summary": summary,
            },
            metadata={
                "protocol": RoutingProtocol.BGP.value,
                "include_details": include_details,
            },
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
            status=OperationStatus.FAILED,
            error_response=error_response,
        )


def _normalize_protocol_parameter(
    protocol: Optional[
        Union[str, List[str], RoutingProtocol, List[RoutingProtocol]]
    ] = None,
) -> List[RoutingProtocol]:
    """
    Normalize protocol parameter to a list of RoutingProtocol enums.

    Args:
        protocol: Various forms of protocol specification

    Returns:
        List of RoutingProtocol enums to query
    """
    if protocol is None:
        # Return all implemented protocols when no filter is specified
        return [RoutingProtocol.BGP, RoutingProtocol.ISIS]

    if isinstance(protocol, str):
        if "," in protocol:
            protocols = _parse_protocol_string(protocol)
            if protocols:
                return _normalize_protocol_parameter(protocols)
            return []
        else:
            try:
                return [RoutingProtocol(protocol)]
            except ValueError:
                logger.warning("Unknown protocol: %s", protocol)
                return []

    if isinstance(protocol, RoutingProtocol):
        return [protocol]

    if isinstance(protocol, list):
        result = []
        for p in protocol:
            if isinstance(p, str):
                try:
                    result.append(RoutingProtocol(p))
                except ValueError:
                    logger.warning("Unknown protocol: %s", p)
            elif isinstance(p, RoutingProtocol):
                result.append(p)
            else:
                logger.warning("Invalid protocol type: %s", type(p))
        return result

    logger.warning("Invalid protocol parameter type: %s", type(protocol))
    return []


def _parse_protocol_string(protocol_str: Optional[str]) -> Optional[List[str]]:
    """
    Parse a comma-separated protocol string into a list of protocol names.

    Args:
        protocol_str: String containing protocol names separated by commas

    Returns:
        List of protocol names, or None if input is None
    """
    if protocol_str is None:
        return None

    protocols = [p.strip() for p in protocol_str.split(",") if p.strip()]
    return protocols if protocols else None


def get_protocol_status(
    result: NetworkOperationResult, protocol_name: str
) -> Optional[str]:
    """
    Get the status of a specific protocol from a NetworkOperationResult.

    Args:
        result: The NetworkOperationResult containing protocol information
        protocol_name: The name of the protocol to retrieve (e.g., 'bgp', 'isis')

    Returns:
        Protocol status string if found, None otherwise
    """
    protocol_statuses = result.metadata.get("protocol_statuses", {})
    return protocol_statuses.get(protocol_name)


def get_protocol_error(
    result: NetworkOperationResult, protocol_name: str
) -> Optional[Dict[str, str]]:
    """
    Get the error information for a specific protocol from a NetworkOperationResult.

    Args:
        result: The NetworkOperationResult containing protocol information
        protocol_name: The name of the protocol to retrieve (e.g., 'bgp', 'isis')

    Returns:
        Error information dictionary if found, None otherwise
    """
    protocol_errors = result.metadata.get("protocol_errors", {})
    return protocol_errors.get(protocol_name)


def get_successful_protocols(result: NetworkOperationResult) -> List[str]:
    """
    Get a list of protocol names that were successfully queried.

    Args:
        result: The NetworkOperationResult containing protocol information

    Returns:
        List of protocol names that were successful
    """
    protocol_statuses = result.metadata.get("protocol_statuses", {})
    return [
        protocol_name
        for protocol_name, status in protocol_statuses.items()
        if status == OperationStatus.SUCCESS.value
    ]


def get_failed_protocols(result: NetworkOperationResult) -> List[str]:
    """
    Get a list of protocol names that failed to be queried.

    Args:
        result: The NetworkOperationResult containing protocol information

    Returns:
        List of protocol names that failed
    """
    protocol_statuses = result.metadata.get("protocol_statuses", {})
    return [
        protocol_name
        for protocol_name, status in protocol_statuses.items()
        if status == OperationStatus.FAILED.value
    ]


def get_unavailable_protocols(result: NetworkOperationResult) -> List[str]:
    """
    Get a list of protocol names that were not found/configured on the device.

    Args:
        result: The NetworkOperationResult containing protocol information

    Returns:
        List of protocol names that were not found
    """
    protocol_statuses = result.metadata.get("protocol_statuses", {})
    return [
        protocol_name
        for protocol_name, status in protocol_statuses.items()
        if status == OperationStatus.FEATURE_NOT_AVAILABLE.value
    ]
