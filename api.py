#!/usr/bin/env python3
"""
API module for gNMIBuddy - Contains the core network tool functions
that can be used by both MCP and CLI interfaces.
"""
from typing import Dict, Any, Optional

from src.services.commands import run
from src.inventory import list_available_devices
from src.network_tools.vpn_info import get_vpn_information
from src.network_tools.mpls_info import get_mpls_information
from src.network_tools.routing_info import get_routing_information
from src.network_tools.interfaces_info import get_interface_information
from src.network_tools.logging import get_logging_information
from src.network_tools.system_info import get_system_information
from src.network_tools.deviceprofile import get_device_profile
from src.network_tools.topology.path import path
from src.network_tools.topology.segment import segment
from src.network_tools.topology.neighbors import neighbors
from src.network_tools.topology.ip_adjacency_dump import ip_adjacency_dump


def get_device_profile_api(device_name: str) -> Dict[str, Any]:
    """
    Retrieve a comprehensive device profile summarizing the core service provider role and key protocol features for a network device.

    This function queries the device using gNMI and analyzes its configuration to determine:
      - If MPLS is enabled (is_mpls_enabled)
      - If ISIS is enabled (is_isis_enabled)
      - If BGP L3VPN is enabled (is_bgp_l3vpn_enabled)
      - If the device is acting as a BGP Route Reflector (is_route_reflector)
      - If any non-default VPN/VRF has BGP IPv4 Unicast enabled (has_vpn_ipv4_unicast_bgp)
      - The overall device role (role): PE, P, RR, CE, or IGP-only

    The resulting profile is essential for automation, troubleshooting, and intent-based operations in service provider networks. It allows higher-level systems (including LLMs) to:
      - Dynamically adjust what data to query (e.g., only look for VPNs on PE routers, ignore VPNs on P routers, avoid interface queries in VPNs on RRs, etc.)
      - Make topology-aware decisions and recommendations
      - Filter or target operational commands based on device function
      - Provide context-aware diagnostics and explanations

    Example output for a PE device:
        {
            "is_mpls_enabled": true,
            "is_isis_enabled": true,
            "is_bgp_l3vpn_enabled": true,
            "is_route_reflector": false,
            "has_vpn_ipv4_unicast_bgp": true,
            "role": "PE"
        }

    :param device: Device object from inventory
    :return: SystemInfoResponse containing the device profile and role
    """
    return run(device_name, get_device_profile)


def get_system_info(
    device_name: str,
) -> Dict[str, Any]:
    """
    Retrieve structured system-level information from a network device via gNMI.

    Returns key attributes such as hostname, software version, timezone, memory, gRPC server config, logging, users, boot time, and uptime. Useful for inventory, monitoring, and diagnostics.

    Args:
        device_name: Name of the device in the inventory

    Returns:
        Dictionary with system information fields
    """
    return run(device_name, get_system_information)


def get_routing_info(
    device_name: str,
    protocol: Optional[str] = None,
    include_details: bool = False,
) -> Dict[str, Any]:
    """
    Get routing information from a network device.

    Args:
        device_name: Name of the device in the inventory
        protocol: Optional protocol filter (bgp, isis)
        include_details: Whether to show detailed information (default: False, returns summary only)

    Returns:
        Structured routing information
    """
    return run(device_name, get_routing_information, protocol, include_details)


def get_logs(
    device_name: str,
    keywords: Optional[str] = None,
    minutes: Optional[int] = 5,
    show_all_logs: bool = False,
) -> Dict[str, Any]:
    """
    Get logs from a network device.

    Args:
        device_name: Name of the device in the inventory
        keywords: Optional keywords to filter logs
        minutes: Number of minutes to filter logs (default: 5 minutes)
        show_all_logs: If True, return all logs without time filtering (default: False)

    Returns:
        Structured log information
    """
    return run(
        device_name,
        get_logging_information,
        keywords,
        minutes,
        show_all_logs,
    )


