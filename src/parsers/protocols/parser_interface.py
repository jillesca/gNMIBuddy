#!/usr/bin/env python3
"""
Protocol parser interfaces.
Defines standard interfaces for parsers that work with network protocol data.
"""

from typing import Dict, Any, Optional
from src.parsers.base import BaseParser


class ProtocolParser(BaseParser):
    """
    Base class for protocol data parsers.

    This class provides a consistent interface for extracting and transforming
    protocol data from OpenConfig models.
    """

    def transform_data(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform extracted protocol data into the final output format.

        Args:
            extracted_data: Data extracted from the gNMI response

        Returns:
            Transformed protocol data in the expected output format
        """
        # Initialize result structure with timestamp
        result = {
            "timestamp": extracted_data.get("timestamp"),
            "timestamp_readable": self.format_timestamp(
                extracted_data.get("timestamp")
            ),
        }

        # Process the extracted data into structured format
        processed_data = self.process_protocol_data(extracted_data)

        # Merge processed data into result
        result.update(processed_data)

        return result

    def extract_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract data from gNMI response structure.

        This method handles the common pattern of working with gNMI responses
        that contain a "response" array of path/value pairs.

        Args:
            data: Input data to extract from, expected to have a "response" key.

        Returns:
            Extracted data from the "response" field.

        Raises:
            ValueError: If "response" key is not found in data.
        """
        if "response" not in data:
            raise ValueError("Input data must contain a 'response' key.")
        return {"response": data["response"]}

    def parse(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse gNMI data through extraction and transformation."""
        extracted_data = self.extract_data(data)
        return self.transform_data(extracted_data)

    def format_timestamp(self, timestamp: Optional[int]) -> Optional[str]:
        """
        Format a numeric timestamp into a human-readable string.

        Args:
            timestamp: Numeric timestamp (nanoseconds since epoch)

        Returns:
            Formatted timestamp string or None
        """
        if timestamp is None:
            return None

        import time

        return time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(timestamp / 1e9)
        )

    def process_protocol_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process extracted data into structured protocol information.

        Args:
            data: Extracted data containing protocol information

        Returns:
            Dictionary with structured protocol information
        """
        raise NotImplementedError

    def generate_summary(self, data: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of the protocol data.

        Args:
            data: Protocol data to summarize

        Returns:
            String containing a human-readable summary
        """
        raise NotImplementedError


class MplsParser(ProtocolParser):
    """
    Parser for MPLS data.

    This class handles parsing MPLS configuration and state data
    from OpenConfig models.
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

        # Implementation should be provided by concrete classes
        return result


class VrfParser(ProtocolParser):
    """
    Parser for VRF data.

    This class handles parsing VRF configuration and state data
    from OpenConfig models.
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

        # Implementation should be provided by concrete classes
        return result


class RoutingParser(ProtocolParser):
    """
    Parser for routing protocol data.

    This class handles parsing routing protocol (BGP, ISIS, etc.) configuration
    and state data from OpenConfig models.
    """

    def process_protocol_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process extracted data into structured routing protocol information.

        Args:
            data: Extracted data containing routing protocol information

        Returns:
            Dictionary with structured routing protocol information
        """
        result = {
            "protocol_type": self.get_protocol_type(),
            "enabled": False,
            "router_id": None,
        }

        # Implementation should be provided by concrete classes
        return result

    def get_protocol_type(self) -> str:
        """
        Get the type of routing protocol this parser handles.

        Returns:
            String identifying the protocol type (e.g., "bgp", "isis")
        """
        raise NotImplementedError
