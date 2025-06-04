#!/usr/bin/env python3
"""
Tests for the single_interface_parser module in parsers/interfaces.
"""
import json
import os
import pytest
from src.parsers.interfaces.single_interface_parser import (
    parse_single_interface_data,
    extract_interface_data,
    extract_single_interface,
    extract_ip_and_vrf,
)


@pytest.fixture
def test_data_dir():
    """Return the path to the test data directory."""
    return os.path.dirname(os.path.realpath(__file__))


@pytest.fixture
def openconfig_data(test_data_dir):
    """Load OpenConfig single interface data."""
    # Extract GigabitEthernet0/0/0/2 from the complete interfaces data
    with open(
        os.path.join(test_data_dir, "interfaces_open_config.json"), "r"
    ) as f:
        data = json.load(f)

        # Filter to just include GigabitEthernet0/0/0/2
        interface_data = None
        for item in data["response"]:
            if "val" in item and "interface" in item["val"]:
                for interface in item["val"]["interface"]:
                    if interface["name"] == "GigabitEthernet0/0/0/2":
                        interface_data = interface.copy()
                        # Add VRF information to the interface data
                        # in the format the parser expects
                        if (
                            "subinterfaces" in interface_data
                            and "subinterface"
                            in interface_data["subinterfaces"]
                        ):
                            subif = interface_data["subinterfaces"][
                                "subinterface"
                            ][0]
                            if (
                                "openconfig-network-instance:network-instance"
                                not in subif
                            ):
                                subif[
                                    "openconfig-network-instance:network-instance"
                                ] = [{"name": "100"}]
                        break
                if interface_data:
                    break

        # Construct a simulated response containing just this interface
        filtered_data = {
            "response": [
                {
                    "path": "interfaces/interface[name=GigabitEthernet0/0/0/2]",
                    "val": interface_data,
                }
            ],
            "timestamp": data["timestamp"],
        }

        return filtered_data


@pytest.fixture
def expected_output(test_data_dir):
    """Load expected output data from JSON file."""
    with open(
        os.path.join(test_data_dir, "_single_interface_parser_output.json"),
        "r",
    ) as f:
        data = json.load(f)

        # Update the expected output to match the interface being tested
        data["interface"]["name"] = "GigabitEthernet0/0/0/2"
        data["interface"]["description"] = None
        data["interface"]["ip_address"] = "10.1.1.3"
        data["interface"]["prefix_length"] = 24
        data["interface"][
            "vrf"
        ] = "100"  # Set VRF to match what's in the test data
        data["interface"]["mac_address"] = "02:42:ac:14:00:02"
        data["interface"]["counters"]["in_packets"] = "310"
        data["interface"]["counters"]["out_packets"] = "1"

        return data


def test_parse_single_interface_data(openconfig_data, expected_output):
    """Test the full interface parsing function with OpenConfig data."""
    result = parse_single_interface_data(openconfig_data)

    # Verify the overall structure
    assert "interface" in result
    assert "timestamp" in result

    # Timestamp may be different between test runs, so just check it exists
    assert isinstance(result["timestamp"], int)

    # Verify interface details
    interface = result["interface"]
    expected_interface = expected_output["interface"]

    assert interface["name"] == expected_interface["name"]
    assert interface["admin_state"] == expected_interface["admin_state"]
    assert interface["oper_state"] == expected_interface["oper_state"]
    assert interface["ip_address"] == expected_interface["ip_address"]
    assert interface["prefix_length"] == expected_interface["prefix_length"]
    assert interface["vrf"] == expected_interface["vrf"]
    assert interface["mtu"] == expected_interface["mtu"]
    assert interface["mac_address"] == expected_interface["mac_address"]
    assert interface["speed"] == expected_interface["speed"]
    assert interface["duplex"] == expected_interface["duplex"]

    # Verify the interface counters
    assert (
        interface["counters"]["in_packets"]
        == expected_interface["counters"]["in_packets"]
    )
    assert (
        interface["counters"]["out_packets"]
        == expected_interface["counters"]["out_packets"]
    )
    assert (
        interface["counters"]["in_errors"]
        == expected_interface["counters"]["in_errors"]
    )
    assert (
        interface["counters"]["out_errors"]
        == expected_interface["counters"]["out_errors"]
    )


