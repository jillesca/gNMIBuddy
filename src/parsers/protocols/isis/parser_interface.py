#!/usr/bin/env python3
"""
ISIS parser interfaces.
Defines standard interfaces for parsers that work with ISIS protocol data.
"""

from typing import Dict, Any, List
from src.parsers.protocols.parser_interface import RoutingParser


class IsisParser(RoutingParser):
    """
    Parser for ISIS protocol data.

    This class handles parsing ISIS configuration and state data
    from OpenConfig models.
    """

    def get_protocol_type(self) -> str:
        """
        Get the type of routing protocol this parser handles.

        Returns:
            "isis" as the protocol type
        """
        return "isis"

    def process_protocol_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process extracted data into structured ISIS protocol information.

        Args:
            data: Extracted data containing ISIS information

        Returns:
            Dictionary with structured ISIS information
        """
        result = {
            "protocol_type": self.get_protocol_type(),
            "enabled": False,
            "router_id": None,
            "net": None,
            "level_capability": None,
            "authentication_check": None,
            "segment_routing_enabled": None,
            "interfaces": [],
            "adjacencies": [],
        }

        # Parse ISIS data from extracted items
        for item in data.get("items", []):
            path = item.get("path", "")
            val = item.get("val", {})

            # Process ISIS data based on path patterns
            # Implementation details should be provided by concrete classes

        return result

    def generate_summary(self, data: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of the ISIS protocol data.

        Args:
            data: ISIS protocol data to summarize

        Returns:
            String containing a human-readable summary of ISIS state
        """
        if not data.get("enabled", False) and not data.get("interfaces"):
            return "ISIS is not configured or enabled on this device."

        summary_lines = ["ISIS Configuration Summary:"]

        # Add basic ISIS information
        summary_lines.append(
            f"- Router ID: {data.get('router_id', 'Not configured')}"
        )
        summary_lines.append(f"- NET: {data.get('net', 'Not configured')}")
        summary_lines.append(
            f"- Level Capability: {data.get('level_capability', 'Not configured')}"
        )

        # Add interface information if available
        interfaces = data.get("interfaces", [])
        if interfaces:
            summary_lines.append(f"\nISIS Interfaces: {len(interfaces)}")
            for i, interface in enumerate(
                interfaces[:5]
            ):  # Show first 5 interfaces
                status = "Enabled" if interface.get("enabled") else "Disabled"
                passive = "Passive" if interface.get("passive") else "Active"
                summary_lines.append(
                    f"- {interface.get('name')}: {status}, {passive}"
                )

                # Add level information for this interface
                for level in interface.get("levels", []):
                    if level:
                        level_num = level.get("level_number")
                        level_status = (
                            "Enabled" if level.get("enabled") else "Disabled"
                        )
                        summary_lines.append(
                            f"  Level-{level_num}: {level_status}"
                        )

            if len(interfaces) > 5:
                summary_lines.append(
                    f"... and {len(interfaces) - 5} more interfaces"
                )

        # Add adjacency information if available
        adjacencies = data.get("adjacencies", [])
        if adjacencies:
            summary_lines.append(f"\nISIS Adjacencies: {len(adjacencies)}")
            for i, adj in enumerate(
                adjacencies[:5]
            ):  # Show first 5 adjacencies
                summary_lines.append(
                    f"- {adj.get('interface')} -> {adj.get('system_id')} "
                    f"({adj.get('neighbor_ipv4')})"
                )

            if len(adjacencies) > 5:
                summary_lines.append(
                    f"... and {len(adjacencies) - 5} more adjacencies"
                )

        return "\n".join(summary_lines)
