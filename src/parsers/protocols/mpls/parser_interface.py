#!/usr/bin/env python3
"""
MPLS parser interfaces.
Defines standard interfaces for parsers that work with MPLS data.
"""

from typing import Dict, Any, List
from src.parsers.protocols.parser_interface import MplsParser


class OpenConfigMplsParser(MplsParser):
    """
    Parser for MPLS data using OpenConfig model.

    This class handles parsing MPLS configuration and state data
    from OpenConfig YANG models.
    """

    def process_protocol_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process extracted data into structured MPLS information.

        Args:
            data: Extracted data containing MPLS information

        Returns:
            Dictionary with structured MPLS information
        """
        result = {
            "enabled": False,
            "label_blocks": [],
            "interfaces": ["NO_INTERFACES_CONFIGURED"],
            "global_settings": {},
        }

        for item in data.get("items", []):
            val = item.get("val", {})

            if "global" in val:
                global_data = val["global"]
                result["global_settings"] = self._parse_global_settings(
                    global_data
                )

                # Parse interfaces with MPLS enabled
                interface_list = []
                if (
                    "interface-attributes" in global_data
                    and "interface" in global_data["interface-attributes"]
                ):
                    interface_list = self._parse_interfaces(
                        global_data["interface-attributes"]
                    )

                # Replace default message only if we actually have interfaces
                if interface_list:
                    result["interfaces"] = interface_list
                    result["enabled"] = (
                        True  # If we have interfaces, MPLS is enabled
                    )

                # Parse label blocks
                label_blocks = []
                if (
                    "reserved-label-blocks" in global_data
                    and "reserved-label-block"
                    in global_data["reserved-label-blocks"]
                ):
                    label_blocks = self._parse_label_blocks(
                        global_data["reserved-label-blocks"]
                    )

                # If we have label blocks, update them, otherwise keep the default empty list
                if label_blocks:
                    result["label_blocks"] = label_blocks

        # Create a summary from the parsed data
        result["summary"] = self._create_summary(result)

        return result

    def _parse_global_settings(
        self, global_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse global MPLS settings."""
        settings = {}

        if "state" in global_data:
            state = global_data["state"]
            if "null-label" in state:
                settings["null_label"] = state["null-label"]
            if "ttl-propagation" in state:
                settings["ttl_propagation"] = state["ttl-propagation"]

        return settings

    def _parse_interfaces(
        self, interface_attributes: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Parse MPLS-enabled interfaces."""
        interfaces = []

        if "interface" in interface_attributes:
            for interface in interface_attributes["interface"]:
                interface_info = {
                    "name": interface.get("interface-id", "Unknown"),
                    "mpls_enabled": False,
                }

                if (
                    "state" in interface
                    and "mpls-enabled" in interface["state"]
                ):
                    interface_info["mpls_enabled"] = interface["state"][
                        "mpls-enabled"
                    ]

                interfaces.append(interface_info)

        return interfaces

    def _parse_label_blocks(
        self, label_blocks_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Parse MPLS label blocks."""
        label_blocks = []

        if "reserved-label-block" in label_blocks_data:
            for block in label_blocks_data["reserved-label-block"]:
                block_info = {
                    "lower_bound": block.get("lower-bound"),
                    "upper_bound": block.get("upper-bound"),
                    "description": block.get("description", ""),
                }
                label_blocks.append(block_info)

        return label_blocks

    def _create_summary(self, mpls_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of the MPLS data."""
        summary = {
            "enabled": mpls_data["enabled"],
            "interface_count": (
                len(mpls_data["interfaces"])
                if mpls_data["interfaces"] != ["NO_INTERFACES_CONFIGURED"]
                else 0
            ),
            "label_block_count": len(mpls_data["label_blocks"]),
        }

        # Add global settings summary
        global_settings = mpls_data["global_settings"]
        if global_settings:
            summary["ttl_propagation"] = global_settings.get(
                "ttl_propagation", False
            )

        return summary

    def generate_summary(self, data: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of the MPLS data.

        Args:
            data: MPLS data to summarize

        Returns:
            String containing a human-readable summary of MPLS configuration
        """
        if not data.get("enabled", False):
            return "MPLS is not configured or enabled on this device."

        summary_lines = ["MPLS Configuration Summary:"]

        # Global settings
        global_settings = data.get("global_settings", {})
        summary_lines.append(
            f"- TTL Propagation: {'Enabled' if global_settings.get('ttl_propagation', False) else 'Disabled'}"
        )

        # Label blocks
        label_blocks = data.get("label_blocks", [])
        if label_blocks:
            summary_lines.append(f"\nLabel Blocks: {len(label_blocks)}")
            for block in label_blocks:
                summary_lines.append(
                    f"- Range: {block.get('lower_bound')} - {block.get('upper_bound')}"
                    f" ({block.get('description', '')})"
                )

        # Interfaces
        interfaces = data.get("interfaces", [])
        if interfaces and interfaces != ["NO_INTERFACES_CONFIGURED"]:
            summary_lines.append(
                f"\nMPLS Enabled Interfaces: {len(interfaces)}"
            )
            for i, interface in enumerate(
                interfaces[:10]
            ):  # Show first 10 interfaces
                status = (
                    "Enabled"
                    if interface.get("mpls_enabled", False)
                    else "Disabled"
                )
                summary_lines.append(f"- {interface.get('name')}: {status}")

            if len(interfaces) > 10:
                summary_lines.append(
                    f"... and {len(interfaces) - 10} more interfaces"
                )
        else:
            summary_lines.append("\nNo MPLS enabled interfaces found")

        return "\n".join(summary_lines)
