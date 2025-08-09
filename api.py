#!/usr/bin/env python3
"""
API module for gNMIBuddy - Contains the core network tool functions
that can be used by both MCP and CLI interfaces.
"""
from typing import Optional, Union

from src.schemas.models import DeviceListResult
from src.schemas.responses import NetworkOperationResult
from src.services.commands import run
from src.inventory import list_available_devices_safe
from src.collectors.logs import get_logs as collect_logs
from src.collectors.vpn import get_vpn_info as collect_vpn_info
from src.collectors.mpls import get_mpls_info as collect_mpls_info
from src.collectors.routing import get_routing_info as collect_routing_info
from src.collectors.system import get_system_info as collect_system_info
from src.collectors.interfaces import get_interfaces as collect_interfaces
from src.collectors.profile import get_device_profile as collect_device_profile
from src.collectors.topology.neighbors import neighbors
from src.collectors.topology.network_topology import get_network_topology


def get_device_profile_api(device_name: str) -> NetworkOperationResult:
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

    :param device_name: Name of the device in inventory
    :return: Dictionary containing the device profile and role information
    """
    return run(device_name, collect_device_profile)


def get_system_info(
    device_name: str,
) -> NetworkOperationResult:
    """
    Retrieve structured system-level information from a network device via gNMI.

    Returns key attributes such as hostname, software version, timezone, memory, gRPC server config, logging, users, boot time, and uptime. Useful for inventory, monitoring, and diagnostics.

    Args:
        device_name: Name of the device in the inventory

    Returns:
        Dictionary with system information fields
    """
    return run(device_name, collect_system_info)


def get_routing_info(
    device_name: str,
    protocol: Optional[str] = None,
    include_details: bool = False,
) -> NetworkOperationResult:
    """
    Get routing information from a network device.

    Args:
        device_name: Name of the device in the inventory
        protocol: Optional protocol filter. Supported values: 'bgp', 'isis'
                 Can be a single protocol or comma-separated list (e.g., 'bgp,isis')
        include_details: Whether to show detailed information (default: False, returns summary only)

    Returns:
        Structured routing information
    """
    return run(device_name, collect_routing_info, protocol, include_details)


def get_logs(
    device_name: str,
    keywords: Optional[str] = None,
    minutes: Optional[Union[str, int]] = 5,
    show_all_logs: bool = False,
) -> NetworkOperationResult:
    """
    Get logs from a network device.

    Args:
        device_name: Name of the device in the inventory
        keywords: Optional keywords to filter logs
        minutes: Number of minutes to filter logs (default: 5 minutes). Can be provided as string or integer.
        show_all_logs: If True, return all logs without time filtering (default: False)

    Returns:
        Structured log information
    """
    return run(
        device_name,
        collect_logs,
        keywords,
        minutes,
        show_all_logs,
    )


def get_interface_info(
    device_name: str,
    interface: Optional[str] = None,
) -> NetworkOperationResult:
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
    return run(device_name, collect_interfaces, interface)


def get_mpls_info(
    device_name: str,
    include_details: bool = False,
) -> NetworkOperationResult:
    """
    Get MPLS information from a network device.

    Args:
        device_name: Name of the device in the inventory
        include_details: Whether to show detailed information (default: False, returns summary only)

    Returns:
        Structured MPLS information
    """
    return run(device_name, collect_mpls_info, include_details)


def get_vpn_info(
    device_name: str,
    vrf_name: Optional[str] = None,
    include_details: bool = False,
) -> NetworkOperationResult:
    """
    Get VPN/VRF information from a network device.

    Args:
        device_name: Name of the device in the inventory
        vrf_name: Optional specific VRF name
        include_details: Whether to show detailed information (default: False, returns summary only)

    Returns:
        Structured VPN information
    """
    return run(device_name, collect_vpn_info, vrf_name, include_details)


def get_devices() -> DeviceListResult:
    """
    Get information about all available devices in the inventory.

    Returns:
        A dictionary containing a list of all devices with their name, IP address, and network OS
        (sensitive authentication data is redacted for security)
    """
    return list_available_devices_safe()


def get_topology_neighbors(
    device_name: str,
) -> NetworkOperationResult:
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


def get_network_topology_api() -> NetworkOperationResult:
    """
    Retrieve the full L3 IP-only direct connection list for all devices in the network inventory (excluding management interfaces).

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

    return run(None, get_network_topology)
