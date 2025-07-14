#!/usr/bin/env python3
"""
Cisco IOS-XR VRF processor implementation.
Implements the standard VRF processor interface for Cisco IOS-XR devices.
"""

import logging
from typing import Dict, Any, List
from src.processors.protocols.vrf.processor_interface import VrfProcessor

logger = logging.getLogger(__name__)


class CiscoIosXrVrfProcessor(VrfProcessor):
    """
    Processor for VRF data from Cisco IOS-XR devices.

    This class implements the VrfProcessor interface for Cisco IOS-XR devices,
    extracting VRF information from OpenConfig paths.
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

        # Process each item in the extracted data
        for item in data.get("items", []):
            val = item.get("val", {})

            # Extract VRF name
            vrf_name = val.get("name")

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
                "description": val.get("state", {}).get("description"),
                "enabled": val.get("state", {}).get("enabled", True),
                "type": val.get("state", {}).get("type"),
                "router_id": val.get("state", {}).get("router-id"),
                "route_distinguisher": self._extract_route_distinguisher(val),
                "interfaces": self._extract_interfaces(val),
                "route_targets": self._extract_route_targets(val),
                "protocols": self._extract_protocols(val),
            }

            result["vrfs"].append(vrf_info)

        return result

    def _extract_route_distinguisher(self, vrf_data: Dict[str, Any]) -> str:
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

    def _extract_interfaces(
        self, vrf_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
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
                    for af in interface["state"][
                        "associated-address-families"
                    ]:
                        # Clean up the address family name
                        af_name = af.replace("openconfig-types:", "")
                        interface_info["address_families"].append(af_name)

                interfaces.append(interface_info)

        return interfaces

    def _extract_route_targets(
        self, vrf_data: Dict[str, Any]
    ) -> Dict[str, List[str]]:
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
                    route_targets["import"] = policy_state[
                        "import-route-target"
                    ]

                if "export-route-target" in policy_state:
                    route_targets["export"] = policy_state[
                        "export-route-target"
                    ]

        # Original check for vpn-targets structure
        if (
            "vpn-targets" in vrf_data
            and "vpn-target" in vrf_data["vpn-targets"]
        ):
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

    def _extract_protocols(
        self, vrf_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
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
                }

                # Add specific fields based on protocol type
                if protocol_info["type"] == "BGP":
                    protocol_info.update(self._extract_bgp_info(protocol))
                elif protocol_info["type"] == "ISIS":
                    protocol_info.update(self._extract_isis_info(protocol))
                elif protocol_info["type"] == "OSPF":
                    protocol_info.update(self._extract_ospf_info(protocol))
                elif protocol_info["type"] == "STATIC":
                    protocol_info.update(self._extract_static_info(protocol))

                protocols.append(protocol_info)

        return protocols

    def _extract_bgp_info(
        self, protocol_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract BGP-specific information from protocol data.

        Args:
            protocol_data: Protocol data from gNMI response

        Returns:
            Dictionary with BGP-specific information
        """
        bgp_info = {
            "router_id": None,
            "as_number": None,
            "neighbors": [],
        }

        if "bgp" in protocol_data and "global" in protocol_data["bgp"]:
            global_config = protocol_data["bgp"]["global"]
            if "state" in global_config:
                state = global_config["state"]
                bgp_info["router_id"] = state.get("router-id")
                bgp_info["as_number"] = state.get("as")

        if "bgp" in protocol_data and "neighbors" in protocol_data["bgp"]:
            for neighbor in protocol_data["bgp"]["neighbors"].get(
                "neighbor", []
            ):
                if "state" in neighbor:
                    neighbor_info = {
                        "address": neighbor.get("neighbor-address"),
                        "as": neighbor["state"].get("peer-as"),
                    }
                    bgp_info["neighbors"].append(neighbor_info)

        return bgp_info

    def _extract_isis_info(
        self, protocol_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract ISIS-specific information from protocol data.

        Args:
            protocol_data: Protocol data from gNMI response

        Returns:
            Dictionary with ISIS-specific information
        """
        isis_info = {
            "net": None,
            "level_capability": None,
            "interfaces": [],
        }

        if "isis" in protocol_data and "global" in protocol_data["isis"]:
            global_config = protocol_data["isis"]["global"]
            if "state" in global_config:
                state = global_config["state"]
                isis_info["net"] = state.get("net")
                isis_info["level_capability"] = state.get("level-capability")

        if "isis" in protocol_data and "interfaces" in protocol_data["isis"]:
            for interface in protocol_data["isis"]["interfaces"].get(
                "interface", []
            ):
                isis_info["interfaces"].append(interface.get("interface-id"))

        return isis_info

    def _extract_ospf_info(
        self, protocol_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract OSPF-specific information from protocol data.

        Args:
            protocol_data: Protocol data from gNMI response

        Returns:
            Dictionary with OSPF-specific information
        """
        ospf_info = {
            "router_id": None,
            "areas": [],
        }

        if "ospf" in protocol_data and "global" in protocol_data["ospf"]:
            global_config = protocol_data["ospf"]["global"]
            if "state" in global_config:
                ospf_info["router_id"] = global_config["state"].get(
                    "router-id"
                )

        if "ospf" in protocol_data and "areas" in protocol_data["ospf"]:
            for area in protocol_data["ospf"]["areas"].get("area", []):
                area_info = {
                    "id": area.get("identifier"),
                    "interfaces": [],
                }

                if "interfaces" in area and "interface" in area["interfaces"]:
                    for interface in area["interfaces"]["interface"]:
                        area_info["interfaces"].append(interface.get("id"))

                ospf_info["areas"].append(area_info)

        return ospf_info

    def _extract_static_info(
        self, protocol_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract static route information from protocol data.

        Args:
            protocol_data: Protocol data from gNMI response

        Returns:
            Dictionary with static route information
        """
        static_info = {
            "routes": [],
        }

        if "static-routes" in protocol_data:
            for route in protocol_data["static-routes"].get("static", []):
                route_info = {
                    "prefix": route.get("prefix"),
                    "next_hops": [],
                }

                if "next-hops" in route and "next-hop" in route["next-hops"]:
                    for nexthop in route["next-hops"]["next-hop"]:
                        if "state" in nexthop:
                            route_info["next_hops"].append(
                                nexthop["state"].get("next-hop")
                            )

                static_info["routes"].append(route_info)

        return static_info

    def generate_summary(self, data: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of the VRF data.

        Args:
            data: VRF data to summarize

        Returns:
            String containing a human-readable summary
        """
        vrfs = data.get("vrfs", [])

        if not vrfs:
            return "No VRFs found on the device."

        summary_lines = [f"Found {len(vrfs)} VRF(s):"]

        for vrf in vrfs:
            vrf_name = vrf.get("name", "Unknown")
            rd = vrf.get("route_distinguisher", "None")
            interfaces_count = len(vrf.get("interfaces", []))

            # Get route target counts
            route_targets = vrf.get("route_targets", {})
            import_rts = len(route_targets.get("import", []))
            export_rts = len(route_targets.get("export", []))

            # Get protocol types
            protocol_types = [p.get("type") for p in vrf.get("protocols", [])]

            summary_lines.append(
                f"- {vrf_name}: RD={rd}, {interfaces_count} interfaces, "
                f"{import_rts} import RTs, {export_rts} export RTs, "
                f"Protocols: {', '.join(protocol_types) if protocol_types else 'None'}"
            )

        return "\n".join(summary_lines)