def test_extract_interface_data(openconfig_data):
    """Test extraction of interface data from OpenConfig response."""
    # Initialize a result structure
    result = {
        "interface": {
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
        },
        "timestamp": openconfig_data["timestamp"],
    }

    # Extract the interface data
    extract_interface_data(openconfig_data, result)

    # Verify key fields were extracted
    assert result["interface"]["name"] == "GigabitEthernet0/0/0/2"
    assert result["interface"]["admin_state"] == "UP"
    assert result["interface"]["oper_state"] == "UP"
    assert result["interface"]["mtu"] == 1514
    assert result["interface"]["mac_address"] == "02:42:ac:14:00:02"
    assert result["interface"]["speed"] == "SPEED_1GB"
    assert result["interface"]["duplex"] == "FULL"


def test_extract_single_interface():
    """Test extraction of data from a single interface object."""
    # Sample interface data
    interface_data = {
        "name": "GigabitEthernet0/0/0/2",
        "state": {
            "name": "GigabitEthernet0/0/0/2",
            "admin-status": "UP",
            "oper-status": "UP",
            "mtu": 1514,
            "counters": {
                "in-pkts": "310",
                "out-pkts": "1",
                "in-errors": "0",
                "out-errors": "0",
            },
        },
        "openconfig-if-ethernet:ethernet": {
            "state": {
                "mac-address": "02:42:ac:14:00:02",
                "duplex-mode": "FULL",
                "port-speed": "SPEED_1GB",
            }
        },
        "subinterfaces": {
            "subinterface": [
                {
                    "index": 0,
                    "openconfig-if-ip:ipv4": {
                        "addresses": {
                            "address": [
                                {
                                    "ip": "10.1.1.3",
                                    "state": {
                                        "ip": "10.1.1.3",
                                        "prefix-length": 24,
                                    },
                                }
                            ]
                        }
                    },
                }
            ]
        },
    }

    # Initialize a result structure
    result = {
        "interface": {
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
        },
        "timestamp": 12345678,
    }

    # Extract data
    extract_single_interface(interface_data, result)

    # Verify extraction
    assert result["interface"]["name"] == "GigabitEthernet0/0/0/2"
    assert result["interface"]["admin_state"] == "UP"
    assert result["interface"]["oper_state"] == "UP"
    assert result["interface"]["mtu"] == 1514
    assert result["interface"]["mac_address"] == "02:42:ac:14:00:02"
    assert result["interface"]["speed"] == "SPEED_1GB"
    assert result["interface"]["duplex"] == "FULL"
    assert result["interface"]["counters"]["in_packets"] == "310"
    assert result["interface"]["counters"]["out_packets"] == "1"
    assert result["interface"]["counters"]["in_errors"] == "0"
    assert result["interface"]["counters"]["out_errors"] == "0"


def test_extract_ip_and_vrf():
    """Test extraction of IP and VRF information."""
    # Sample subinterface data
    subinterface_data = {
        "index": 0,
        "openconfig-if-ip:ipv4": {
            "addresses": {
                "address": [
                    {
                        "ip": "10.1.1.3",
                        "state": {"ip": "10.1.1.3", "prefix-length": 24},
                    }
                ]
            }
        },
        "openconfig-network-instance:network-instance": [{"name": "100"}],
    }

    # Initialize a result structure
    result = {
        "interface": {
            "name": "GigabitEthernet0/0/0/2",
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
        },
        "timestamp": 12345678,
    }

    # Extract data
    extract_ip_and_vrf(subinterface_data, result)

    # Verify extraction
    assert result["interface"]["ip_address"] == "10.1.1.3"
    assert result["interface"]["prefix_length"] == 24
    assert result["interface"]["vrf"] == "100"


def test_interface_brief_data_compatibility(test_data_dir):
    """
    Test if the parser can handle the interface brief data format from OpenConfig.
    This ensures compatibility with different data formats.
    """
    # Load the OpenConfig interfaces data
    with open(
        os.path.join(test_data_dir, "interfaces_open_config.json"), "r"
    ) as f:
        oc_data = json.load(f)

    # Process the data through our parser
    result = parse_single_interface_data(oc_data)

    # Basic verification - we should get some kind of interface data
    assert "interface" in result
    assert result["interface"]["name"] is not None

    # The parser should default to the first interface in the list if multiple are present
    # as long as at least some data is extracted (like admin/oper state), the test passes
    assert result["interface"]["admin_state"] is not None
    assert result["interface"]["oper_state"] is not None
