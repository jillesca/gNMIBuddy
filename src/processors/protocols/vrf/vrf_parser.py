#!/usr/bin/env python3
"""
VRF Parser module.
Parses VRF configuration and state data from gNMI responses and formats it
in a simplified way for easier consumption by small LLMs.
"""

import logging
import time
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def parse_vrf_data(gnmi_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Parse VRF data from a gNMI response.

    Args:
        gnmi_data: The gNMI response data (list of update dictionaries) containing VRF data

    Returns:
        Dict containing parsed VRF data in a simplified format for small LLMs
    """
    # logger.debug("Parsing VRF data from gNMI response")

    # Initialize the result structure
    result = {
        "timestamp": int(time.time() * 1e9),
        "timestamp_readable": time.strftime(
            "%Y-%m-%d %H:%M:%S",
            time.localtime(int(time.time())),
        ),
        "vrfs": [],
    }

    # Check if we have valid gNMI data
    if not gnmi_data:
        logger.error("Empty gNMI data")
        return result

    # Work directly with the gNMI response data
    response_data = gnmi_data
    if not response_data:
        logger.warning("No response data found in gNMI data")
        return result

    # Track VRF names to avoid duplicates
    processed_vrfs = set()

    # Process each VRF in the response
    for item in response_data:
        if not isinstance(item, dict) or "val" not in item:
            continue

        vrf_data = item["val"]
        if not isinstance(vrf_data, dict):
            continue

        vrf_name = vrf_data.get("name")

        # Skip DEFAULT VRF
        if vrf_name == "DEFAULT":
            logger.debug("Skipping DEFAULT VRF")
            continue

        # Skip if this VRF was already processed (avoid duplicates)
        if vrf_name in processed_vrfs:
            logger.debug("Skipping duplicate VRF: %s", vrf_name)
            continue

        # Mark this VRF as processed
        processed_vrfs.add(vrf_name)

        vrf_info = {
            "name": vrf_name,
            "description": vrf_data.get("state", {}).get("description"),
            "enabled": vrf_data.get("state", {}).get("enabled", True),
            "type": vrf_data.get("state", {}).get("type"),
            "router_id": vrf_data.get("state", {}).get("router-id"),
            "route_distinguisher": _extract_route_distinguisher(vrf_data),
            "interfaces": _extract_interfaces(vrf_data),
            "route_targets": _extract_route_targets(vrf_data),
            "protocols": _extract_protocols(vrf_data),
        }

        result["vrfs"].append(vrf_info)

    return result


def _extract_route_distinguisher(vrf_data: Dict[str, Any]) -> str:
    """
    Extract route distinguisher (RD) from VRF data.

    Args:
        vrf_data: The VRF data from gNMI response

    Returns:
        The route distinguisher (RD) or None if not found
    """
    # Check in the state directly first (common structure in test data)
    if "state" in vrf_data and "route-distinguisher" in vrf_data["state"]:
        return vrf_data["state"]["route-distinguisher"]

    # Original check for nested route-distinguisher object
    if (
        "route-distinguisher" in vrf_data
        and "state" in vrf_data["route-distinguisher"]
    ):
        return vrf_data["route-distinguisher"]["state"].get("rd")

    return ""


def _extract_interfaces(vrf_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract interface information from VRF data.

    Args:
        vrf_data: The VRF data from gNMI response

    Returns:
        List of interfaces with their associated address families
    """
    interfaces = []

    if "interfaces" in vrf_data and "interface" in vrf_data["interfaces"]:
        for interface in vrf_data["interfaces"]["interface"]:
            interface_info = {
                "name": interface.get("id"),
                "address_families": [],
            }

            # Extract address families
            if (
                "state" in interface
                and "associated-address-families" in interface["state"]
            ):
                for af in interface["state"]["associated-address-families"]:
                    # Clean up the address family name
                    af_name = af.replace("openconfig-types:", "")
                    interface_info["address_families"].append(af_name)

            interfaces.append(interface_info)

    return interfaces


def _extract_route_targets(vrf_data: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Extract import and export route targets from VRF data.

    Args:
        vrf_data: The VRF data from gNMI response

    Returns:
        Dictionary with import and export route targets
    """
    route_targets = {"import": [], "export": []}

    # First check the common structure in the test data (inter-instance-policies)
    if "inter-instance-policies" in vrf_data:
        policies = vrf_data["inter-instance-policies"]

        # Check import-export-policy structure
        if (
            "import-export-policy" in policies
            and "state" in policies["import-export-policy"]
        ):
            policy_state = policies["import-export-policy"]["state"]

            if "import-route-target" in policy_state:
                route_targets["import"] = policy_state["import-route-target"]

            if "export-route-target" in policy_state:
                route_targets["export"] = policy_state["export-route-target"]

    # Original check for vpn-targets structure
    if "vpn-targets" in vrf_data and "vpn-target" in vrf_data["vpn-targets"]:
        for rt in vrf_data["vpn-targets"]["vpn-target"]:
            if "state" in rt:
                rt_type = rt["state"].get("rt-type")
                rt_value = rt["state"].get("rt-value")

                if rt_type and rt_value:
                    if rt_type == "import":
                        route_targets["import"].append(rt_value)
                    elif rt_type == "export":
                        route_targets["export"].append(rt_value)

    return route_targets


def _extract_protocols(vrf_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract routing protocol information from VRF data.

    Args:
        vrf_data: The VRF data from gNMI response

    Returns:
        List of protocols configured in the VRF
    """
    protocols = []

    if "protocols" in vrf_data and "protocol" in vrf_data["protocols"]:
        for protocol in vrf_data["protocols"]["protocol"]:
            protocol_info = {
                "type": protocol.get("identifier"),
                "name": protocol.get("name"),
                "details": {},
            }

            # Extract protocol-specific details
            if (
                protocol.get("identifier") == "openconfig-policy-types:BGP"
                or protocol.get("identifier") == "BGP"
            ):
                if "bgp" in protocol:
                    # Extract BGP global state information
                    if (
                        "global" in protocol["bgp"]
                        and "state" in protocol["bgp"]["global"]
                    ):
                        bgp_state = protocol["bgp"]["global"]["state"]
                        protocol_info["details"] = {
                            "as_number": bgp_state.get("as"),
                            "router_id": bgp_state.get("router-id"),
                            "total_paths": bgp_state.get("total-paths"),
                            "total_prefixes": bgp_state.get("total-prefixes"),
                        }
            elif (
                protocol.get("identifier") == "STATIC"
                or protocol.get("identifier")
                == "openconfig-policy-types:STATIC"
            ):
                # Use static-routes as the type for better clarity
                protocol_info["type"] = "static-routes"

                # Extract static routes information
                if (
                    "static-routes" in protocol
                    and "static" in protocol["static-routes"]
                ):
                    routes = []
                    for route in protocol["static-routes"]["static"]:
                        route_info = {
                            "prefix": route.get("prefix"),
                            "next_hops": [],
                        }

                        # Extract next hops
                        if (
                            "next-hops" in route
                            and "next-hop" in route["next-hops"]
                        ):
                            for next_hop in route["next-hops"]["next-hop"]:
                                if "state" in next_hop:
                                    hop_info = {
                                        "address": next_hop["state"].get(
                                            "next-hop"
                                        ),
                                        "metric": next_hop["state"].get(
                                            "metric"
                                        ),
                                        "preference": next_hop["state"].get(
                                            "preference"
                                        ),
                                    }
                                    route_info["next_hops"].append(hop_info)

                        routes.append(route_info)

                    protocol_info["details"]["routes"] = routes
            elif protocol.get("identifier") == "OSPF" and "ospfv2" in protocol:
                if (
                    "global" in protocol["ospfv2"]
                    and "state" in protocol["ospfv2"]["global"]
                ):
                    protocol_info["details"] = {
                        "router_id": protocol["ospfv2"]["global"]["state"].get(
                            "router-id"
                        )
                    }
            elif protocol.get("identifier") == "ISIS" and "isis" in protocol:
                if (
                    "global" in protocol["isis"]
                    and "state" in protocol["isis"]["global"]
                ):
                    protocol_info["details"] = {
                        "net": protocol["isis"]["global"]["state"].get("net")
                    }

            protocols.append(protocol_info)

    return protocols


def generate_vrf_summary(vrf_data: Dict[str, Any]) -> str:
    """
    Generate a human-readable summary of VRF data suitable for small LLMs.

    Args:
        vrf_data: Parsed VRF data

    Returns:
        String containing a summary of VRF data
    """
    if not vrf_data or not vrf_data.get("vrfs"):
        return "No VRF data available."

    timestamp = vrf_data.get("timestamp_readable", "Unknown time")
    summary_lines = [f"VRF Configuration Summary (as of {timestamp}):", ""]

    for vrf in vrf_data["vrfs"]:
        status = "Enabled" if vrf.get("enabled") else "Disabled"
        summary_lines.append(f"VRF: {vrf.get('name', 'Unknown')} ({status})")

        if vrf.get("description"):
            summary_lines.append(f"  Description: {vrf['description']}")

        if vrf.get("type"):
            summary_lines.append(f"  Type: {vrf['type']}")

        if vrf.get("router_id"):
            summary_lines.append(f"  Router ID: {vrf['router_id']}")

        if vrf.get("route_distinguisher"):
            summary_lines.append(
                f"  Route Distinguisher: {vrf['route_distinguisher']}"
            )

        # Route targets
        if vrf.get("route_targets"):
            if vrf["route_targets"].get("import"):
                rt_list = ", ".join(vrf["route_targets"]["import"])
                summary_lines.append(f"  Import Route Targets: {rt_list}")

            if vrf["route_targets"].get("export"):
                rt_list = ", ".join(vrf["route_targets"]["export"])
                summary_lines.append(f"  Export Route Targets: {rt_list}")

        # Interfaces
        if vrf.get("interfaces"):
            summary_lines.append("  Interfaces:")
            for interface in vrf["interfaces"]:
                af_list = ", ".join(interface.get("address_families", []))
                summary_lines.append(
                    f"    - {interface.get('name', 'Unknown')} (Address Families: {af_list or 'None'})"
                )

        # Protocols
        if vrf.get("protocols"):
            summary_lines.append("  Protocols:")
            for protocol in vrf["protocols"]:
                protocol_type = protocol.get("type", "Unknown")
                protocol_name = protocol.get("name", "default")
                protocol_line = f"    - {protocol_type} {protocol_name}"

                # Add protocol-specific details
                details = protocol.get("details", {})
                if protocol_type == "BGP" and "as_number" in details:
                    protocol_line += f" (AS: {details['as_number']})"
                elif protocol_type == "OSPF" and "router_id" in details:
                    protocol_line += f" (Router ID: {details['router_id']})"
                elif protocol_type == "ISIS" and "net" in details:
                    protocol_line += f" (NET: {details['net']})"

                summary_lines.append(protocol_line)

        summary_lines.append("")  # Add blank line between VRFs

    return "\n".join(summary_lines)


def generate_llm_friendly_data(vrf_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a simplified data structure that's optimized for small LLMs to understand.

    Args:
        vrf_data: The parsed VRF data

    Returns:
        Dict with simplified VRF information focused on what's important for LLMs
    """
    llm_data = {
        "timestamp": vrf_data.get("timestamp_readable", "Unknown"),
        "vrfs": [],
    }

    for vrf in vrf_data.get("vrfs", []):
        # Create a list for protocols with their details embedded
        protocols_with_details = []

        for protocol in vrf.get("protocols", []):
            protocol_type = protocol.get("type", "")
            protocol_name = protocol.get("name", "")
            protocol_entry = {"type": protocol_type, "name": protocol_name}

            # Extract BGP details
            if protocol_type in ["openconfig-policy-types:BGP", "BGP"]:
                details = protocol.get("details", {})
                if details:
                    protocol_entry.update(
                        {
                            "as_number": details.get("as_number"),
                            "router_id": details.get("router_id"),
                            "paths": details.get("total_paths"),
                            "prefixes": details.get("total_prefixes"),
                        }
                    )

            # Extract static routes
            elif protocol_type == "static-routes":
                details = protocol.get("details", {})
                if "routes" in details:
                    routes = []
                    for route in details["routes"]:
                        route_entry = {
                            "prefix": route.get("prefix"),
                            "next_hops": [],
                        }
                        for next_hop in route.get("next_hops", []):
                            route_entry["next_hops"].append(
                                {
                                    "address": next_hop.get("address"),
                                    "metric": next_hop.get("metric"),
                                    "preference": next_hop.get("preference"),
                                }
                            )
                        routes.append(route_entry)
                    protocol_entry["routes"] = routes

            # Add other protocol specific details as needed
            protocols_with_details.append(protocol_entry)

        simplified_vrf = {
            "name": vrf.get("name"),
            "description": vrf.get("description"),
            "rd": vrf.get("route_distinguisher"),
            "interfaces": [
                intf.get("name") for intf in vrf.get("interfaces", [])
            ],
            "route_targets": {
                "import": vrf.get("route_targets", {}).get("import", []),
                "export": vrf.get("route_targets", {}).get("export", []),
            },
            "protocols": protocols_with_details,
        }
        llm_data["vrfs"].append(simplified_vrf)

    return llm_data
