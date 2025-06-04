#!/usr/bin/env python3
"""
BGP Parser Module

This module parses BGP configuration and state data from network devices and formats it in a way
that is easier for smaller LLMs to understand. It supports the OpenConfig YANG model.
"""

from typing import Dict, Any, List
import re
import time


def parse_bgp_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse BGP configuration and state data from GNMI responses.

    Args:
        data: GNMI response containing BGP configuration and state data in OpenConfig format

    Returns:
        Dict containing BGP configuration and state information optimized for small LLMs
    """
    try:
        # Check for valid response data
        if "response" in data and data["response"]:
            return _parse_openconfig_bgp(data)
        return {"parse_error": "Unsupported BGP data format"}
    except Exception as e:
        return {"parse_error": str(e)}


def _parse_openconfig_bgp(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse BGP configuration and state data from OpenConfig YANG model.

    Args:
        data: GNMI response containing BGP configuration and state data

    Returns:
        Dict containing BGP configuration and state information
    """
    try:
        # Find the DEFAULT network instance BGP data
        default_bgp = None
        vrf_bgp_data = []

        for response in data["response"]:
            path = response.get("path", "")
            if (
                "network-instance[name=DEFAULT]" in path
                and "protocol[identifier=BGP]" in path
            ):
                default_bgp = response.get("val", {})
            elif (
                "network-instance" in path
                and "protocol[identifier=BGP]" in path
            ):
                # This is a VRF BGP instance
                vrf_bgp_data.append(response)

        if not default_bgp:
            return {
                "parse_error": "No DEFAULT BGP instance found in OpenConfig data"
            }

        # Get timestamp from the data if available
        timestamp = data.get("timestamp", int(time.time() * 1e9))

        # Extract only LLM-friendly information
        return _extract_llm_friendly_bgp_data(
            default_bgp, vrf_bgp_data, timestamp
        )
    except (KeyError, IndexError) as e:
        return {"parse_error": f"Error parsing OpenConfig BGP data: {str(e)}"}


def generate_bgp_summary(bgp_config: Dict[str, Any]) -> str:
    """
    Generate a human-readable summary of the BGP configuration and state.

    Args:
        bgp_config: The BGP configuration and state data

    Returns:
        A string containing a summary of the BGP configuration and state
    """
    if "parse_error" in bgp_config:
        return f"Error parsing BGP configuration: {bgp_config['parse_error']}"

    summary_lines = []

    # Add timestamp information if available
    if "data_timestamp_str" in bgp_config:
        summary_lines.append(
            f"Data collected at: {bgp_config['data_timestamp_str']}"
        )

    # Basic router information
    router = bgp_config.get("router", {})
    summary_lines.append(f"AS Number: {router.get('as_number', 'N/A')}")
    summary_lines.append(f"Router ID: {router.get('router_id', 'N/A')}")
    summary_lines.append(
        f"Total Prefixes: {router.get('total_prefixes', 'N/A')}"
    )

    # Address families
    if "address_families" in bgp_config and bgp_config["address_families"]:
        af_names = [af["name"] for af in bgp_config["address_families"]]
        summary_lines.append(f"Address Families: {', '.join(af_names)}")

    # Neighbor groups
    if "neighbor_groups" in bgp_config and bgp_config["neighbor_groups"]:
        summary_lines.append("Neighbor Groups:")
        for group in bgp_config["neighbor_groups"]:
            summary_lines.append(
                f"  * {group['name']} (Remote AS: {group.get('remote_as', 'N/A')})"
            )
            if "address_families" in group and group["address_families"]:
                for af in group["address_families"]:
                    af_line = f"    - {af['name']}"
                    if af.get("is_rr_client"):
                        af_line += " RR Client"
                    summary_lines.append(af_line)

    # Neighbors
    if "neighbors" in bgp_config and bgp_config["neighbors"]:
        summary_lines.append("Neighbors:")
        for neighbor in bgp_config["neighbors"]:
            summary_lines.append(
                f"  * {neighbor['address']} (AS: {neighbor.get('remote_as', 'N/A')}, "
                f"Group: {neighbor.get('group', 'N/A')}, "
                f"State: {neighbor.get('state', 'UNKNOWN')})"
            )

            # Add uptime info if established
            if neighbor.get("state") == "ESTABLISHED":
                summary_lines.append(
                    f"    - Up since: {neighbor.get('uptime', 'Unknown')}"
                )

            # Add prefix information
            if "prefixes" in neighbor and neighbor["prefixes"]:
                for af_name, prefix_data in neighbor["prefixes"].items():
                    summary_lines.append(
                        f"    - {af_name}: received {prefix_data.get('received', 0)}, "
                        f"sent {prefix_data.get('sent', 0)}"
                    )

    # VRFs
    if "vrfs" in bgp_config and bgp_config["vrfs"]:
        summary_lines.append("VRFs:")
        for vrf in bgp_config["vrfs"]:
            summary_lines.append(
                f"  * {vrf['name']} - AS: {vrf.get('as_number', 'N/A')}, "
                f"Router ID: {vrf.get('router_id', 'N/A')}"
            )

            if "prefixes" in vrf:
                summary_lines.append(
                    f"    - Total Prefixes: {vrf['total_prefixes']}"
                )

            # Add address families
            if "address_families" in vrf and vrf["address_families"]:
                for af in vrf["address_families"]:
                    summary_lines.append(
                        f"    - {af['name']} (Prefixes: {af.get('prefixes', 0)})"
                    )

    return "\n".join(summary_lines)


