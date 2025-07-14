#!/usr/bin/env python3
"""
Test case for MPLS parser - Testing non-configured MPLS scenario
"""

import unittest
from src.parsers.protocols.mpls.mpls_parser import (
    parse_mpls_data,
    generate_mpls_summary,
)


class TestMPLSParserNonConfigured(unittest.TestCase):
    """Test cases for MPLS parser module with non-configured MPLS."""

    def setUp(self):
        """Set up test fixtures."""
        # Sample data for a device where MPLS is not effectively configured
        # It has ttl-propagation set but no interfaces or label blocks
        self.test_data = {
            "response": [
                {
                    "path": "network-instances/network-instance[name=DEFAULT]/mpls",
                    "val": {"global": {"state": {"ttl-propagation": True}}},
                }
            ],
            "timestamp": 1745245365163493928,
        }

    def test_parse_non_configured_mpls_data(self):
        """Test parsing MPLS data when MPLS is not effectively configured."""
        # Extract the response data from test_data
        response_data = self.test_data["response"]
        parsed_data = parse_mpls_data(response_data)

        # Verify the parser correctly identified MPLS is not effectively enabled
        self.assertFalse(parsed_data["enabled"])

        # Verify global settings are parsed correctly
        self.assertIn("global_settings", parsed_data)
        self.assertTrue(parsed_data["global_settings"]["ttl_propagation"])

        # Verify label blocks have the default message
        self.assertEqual(len(parsed_data["label_blocks"]), 1)
        self.assertEqual(
            parsed_data["label_blocks"][0], "NO_LABEL_BLOCKS_CONFIGURED"
        )

        # Verify interfaces have the default message
        self.assertEqual(len(parsed_data["interfaces"]), 1)
        self.assertEqual(
            parsed_data["interfaces"][0], "NO_INTERFACES_CONFIGURED"
        )

    def test_generate_summary_non_configured_mpls(self):
        """Test generating a summary for non-configured MPLS."""
        # Extract the response data from test_data
        response_data = self.test_data["response"]
        parsed_data = parse_mpls_data(response_data)
        summary = generate_mpls_summary(parsed_data)

        # Verify the summary indicates MPLS is not effectively configured
        self.assertIn("MPLS is not effectively configured", summary)
        self.assertIn("no MPLS-enabled interfaces or label blocks", summary)


if __name__ == "__main__":
    unittest.main()
