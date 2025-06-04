#!/usr/bin/env python3
"""
Interface functions module.
Provides functions for retrieving interface information from network devices using XPath.
"""

import logging
from typing import Dict, Any, Optional
from src.gnmi.client import get_gnmi_data
from src.gnmi.parameters import GnmiRequest
from src.gnmi.responses import GnmiError
from src.inventory.models import Device
from src.network_tools.responses import InterfaceResponse
from src.parsers.interfaces.data_formatter import format_interface_data_for_llm
from src.parsers.interfaces.single_interface_parser import (
    parse_single_interface_data,
)

logger = logging.getLogger(__name__)


def get_interface_information(
    device: Device,
    interface: Optional[str] = None,
) -> InterfaceResponse:
    """
    Retrieve interface information from the device.

    Args:
        device: Target device dictionary with device information
        interface: Optional interface name to filter results

    Returns:
        InterfaceResponse object containing structured interface information
    """
    if interface:
        return _get_single_interface_info(device, interface)

    return _get_interface_brief(device)


def _get_interface_brief(
    device: Device,
) -> InterfaceResponse:
    """
    Get a summary of all interfaces (similar to 'show ip int brief').

    Args:
        device: Target device

    Returns:
        InterfaceResponse object containing structured summary information
    """
    interface_brief_request = GnmiRequest(
        xpath=["openconfig-interfaces:interfaces"],
    )
    response = get_gnmi_data(device, interface_brief_request)

    if response.is_error():
        logger.error(
            f"Error retrieving interface brief information: {response.error}"
        )
        return InterfaceResponse.error_response(response.error)

    formatted_data = format_interface_data_for_llm(response.to_dict())
    return InterfaceResponse.interface_brief(
        formatted_data, device_name=device.name
    )


def _get_single_interface_info(
    device: Device,
    interface_name: str,
) -> InterfaceResponse:
    """
    Get detailed information for a single interface using OpenConfig model.

    Args:
        device: Target device
        interface_name: Name of the interface to query

    Returns:
        InterfaceResponse object containing structured interface information
    """
    request = _create_single_interface_request(interface_name)
    response = get_gnmi_data(device, request)

    if response.is_error():
        logger.error(
            f"Error retrieving information for interface {interface_name}: {response.error}"
        )
        return InterfaceResponse.error_response(response.error)

    # If no data was returned but no error occurred, the interface likely doesn't exist
    if not response.data:
        error_msg = f"Interface {interface_name} not found"
        logger.error(error_msg)
        return InterfaceResponse.error_response(
            GnmiError(
                type="INTERFACE_NOT_FOUND",
                message=error_msg,
                details={"interface": interface_name, "status": "NOT_FOUND"},
            )
        )

    parsed_result = parse_single_interface_data(response.to_dict())
    interface_response = InterfaceResponse.single_interface(
        parsed_result, device_name=device.name
    )

    if _is_empty_interface(parsed_result):
        logger.info(
            f"Interface {interface_name} exists but appears to be empty/unconfigured"
        )
        if (
            interface_response.interfaces
            and len(interface_response.interfaces) > 0
        ):
            interface_response.interfaces[0]["status"] = "EMPTY"
            interface_response.interfaces[0][
                "notes"
            ] = "Interface exists but has no configuration"

    return interface_response


def _create_single_interface_request(interface_name: str) -> GnmiRequest:
    return GnmiRequest(
        xpath=[
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
