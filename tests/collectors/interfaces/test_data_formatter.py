#!/usr/bin/env python3
"""
Tests for the data_formatter module in parsers/interfaces.
"""
import json
import os
import pytest
from src.parsers.interfaces.data_formatter import (
    format_interface_data_for_llm,
    extract_interfaces,
    extract_interface_info,
    extract_ip_and_vrf_for_brief,
    calculate_interface_statistics,
    prefix_to_subnet_mask,
)


@pytest.fixture
def test_data_dir():
    """Return the path to the test data directory."""
    return os.path.dirname(os.path.realpath(__file__))


@pytest.fixture
def openconfig_data(test_data_dir):
    """Load OpenConfig interface data from JSON file."""
    with open(
        os.path.join(test_data_dir, "interfaces_open_config.json"), "r"
    ) as f:
        data = json.load(f)

        # Ensure VRF information exists for GigabitEthernet0/0/0/2
        for item in data["response"]:
            if "val" in item and "interface" in item["val"]:
                for interface in item["val"]["interface"]:
                    # Add VRF for GigabitEthernet0/0/0/2
                    if interface["name"] == "GigabitEthernet0/0/0/2":
                        if (
                            "subinterfaces" in interface
                            and "subinterface" in interface["subinterfaces"]
                        ):
                            subif = interface["subinterfaces"]["subinterface"][
                                0
                            ]
                            if (
                                "openconfig-network-instance:network-instance"
                                not in subif
                            ):
                                subif[
                                    "openconfig-network-instance:network-instance"
                                ] = [{"name": "100"}]

                    # Add VRF for MgmtEth0/RP0/CPU0/0
                    if interface["name"] == "MgmtEth0/RP0/CPU0/0":
                        if (
                            "subinterfaces" in interface
                            and "subinterface" in interface["subinterfaces"]
                        ):
                            subif = interface["subinterfaces"]["subinterface"][
                                0
                            ]
                            if (
                                "openconfig-network-instance:network-instance"
                                not in subif
                            ):
                                subif[
                                    "openconfig-network-instance:network-instance"
                                ] = [{"name": "Mgmt"}]

        return data


@pytest.fixture
def expected_output(test_data_dir):
    """Load expected output data from JSON file."""
    with open(
        os.path.join(test_data_dir, "_get_interface_brief_output.json"), "r"
    ) as f:
        return json.load(f)


def test_format_interface_data_for_llm(openconfig_data, expected_output):
    """Test the full formatting pipeline with OpenConfig data."""
    # Pass gNMI data directly to formatter
    gnmi_data = openconfig_data["response"]
    result = format_interface_data_for_llm(gnmi_data)

    # Sort interfaces by name for comparison, as order might differ
    result["interfaces"] = sorted(
        result["interfaces"], key=lambda x: x["name"]
    )
    expected_interfaces = sorted(
        expected_output["interfaces"], key=lambda x: x["name"]
    )

    # Compare interface data - names, statuses, and presence of IPs
    assert len(result["interfaces"]) >= len(expected_interfaces)
    for i, interface in enumerate(expected_interfaces):
        # Find corresponding interface in result
        matching_interfaces = [
            intf
            for intf in result["interfaces"]
            if intf["name"] == interface["name"]
        ]
        if matching_interfaces:
            result_interface = matching_interfaces[0]
            # Check basic properties
            assert result_interface["name"] == interface["name"]
            assert result_interface.get("admin_status") == interface.get(
                "admin_status"
            )
            assert result_interface.get("oper_status") == interface.get(
                "oper_status"
            )

            # Check if IP address exists if expected
            if "ip_address" in interface:
                assert "ip_address" in result_interface

            # Check if VRF exists if expected
            if "vrf" in interface:
                assert "vrf" in result_interface

    # Check summary statistics types
    for key in expected_output["summary"]:
        assert key in result["summary"]
        assert isinstance(result["summary"][key], int)


def test_extract_interfaces(openconfig_data):
    """Test extraction of interfaces from OpenConfig data."""
    gnmi_data = openconfig_data["response"]
    interfaces = extract_interfaces(gnmi_data)

    # Verify we extracted interfaces
    assert len(interfaces) > 0

    # Check basic structure of extracted interfaces
    for interface in interfaces:
        assert "name" in interface
        assert interface["name"]  # Name is not empty


def test_extract_interface_info():
    """Test extraction of information from a single interface."""
    # Create sample interface data
    interface_data = {
        "name": "GigabitEthernet0/0/0/0",
        "state": {
            "admin-status": "UP",
            "oper-status": "UP",
            "description": "test interface",
        },
        "subinterfaces": {
            "subinterface": [
                {
                    "index": 0,
                    "openconfig-if-ip:ipv4": {
                        "addresses": {
                            "address": [
                                {
                                    "ip": "192.168.1.1",
                                    "state": {
                                        "ip": "192.168.1.1",
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

    result = extract_interface_info(interface_data)

    # Verify extracted data
    assert result["name"] == "GigabitEthernet0/0/0/0"
    assert result["admin_status"] == "UP"
    assert result["oper_status"] == "UP"
    assert "ip_address" in result


def test_prefix_to_subnet_mask():
    """Test conversion of prefix length to subnet mask."""
    assert prefix_to_subnet_mask(24) == "255.255.255.0"
    assert prefix_to_subnet_mask(16) == "255.255.0.0"
    assert prefix_to_subnet_mask(8) == "255.0.0.0"
    assert prefix_to_subnet_mask(32) == "255.255.255.255"


def test_calculate_interface_statistics():
    """Test calculation of interface statistics."""
    interfaces = [
        {
            "name": "Loopback0",
            "admin_status": "UP",
            "oper_status": "UP",
            "ip_address": "10.0.0.1/255.255.255.255",
        },
        {
            "name": "GigabitEthernet0/0/0/0",
            "admin_status": "UP",
            "oper_status": "UP",
            "ip_address": "192.168.1.1/255.255.255.0",
        },
        {
            "name": "GigabitEthernet0/0/0/1",
            "admin_status": "UP",
            "oper_status": "DOWN",
        },
        {
            "name": "GigabitEthernet0/0/0/2",
            "admin_status": "DOWN",
            "oper_status": "DOWN",
            "ip_address": "10.1.1.1/255.255.255.0",
            "vrf": "VRF1",
        },
        {"name": "Null0", "admin_status": "UP", "oper_status": "UP"},
        {
            "name": "MgmtEth0/RP0/CPU0/0",
            "admin_status": "UP",
            "oper_status": "UP",
            "ip_address": "172.16.1.1/255.255.0.0",
            "vrf": "mgmt",
        },
    ]

    result = calculate_interface_statistics(interfaces)

    assert result["total_interfaces"] == 6
    assert result["admin_up"] == 5
    assert result["admin_down"] == 1
    assert result["oper_up"] == 4
    assert result["oper_down"] == 2
    assert result["with_ip"] == 4
    assert result["with_vrf"] == 2
