#!/usr/bin/env python3
"""
Device profile processor module.
Processes device profile data from gNMI responses into a structured format.
"""

from typing import Dict, Any, List
from src.processors.base import BaseProcessor


class DeviceProfileProcessor(BaseProcessor):
    """
    Processor for device profile data from gNMI responses.

    Accepts raw gNMI data (List[Dict[str, Any]]) directly and determines
    device role and capabilities including MPLS, ISIS, BGP L3VPN,
    route reflector status, and VPN BGP configuration.
    """

    def process_data(
        self,
        gnmi_data: List[Dict[str, Any]],
        vpn_info: Any = None,
        vpn_bgp_afi_safi_states: Any = None,
    ) -> Dict[str, Any]:
        """
        Process device profile information from gNMI data.

        Args:
            gnmi_data: Raw gNMI response data (list of update dictionaries)
            vpn_info: Optional VPN information for enhanced analysis
            vpn_bgp_afi_safi_states: Optional BGP AFI/SAFI states for VPN analysis

        Returns:
            Device profile dictionary with capabilities and role
        """
        extracted = self.extract_data(gnmi_data)
        return self.transform_data(
            extracted,
            vpn_info=vpn_info,
            vpn_bgp_afi_safi_states=vpn_bgp_afi_safi_states,
        )

    def extract_data(
        self, gnmi_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract device profile data from gNMI response.

        Args:
            gnmi_data: Raw gNMI response data (list of update dictionaries)

        Returns:
            Extracted device profile data ready for processing
        """
        # Return the raw data directly
        return gnmi_data if gnmi_data else []

    def transform_data(
        self, extracted_data: List[Dict[str, Any]], **kwargs
    ) -> Dict[str, Any]:
        """
        Transform extracted device profile data into structured format.

        Args:
            extracted_data: Device profile data extracted from gNMI response
            **kwargs: Additional parameters including vpn_info and vpn_bgp_afi_safi_states

        Returns:
            Device profile dictionary with capabilities and determined role
        """
        all_entries = (
            extracted_data if isinstance(extracted_data, list) else []
        )
        vpn_bgp_afi_safi_states = kwargs.get("vpn_bgp_afi_safi_states", [])

        features = {
            "is_mpls_enabled": self._is_mpls_enabled(all_entries),
            "is_isis_enabled": self._is_isis_enabled(all_entries),
            "is_bgp_l3vpn_enabled": self._is_bgp_l3vpn_enabled(all_entries),
            "is_route_reflector": self._is_route_reflector(all_entries),
            "has_vpn_ipv4_unicast_bgp": self._has_vpn_ipv4_unicast_bgp(
                vpn_bgp_afi_safi_states
            ),
        }
        role = self._determine_role(features)
        return {**features, "role": role}

    def _is_mpls_enabled(self, entries):
        return any(
            "/mpls/global/interface-attributes/interface" in e.get("path", "")
            and e.get("val", {}).get("mpls-enabled")
            for e in entries
        )

    def _is_isis_enabled(self, entries):
        return any(
            "/isis/global/state" in e.get("path", "") and e.get("val", {})
            for e in entries
        )

    def _is_bgp_l3vpn_enabled(self, entries):
        return any(
            "/afi-safi" in e.get("path", "")
            and e.get("val", {}).get("afi-safi-name")
            == "openconfig-bgp-types:L3VPN_IPV4_UNICAST"
            and e.get("val", {}).get("enabled")
            for e in entries
        )

    def _is_route_reflector(self, entries):
        return any(
            "/route-reflector/state" in e.get("path", "")
            and e.get("val", {}).get("route-reflector-client")
            and e.get("val", {}).get("route-reflector-cluster-id")
            for e in entries
        )

    def _has_vpn_ipv4_unicast_bgp(self, vpn_bgp_afi_safi_states):
        if vpn_bgp_afi_safi_states is None:
            return False
        return any(
            v.get("val", {}).get("afi-safi-name")
            == "openconfig-bgp-types:IPV4_UNICAST"
            and v.get("val", {}).get("enabled") is True
            for v in vpn_bgp_afi_safi_states
        )

    def _determine_role(self, f):
        if f["is_route_reflector"]:
            return "RR"
        elif (
            f["is_bgp_l3vpn_enabled"]
            and f["is_mpls_enabled"]
            and f["is_isis_enabled"]
            and f["has_vpn_ipv4_unicast_bgp"]
        ):
            return "PE"
        elif f["is_mpls_enabled"] and f["is_isis_enabled"]:
            return "P"
        elif f["is_isis_enabled"]:
            return "IGP-only"
        elif (
            not f["is_mpls_enabled"]
            and not f["is_isis_enabled"]
            and not f["is_bgp_l3vpn_enabled"]
            and not f["is_route_reflector"]
        ):
            return "CE"
        else:
            return "Unknown"
