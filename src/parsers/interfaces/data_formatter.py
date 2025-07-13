#!/usr/bin/env python3
"""
Interface data parser module.
Provides functions for transforming raw gNMI interface data from OpenConfig models into LLM-friendly formats.
"""

from typing import Dict, Any, List, Optional


def format_interface_data_for_llm(
    raw_interface_data: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Process raw gNMI interface data from OpenConfig model into a simplified format better suited for LLM consumption.
    This function transforms a complete OpenConfig interfaces structure into an interface brief output.

    Args:
        raw_interface_data: Raw interface data from gNMI query using OpenConfig model

    Returns:
        A dictionary with simplified interface information and summary statistics
    """
    # Initialize result structure
    result = {
        "interfaces": [],
        "summary": {
            "total_interfaces": 0,
            "admin_up": 0,
            "admin_down": 0,
            "oper_up": 0,
            "oper_down": 0,
            "with_ip": 0,
            "with_vrf": 0,
        },
        "timestamp": "",
    }

    if not raw_interface_data:
        return result

    # Extract interfaces from the raw data
    interfaces = []
    for update in raw_interface_data:
        if "val" in update:
            # Wrap in the expected format for extract_interfaces
            wrapped_data = {"response": [{"val": update["val"]}]}
            extracted = extract_interfaces(wrapped_data)
            interfaces.extend(extracted)

    # Calculate summary statistics
    result["interfaces"] = interfaces
    result["summary"] = calculate_interface_statistics(interfaces)

    return result


def extract_interfaces(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract interface information from the OpenConfig interfaces model.

    Args:
        raw_data: Raw interface data from gNMI query

    Returns:
        List of interface dictionaries with key information
    """
    interfaces = []

    if "response" not in raw_data:
        return interfaces

    for item in raw_data["response"]:
        if "val" not in item:
            continue

        val = item.get("val", {})

        # Extract interfaces from the interfaces container
        if "interface" in val:
            for interface in val["interface"]:
                interface_info = extract_interface_info(interface)
                if interface_info:
                    interfaces.append(interface_info)

    return interfaces


def extract_interface_info(
    interface: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Extract key information from a single interface in the OpenConfig model.

    Args:
        interface: Interface object from OpenConfig model

    Returns:
        Dictionary with interface information, or None if invalid
    """
    # Skip if no interface name
    if "name" not in interface:
        return None

    # Create base interface info
    interface_info = {
        "name": interface["name"],
    }

    # Extract state information
    if "state" in interface:
        state = interface["state"]

        # Extract admin and operational status
        if "admin-status" in state:
            interface_info["admin_status"] = state["admin-status"]
        if "oper-status" in state:
            interface_info["oper_status"] = state["oper-status"]

    # Extract IP address and VRF from subinterfaces
    if (
        "subinterfaces" in interface
        and "subinterface" in interface["subinterfaces"]
    ):
        subinterfaces = interface["subinterfaces"]["subinterface"]
        for subif in subinterfaces:
            # We're primarily interested in the main subinterface (index 0)
            if subif.get("index") == 0:
                extract_ip_and_vrf_for_brief(subif, interface_info)
                break

    return interface_info


def extract_ip_and_vrf_for_brief(
    subinterface: Dict[str, Any], interface_info: Dict[str, Any]
) -> None:
    """
    Extract IP address and VRF information from a subinterface for the interface brief output.

    Args:
        subinterface: Subinterface object from OpenConfig model
        interface_info: Interface info dictionary to update
    """
    # Extract IPv4 address
    if "openconfig-if-ip:ipv4" in subinterface:
        ipv4 = subinterface["openconfig-if-ip:ipv4"]

        if "addresses" in ipv4 and "address" in ipv4["addresses"]:
            addresses = ipv4["addresses"]["address"]
            if addresses and len(addresses) > 0:
                # Get the first address (primary)
                address = addresses[0]
                ip = address.get("ip")

                # Get prefix length from the state if available
                prefix_length = None
                if "state" in address and "prefix-length" in address["state"]:
                    prefix_length = address["state"]["prefix-length"]

                # Format IP with subnet mask for brief display
                if ip and prefix_length is not None:
                    subnet_mask = prefix_to_subnet_mask(prefix_length)
                    interface_info["ip_address"] = f"{ip}/{subnet_mask}"

    # Extract VRF information if available
    # In OpenConfig, VRF might be in different paths depending on the implementation
    if "openconfig-network-instance:network-instance" in subinterface:
        instances = subinterface[
            "openconfig-network-instance:network-instance"
        ]
        if instances and len(instances) > 0:
            interface_info["vrf"] = instances[0].get("name")

    # Check for alternative VRF location in OpenConfig (varies by vendor implementation)
    if "vrf-instance" in subinterface:
        interface_info["vrf"] = subinterface["vrf-instance"]


def prefix_to_subnet_mask(prefix_length: int) -> str:
    """
    Convert a prefix length to a subnet mask in dotted decimal format.

    Args:
        prefix_length: CIDR prefix length (e.g., 24)

    Returns:
        Subnet mask in dotted decimal format (e.g., 255.255.255.0)
    """
    # Create a 32-bit mask with prefix_length 1's followed by (32-prefix_length) 0's
    mask = ((1 << 32) - 1) ^ ((1 << (32 - prefix_length)) - 1)

    # Convert to dotted decimal format
    return ".".join([str((mask >> i) & 0xFF) for i in [24, 16, 8, 0]])


def calculate_interface_statistics(
    interfaces: List[Dict[str, Any]],
) -> Dict[str, int]:
    """
    Calculate summary statistics for interface information.

    Args:
        interfaces: List of interface dictionaries

    Returns:
        Dictionary of summary statistics
    """
    total_interfaces = len(interfaces)

    # Count interfaces with various statuses
    admin_up = sum(
        1 for intf in interfaces if intf.get("admin_status") == "UP"
    )
    oper_up = sum(1 for intf in interfaces if intf.get("oper_status") == "UP")
    with_ip = sum(1 for intf in interfaces if "ip_address" in intf)
    with_vrf = sum(1 for intf in interfaces if "vrf" in intf)

    return {
        "total_interfaces": total_interfaces,
        "admin_up": admin_up,
        "admin_down": total_interfaces - admin_up,
        "oper_up": oper_up,
        "oper_down": total_interfaces - oper_up,
        "with_ip": with_ip,
        "with_vrf": with_vrf,
    }
