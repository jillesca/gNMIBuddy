#!/usr/bin/env python3
"""
Device profile parser module.
Parses device profile data from gNMI responses into a structured format.
"""

from typing import Dict, Any, List
from src.parsers.base import BaseParser


class DeviceProfileParser(BaseParser):
    """
    Parser for device profile data from gNMI responses.
    """

    def parse(
        self,
        data: List[Dict[str, Any]],
        vpn_info: Any = None,
        vpn_bgp_afi_safi_states: Any = None,
    ) -> Dict[str, Any]:
        extracted = self.extract_data(data)
        return self.transform_data(
            extracted,
            vpn_info=vpn_info,
            vpn_bgp_afi_safi_states=vpn_bgp_afi_safi_states,
        )

    def extract_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Return the raw data directly
        return data if data else []

    def transform_data(
        self, extracted_data: List[Dict[str, Any]], **kwargs
    ) -> Dict[str, Any]:
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
