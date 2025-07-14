#!/usr/bin/env python3
"""
Test module for MPLS parser.
"""

import json
import os
import unittest
from src.processors.protocols.mpls.mpls_processor import (
    process_mpls_data,
    generate_mpls_summary,
)


class TestMPLSParser(unittest.TestCase):
    """Test cases for MPLS parser module."""

    def setUp(self):
        """Set up test fixtures."""
        # Get the directory of this test file
        self.current_dir = os.path.dirname(os.path.abspath(__file__))

        # Load test input data
        test_file = os.path.join(
            self.current_dir, "test_mpls_parser_open_config.json"
        )
        with open(test_file, "r") as f:
            self.test_data = json.load(f)

        # Load expected output data
        expected_output_file = os.path.join(
            self.current_dir, "expected_configured_mpls.json"
        )
        with open(expected_output_file, "r") as f:
            self.expected_output = json.load(f)

        # Load expected summary
        expected_summary_file = os.path.join(
            self.current_dir, "expected_configured_mpls_summary.txt"
        )
        with open(expected_summary_file, "r") as f:
            self.expected_summary = f.read().strip()

    def test_process_mpls_data(self):
        """Test parsing MPLS data from gNMI response."""
        # Pass gNMI data directly to parser
        gnmi_data = self.test_data["response"]
        parsed_data = process_mpls_data(gnmi_data)

        # Verify the parser correctly identified MPLS is enabled
        self.assertEqual(
            parsed_data["enabled"], self.expected_output["enabled"]
        )

        # Verify global settings are parsed correctly
        self.assertDictEqual(
            parsed_data["global_settings"],
            self.expected_output["global_settings"],
        )

        # Verify label blocks are parsed correctly
        self.assertEqual(
            len(parsed_data["label_blocks"]),
            len(self.expected_output["label_blocks"]),
        )
        for i, block in enumerate(parsed_data["label_blocks"]):
            expected_block = self.expected_output["label_blocks"][i]
            self.assertEqual(block["name"], expected_block["name"])
            self.assertEqual(
                block["lower_bound"], expected_block["lower_bound"]
            )
            self.assertEqual(
                block["upper_bound"], expected_block["upper_bound"]
            )

        # Verify interfaces are parsed correctly
        self.assertEqual(
            len(parsed_data["interfaces"]),
            len(self.expected_output["interfaces"]),
        )
        for i, interface in enumerate(parsed_data["interfaces"]):
            expected_interface = self.expected_output["interfaces"][i]
            self.assertEqual(interface["name"], expected_interface["name"])
            self.assertEqual(
                interface["mpls_enabled"], expected_interface["mpls_enabled"]
            )

    def test_generate_mpls_summary(self):
        """Test generating a human-readable summary of MPLS data."""
        # Pass gNMI data directly to parser
        gnmi_data = self.test_data["response"]
        parsed_data = process_mpls_data(gnmi_data)
        summary = generate_mpls_summary(parsed_data)

        # Verify the summary matches the expected output
        self.assertEqual(summary, self.expected_summary)


class TestMPLSParserNonConfigured(unittest.TestCase):
    """Test cases for MPLS parser module with non-configured MPLS."""

    def setUp(self):
        """Set up test fixtures."""
        # Get the directory of this test file
        self.current_dir = os.path.dirname(os.path.abspath(__file__))

        # Sample data for a device where MPLS is not effectively configured
        # It has ttl-propagation set but no interfaces or label blocks
        self.test_data = {
            "response": [
                {
                    "path": "network-instances/network-instance[name=DEFAULT]/mpls",
                    "val": {
                        "global": {
                            "state": {"ttl-propagation": True},
                            "interface-attributes": {"interface": []},
                            "reserved-label-blocks": {
                                "reserved-label-block": []
                            },
                        }
                    },
                }
            ],
            "timestamp": 1745245365163493928,
        }

        # Load expected output data
        expected_output_file = os.path.join(
            self.current_dir, "expected_non_configured_mpls.json"
        )
        with open(expected_output_file, "r") as f:
            self.expected_output = json.load(f)

        # Load expected summary
        expected_summary_file = os.path.join(
            self.current_dir, "expected_non_configured_mpls_summary.txt"
        )
        with open(expected_summary_file, "r") as f:
            self.expected_summary = f.read().strip()

    def test_parse_non_configured_mpls_data(self):
        """Test parsing MPLS data when MPLS is not effectively configured."""
        # Pass gNMI data directly to parser
        gnmi_data = self.test_data["response"]
        parsed_data = process_mpls_data(gnmi_data)

        # Verify the parser correctly identified MPLS is not effectively enabled
        self.assertEqual(
            parsed_data["enabled"], self.expected_output["enabled"]
        )

        # Verify global settings are parsed correctly
        self.assertDictEqual(
            parsed_data["global_settings"],
            self.expected_output["global_settings"],
        )

        # Verify label blocks have the default message
        self.assertEqual(
            parsed_data["label_blocks"], self.expected_output["label_blocks"]
        )

        # Verify interfaces have the default message
        self.assertEqual(
            parsed_data["interfaces"], self.expected_output["interfaces"]
        )

    def test_generate_summary_non_configured_mpls(self):
        """Test generating a summary for non-configured MPLS."""
        # Pass gNMI data directly to parser
        gnmi_data = self.test_data["response"]
        parsed_data = process_mpls_data(gnmi_data)
        summary = generate_mpls_summary(parsed_data)

        # Verify the summary matches the expected output
        self.assertEqual(summary, self.expected_summary)


if __name__ == "__main__":
    unittest.main()
