#!/usr/bin/env python3
"""
MPLS Processor module.
Processes MPLS data from gNMI responses and formats it for easier consumption by small LLMs.
"""

from typing import Dict, Any, List
from src.logging import get_logger

logger = get_logger(__name__)


def process_mpls_data(gnmi_response: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process MPLS data from gNMI response.

    Args:
        gnmi_response: List of gNMI response items containing MPLS configuration

    Returns:
        Dictionary containing the processed MPLS data in a simplified format for LLMs
    """
    logger.debug("Processing MPLS data from gNMI response")
    """
    Parse MPLS data from gNMI response.

    Args:
        gnmi_response: The gNMI response data (list of update dictionaries)

    Returns:
        Dictionary containing the parsed MPLS data in a simplified format for LLMs
    """
    logger.debug("Parsing MPLS data from gNMI response")

    processed_data = {
        "enabled": False,
        "label_blocks": [],
        "interfaces": [
            "NO_INTERFACES_CONFIGURED"
        ],  # Default message for empty interfaces
        "global_settings": {},
    }

    try:
        if not gnmi_response:
            return processed_data

        for item in gnmi_response:
            if "val" not in item:
                continue

            mpls_data = item["val"]
            if "global" in mpls_data:
                global_data = mpls_data["global"]
                processed_data["global_settings"] = _process_global_settings(
                    global_data
                )

                # Process interfaces with MPLS enabled
                interface_list = []
                if (
                    "interface-attributes" in global_data
                    and "interface" in global_data["interface-attributes"]
                ):
                    interface_list = _process_interfaces(
                        global_data["interface-attributes"]
                    )

                # Replace default message only if we actually have interfaces
                if interface_list:
                    processed_data["interfaces"] = interface_list

                # Process label blocks
                label_blocks = []
                if (
                    "reserved-label-blocks" in global_data
                    and "reserved-label-block"
                    in global_data["reserved-label-blocks"]
                ):
                    label_blocks = _process_label_blocks(
                        global_data["reserved-label-blocks"]
                    )

                # If we have label blocks, update them, otherwise keep the default empty list
                if label_blocks:
                    processed_data["label_blocks"] = label_blocks
                else:
                    processed_data["label_blocks"] = [
                        "NO_LABEL_BLOCKS_CONFIGURED"
                    ]

                # MPLS is considered effectively enabled only if it has interfaces or label blocks configured
                has_interfaces = interface_list and not (
                    len(interface_list) == 1
                    and interface_list[0] == "NO_INTERFACES_CONFIGURED"
                )
                has_label_blocks = label_blocks and not (
                    len(label_blocks) == 1
                    and label_blocks[0] == "NO_LABEL_BLOCKS_CONFIGURED"
                )

                # If both interface_list and label_blocks are empty lists, set enabled to False
                if (
                    isinstance(interface_list, list)
                    and len(interface_list) == 0
                    and isinstance(label_blocks, list)
                    and len(label_blocks) == 0
                ):
                    processed_data["enabled"] = False
                else:
                    processed_data["enabled"] = (
                        has_interfaces or has_label_blocks
                    )
    except (KeyError, ValueError, TypeError) as e:
        logger.error("Error processing MPLS data: %s", str(e))

    return processed_data


def _process_global_settings(global_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process global MPLS settings."""
    settings = {}

    if "state" in global_data:
        state = global_data["state"]
        if "null-label" in state:
            settings["null_label"] = state["null-label"]
        if "ttl-propagation" in state:
            settings["ttl_propagation"] = state["ttl-propagation"]

    return settings


def _process_interfaces(
    interface_attributes: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Process MPLS-enabled interfaces."""
    interfaces = []

    if "interface" in interface_attributes:
        for interface in interface_attributes["interface"]:
            interface_info = {
                "name": interface.get("interface-id", "Unknown"),
                "mpls_enabled": False,
            }

            if "state" in interface and "mpls-enabled" in interface["state"]:
                interface_info["mpls_enabled"] = interface["state"][
                    "mpls-enabled"
                ]

            interfaces.append(interface_info)

    return interfaces


def _process_label_blocks(
    label_blocks_data: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Process MPLS label blocks."""
    label_blocks = []

    if "reserved-label-block" in label_blocks_data:
        for block in label_blocks_data["reserved-label-block"]:
            block_info = {
                "name": block.get("local-id", "Unknown"),
                "lower_bound": None,
                "upper_bound": None,
            }

            if "state" in block:
                state = block["state"]
                if "lower-bound" in state:
                    block_info["lower_bound"] = state["lower-bound"]
                if "upper-bound" in state:
                    block_info["upper_bound"] = state["upper-bound"]

            label_blocks.append(block_info)

    return label_blocks


def generate_mpls_summary(mpls_data: Dict[str, Any]) -> str:
    """
    Generate a human-readable summary of MPLS data for small LLMs.

    Args:
        mpls_data: Parsed MPLS data

    Returns:
        String containing a summary of MPLS data in a format suitable for small LLMs
    """
    if not mpls_data["enabled"]:
        return "MPLS is not effectively configured on this device. While some global settings may exist, there are no MPLS-enabled interfaces or label blocks detected."

    summary_lines = ["MPLS Configuration Summary:"]

    # Global settings
    global_settings = mpls_data["global_settings"]
    summary_lines.append(
        f"- TTL Propagation: {'Enabled' if global_settings.get('ttl_propagation', False) else 'Disabled'}"
    )

    # Label blocks
    if mpls_data["label_blocks"]:
        summary_lines.append("\nMPLS Label Blocks:")
        for block in mpls_data["label_blocks"]:
            if "NO_LABEL_BLOCKS_CONFIGURED" in block:
                summary_lines.append("- No label blocks configured")
            else:
                summary_lines.append(
                    f"- {block['name']}: Range {block['lower_bound']}-{block['upper_bound']}"
                )

    # Interfaces
    mpls_interfaces = [
        interface
        for interface in mpls_data["interfaces"]
        if interface["mpls_enabled"]
    ]
    if mpls_interfaces:
        summary_lines.append("\nMPLS-Enabled Interfaces:")
        for interface in mpls_interfaces:
            summary_lines.append(f"- {interface['name']}")

    return "\n".join(summary_lines)
