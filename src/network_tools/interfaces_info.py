#!/usr/bin/env python3
"""
Interface functions module.
Provides functions for retrieving interface information from network devices using gNMI.
"""

import logging
from typing import Optional, Dict, Any
from src.gnmi.client import get_gnmi_data
from src.gnmi.parameters import GnmiRequest
from src.gnmi.responses import (
    ErrorResponse,
    SuccessResponse,
    NetworkOperationResult,
)
from src.inventory.models import Device
from src.parsers.interfaces.data_formatter import format_interface_data_for_llm
from src.parsers.interfaces.single_interface_parser import (
    parse_single_interface_data,
)

logger = logging.getLogger(__name__)


def get_interface_information(
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
            operation_type="interface_brief",
            status="failed",
            error_response=response,
        )

    data_to_format = []
    if isinstance(response, SuccessResponse):
        if response.data:
            data_to_format = response.data

    formatted_data = format_interface_data_for_llm(data_to_format)

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
        operation_type="interface_brief",
        status="success",
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
            operation_type="interface_details",
            status="failed",
            error_response=response,
        )

    data_for_parsing = {}
    if isinstance(response, SuccessResponse):
        if response.data:
            data_for_parsing = {"response": response.data}

    if not data_for_parsing:
        return NetworkOperationResult(
            device_name=device.name,
            operation_type="interface_details",
            status="failed",
            metadata={
                "interface": interface_name,
                "issue_type": "INTERFACE_NOT_FOUND",
                "message": f"Interface {interface_name} not found",
            },
        )

    parsed_result = parse_single_interface_data(data_for_parsing)
    interfaces = [parsed_result] if parsed_result else []

    if _is_empty_interface(parsed_result):
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
        operation_type="interface_details",
        status="success",
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
