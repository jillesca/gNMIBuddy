#!/usr/bin/env python3
"""
BGP parser interfaces.
Defines standard interfaces for parsers that work with BGP protocol data.
"""

from typing import Dict, Any, List
from src.parsers.protocols.parser_interface import RoutingParser


class BgpParser(RoutingParser):
    """
    Parser for BGP protocol data.

    This class handles parsing BGP configuration and state data
    from OpenConfig models.
    """

    def get_protocol_type(self) -> str:
        """
        Get the type of routing protocol this parser handles.

        Returns:
            "bgp" as the protocol type
        """
        return "bgp"

    def process_protocol_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process extracted data into structured BGP protocol information.

        Args:
            data: Extracted data containing BGP information

        Returns:
            Dictionary with structured BGP information
        """
        result = {
            "protocol_type": self.get_protocol_type(),
            "enabled": False,
            "router_id": None,
            "as_number": None,
            "global_af": [],
            "neighbor_groups": [],
            "neighbors": [],
            "vrfs": [],
        }

        # Parse BGP data from extracted items
        for item in data.get("items", []):
            path = item.get("path", "")
            val = item.get("val", {})

            # Process BGP data based on path patterns
            # Implementation details should be provided by concrete classes

        return result

    def generate_summary(self, data: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of the BGP protocol data.

        Args:
            data: BGP protocol data to summarize

        Returns:
            String containing a human-readable summary of BGP state
        """
        if not data.get("enabled", False):
            return "BGP is not configured or enabled on this device."

        summary_lines = ["BGP Configuration Summary:"]

        # Add basic BGP information
        summary_lines.append(
            f"- AS Number: {data.get('as_number', 'Not configured')}"
        )
        summary_lines.append(
            f"- Router ID: {data.get('router_id', 'Not configured')}"
        )

        # Add neighbor information if available
        neighbors = data.get("neighbors", [])
        if neighbors:
            summary_lines.append(f"\nBGP Neighbors: {len(neighbors)}")
            for i, neighbor in enumerate(
                neighbors[:5]
            ):  # Show first 5 neighbors
                summary_lines.append(
                    f"- {neighbor.get('address')}: "
                    f"AS {neighbor.get('remote_as')}, "
                    f"State: {neighbor.get('session_state', 'Unknown')}"
                )

            if len(neighbors) > 5:
                summary_lines.append(
                    f"... and {len(neighbors) - 5} more neighbors"
                )

        return "\n".join(summary_lines)