def _extract_llm_friendly_bgp_data(
    default_bgp: Dict[str, Any],
    vrf_bgp_data: List[Dict[str, Any]],
    timestamp: int,
) -> Dict[str, Any]:
    """
    Extract only the information that's relevant for small LLMs from OpenConfig BGP data.

    Args:
        default_bgp: The DEFAULT BGP instance data
        vrf_bgp_data: List of VRF BGP instance data
        timestamp: The timestamp of the data collection

    Returns:
        Dict containing simplified BGP configuration and state information
    """
    # Create timestamp strings
    timestamp_str = time.strftime(
        "%Y-%m-%d %H:%M:%S", time.localtime(timestamp / 1e9)
    )

    # Extract basic router information
    global_data = default_bgp.get("global", {})
    state = global_data.get("state", {})

    as_number = state.get("as")
    router_id = state.get("router-id")
    total_prefixes = state.get("total-prefixes")

    # Create the simplified BGP data structure
    bgp_data = {
        "data_timestamp": timestamp,
        "data_timestamp_str": timestamp_str,
        "router": {
            "as_number": as_number,
            "router_id": router_id,
            "total_prefixes": total_prefixes,
        },
        "address_families": [],
        "neighbor_groups": [],
        "neighbors": [],
        "vrfs": [],
    }

    # Extract address families
    _extract_global_address_families(bgp_data, default_bgp)

    # Extract neighbor groups
    _extract_peer_groups(bgp_data, default_bgp)

    # Extract neighbors
    _extract_neighbors(bgp_data, default_bgp)

    # Extract VRFs
    _extract_vrfs(bgp_data, vrf_bgp_data)

    return bgp_data


def _extract_global_address_families(
    bgp_data: Dict[str, Any], bgp_input: Dict[str, Any]
) -> None:
    """
    Extract only essential address family information.

    Args:
        bgp_data: The output BGP dictionary to update
        bgp_input: The input OpenConfig BGP data
    """
    global_data = bgp_input.get("global", {})
    afi_safis = global_data.get("afi-safis", {}).get("afi-safi", [])

    for afi_safi in afi_safis:
        af_name = afi_safi.get("afi-safi-name")
        if af_name:
            # Convert OpenConfig AFI-SAFI name to standard format
            cleaned_name = af_name.replace("openconfig-bgp-types:", "").lower()

            # Get state information
            state = afi_safi.get("state", {})

            # Create simplified address family info
            af_info = {
                "name": cleaned_name,
                "prefixes": state.get("total-prefixes"),
            }

            bgp_data["address_families"].append(af_info)


def _extract_peer_groups(
    bgp_data: Dict[str, Any], bgp_input: Dict[str, Any]
) -> None:
    """
    Extract only essential peer group information.

    Args:
        bgp_data: The output BGP dictionary to update
        bgp_input: The input OpenConfig BGP data
    """
    peer_groups_data = bgp_input.get("peer-groups", {}).get("peer-group", [])

    if not peer_groups_data:
        return

    for group in peer_groups_data:
        state = group.get("state", {})
        transport = group.get("transport", {}).get("state", {})

        # Create simplified group info
        group_info = {
            "name": state.get("peer-group-name"),
            "remote_as": state.get("peer-as"),
            "update_source": transport.get("local-address"),
            "address_families": [],
        }

        # Add enabled address families
        afi_safis = group.get("afi-safis", {}).get("afi-safi", [])
        for af in afi_safis:
            af_state = af.get("state", {})
            af_name = af_state.get("afi-safi-name")

            if af_name and af_state.get("enabled", False):
                # Convert OpenConfig AFI-SAFI name to standard format
                cleaned_name = af_name.replace(
                    "openconfig-bgp-types:", ""
                ).lower()

                af_info = {"name": cleaned_name}

                # Add RR client info if available
                apply_policy = af.get("apply-policy", {})
                if apply_policy:
                    # This is a simplification - in real OpenConfig, route-reflector-client
                    # might be set differently. This is just a placeholder for the concept.
                    if apply_policy.get("route-reflector-client", False):
                        af_info["is_rr_client"] = True

                group_info["address_families"].append(af_info)

        bgp_data["neighbor_groups"].append(group_info)


