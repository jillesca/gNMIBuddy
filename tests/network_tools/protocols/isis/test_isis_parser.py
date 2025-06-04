#!/usr/bin/env python3
"""
Tests for the ISIS parser module.
"""

import json
import os
import sys
import unittest
from typing import Dict, Any

# Adding the project root to sys.path to import project modules
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
)

from src.parsers.protocols.isis.isis_parser import (
    parse_isis_data,
    generate_isis_summary,
)


class TestISISParser(unittest.TestCase):
    """Test cases for the ISIS parser module."""

    def setUp(self):
        """Set up test fixtures."""
        # Load test data from the test file
        test_file_path = os.path.join(
            os.path.dirname(__file__), "test_isis_parser_open_config.json"
        )
        with open(test_file_path, "r") as file:
            self.test_data = json.load(file)

        # Expected output from the parser for known test data
        self.expected_output = {
            "router_id": None,
            "net": "49.0100.0100.0100.0101.00",
            "level_capability": "LEVEL_1_2",
            "authentication_check": True,
            "segment_routing_enabled": True,
            "interfaces": [
                {
                    "name": "Loopback0",
                    "enabled": True,
                    "passive": True,
                    "circuit_type": "POINT_TO_POINT",
                    "levels": [
                        {
                            "level_number": 1,
                            "enabled": True,
                            "hello_authentication": False,
                        },
                        {
                            "level_number": 2,
                            "enabled": True,
                            "hello_authentication": False,
                        },
                    ],
                    "authentication_enabled": False,
                    "bfd_enabled": False,
                },
                {
                    "name": "GigabitEthernet0/0/0/0",
                    "enabled": True,
                    "passive": False,
                    "circuit_type": "POINT_TO_POINT",
                    "levels": [
                        {
                            "level_number": 1,
                            "enabled": True,
                            "hello_authentication": False,
                        }
                    ],
                    "authentication_enabled": False,
                    "bfd_enabled": False,
                },
                {
                    "name": "GigabitEthernet0/0/0/1",
                    "enabled": True,
                    "passive": False,
                    "circuit_type": "POINT_TO_POINT",
                    "levels": [
                        {
                            "level_number": 1,
                            "enabled": True,
                            "hello_authentication": False,
                        }
                    ],
                    "authentication_enabled": False,
                    "bfd_enabled": False,
                },
            ],
            "adjacencies": [
                {
                    "interface": "GigabitEthernet0/0/0/0",
                    "system_id": "0100.0100.0103",
                    "neighbor_ipv4": "100.101.103.103",
                    "neighbor_ipv6": "::",
                    "level": 1,
                    "adjacency_type": "LEVEL_1",
                    "state": "UP",
                    "area_address": ["49.0100"],
                },
                {
                    "interface": "GigabitEthernet0/0/0/1",
                    "system_id": "0100.0100.0105",
                    "neighbor_ipv4": "100.101.105.105",
                    "neighbor_ipv6": "::",
                    "level": 1,
                    "adjacency_type": "LEVEL_1",
                    "state": "UP",
                    "area_address": ["49.0100"],
                },
            ],
        }

        # Expected summary output sample
        self.expected_summary = """ISIS Router Information:
  Network Entity Title (NET): 49.0100.0100.0100.0101.00
  Level Capability: LEVEL_1_2
  Segment Routing: Enabled

ISIS Interfaces:
  Loopback0: Enabled, Passive
    Level-1: Enabled
    Level-2: Enabled
  GigabitEthernet0/0/0/0: Enabled, Active
    Level-1: Enabled
  GigabitEthernet0/0/0/1: Enabled, Active
    Level-1: Enabled

ISIS Adjacencies:
  GigabitEthernet0/0/0/0 -> 0100.0100.0103 (100.101.103.103)
    Level: 1, State: UP
  GigabitEthernet0/0/0/1 -> 0100.0100.0105 (100.101.105.105)
    Level: 1, State: UP"""

    def test_parse_isis_data(self):
        """Test parsing ISIS data from gNMI response."""
        parsed_data = parse_isis_data(self.test_data)

        # Verify basic structure
        self.assertIsInstance(parsed_data, dict)
        self.assertNotIn("error", parsed_data)

        # Compare with expected output
        # Note: This is a more comprehensive test than individual attribute checks
        self.assertEqual(parsed_data["net"], self.expected_output["net"])
        self.assertEqual(
            parsed_data["level_capability"],
            self.expected_output["level_capability"],
        )
        self.assertEqual(
            parsed_data["segment_routing_enabled"],
            self.expected_output["segment_routing_enabled"],
        )

        # Check interfaces count
        self.assertEqual(
            len(parsed_data["interfaces"]),
            len(self.expected_output["interfaces"]),
        )

        # Check Loopback0 interface
        loopback = next(
            (i for i in parsed_data["interfaces"] if i["name"] == "Loopback0"),
            None,
        )
        self.assertIsNotNone(loopback)
        self.assertTrue(loopback["enabled"])
        self.assertTrue(loopback["passive"])

        # Check that level data exists but doesn't contain metrics
        self.assertGreaterEqual(len(loopback["levels"]), 1)
        level = loopback["levels"][0]
        self.assertIn("level_number", level)
        self.assertNotIn("metrics", level)

        # Check adjacencies - there should be exactly 2 for our test data
        self.assertEqual(len(parsed_data["adjacencies"]), 2)

        # Check one adjacency
        adj = parsed_data["adjacencies"][0]
        self.assertEqual(adj["state"], "UP")
        self.assertIn(
            adj["interface"],
            ["GigabitEthernet0/0/0/0", "GigabitEthernet0/0/0/1"],
        )

        # Verify that removed fields don't exist
        self.assertNotIn("restart_support", adj)
        self.assertNotIn("nlpid", adj)

        # Save parsed data to a file for reference (useful for debugging)
        output_path = os.path.join(
            os.path.dirname(__file__), "isis_parser_output_sample.json"
        )
        with open(output_path, "w") as file:
            json.dump(parsed_data, file, indent=2)

    def test_generate_isis_summary(self):
        """Test generating a human-readable summary of ISIS status."""
        parsed_data = parse_isis_data(self.test_data)
        summary = generate_isis_summary(parsed_data)

        # Check if summary matches the expected format
        self.assertEqual(
            summary.strip().split("\n")[0], "ISIS Router Information:"
        )
        self.assertIn(
            "Network Entity Title (NET): 49.0100.0100.0100.0101.00", summary
        )
        self.assertIn("Level Capability: LEVEL_1_2", summary)
        self.assertIn("Segment Routing: Enabled", summary)
        self.assertIn("ISIS Interfaces:", summary)
        self.assertIn("ISIS Adjacencies:", summary)

        # Verify the summary mentions both neighbors
        self.assertIn("0100.0100.0103", summary)
        self.assertIn("0100.0100.0105", summary)

        # Save summary to a file for reference (useful for documentation)
        output_path = os.path.join(
            os.path.dirname(__file__), "isis_summary_output_sample.txt"
        )
        with open(output_path, "w") as file:
            file.write(summary)

    def test_empty_response(self):
        """Test handling of an empty response."""
        empty_data = {}
        parsed_data = parse_isis_data(empty_data)

        self.assertIn("error", parsed_data)

        summary = generate_isis_summary(parsed_data)
        self.assertIn("Error", summary)


if __name__ == "__main__":
    unittest.main()
