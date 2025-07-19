#!/usr/bin/env python3
"""
Test module for VRF parser.
Tests the functionality of the VRF parser with sample data to ensure it correctly extracts
route distinguishers (RD) and route targets (RT).
"""

import json
import os
import sys
from pathlib import Path
import datetime

import pytest

# Add the project root to the Python path
project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../..")
)
sys.path.insert(0, project_root)

from src.processors.protocols.vrf import (
    process_vrf_data,
    generate_llm_friendly_data,
)


@pytest.fixture
def vrf_test_data():
    """Load VRF test data from JSON file."""
    current_dir = Path(__file__).parent
    data_file = current_dir / "test_vrf_data.json"

    try:
        with open(data_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        pytest.fail(f"Error: {data_file} file not found")
    except json.JSONDecodeError:
        pytest.fail(f"Error: {data_file} is not valid JSON")


@pytest.fixture
def expected_parsed_data():
    """Load expected parsed VRF data from JSON file."""
    current_dir = Path(__file__).parent
    expected_file = current_dir / "expected_outputs" / "parsed_vrf_data.json"

    try:
        with open(expected_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        pytest.fail(f"Error: {expected_file} file not found")
    except json.JSONDecodeError:
        pytest.fail(f"Error: {expected_file} is not valid JSON")


@pytest.fixture
def expected_llm_friendly_data():
    """Load expected LLM-friendly VRF data from JSON file."""
    current_dir = Path(__file__).parent
    expected_file = (
        current_dir / "expected_outputs" / "llm_friendly_output.json"
    )

    try:
        with open(expected_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        pytest.fail(f"Error: {expected_file} file not found")
    except json.JSONDecodeError:
        pytest.fail(f"Error: {expected_file} is not valid JSON")


def test_process_vrf_data(vrf_test_data, expected_parsed_data):
    """Test that process_vrf_data correctly parses VRF data from gNMI response."""
    # Pass gNMI data directly to parser
    gnmi_data = vrf_test_data["response"]
    parsed_data = process_vrf_data(gnmi_data)

    # Update the timestamp in the expected data to match the current test run
    # This is needed because the timestamp is generated at runtime
    expected_parsed_data["timestamp"] = parsed_data["timestamp"]
    expected_parsed_data["timestamp_readable"] = parsed_data[
        "timestamp_readable"
    ]

    # Compare the parsed data with the expected output
    assert (
        parsed_data == expected_parsed_data
    ), "Parsed data does not match expected output"

    # Additional specific checks to ensure key fields are correctly extracted
    # Check VRF 100 details
    vrf_100 = next(
        (vrf for vrf in parsed_data["vrfs"] if vrf["name"] == "100"), None
    )
    assert vrf_100 is not None
    assert vrf_100["route_distinguisher"] == "100.100.100.101:100"  # RD value
    assert vrf_100["route_targets"]["import"] == ["100:100"]  # RT import value
    assert vrf_100["route_targets"]["export"] == ["100:100"]  # RT export value

    # Check BGP protocol details
    bgp_protocol = next(
        (
            p
            for p in vrf_100["protocols"]
            if p["type"] == "openconfig-policy-types:BGP"
        ),
        None,
    )
    assert bgp_protocol is not None
    assert bgp_protocol["details"]["as_number"] == 100
    assert bgp_protocol["details"]["router_id"] == "100.100.100.101"
    assert bgp_protocol["details"]["total_paths"] == 1
    assert bgp_protocol["details"]["total_prefixes"] == 1

    # Check static routes details in VRF Mgmt
    vrf_mgmt = next(
        (vrf for vrf in parsed_data["vrfs"] if vrf["name"] == "Mgmt"), None
    )
    assert vrf_mgmt is not None
    static_protocol = next(
        (p for p in vrf_mgmt["protocols"] if p["type"] == "static-routes"),
        None,
    )
    assert static_protocol is not None
    assert len(static_protocol["details"]["routes"]) == 1
    default_route = static_protocol["details"]["routes"][0]
    assert default_route["prefix"] == "0.0.0.0/0"
    assert len(default_route["next_hops"]) == 1
    assert default_route["next_hops"][0]["address"] == "198.18.128.1"


def test_generate_llm_friendly_data(vrf_test_data, expected_llm_friendly_data):
    """Test that generate_llm_friendly_data creates a simplified structure for LLMs."""
    # Extract the response array from the wrapped format
    gnmi_data = vrf_test_data["response"]
    parsed_data = process_vrf_data(gnmi_data)
    llm_data = generate_llm_friendly_data(parsed_data)

    # Update the timestamp in the expected data to match the current test run
    expected_llm_friendly_data["timestamp"] = llm_data["timestamp"]

    # Compare the generated LLM-friendly data with the expected output
    assert (
        llm_data == expected_llm_friendly_data
    ), "Generated LLM-friendly data does not match expected output"

    # Additional specific checks for VRF 100
    vrf_100 = next(
        (vrf for vrf in llm_data["vrfs"] if vrf["name"] == "100"), None
    )
    assert vrf_100 is not None
    assert vrf_100["rd"] == "100.100.100.101:100"

    # Check embedded protocol details
    bgp_protocol = next(
        (
            p
            for p in vrf_100["protocols"]
            if p["type"] == "openconfig-policy-types:BGP"
        ),
        None,
    )
    assert bgp_protocol is not None
    assert bgp_protocol["as_number"] == 100
    assert bgp_protocol["router_id"] == "100.100.100.101"
    assert bgp_protocol["paths"] == 1
    assert bgp_protocol["prefixes"] == 1

    # Check static routes in VRF Mgmt
    vrf_mgmt = next(
        (vrf for vrf in llm_data["vrfs"] if vrf["name"] == "Mgmt"), None
    )
    assert vrf_mgmt is not None
    static_protocol = next(
        (p for p in vrf_mgmt["protocols"] if p["type"] == "static-routes"),
        None,
    )
    assert static_protocol is not None
    assert len(static_protocol["routes"]) == 1
    assert static_protocol["routes"][0]["prefix"] == "0.0.0.0/0"
    assert (
        static_protocol["routes"][0]["next_hops"][0]["address"]
        == "198.18.128.1"
    )


# Create new fixtures to generate updated output files if needed
@pytest.fixture
def update_expected_outputs(request):
    """Fixture to update the expected output files with current parser output."""
    return request.config.getoption("--update-expected")
