#!/usr/bin/env python3
"""
Routing information module.
Provides functions for retrieving routing protocol information from network devices using gNMI.
"""

from typing import Optional, List, Union, Dict
from dataclasses import dataclass
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


@dataclass
class ProtocolCollectionResult:
    """Represents the result of collecting data from multiple protocols."""

    protocols: List[Dict]
    protocol_statuses: Dict[str, str]
    protocol_errors: Dict[str, Dict[str, str]]

    @property
    def successful_count(self) -> int:
        return len(
            [
                s
                for s in self.protocol_statuses.values()
                if s == OperationStatus.SUCCESS.value
            ]
        )

    @property
    def failed_count(self) -> int:
        return len(
            [
                s
                for s in self.protocol_statuses.values()
                if s == OperationStatus.FAILED.value
            ]
        )

    @property
    def feature_not_found_count(self) -> int:
        return len(
            [
                s
                for s in self.protocol_statuses.values()
                if s == OperationStatus.FEATURE_NOT_AVAILABLE.value
            ]
        )

    @property
    def total_count(self) -> int:
        return len(self.protocol_statuses)


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
        protocol: Optional protocol filter
        include_details: Whether to show detailed information

    Returns:
        NetworkOperationResult: Response object containing structured routing information
    """
    logger.debug(
        "Getting routing info from device %s - protocol: %s, include_details: %s",
        device.name,
        protocol,
        include_details,
    )

    protocols_to_query = _normalize_protocols(protocol)
    logger.debug(
        "Normalized protocols to query: %s",
        [p.value for p in protocols_to_query],
    )

    collection_result = _collect_protocol_data(
        device, protocols_to_query, include_details
    )
    logger.debug(
        "Protocol collection result - successful: %d, failed: %d, feature_not_found: %d",
        collection_result.successful_count,
        collection_result.failed_count,
        collection_result.feature_not_found_count,
    )

    overall_status = _determine_overall_status(collection_result)
    logger.debug("Overall routing operation status: %s", overall_status)

    # Warn about partial success conditions
    if overall_status == OperationStatus.PARTIAL_SUCCESS:
        logger.warning(
            "Partial routing protocol collection on %s: %d successful, %d failed, %d not found",
            device.name,
            collection_result.successful_count,
            collection_result.failed_count,
            collection_result.feature_not_found_count,
        )

    return NetworkOperationResult(
        device_name=device.name,
        ip_address=device.ip_address,
        nos=device.nos,
        operation_type="routing_info",
        status=overall_status,
        data={"routing_protocols": collection_result.protocols},
        metadata=_create_metadata(
            protocols_to_query, collection_result, include_details
        ),
    )


def isis_request() -> GnmiRequest:
    """Create a gNMI request for ISIS protocol data."""
    return GnmiRequest(
        path=[
            "openconfig-network-instance:network-instances/network-instance[name=*]/protocols/protocol/isis/interfaces/",
            "openconfig-network-instance:network-instances/network-instance[name=*]/protocols/protocol/isis/global/",
        ],
    )


def bgp_request() -> GnmiRequest:
    """Create a gNMI request for BGP protocol data."""
    return GnmiRequest(
        path=[
            "openconfig-network-instance:network-instances/network-instance[name=*]/protocols/protocol/bgp"
        ],
    )


def get_protocol_status(
    result: NetworkOperationResult, protocol_name: str
) -> Optional[str]:
    """Get the status of a specific protocol from a NetworkOperationResult."""
    return result.metadata.get("protocol_statuses", {}).get(protocol_name)


def get_protocol_error(
    result: NetworkOperationResult, protocol_name: str
) -> Optional[Dict[str, str]]:
    """Get the error information for a specific protocol from a NetworkOperationResult."""
    return result.metadata.get("protocol_errors", {}).get(protocol_name)


def get_successful_protocols(result: NetworkOperationResult) -> List[str]:
    """Get a list of protocol names that were successfully queried."""
    protocol_statuses = result.metadata.get("protocol_statuses", {})
    return [
        protocol_name
        for protocol_name, status in protocol_statuses.items()
        if status == OperationStatus.SUCCESS.value
    ]


def get_failed_protocols(result: NetworkOperationResult) -> List[str]:
    """Get a list of protocol names that failed to be queried."""
    protocol_statuses = result.metadata.get("protocol_statuses", {})
    return [
        protocol_name
        for protocol_name, status in protocol_statuses.items()
        if status == OperationStatus.FAILED.value
    ]


def get_unavailable_protocols(result: NetworkOperationResult) -> List[str]:
    """Get a list of protocol names that were not found/configured on the device."""
    protocol_statuses = result.metadata.get("protocol_statuses", {})
    return [
        protocol_name
        for protocol_name, status in protocol_statuses.items()
        if status == OperationStatus.FEATURE_NOT_AVAILABLE.value
    ]


def _normalize_protocols(
    protocol: Optional[
        Union[str, List[str], RoutingProtocol, List[RoutingProtocol]]
    ],
) -> List[RoutingProtocol]:
    """Normalize protocol parameter to a list of RoutingProtocol enums."""
    if protocol is None:
        return [RoutingProtocol.BGP, RoutingProtocol.ISIS]

    if isinstance(protocol, str):
        return _handle_string_protocol(protocol)

    if isinstance(protocol, RoutingProtocol):
        return [protocol]

    if isinstance(protocol, list):
        return _handle_list_protocol(protocol)

    logger.warning("Invalid protocol parameter type: %s", type(protocol))
    return []


def _collect_protocol_data(
    device: Device,
    protocols_to_query: List[RoutingProtocol],
    include_details: bool,
) -> ProtocolCollectionResult:
    """Collect data from multiple protocols and return aggregated results."""
    logger.debug("Collecting data for %d protocols", len(protocols_to_query))

    protocols = []
    protocol_statuses = {}
    protocol_errors = {}

    for protocol_enum in protocols_to_query:
        protocol_name = protocol_enum.value
        logger.debug("Processing protocol: %s", protocol_name)

        protocol_result = _get_protocol_data(
            device, protocol_enum, include_details
        )
        logger.debug(
            "Protocol %s result status: %s",
            protocol_name,
            protocol_result.status,
        )

        protocol_statuses[protocol_name] = protocol_result.status.value

        if protocol_result.status == OperationStatus.SUCCESS:
            protocols.append(
                _create_protocol_data_entry(protocol_name, protocol_result)
            )
        else:
            protocol_errors[protocol_name] = _create_protocol_error_entry(
                protocol_result
            )

    return ProtocolCollectionResult(
        protocols, protocol_statuses, protocol_errors
    )


def _get_protocol_data(
    device: Device, protocol: RoutingProtocol, include_details: bool
) -> NetworkOperationResult:
    """Get data for a specific protocol."""
    logger.debug("Getting %s data for device %s", protocol.value, device.name)

    if protocol == RoutingProtocol.BGP:
        return _get_bgp_info(device, include_details)
    elif protocol == RoutingProtocol.ISIS:
        return _get_isis_info(device, include_details)
    else:
        logger.warning("Unsupported protocol: %s", protocol.value)
        return _create_unsupported_protocol_result(device, protocol)


def _determine_overall_status(
    collection_result: ProtocolCollectionResult,
) -> OperationStatus:
    """Determine the overall operation status based on individual protocol results."""
    if collection_result.successful_count == collection_result.total_count:
        return OperationStatus.SUCCESS
    elif collection_result.successful_count > 0:
        return OperationStatus.PARTIAL_SUCCESS
    elif (
        collection_result.feature_not_found_count
        == collection_result.total_count
    ):
        return OperationStatus.FEATURE_NOT_AVAILABLE
    else:
        return OperationStatus.FAILED


def _create_metadata(
    protocols_to_query: List[RoutingProtocol],
    collection_result: ProtocolCollectionResult,
    include_details: bool,
) -> Dict:
    """Create metadata dictionary for the operation result."""
    protocol_str = ", ".join([p.value for p in protocols_to_query])

    metadata = {
        "protocol": protocol_str,
        "include_details": include_details,
        "successful_protocols": collection_result.successful_count,
        "failed_protocols": collection_result.failed_count,
        "feature_not_found_protocols": collection_result.feature_not_found_count,
        "total_protocols": collection_result.total_count,
        "protocol_statuses": collection_result.protocol_statuses,
    }

    if collection_result.protocol_errors:
        metadata["protocol_errors"] = collection_result.protocol_errors

    return metadata


def _create_protocol_data_entry(
    protocol_name: str, protocol_result: NetworkOperationResult
) -> Dict:
    """Create a protocol data entry for successful protocol queries."""
    return {
        "protocol": protocol_name,
        "detailed_data": protocol_result.data.get("detailed_data", {}),
        "summary": protocol_result.data.get("summary", {}),
    }


def _create_protocol_error_entry(
    protocol_result: NetworkOperationResult,
) -> Dict[str, str]:
    """Create a protocol error entry for failed protocol queries."""
    if protocol_result.status == OperationStatus.FEATURE_NOT_AVAILABLE:
        return {
            "type": "feature_not_found",
            "message": (
                protocol_result.feature_not_found_response.message
                if protocol_result.feature_not_found_response
                else ""
            ),
        }
    else:
        return {
            "type": "error",
            "message": (
                protocol_result.error_response.message
                if protocol_result.error_response
                and protocol_result.error_response.message
                else "Unknown error"
            ),
        }


def _handle_string_protocol(protocol: str) -> List[RoutingProtocol]:
    """Handle string protocol parameter."""
    if "," in protocol:
        protocols = _parse_protocol_string(protocol)
        return _normalize_protocols(protocols) if protocols else []
    else:
        try:
            return [RoutingProtocol(protocol)]
        except ValueError:
            logger.warning("Unknown protocol: %s", protocol)
            return []


def _handle_list_protocol(protocol: List) -> List[RoutingProtocol]:
    """Handle list protocol parameter."""
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


def _parse_protocol_string(protocol_str: str) -> Optional[List[str]]:
    """Parse a comma-separated protocol string into a list of protocol names."""
    protocols = [p.strip() for p in protocol_str.split(",") if p.strip()]
    return protocols if protocols else None


def _create_unsupported_protocol_result(
    device: Device, protocol: RoutingProtocol
) -> NetworkOperationResult:
    """Create an error result for unsupported protocols."""
    error_response = ErrorResponse(
        type="UNSUPPORTED_PROTOCOL",
        message=f"Protocol {protocol.value} is not supported",
    )
    return NetworkOperationResult(
        device_name=device.name,
        ip_address=device.ip_address,
        nos=device.nos,
        operation_type="routing_info",
        status=OperationStatus.FAILED,
        error_response=error_response,
    )


def _get_isis_info(
    device: Device, include_details: bool = False
) -> NetworkOperationResult:
    """Get ISIS routing information from a device."""
    logger.debug(
        "Getting ISIS info for device %s, include_details: %s",
        device.name,
        include_details,
    )

    response = get_gnmi_data(device, isis_request())
    logger.debug(
        "ISIS gNMI response type: %s, status: %s",
        type(response).__name__,
        getattr(response, "status", "N/A"),
    )

    if isinstance(response, FeatureNotFoundResponse):
        logger.debug("ISIS feature not found: %s", response.message)
        logger.debug("No ISIS configuration found on %s", device.name)
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="routing_info",
            status=OperationStatus.FEATURE_NOT_AVAILABLE,
            feature_not_found_response=response,
        )

    if isinstance(response, ErrorResponse):
        logger.debug(
            "ISIS ErrorResponse details - type: %s, message: %s",
            response.type,
            response.message,
        )
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
        raw_data = (
            response.data if isinstance(response, SuccessResponse) else []
        )
        logger.debug(
            "ISIS raw data length: %d", len(raw_data) if raw_data else 0
        )

        isis_data = process_isis_data(raw_data)
        logger.debug(
            "Processed ISIS data keys: %s",
            str(list(isis_data.keys()) if isis_data else []),
        )

        summary = generate_isis_summary(isis_data)
        logger.debug("Generated ISIS summary type: %s", type(summary).__name__)

        logger.info(
            "ISIS protocol data successfully processed for %s", device.name
        )

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
        logger.debug("Exception details: %s", str(e), exc_info=True)
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
    """Get BGP routing information from a device."""
    logger.debug(
        "Getting BGP info for device %s, include_details: %s",
        device.name,
        include_details,
    )

    response = get_gnmi_data(device, bgp_request())
    logger.debug(
        "BGP gNMI response type: %s, status: %s",
        type(response).__name__,
        getattr(response, "status", "N/A"),
    )

    if isinstance(response, FeatureNotFoundResponse):
        logger.debug("BGP feature not found: %s", response.message)
        logger.debug("No BGP configuration found on %s", device.name)
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="routing_info",
            status=OperationStatus.FEATURE_NOT_AVAILABLE,
            feature_not_found_response=response,
        )

    if isinstance(response, ErrorResponse):
        logger.debug(
            "BGP ErrorResponse details - type: %s, message: %s",
            response.type,
            response.message,
        )
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
        gnmi_data = (
            response.data
            if isinstance(response, SuccessResponse) and response.data
            else []
        )
        logger.debug(
            "BGP gNMI data length: %d", len(gnmi_data) if gnmi_data else 0
        )

        bgp_data = process_bgp_data(gnmi_data)
        logger.debug(
            "Processed BGP data keys: %s",
            str(list(bgp_data.keys()) if bgp_data else []),
        )

        summary = generate_bgp_summary(bgp_data)
        logger.debug("Generated BGP summary type: %s", type(summary).__name__)

        logger.info(
            "BGP protocol data successfully processed for %s", device.name
        )

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
        logger.debug("Exception details: %s", str(e), exc_info=True)
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
