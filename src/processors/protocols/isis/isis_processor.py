#!/usr/bin/env python3
"""
ISIS Processor module.

This module provides functions to process ISIS data received from gNMI queries
and format it in a way that's easier for small LLMs to understand.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def process_isis_data(response: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process ISIS data from gNMI response.

    Args:
        response: The gNMI response data (list of update dictionaries)

    Returns:
        Dict containing structured ISIS information formatted for LLM consumption
    """
    if not response:
        return {"error": "No ISIS data found in response"}

    isis_data = {
        "router_id": None,
        "net": None,
        "level_capability": None,
        "authentication_check": None,
        "segment_routing_enabled": None,
        "interfaces": [],
        "adjacencies": [],
    }

    # Process each update in the response
    for item in response:
        path = item.get("path", "")

        # Process ISIS global configuration
        if "global" in path:
            global_data = item.get("val", {})
            state = global_data.get("state", {})
            isis_data["net"] = state.get("net", [None])[0]
            isis_data["level_capability"] = state.get("level-capability")
            isis_data["authentication_check"] = state.get(
                "authentication-check"
            )

            # Get segment routing state
            segment_routing = global_data.get("segment-routing", {}).get(
                "state", {}
            )
            isis_data["segment_routing_enabled"] = segment_routing.get(
                "enabled"
            )

        # Process ISIS interfaces
        elif "interfaces" in path:
            interfaces = item.get("val", {}).get("interface", [])
            adjacencies = []

            for interface in interfaces:
                interface_info = _process_interface(interface)
                isis_data["interfaces"].append(interface_info)

                # Extract adjacencies from interface
                for level in interface.get("levels", {}).get("level", []):
                    level_adjacencies = _extract_adjacencies(
                        interface["interface-id"], level
                    )
                    if level_adjacencies:
                        adjacencies.extend(level_adjacencies)

            isis_data["adjacencies"] = adjacencies

    return isis_data


def _process_interface(interface: Dict[str, Any]) -> Dict[str, Any]:
    """Parse interface data from ISIS response."""
    state = interface.get("state", {})

    interface_info = {
        "name": state.get("interface-id"),
        "enabled": state.get("enabled", False),
        "passive": state.get("passive", False),
        "circuit_type": state.get("circuit-type"),
        "levels": [],
        "authentication_enabled": interface.get("authentication", {})
        .get("state", {})
        .get("enabled", False),
        "bfd_enabled": interface.get("enable-bfd", {})
        .get("state", {})
        .get("enabled", False),
    }

    # Parse levels
    for level in interface.get("levels", {}).get("level", []):
        level_info = _process_level(level)
        if level_info:
            interface_info["levels"].append(level_info)

    return interface_info


def _process_level(level: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Parse level data from interface."""
    state = level.get("state", {})
    if not state.get("enabled", False):
        return None

    level_info = {
        "level_number": state.get("level-number"),
        "enabled": state.get("enabled", False),
        "hello_authentication": level.get("hello-authentication", {})
        .get("state", {})
        .get("enabled", False),
    }

    return level_info


def _extract_adjacencies(
    interface_name: str, level: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Extract adjacencies from level data."""
    adjacencies = []

    for adj in level.get("adjacencies", {}).get("adjacency", []):
        adj_state = adj.get("state", {})

        if adj_state.get("adjacency-state") == "UP":
            adjacency_info = {
                "interface": interface_name,
                "system_id": adj_state.get("system-id"),
                "neighbor_ipv4": adj_state.get("neighbor-ipv4-address"),
                "neighbor_ipv6": adj_state.get("neighbor-ipv6-address"),
                "level": level.get("state", {}).get("level-number"),
                "adjacency_type": adj_state.get("adjacency-type"),
                "state": adj_state.get("adjacency-state"),
                "area_address": adj_state.get("area-address", []),
            }

            adjacencies.append(adjacency_info)

    return adjacencies


def generate_isis_summary(isis_data: Dict[str, Any]) -> str:
    """
    Generate a human-readable summary of ISIS status.

    Args:
        isis_data: Parsed ISIS data

    Returns:
        A human-readable summary of the ISIS status
    """
    if "error" in isis_data:
        return f"Error: {isis_data['error']}"

    lines = []

    # Add router information
    lines.append("ISIS Router Information:")
    if isis_data.get("net"):
        lines.append(f"  Network Entity Title (NET): {isis_data['net']}")
    if isis_data.get("level_capability"):
        lines.append(f"  Level Capability: {isis_data['level_capability']}")

    # Add segment routing information
    sr_status = (
        "Enabled" if isis_data.get("segment_routing_enabled") else "Disabled"
    )
    lines.append(f"  Segment Routing: {sr_status}")

    # Summarize interfaces
    lines.append("\nISIS Interfaces:")
    for interface in isis_data.get("interfaces", []):
        status = "Enabled" if interface.get("enabled") else "Disabled"
        passive = "Passive" if interface.get("passive") else "Active"
        lines.append(f"  {interface['name']}: {status}, {passive}")

        # Add level information
        for level in interface.get("levels", []):
            if level:
                level_num = level.get("level_number")
                lines.append(
                    f"    Level-{level_num}: {'Enabled' if level.get('enabled') else 'Disabled'}"
                )

    # Summarize adjacencies
    adjacencies = isis_data.get("adjacencies", [])
    if adjacencies:
        lines.append("\nISIS Adjacencies:")
        for adj in adjacencies:
            lines.append(
                f"  {adj['interface']} -> {adj['system_id']} ({adj['neighbor_ipv4']})"
            )
            lines.append(f"    Level: {adj['level']}, State: {adj['state']}")
    else:
        lines.append("\nNo ISIS adjacencies found.")

    return "\n".join(lines)
