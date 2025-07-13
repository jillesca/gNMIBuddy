#!/usr/bin/env python3
"""
Interface functions module.
Provides functions for retrieving interface information from network devices using gNMI.
"""

import logging
from typing import Dict, Any, Optional
from src.gnmi.client import get_gnmi_data
from src.gnmi.parameters import GnmiRequest
from src.gnmi.responses import ErrorResponse
from src.inventory.models import Device
from src.parsers.interfaces.data_formatter import format_interface_data_for_llm
from src.parsers.interfaces.single_interface_parser import (
    parse_single_interface_data,
)

logger = logging.getLogger(__name__)


def get_interface_information(
    device: Device,
    interface: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieve interface information from the device.

    Args:
        device: Target device dictionary with device information
        interface: Optional interface name to filter results

    Returns:
        Dict[str, Any]: Dictionary containing interface information
    """
    if interface:
        return _get_single_interface_info(device, interface)

    return _get_interface_brief(device)


def _get_interface_brief(
    device: Device,
) -> Dict[str, Any]:
    """
    Get a summary of all interfaces (similar to 'show ip int brief').

    Args:
        device: Target device

    Returns:
        Dict[str, Any]: Dictionary containing structured summary information
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
        return {"device_name": device.name, "error": response.to_dict()}

    formatted_data = format_interface_data_for_llm(response.to_dict())
    return {
        "device_name": device.name,
        "interfaces": (
            formatted_data["interfaces"]
            if isinstance(formatted_data, dict)
            else formatted_data
        ),
        "summary": (
            formatted_data.get("summary", {})
            if isinstance(formatted_data, dict)
            else {}
        ),
        "is_single_interface": False,
    }


def _get_single_interface_info(
    device: Device,
    interface_name: str,
) -> Dict[str, Any]:
    """
    Get detailed information for a single interface using OpenConfig model.

    Args:
        device: Target device
        interface_name: Name of the interface to query

    Returns:
        Dict[str, Any]: Dictionary containing structured interface information
    """
    request = _create_single_interface_request(interface_name)
    response = get_gnmi_data(device, request)

    if isinstance(response, ErrorResponse):
        logger.error(
            "Error retrieving information for interface %s: %s",
            interface_name,
            response.message,
        )
        return {"device_name": device.name, "error": response.to_dict()}

    # Check if response has data attribute (SuccessResponse) or if it's empty
    response_dict = response.to_dict()
    if not response_dict:
        error_msg = f"Interface {interface_name} not found"
        logger.error(error_msg)
        error_response = ErrorResponse(
            type="INTERFACE_NOT_FOUND",
            message=error_msg,
            details={"interface": interface_name, "status": "NOT_FOUND"},
        )
        return {"device_name": device.name, "error": error_response.to_dict()}

    parsed_result = parse_single_interface_data(response_dict)
    interface_result = {
        "device_name": device.name,
        "interfaces": [parsed_result] if parsed_result else [],
        "is_single_interface": True,
    }

    if _is_empty_interface(parsed_result):
        logger.info(
            "Interface %s exists but appears to be empty/unconfigured",
            interface_name,
        )
        if (
            interface_result["interfaces"]
            and len(interface_result["interfaces"]) > 0
        ):
            interface_result["interfaces"][0]["status"] = "EMPTY"
            interface_result["interfaces"][0][
                "notes"
            ] = "Interface exists but has no configuration"

    return interface_result


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
