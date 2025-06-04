#!/usr/bin/env python3
"""
VRF parser interfaces.
Defines standard interfaces for parsers that work with VRF data.
"""

from typing import Dict, Any, List
from src.parsers.protocols.parser_interface import VrfParser


class OpenConfigVrfParser(VrfParser):
    """
    Parser for VRF data using OpenConfig model.

    This class handles parsing VRF configuration and state data
    from OpenConfig network-instance models.
    """

    def process_protocol_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process extracted data into structured VRF information.

        Args:
            data: Extracted data containing VRF information

        Returns:
            Dictionary with structured VRF information
        """
        result = {"vrfs": []}

        # Track VRF names to avoid duplicates
        processed_vrfs = set()

        for item in data.get("items", []):
            val = item.get("val", {})
            vrf_name = val.get("name")

            # Skip DEFAULT VRF
            if vrf_name == "DEFAULT":
                continue

            # Skip if this VRF was already processed (avoid duplicates)
            if vrf_name in processed_vrfs:
                continue

            if vrf_name:
                processed_vrfs.add(vrf_name)

                # Process VRF data
                vrf_info = {
                    "name": vrf_name,
                    "description": val.get("description", ""),
                    "route_distinguisher": self._extract_route_distinguisher(
                        val
                    ),
                    "interfaces": self._extract_interfaces(val),
                    "route_targets": self._extract_route_targets(val),
                    "protocols": self._extract_protocols(val),
                }

                result["vrfs"].append(vrf_info)

        # Create summary from the processed VRFs
        result["summary"] = self._create_summary(result["vrfs"])

        return result

    def _extract_route_distinguisher(self, vrf_data: Dict[str, Any]) -> str:
        """Extract route distinguisher (RD) from VRF data."""
        # Check in the state directly first (common structure in test data)
        if "state" in vrf_data and "route-distinguisher" in vrf_data["state"]:
            return vrf_data["state"]["route-distinguisher"]

        # Alternative structure in some OpenConfig implementations
        if "route-distinguisher" in vrf_data:
            rd_container = vrf_data["route-distinguisher"]
            if "state" in rd_container and "rd" in rd_container["state"]:
                return rd_container["state"]["rd"]

        return ""

    def _extract_interfaces(
        self, vrf_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract interfaces assigned to the VRF."""
        interfaces = []

        if "interfaces" in vrf_data and "interface" in vrf_data["interfaces"]:
            for interface in vrf_data["interfaces"]["interface"]:
                interface_info = {
                    "name": interface.get("id", ""),
                    "enabled": True,  # Default to True unless explicitly disabled
                    "address_families": [],  # Can be populated if AF info is available
                }

                # Extract state if available
                if "state" in interface:
                    interface_info["enabled"] = interface["state"].get(
                        "enabled", True
                    )

                # Add interface to list
                interfaces.append(interface_info)

        return interfaces

    def _extract_route_targets(
        self, vrf_data: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Extract route targets from VRF data."""
        route_targets = {"import": [], "export": []}

        # Check for VPN route-targets in OpenConfig model
        if "route-targets" in vrf_data:
            rt_container = vrf_data["route-targets"]

            # Extract import RTs
            if "import-route-targets" in rt_container:
                import_rt = rt_container["import-route-targets"]
                if "import-route-target" in import_rt:
                    for rt in import_rt["import-route-target"]:
                        if "state" in rt and "rt" in rt["state"]:
                            route_targets["import"].append(rt["state"]["rt"])

            # Extract export RTs
            if "export-route-targets" in rt_container:
                export_rt = rt_container["export-route-targets"]
                if "export-route-target" in export_rt:
                    for rt in export_rt["export-route-target"]:
                        if "state" in rt and "rt" in rt["state"]:
                            route_targets["export"].append(rt["state"]["rt"])

        return route_targets

    def _extract_protocols(
        self, vrf_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract routing protocols configured in the VRF."""
        protocols = []

        if "protocols" in vrf_data and "protocol" in vrf_data["protocols"]:
            for protocol in vrf_data["protocols"]["protocol"]:
                protocol_type = (
                    protocol.get("identifier", "")
                    .replace("openconfig-policy-types:", "")
                    .lower()
                )

                protocol_info = {"type": protocol_type, "details": {}}

                # Extract BGP details
                if protocol_type == "bgp" and "bgp" in protocol:
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

                # Extract static route details
                elif (
                    protocol_type == "static"
                    or protocol_type == "static-routes"
                ):
                    protocol_info["type"] = "static-routes"
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
                                            "preference": next_hop[
                                                "state"
                                            ].get("preference"),
                                        }
                                        route_info["next_hops"].append(
                                            hop_info
                                        )

                            routes.append(route_info)

                        protocol_info["details"]["routes"] = routes

                protocols.append(protocol_info)

        return protocols

    def _create_summary(self, vrfs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a summary of the VRF data."""
        summary = {
            "vrf_count": len(vrfs),
            "vrfs_with_interfaces": 0,
            "total_interfaces": 0,
            "vrf_types": {"l3vpn": 0, "management": 0, "other": 0},
        }

        for vrf in vrfs:
            # Count interfaces
            interfaces = vrf.get("interfaces", [])
            if interfaces:
                summary["vrfs_with_interfaces"] += 1
                summary["total_interfaces"] += len(interfaces)

            # Categorize VRF types based on names or other attributes
            vrf_name = vrf.get("name", "").lower()
            if vrf_name == "mgmt" or vrf_name == "management":
                summary["vrf_types"]["management"] += 1
            elif vrf.get("route_distinguisher"):
                summary["vrf_types"]["l3vpn"] += 1
            else:
                summary["vrf_types"]["other"] += 1

        return summary

    def generate_summary(self, data: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of the VRF data.

        Args:
            data: VRF data to summarize

        Returns:
            String containing a human-readable summary of VRF configuration
        """
        vrfs = data.get("vrfs", [])
        if not vrfs:
            return "No VRFs configured on this device."

        summary_lines = [
            f"VRF Configuration Summary: {len(vrfs)} VRFs configured"
        ]

        # Show details for each VRF
        for vrf in vrfs:
            summary_lines.append(f"\nVRF: {vrf.get('name')}")

            if vrf.get("description"):
                summary_lines.append(
                    f"  Description: {vrf.get('description')}"
                )

            if vrf.get("route_distinguisher"):
                summary_lines.append(
                    f"  Route Distinguisher: {vrf.get('route_distinguisher')}"
                )

            # Route targets
            if vrf.get("route_targets"):
                rt = vrf["route_targets"]
                if rt.get("import"):
                    summary_lines.append(
                        f"  Import RTs: {', '.join(rt['import'])}"
                    )
                if rt.get("export"):
                    summary_lines.append(
                        f"  Export RTs: {', '.join(rt['export'])}"
                    )

            # Interfaces
            if vrf.get("interfaces"):
                interfaces = vrf["interfaces"]
                summary_lines.append(f"  Interfaces: {len(interfaces)}")
                for i, intf in enumerate(
                    interfaces[:3]
                ):  # Show first 3 interfaces
                    summary_lines.append(f"    - {intf.get('name')}")

                if len(interfaces) > 3:
                    summary_lines.append(
                        f"    ... and {len(interfaces) - 3} more"
                    )

            # Protocols
            if vrf.get("protocols"):
                protocols = vrf["protocols"]
                summary_lines.append(f"  Protocols: {len(protocols)}")
                for protocol in protocols:
                    proto_type = protocol.get("type", "unknown").upper()
                    details = protocol.get("details", {})

                    if proto_type == "BGP" and details:
                        summary_lines.append(
                            f"    - BGP AS {details.get('as_number')}, "
                            f"RID {details.get('router_id')}"
                        )
                    elif proto_type == "STATIC-ROUTES" and "routes" in details:
                        routes = details["routes"]
                        summary_lines.append(
                            f"    - {len(routes)} Static Routes"
                        )
                    else:
                        summary_lines.append(f"    - {proto_type}")

        return "\n".join(summary_lines)

    def generate_llm_friendly_data(
        self, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a simplified format optimized for LLM consumption.

        Args:
            data: VRF data to transform

        Returns:
            Dictionary with simplified VRF information for LLMs
        """
        llm_data = {
            "timestamp": data.get("timestamp"),
            "timestamp_readable": data.get("timestamp_readable"),
            "vrfs": [],
        }

        for vrf in data.get("vrfs", []):
            # Process protocols to simplify structure
            protocols_with_details = []
            for protocol in vrf.get("protocols", []):
                protocol_type = protocol.get("type", "unknown")
                protocol_entry = {"type": protocol_type}

                details = protocol.get("details", {})

                # Extract BGP details
                if protocol_type == "bgp":
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
                                        "preference": next_hop.get(
                                            "preference"
                                        ),
                                    }
                                )
                            routes.append(route_entry)
                        protocol_entry["routes"] = routes

                protocols_with_details.append(protocol_entry)

            # Create a simplified VRF entry
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
