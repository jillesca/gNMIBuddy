#!/usr/bin/env python3
"""
Interface functions module.
Provides functions for retrieving interface information from network devices using gNMI.
"""

from typing import Optional, Dict, Any
from src.schemas.responses import (
    ErrorResponse,
    SuccessResponse,
    OperationStatus,
    NetworkOperationResult,
)
from src.schemas.models import Device
from src.gnmi.client import get_gnmi_data
from src.gnmi.parameters import GnmiRequest
from src.processors.interfaces.data_processor import (
    format_interface_data_for_llm,
)
from src.processors.interfaces.single_interface_processor import (
    process_single_interface_data,
)
from src.logging.config import get_logger, log_operation

logger = get_logger(__name__)


@log_operation("get_interfaces")
def get_interfaces(
    device: Device,
    interface: Optional[str] = None,
) -> NetworkOperationResult:
    """
    Retrieve interface information from the device.

    Args:
        device: Target device dictionary with device information
        interface: Optional interface name to filter results

    Returns:
        NetworkOperationResult: Response object containing interface information
    """
    logger.debug(
        "Getting interface information",
        extra={"device_name": device.name, "interface": interface},
    )

    if interface:
        return _get_single_interface_info(device, interface)

    return _get_interface_brief(device)


def _get_interface_brief(
    device: Device,
) -> NetworkOperationResult:
    """
    Get a summary of all interfaces (similar to 'show ip int brief').

    Args:
        device: Target device

    Returns:
        NetworkOperationResult: Response object containing structured summary information
    """
    interface_brief_request = GnmiRequest(
        path=["openconfig-interfaces:interfaces"],
    )
    response = get_gnmi_data(device, interface_brief_request)

    if isinstance(response, ErrorResponse):
        logger.error(
            "Error retrieving interface brief information: %s",
            response.message,
        )
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="interface_brief",
            status=OperationStatus.FAILED,
            error_response=response,
        )

    gnmi_data = []
    if isinstance(response, SuccessResponse):
        if response.data:
            gnmi_data = response.data

    formatted_data = format_interface_data_for_llm(gnmi_data)

    interfaces = (
        formatted_data["interfaces"]
        if isinstance(formatted_data, dict)
        else formatted_data
    )
    summary = (
        formatted_data.get("summary", {})
        if isinstance(formatted_data, dict)
        else {}
    )

    result_data = {
        "interfaces": interfaces,
        "summary": summary,
        "interface_count": (
            len(interfaces) if isinstance(interfaces, list) else 0
        ),
    }

    metadata = {
        "is_single_interface": False,
        "operation_details": "Retrieved summary of all interfaces",
    }

    return NetworkOperationResult(
        device_name=device.name,
        ip_address=device.ip_address,
        nos=device.nos,
        operation_type="interface_brief",
        status=OperationStatus.SUCCESS,
        data=result_data,
        metadata=metadata,
    )


def _get_single_interface_info(
    device: Device,
    interface_name: str,
) -> NetworkOperationResult:
    """
    Get detailed information for a single interface using OpenConfig model.

    Args:
        device: Target device
        interface_name: Name of the interface to query

    Returns:
        NetworkOperationResult: Response object containing structured interface information
    """
    request = _create_single_interface_request(interface_name)
    response = get_gnmi_data(device, request)

    if isinstance(response, ErrorResponse):
        logger.error(
            "Error retrieving information for interface %s: %s",
            interface_name,
            response.message,
        )
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="interface_details",
            status=OperationStatus.FAILED,
            error_response=response,
        )

    gnmi_data = []
    if isinstance(response, SuccessResponse):
        if response.data:
            gnmi_data = response.data

    if not gnmi_data:
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="interface_details",
            status=OperationStatus.FAILED,
            metadata={
                "interface": interface_name,
                "issue_type": "INTERFACE_NOT_FOUND",
                "message": f"Interface {interface_name} not found",
            },
        )

    processed_result = process_single_interface_data(gnmi_data)
    interfaces = [processed_result] if processed_result else []

    if _is_empty_interface(processed_result):
        logger.info(
            "Interface %s exists but appears to be empty/unconfigured",
            interface_name,
        )
        if interfaces and len(interfaces) > 0:
            interfaces[0]["status"] = "EMPTY"
            interfaces[0][
                "notes"
            ] = "Interface exists but has no configuration"

    result_data = {
        "interfaces": interfaces,
        "interface_count": len(interfaces),
        "interface_name": interface_name,
    }

    metadata = {
        "is_single_interface": True,
        "operation_details": f"Retrieved details for interface {interface_name}",
    }

    return NetworkOperationResult(
        device_name=device.name,
        ip_address=device.ip_address,
        nos=device.nos,
        operation_type="interface_details",
        status=OperationStatus.SUCCESS,
        data=result_data,
        metadata=metadata,
    )


def _create_single_interface_request(interface_name: str) -> GnmiRequest:
    return GnmiRequest(
        path=[
            f"openconfig-interfaces:interfaces/interface[name={interface_name}]"
        ],
    )


def _is_empty_interface(parsed_interface: Dict[str, Any]) -> bool:
    """
    Determine if an interface exists but has no significant configuration.

    An interface is considered empty/unconfigured if:
    1. It has no IP address
    2. It has no description
    3. It has no VRF assignment

    Args:
        parsed_interface: Parsed interface information

    Returns:
        True if the interface exists but has minimal/no configuration
    """
    interface = parsed_interface.get("interface", {})

    has_ip = interface.get("ip_address") is not None
    has_description = interface.get("description") not in (None, "")
    has_vrf = interface.get("vrf") is not None

    # If the interface has any of these configurations, it's not empty
    if has_ip or has_description or has_vrf:
        return False

    # If we're here, the interface exists but has no significant configuration
    return True
