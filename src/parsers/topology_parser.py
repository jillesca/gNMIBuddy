# filepath: src/parsers/topology_parser.py
#!/usr/bin/env python3
"""
Topology parser module.
Provides functions for extracting interface subnet data for topology discovery.
"""
from typing import List, Dict, Any
import ipaddress


def extract_interface_subnets(
    interface_results: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Extract interface IP and network information from interface API results.

    Args:
        interface_results: List of dicts as returned by get_interface_info API (one per device)

    Returns:
        List of entries with device, interface, ip, and network (CIDR string)
    """
    entries: List[Dict[str, Any]] = []
    for res in interface_results:
        device = res.get("device")
        # Support both top-level 'interfaces' and nested 'response'->'interfaces'
        if "interfaces" in res:
            interfaces = res.get("interfaces", [])
        else:
            resp = res.get("response", {})
            interfaces = resp.get("interfaces", [])
        for iface in interfaces:
            ip_addr = iface.get("ip_address")
            name = (
                iface.get("name")
                or iface.get("interface")
                or iface.get("name")
            )
            if not ip_addr or not device or not name:
                continue
            # Convert "100.103.104.104/255.255.255.0" to "100.103.104.104/24"
            try:
                ip, mask = ip_addr.split("/")
                network = str(
                    ipaddress.IPv4Network(f"{ip}/{mask}", strict=False)
                )
            except Exception:
                continue
            entries.append(
                {
                    "device": device,
                    "interface": name,
                    "ip": ip,
                    "network": network,
                }
            )
    return entries
