#!/usr/bin/env python3
"""
Single interface data parser module.
Provides functions for transforming raw gNMI interface data into a simplified format
optimized for smaller LLMs to understand network interface state.
Uses exclusively OpenConfig models.
"""

from typing import Dict, Any, List


def process_single_interface_data(
    gnmi_data: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Process raw gNMI data for a single interface into a simplified format better suited for LLM consumption.
    This function is specifically designed for smaller offline LLMs, focusing on the most important information.

    Args:
        gnmi_data: Raw gNMI response data containing interface information

    Returns:
        A dictionary with simplified interface information focused on key attributes
    """
    # Initialize the result structure
    result = {
        "interface": {
            "name": None,
            "admin_state": None,
            "oper_state": None,
            "description": None,
            "ip_address": None,
            "prefix_length": None,
            "vrf": None,
            "mtu": None,
            "mac_address": None,
            "speed": None,
            "duplex": None,
            "counters": {
                "in_packets": None,
                "out_packets": None,
                "in_errors": None,
                "out_errors": None,
            },
        },
        "timestamp": None,
    }  # Process the interface data from OpenConfig model
    extract_interface_data(gnmi_data, result)

    # Try to extract timestamp from gNMI data if available
    if gnmi_data:
        for item in gnmi_data:
            if isinstance(item, dict) and "timestamp" in item:
                result["timestamp"] = item["timestamp"]
                break

    return result


def extract_interface_data(
    gnmi_data: List[Dict[str, Any]], result: Dict[str, Any]
) -> None:
    """
    Extract interface data from the gNMI response using OpenConfig model.

    Args:
        gnmi_data: List of gNMI response updates containing interface information
        result: Result dictionary to update
    """
    if not gnmi_data:
        return

    # Handle the case where we have a complete interfaces structure
    for item in gnmi_data:
        if "val" not in item:
            continue

        val = item.get("val", {})

        # Extract interface data from interfaces/interface structure
        if "interface" in val:
            interfaces = val.get("interface", [])
            if interfaces and len(interfaces) > 0:
                # Process the first (and likely only) interface
                extract_single_interface(interfaces[0], result)
                return

        # Extract interface data from direct interface structure (when querying a specific interface)
        extract_single_interface(val, result)


def extract_single_interface(
    interface: Dict[str, Any], result: Dict[str, Any]
) -> None:
    """
    Extract data from a single interface object.

    Args:
        interface: Interface object from OpenConfig model
        result: Result dictionary to update
    """
    # Extract basic interface information
    if "name" in interface:
        result["interface"]["name"] = interface["name"]

    # Extract state information
    if "state" in interface:
        state = interface["state"]

        # Extract basic state fields
        if "admin-status" in state:
            result["interface"]["admin_state"] = state["admin-status"]
        if "oper-status" in state:
            result["interface"]["oper_state"] = state["oper-status"]
        if "description" in state:
            result["interface"]["description"] = state["description"]
        if "mtu" in state:
            result["interface"]["mtu"] = state["mtu"]

        # Extract counters if available
        if "counters" in state:
            counters = state["counters"]
            result["interface"]["counters"]["in_packets"] = counters.get(
                "in-pkts"
            )
            result["interface"]["counters"]["out_packets"] = counters.get(
                "out-pkts"
            )
            result["interface"]["counters"]["in_errors"] = counters.get(
                "in-errors"
            )
            result["interface"]["counters"]["out_errors"] = counters.get(
                "out-errors"
            )

    # Extract Ethernet-specific information
    if (
        "openconfig-if-ethernet:ethernet" in interface
        and "state" in interface["openconfig-if-ethernet:ethernet"]
    ):
        eth_state = interface["openconfig-if-ethernet:ethernet"]["state"]
        result["interface"]["mac_address"] = eth_state.get("mac-address")
        result["interface"]["speed"] = eth_state.get("port-speed")
        result["interface"]["duplex"] = eth_state.get("duplex-mode")

    # Extract IP address and VRF information from subinterfaces
    if (
        "subinterfaces" in interface
        and "subinterface" in interface["subinterfaces"]
    ):
        subinterfaces = interface["subinterfaces"]["subinterface"]
        for subif in subinterfaces:
            # We're mainly interested in the main subinterface (index 0)
            if subif.get("index") == 0:
                extract_ip_and_vrf(subif, result)
                break


def extract_ip_and_vrf(
    subinterface: Dict[str, Any], result: Dict[str, Any]
) -> None:
    """
    Extract IP address and VRF information from a subinterface.

    Args:
        subinterface: Subinterface object from OpenConfig model
        result: Result dictionary to update
    """
    # Extract IPv4 address
    if "openconfig-if-ip:ipv4" in subinterface:
        ipv4 = subinterface["openconfig-if-ip:ipv4"]

        if "addresses" in ipv4 and "address" in ipv4["addresses"]:
            addresses = ipv4["addresses"]["address"]
            if addresses and len(addresses) > 0:
                # Get the first address (primary)
                address = addresses[0]
                result["interface"]["ip_address"] = address.get("ip")

                # Get prefix length from the state if available
                if "state" in address and "prefix-length" in address["state"]:
                    result["interface"]["prefix_length"] = address["state"][
                        "prefix-length"
                    ]

    # Extract VRF information if available
    # In OpenConfig, VRF is often found in a dedicated container
    if "openconfig-network-instance:network-instance" in subinterface:
        instances = subinterface[
            "openconfig-network-instance:network-instance"
        ]
        if instances and len(instances) > 0:
            result["interface"]["vrf"] = instances[0].get("name")
