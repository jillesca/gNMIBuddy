#!/usr/bin/env python3
"""
BGP Parser Test Script

This module contains tests for the BGP parser functionality with OpenConfig YANG.
"""

import json
import sys
import os
from pathlib import Path
import pytest

# Get the absolute path to the project root
project_root = str(Path(__file__).resolve().parents[4])
sys.path.insert(0, project_root)

from src.processors.protocols.bgp.config_processor import (
    parse_bgp_data,
    generate_bgp_summary,
    generate_simple_bgp_state_summary,
)


@pytest.fixture
def sample_openconfig_bgp_data():
    """
    Fixture to load the sample OpenConfig BGP data from test_bgp_parser_open_config.json.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.join(current_dir, "test_bgp_parser_open_config.json")

    try:
        with open(data_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        pytest.fail(f"Error: {data_file} file not found")
    except json.JSONDecodeError:
        pytest.fail(f"Error: {data_file} is not valid JSON")


def test_parse_openconfig_bgp_data(sample_openconfig_bgp_data):
    """
    Test that the OpenConfig BGP data is correctly parsed with the LLM-friendly format.
    """
    # Pass gNMI data directly to parser
    gnmi_data = sample_openconfig_bgp_data["response"]
    parsed_data = parse_bgp_data(gnmi_data)

    # Test basic structure
    assert isinstance(parsed_data, dict)
    assert "parse_error" not in parsed_data

    # Test router information
    assert "router" in parsed_data
    router = parsed_data["router"]
    assert router.get("as_number") == 100
    assert router.get("router_id") == "100.100.100.101"
    assert router.get("total_prefixes") == 57

    # Test Address Families
    assert "address_families" in parsed_data
    assert len(parsed_data["address_families"]) > 0

    # Find the L3VPN address family
    l3vpn_af = None
    for af in parsed_data["address_families"]:
        if af["name"] == "l3vpn_ipv4_unicast":
            l3vpn_af = af
            break

    assert l3vpn_af is not None
    assert "prefixes" in l3vpn_af

    # Test Neighbor Groups (peer groups)
    assert "neighbor_groups" in parsed_data
    assert len(parsed_data["neighbor_groups"]) == 2

    # Verify RR group
    rr_group = None
    for group in parsed_data["neighbor_groups"]:
        if group["name"] == "RR":
            rr_group = group
            break

    assert rr_group is not None
    assert rr_group["remote_as"] == 100
    assert rr_group["update_source"] == "Loopback0"

    # Test Neighbors
    assert "neighbors" in parsed_data
    assert len(parsed_data["neighbors"]) == 2

    # Test for specific neighbor details
    neighbor = next(
        (
            n
            for n in parsed_data["neighbors"]
            if n["address"] == "100.100.100.108"
        ),
        None,
    )
    assert neighbor is not None
    assert neighbor["group"] == "RR"
    assert neighbor["state"] == "ESTABLISHED"
    assert "uptime" in neighbor

    # Verify prefix counts for one neighbor
    assert "prefixes" in neighbor
    assert "l3vpn_ipv4_unicast" in neighbor["prefixes"]
    assert neighbor["prefixes"]["l3vpn_ipv4_unicast"]["received"] == 1
    assert neighbor["prefixes"]["l3vpn_ipv4_unicast"]["sent"] == 1

    # Test for VRF
    assert "vrfs" in parsed_data
    # Verify VRF 100 exists
    vrf_100 = next(
        (v for v in parsed_data["vrfs"] if v["name"] == "100"), None
    )
    assert vrf_100 is not None
    assert vrf_100["as_number"] == 100
    assert vrf_100["total_prefixes"] == 1

    # Check VRF address families
    assert "address_families" in vrf_100
    assert len(vrf_100["address_families"]) == 1
    assert vrf_100["address_families"][0]["name"] == "ipv4_unicast"


def test_generate_openconfig_bgp_summary(sample_openconfig_bgp_data):
    """
    Test that the OpenConfig BGP summary is correctly generated.
    """
    # Pass gNMI data directly to parser
    gnmi_data = sample_openconfig_bgp_data["response"]
    parsed_data = parse_bgp_data(gnmi_data)
    summary = generate_bgp_summary(parsed_data)

    # Test that the summary is a non-empty string
    assert isinstance(summary, str)
    assert len(summary) > 0

    # Test summary content
    assert "AS Number: 100" in summary
    assert "Router ID: 100.100.100.101" in summary
    assert "Total Prefixes:" in summary
    assert "Address Families:" in summary
    assert "Neighbor Groups:" in summary
    assert "* RR (Remote AS: 100)" in summary
    assert "* SR-PCE (Remote AS: 100)" in summary
    assert "Neighbors:" in summary

    # Updated test to match the new format which includes state information
    assert "100.100.100.107" in summary
    assert "100.100.100.108" in summary
    assert "ESTABLISHED" in summary

    # Test for uptime and prefix information
    assert "Up since:" in summary
    assert "l3vpn_ipv4_unicast: received" in summary

    assert "VRFs:" in summary
    assert "* 100" in summary


def test_parse_error_handling():
    """
    Test that the parser handles errors gracefully.
    """
    # Test with empty data
    empty_result = parse_bgp_data([])
    assert isinstance(empty_result, dict)
    assert "parse_error" in empty_result

    # Test with invalid data structure
    invalid_data = [{"invalid": "structure"}]
    invalid_result = parse_bgp_data(invalid_data)
    assert isinstance(invalid_result, dict)
    assert "parse_error" in invalid_result


def test_neighbor_state_extraction(sample_openconfig_bgp_data):
    """
    Test that neighbor state information is correctly extracted from OpenConfig data.
    """
    # Pass gNMI data directly to parser
    gnmi_data = sample_openconfig_bgp_data["response"]
    parsed_data = parse_bgp_data(gnmi_data)

    # Ensure we have neighbors
    assert "neighbors" in parsed_data
    assert len(parsed_data["neighbors"]) == 2

    # Test neighbor state information
    for neighbor in parsed_data["neighbors"]:
        # Verify basic state information
        assert "address" in neighbor
        assert "state" in neighbor
        assert neighbor["state"] == "ESTABLISHED"
        assert "uptime" in neighbor

        # Test prefix information for established sessions
        if neighbor["address"] == "100.100.100.108":
            assert "prefixes" in neighbor
            assert "l3vpn_ipv4_unicast" in neighbor["prefixes"]
            assert neighbor["prefixes"]["l3vpn_ipv4_unicast"]["received"] == 1
            assert neighbor["prefixes"]["l3vpn_ipv4_unicast"]["sent"] == 1


def test_simplified_bgp_state_summary(sample_openconfig_bgp_data):
    """
    Test that the simplified BGP state summary for small LLMs is correctly generated.
    """
    # Pass gNMI data directly to parser
    gnmi_data = sample_openconfig_bgp_data["response"]
    parsed_data = parse_bgp_data(gnmi_data)
    summary = generate_simple_bgp_state_summary(parsed_data)

    # Test that the summary is a non-empty string
    assert isinstance(summary, str)
    assert len(summary) > 0

    # Test summary content
    assert "BGP Router AS100" in summary
    assert "Router ID: 100.100.100.101" in summary
    assert "Total network prefixes:" in summary

    # Test neighbor state summary
    assert "Neighbor State Summary:" in summary
    assert "neighbors in ESTABLISHED state" in summary

    # Test neighbor details
    assert "Neighbor Details:" in summary
    assert "100.100.100.107 (AS100): ESTABLISHED" in summary
    assert "100.100.100.108 (AS100): ESTABLISHED" in summary

    # Test VRF summary information
    assert "VRF Summary:" in summary
    assert "VRF 100:" in summary


# This allows the script to be run directly for manual testing
if __name__ == "__main__":
    # Load the sample OpenConfig data
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.join(current_dir, "test_bgp_parser_open_config.json")

    try:
        with open(data_file, "r") as f:
            sample_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {data_file} file not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: {data_file} is not valid JSON")
        sys.exit(1)

    # Parse the BGP data
    gnmi_data = sample_data["response"]
    parsed_data = parse_bgp_data(gnmi_data)

    # Generate a readable summary
    summary = generate_bgp_summary(parsed_data)

    # Generate a simplified summary for small LLMs
    simple_summary = generate_simple_bgp_state_summary(parsed_data)

    # Print the results
    print("\n=== OpenConfig BGP Configuration and State Summary ===\n")
    print(summary)

    print("\n=== Simplified BGP State Summary (for small LLMs) ===\n")
    print(simple_summary)

    print("\n=== Detailed Parsed Data ===\n")
    print(json.dumps(parsed_data, indent=2))
