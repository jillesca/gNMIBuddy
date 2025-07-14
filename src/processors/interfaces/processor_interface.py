#!/usr/bin/env python3
"""
Interface data processor interfaces.
Defines standard interfaces for processors that work with interface data.
"""

from typing import Dict, Any, List, Optional
from src.processors.base import BaseProcessor


class InterfaceProcessor(BaseProcessor):
    """
    Base class for interface data processors.

    This class provides a consistent interface for extracting and transforming
    interface data from OpenConfig models.
    """

    def transform_data(
        self, extracted_data: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        """
        Transform extracted interface data into the final output format.

        Args:
            extracted_data: Data extracted from the gNMI response

        Returns:
            Transformed interface data in the expected output format
        """
        # Initialize result structure with timestamp
        result = {"timestamp": extracted_data.get("timestamp")}

        # Extract and process interfaces from the data
        interfaces = self.process_interfaces(extracted_data)

        # Populate result with processed interfaces
        if self.is_single_interface():
            if interfaces and len(interfaces) > 0:
                result["interface"] = interfaces[0]
            else:
                result["interface"] = self.get_empty_interface()
        else:
            result["interfaces"] = interfaces
            result["summary"] = self.calculate_statistics(interfaces)

        return result

    def extract_data(self, gnmi_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract data from raw gNMI response data.

        This method processes the raw gNMI response data directly.
        It creates a structured format suitable for interface processing.

        Args:
            gnmi_data: Raw gNMI response data (list of update dictionaries)

        Returns:
            Structured data ready for interface processing with 'items' key
        """
        return {"items": gnmi_data if gnmi_data else []}

    def process_data(self, gnmi_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse gNMI data through extraction and transformation."""
        extracted_data = self.extract_data(gnmi_data)
        return self.transform_data(extracted_data)

    def process_interfaces(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process extracted data into a list of interface objects.

        Args:
            data: Extracted data containing interface information

        Returns:
            List of interface dictionaries with standardized structure
        """
        interfaces = []

        for item in data.get("items", []):
            # Skip items without values
            if not item.get("val"):
                continue

            # Extract interface data based on the path pattern
            interface = self.extract_interface(item)
            if interface:
                interfaces.append(interface)

        return interfaces

    def extract_interface(
        self, item: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Extract a single interface from an item in the response.

        Args:
            item: Single item from the response data

        Returns:
            Interface dictionary or None if not an interface
        """
        # Should be implemented by child classes
        raise NotImplementedError

    def is_single_interface(self) -> bool:
        """
        Determine if the parser is for a single interface or multiple interfaces.

        Returns:
            True if the parser is for a single interface, False otherwise
        """
        # Should be overridden by child classes
        return False

    def get_empty_interface(self) -> Dict[str, Any]:
        """
        Get an empty interface structure with default values.

        Returns:
            Dictionary with default interface structure
        """
        # Should be implemented by child classes
        raise NotImplementedError

    def calculate_statistics(
        self, interfaces: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate summary statistics for a list of interfaces.

        Args:
            interfaces: List of interface dictionaries

        Returns:
            Dictionary containing summary statistics
        """
        # Should be implemented by child classes
        raise NotImplementedError


class SingleInterfaceProcessor(InterfaceProcessor):
    """
    Parser for single interface data.

    This class specifically handles parsing data for a single interface,
    providing more detailed information about that interface.
    """

    def is_single_interface(self) -> bool:
        """
        Always returns True since this parser is for single interfaces.

        Returns:
            True
        """
        return True

    def get_empty_interface(self) -> Dict[str, Any]:
        """
        Get an empty interface structure with default values.

        Returns:
            Dictionary with default interface structure for a single interface
        """
        return {
            "name": None,
            "admin_state": None,
            "oper_state": None,
            "description": None,
            "ip_address": None,
            "prefix_length": None,
            "vrf": None,
            "mtu": None,
            "mac_address": None,
            "speed": None,
            "duplex": None,
            "counters": {
                "in_packets": None,
                "out_packets": None,
                "in_errors": None,
                "out_errors": None,
            },
        }

    def calculate_statistics(
        self, interfaces: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Not used for single interfaces.

        Args:
            interfaces: List of interface dictionaries

        Returns:
            Empty dictionary since statistics aren't needed for single interfaces
        """
        return {}


class InterfaceBriefProcessor(InterfaceProcessor):
    """
    Parser for interface brief data.

    This class handles parsing data for multiple interfaces,
    focusing on key summary information about each interface.
    """

    def is_single_interface(self) -> bool:
        """
        Always returns False since this parser is for multiple interfaces.

        Returns:
            False
        """
        return False

    def get_empty_interface(self) -> Dict[str, Any]:
        """
        Get an empty interface structure with default values.

        Returns:
            Dictionary with default interface structure for brief output
        """
        return {
            "name": None,
            "admin_status": None,
            "oper_status": None,
            "ip_address": None,
            "vrf": None,
        }

    def calculate_statistics(
        self, interfaces: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate summary statistics for a list of interfaces.

        Args:
            interfaces: List of interface dictionaries

        Returns:
            Dictionary containing summary statistics for interface brief
        """
        stats = {
            "total_interfaces": len(interfaces),
            "admin_up": 0,
            "admin_down": 0,
            "oper_up": 0,
            "oper_down": 0,
            "with_ip": 0,
            "with_vrf": 0,
        }

        for interface in interfaces:
            # Count admin status stats
            if interface.get("admin_status") == "UP":
                stats["admin_up"] += 1
            elif interface.get("admin_status") == "DOWN":
                stats["admin_down"] += 1

            # Count operational status stats
            if interface.get("oper_status") == "UP":
                stats["oper_up"] += 1
            elif interface.get("oper_status") == "DOWN":
                stats["oper_down"] += 1

            # Count interfaces with IP and VRF
            if interface.get("ip_address"):
                stats["with_ip"] += 1

            if interface.get("vrf"):
                stats["with_vrf"] += 1

        return stats