def get_interface_info(
    device_name: str,
    interface: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get interface information from a network device.

    Args:
        device_name: Name of the device in the inventory
        interface: Optional interface name (e.g., GigabitEthernet0/0/0)
                  When not specified, returns state of all interfaces on the device.
                  When specified, returns detailed configuration and state of only that interface.

    Returns:
        Structured interface information containing operational state and configuration details
    """
    return run(device_name, get_interface_information, interface)


def get_mpls_info(
    device_name: str,
    include_details: bool = False,
) -> Dict[str, Any]:
    """
    Get MPLS information from a network device.

    Args:
        device_name: Name of the device in the inventory
        include_details: Whether to show detailed information (default: False, returns summary only)

    Returns:
        Structured MPLS information
    """
    return run(device_name, get_mpls_information, include_details)


def get_vpn_info(
    device_name: str,
    vrf: Optional[str] = None,
    include_details: bool = False,
) -> Dict[str, Any]:
    """
    Get VPN/VRF information from a network device.

    Args:
        device_name: Name of the device in the inventory
        vrf: Optional specific VRF name
        include_details: Whether to show detailed information (default: False, returns summary only)

    Returns:
        Structured VPN information
    """
    return run(device_name, get_vpn_information, vrf, include_details)


def get_devices() -> Dict[str, Any]:
    """
    Get information about all available devices in the inventory.

    Returns:
        A dictionary containing a list of all devices with their name, IP address, and network OS
    """
    return list_available_devices()


def get_topology_neighbors(
    device_name: str,
) -> Dict[str, Any]:
    """
    Get direct neighbors of a specified device.

    Args:
        device_name: Name of the device in the inventory

    Returns:
        Dictionary with the device name and a list of its direct neighbors.
        Example:
        {
            "device": "PE1",
            "neighbors": [
                {"neighbor": "P1", "attributes": {...}},
                ...
            ]
        }
    """

    return run(device_name, neighbors)


def get_topology_path(
    device_name: str,
    target: str,
) -> Dict[str, Any]:
    """
    Compute the shortest path between two devices.

    Args:
        device_name: Name of the source device in the inventory
        target: Name of the target device

    Returns:
        Dictionary with the device name and the path (nodes and edges) between the devices.
        Example:
        {
            "device": "PE1",
            "path": {
                "nodes": ["PE1", "P1", "PE2"],
                "edges": [
                    {"source": "PE1", "target": "P1", "attributes": {...}},
                    {"source": "P1", "target": "PE2", "attributes": {...}}
                ]
            }
        }
    """

    return run(device_name, path, target)


def get_topology_segment(
    device_name: str,
    network: str,
) -> Dict[str, Any]:
    """
    List devices on the specified L3 segment.

    Args:
        device_name: Name of the device in the inventory (used for context)
        network: The L3 network segment (e.g., "10.0.0.0/30")

    Returns:
        Dictionary with the device name and the list of devices on the specified segment.
        Example:
        {
            "device": "PE1",
            "segment": {
                "network": "10.0.0.0/30",
                "devices": ["PE1", "P1"]
            }
        }
    """

    return run(device_name, segment, network)


def get_topology_ip_adjacency_dump(device_name: str) -> Dict[str, Any]:
    """
    Retrieve the full L3 IP-only direct connection list for all devices in the network (excluding management interfaces).

    This function returns a detailed list of all discovered L3 IP direct connections (edges) in the network topology graph. Each connection describes a direct L3 IP connectivity between two devices, including interface names, IP addresses, and the shared network segment. The output is suitable for LLMs and automation tools to reason about network structure, connectivity, and path computation.

    Output Structure:
        {
            "device": <queried device name>,
            "direct_connections": [
                {
                    "source": <device name>,
                    "target": <device name>,
                    "attributes": {
                        "network": <L3 network in CIDR>,
                        "local_interface": <interface name on source>,
                        "remote_interface": <interface name on target>,
                        "local_ip": <IP address on source>,
                        "remote_ip": <IP address on target>
                    }
                },
                ...
            ]
        }
    Notes:
    - Management interfaces (e.g., MgmtEth0/RP0/CPU0/0) are excluded from direct connections.
    - Self-loops (connections where source == target) may be present for loopbacks or virtual interfaces.


    Args:
        device_name: Name of the device in the inventory (used for context)

    Returns:
        Dictionary with the device name and a list of all IP direct connections in the topology graph.
    """

    return run(device_name, ip_adjacency_dump)