def _extract_neighbors(
    bgp_data: Dict[str, Any], bgp_input: Dict[str, Any]
) -> None:
    """
    Extract only essential neighbor information.

    Args:
        bgp_data: The output BGP dictionary to update
        bgp_input: The input OpenConfig BGP data
    """
    raw_neighbors = bgp_input.get("neighbors", {}).get("neighbor", [])

    if not raw_neighbors:
        return

    for neighbor in raw_neighbors:
        state = neighbor.get("state", {})

        # Create simplified neighbor info
        neighbor_info = {
            "address": state.get("neighbor-address"),
            "remote_as": state.get("peer-as"),
            "group": state.get("peer-group"),
            "state": state.get("session-state"),
            "prefixes": {},
        }

        # Add last established time
        last_established = state.get("last-established")
        if last_established:
            try:
                timestamp_sec = int(last_established) / 1e9
                neighbor_info["uptime"] = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(timestamp_sec)
                )
            except (ValueError, OverflowError):
                neighbor_info["uptime"] = "Unknown"

        # Add prefix information by address family
        afi_safis = neighbor.get("afi-safis", {}).get("afi-safi", [])
        for af in afi_safis:
            af_state = af.get("state", {})
            af_name = af_state.get("afi-safi-name")

            if af_name:
                cleaned_name = af_name.replace(
                    "openconfig-bgp-types:", ""
                ).lower()

                # Add prefix counts if available
                prefixes = af_state.get("prefixes", {})
                if prefixes:
                    neighbor_info["prefixes"][cleaned_name] = {
                        "received": prefixes.get("received", 0),
                        "sent": prefixes.get("sent", 0),
                    }

        bgp_data["neighbors"].append(neighbor_info)


def _extract_vrfs(
    bgp_data: Dict[str, Any], vrf_bgp_data: List[Dict[str, Any]]
) -> None:
    """
    Extract only essential VRF information.

    Args:
        bgp_data: The output BGP dictionary to update
        vrf_bgp_data: List of VRF BGP instance data
    """
    if not vrf_bgp_data:
        return

    for vrf_data in vrf_bgp_data:
        path = vrf_data.get("path", "")
        # Extract VRF name from path
        vrf_name = None
        if "network-instance[name=" in path:
            match = re.search(r"network-instance\[name=([^\]]+)\]", path)
            if match and match.group(1) != "DEFAULT":
                vrf_name = match.group(1)

        if vrf_name:
            vrf_val = vrf_data.get("val", {})
            global_data = vrf_val.get("global", {})
            state = global_data.get("state", {})

            # Create simplified VRF info
            vrf_info = {
                "name": vrf_name,
                "as_number": state.get("as"),
                "router_id": state.get("router-id"),
                "total_prefixes": state.get("total-prefixes"),
                "address_families": [],
            }

            # Add address families
            afi_safis = global_data.get("afi-safis", {}).get("afi-safi", [])
            for afi_safi in afi_safis:
                af_state = afi_safi.get("state", {})
                af_name = af_state.get("afi-safi-name")

                if af_name:
                    cleaned_name = af_name.replace(
                        "openconfig-bgp-types:", ""
                    ).lower()

                    af_info = {
                        "name": cleaned_name,
                        "prefixes": af_state.get("total-prefixes"),
                    }

                    vrf_info["address_families"].append(af_info)

            bgp_data["vrfs"].append(vrf_info)


def generate_simple_bgp_state_summary(bgp_config: Dict[str, Any]) -> str:
    """
    Generate a simplified summary of BGP state that's optimized for small LLMs.

    Args:
        bgp_config: The BGP configuration and state data

    Returns:
        A string containing a simplified summary focused on operational state
    """
    if "parse_error" in bgp_config:
        return f"Error parsing BGP data: {bgp_config['parse_error']}"

    lines = []

    # Basic router information
    router = bgp_config.get("router", {})
    lines.append(f"BGP Router AS{router.get('as_number', 'unknown')}")
    lines.append(f"Router ID: {router.get('router_id', 'unknown')}")

    # Overall statistics
    if "total_prefixes" in router:
        lines.append(f"Total network prefixes: {router['total_prefixes']}")

    # Neighbor state summary
    if "neighbors" in bgp_config:
        lines.append("\nNeighbor State Summary:")

        # Count neighbors by state
        state_count = {}
        for neighbor in bgp_config["neighbors"]:
            state = neighbor.get("state", "UNKNOWN")
            state_count[state] = state_count.get(state, 0) + 1

        for state, count in state_count.items():
            lines.append(f"- {count} neighbors in {state} state")

        # Detailed neighbor information
        lines.append("\nNeighbor Details:")
        for neighbor in bgp_config["neighbors"]:
            addr = neighbor["address"]
            state = neighbor.get("state", "UNKNOWN")
            remote_as = neighbor.get("remote_as", "Unknown")

            line = f"- {addr} (AS{remote_as}): {state}"
            lines.append(line)

            # Show prefix counts for established sessions
            if state == "ESTABLISHED" and "prefixes" in neighbor:
                for af_name, prefix_data in neighbor["prefixes"].items():
                    lines.append(
                        f"  {af_name}: {prefix_data.get('received', 0)} received, "
                        f"{prefix_data.get('sent', 0)} sent"
                    )

    # VRF summary information
    if "vrfs" in bgp_config and bgp_config["vrfs"]:
        lines.append("\nVRF Summary:")
        for vrf in bgp_config["vrfs"]:
            lines.append(
                f"- VRF {vrf['name']}: {vrf.get('prefixes', 0)} prefixes "
                f"across {len(vrf.get('address_families', []))} address families"
            )

    return "\n".join(lines)
