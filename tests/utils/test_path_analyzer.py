#!/usr/bin/env python3
"""
Unit tests for path analyzer utility.

Tests the path analysis functionality for extracting OpenConfig models
from gNMI paths.
"""

from src.utils.path_analyzer import (
    extract_model_from_path,
    extract_models_from_paths,
    is_openconfig_path,
    get_model_name_from_path,
)
from src.schemas.openconfig_models import OpenConfigModel


class TestExtractModelFromPath:
    """Test extract_model_from_path function."""

    def test_system_paths(self):
        """Test extraction of system model from various path formats."""
        system_paths = [
            "openconfig-system:/system",
            "openconfig-system:system",
            "openconfig-system:/system/config",
            "openconfig-system:/system/state",
            "/system/config",
            "/system",
        ]

        for path in system_paths:
            model = extract_model_from_path(path)
            assert model == OpenConfigModel.SYSTEM, f"Failed for path: {path}"

    def test_interfaces_paths(self):
        """Test extraction of interfaces model from various path formats."""
        interfaces_paths = [
            "openconfig-interfaces:interfaces",
            "openconfig-interfaces:/interfaces",
            "openconfig-interfaces:interfaces/interface[name=*]",
            "openconfig-interfaces:interfaces/interface[name=GigabitEthernet0/0/0]",
            "/interfaces/interface[name=*]",
            "/interfaces",
        ]

        for path in interfaces_paths:
            model = extract_model_from_path(path)
            assert (
                model == OpenConfigModel.INTERFACES
            ), f"Failed for path: {path}"

    def test_network_instance_paths(self):
        """Test extraction of network instance model from various path formats."""
        network_instance_paths = [
            "openconfig-network-instance:network-instances",
            "openconfig-network-instance:network-instances/network-instance[name=*]",
            "openconfig-network-instance:network-instances/network-instance[name=default]",
            "openconfig-network-instance:network-instances/network-instance[name=*]/protocols/protocol/bgp",
            "openconfig-network-instance:network-instances/network-instance[name=*]/protocols/protocol/isis",
            "openconfig-network-instance:network-instances/network-instance[name=*]/mpls",
            "/network-instances/network-instance[name=*]",
            "network-instance[name=default]",
        ]

        for path in network_instance_paths:
            model = extract_model_from_path(path)
            assert (
                model == OpenConfigModel.NETWORK_INSTANCE
            ), f"Failed for path: {path}"

    def test_real_collector_paths(self):
        """Test extraction from real paths used in collectors."""
        # From system collector
        assert (
            extract_model_from_path("openconfig-system:/system")
            == OpenConfigModel.SYSTEM
        )

        # From interfaces collector
        assert (
            extract_model_from_path("openconfig-interfaces:interfaces")
            == OpenConfigModel.INTERFACES
        )
        assert (
            extract_model_from_path(
                "openconfig-interfaces:interfaces/interface[name=GigabitEthernet0/0/0]"
            )
            == OpenConfigModel.INTERFACES
        )

        # From routing collector
        assert (
            extract_model_from_path(
                "openconfig-network-instance:network-instances/network-instance[name=*]/protocols/protocol/isis/interfaces/"
            )
            == OpenConfigModel.NETWORK_INSTANCE
        )
        assert (
            extract_model_from_path(
                "openconfig-network-instance:network-instances/network-instance[name=*]/protocols/protocol/bgp"
            )
            == OpenConfigModel.NETWORK_INSTANCE
        )

        # From VPN collector
        assert (
            extract_model_from_path(
                "openconfig-network-instance:network-instances/network-instance[name=*]/state/name"
            )
            == OpenConfigModel.NETWORK_INSTANCE
        )

        # From MPLS collector
        assert (
            extract_model_from_path(
                "openconfig-network-instance:network-instances/network-instance[name=*]/mpls"
            )
            == OpenConfigModel.NETWORK_INSTANCE
        )

        # From profile collector
        assert (
            extract_model_from_path(
                "openconfig-network-instance:network-instances/network-instance[name=*]/protocols/protocol/bgp/global/afi-safis/afi-safi[name=*]/state"
            )
            == OpenConfigModel.NETWORK_INSTANCE
        )

    def test_invalid_paths(self):
        """Test paths that should return None."""
        invalid_paths = [
            "",
            None,
            "invalid-path",
            "not-openconfig:/path",
            "random-string",
            "/some/random/path",
            "openconfig-unknown:path",
        ]

        for path in invalid_paths:
            model = extract_model_from_path(path)
            assert model is None, f"Should return None for path: {path}"

    def test_edge_cases(self):
        """Test edge cases for path analysis."""
        # Whitespace handling
        assert (
            extract_model_from_path("  openconfig-system:/system  ")
            == OpenConfigModel.SYSTEM
        )

        # Case sensitivity
        assert (
            extract_model_from_path("openconfig-system:/system")
            == OpenConfigModel.SYSTEM
        )

        # Empty string
        assert extract_model_from_path("") is None

        # Non-string input
        assert extract_model_from_path(None) is None


class TestExtractModelsFromPaths:
    """Test extract_models_from_paths function."""

    def test_mixed_paths(self):
        """Test extraction from mixed OpenConfig paths."""
        paths = [
            "openconfig-system:/system",
            "openconfig-interfaces:interfaces",
            "openconfig-network-instance:network-instances/network-instance[name=*]",
            "invalid-path",
        ]

        models = extract_models_from_paths(paths)
        expected_models = {
            OpenConfigModel.SYSTEM,
            OpenConfigModel.INTERFACES,
            OpenConfigModel.NETWORK_INSTANCE,
        }

        assert models == expected_models

    def test_duplicate_models(self):
        """Test that duplicate models are handled correctly."""
        paths = [
            "openconfig-system:/system",
            "openconfig-system:/system/config",
            "openconfig-system:/system/state",
        ]

        models = extract_models_from_paths(paths)
        assert models == {OpenConfigModel.SYSTEM}

    def test_empty_paths(self):
        """Test extraction from empty path list."""
        models = extract_models_from_paths([])
        assert models == set()

    def test_all_invalid_paths(self):
        """Test extraction from all invalid paths."""
        paths = ["invalid", "not-openconfig", "random"]
        models = extract_models_from_paths(paths)
        assert models == set()


class TestIsOpenConfigPath:
    """Test is_openconfig_path function."""

    def test_valid_openconfig_paths(self):
        """Test valid OpenConfig paths."""
        valid_paths = [
            "openconfig-system:/system",
            "openconfig-interfaces:interfaces",
            "openconfig-network-instance:network-instances",
            "/system",
            "/interfaces",
            "/network-instances",
            "network-instance[name=default]",
            "/protocols/protocol",
            "/afi-safis/afi-safi",
        ]

        for path in valid_paths:
            assert is_openconfig_path(
                path
            ), f"Should be OpenConfig path: {path}"

    def test_invalid_paths(self):
        """Test invalid OpenConfig paths."""
        invalid_paths = [
            "",
            None,
            "invalid-path",
            "not-openconfig:/path",
            "random-string",
            "/some/random/path",
        ]

        for path in invalid_paths:
            assert not is_openconfig_path(
                path
            ), f"Should not be OpenConfig path: {path}"


class TestGetModelNameFromPath:
    """Test get_model_name_from_path function."""

    def test_valid_paths(self):
        """Test extraction of model names from valid paths."""
        test_cases = [
            ("openconfig-system:/system", "openconfig-system"),
            ("openconfig-interfaces:interfaces", "openconfig-interfaces"),
            (
                "openconfig-network-instance:network-instances",
                "openconfig-network-instance",
            ),
            ("/system", "openconfig-system"),
            ("/interfaces", "openconfig-interfaces"),
            ("network-instance[name=default]", "openconfig-network-instance"),
        ]

        for path, expected_name in test_cases:
            name = get_model_name_from_path(path)
            assert (
                name == expected_name
            ), f"Path {path} should return {expected_name}, got {name}"

    def test_invalid_paths(self):
        """Test extraction from invalid paths."""
        invalid_paths = ["", None, "invalid-path", "not-openconfig:/path"]

        for path in invalid_paths:
            name = get_model_name_from_path(path)
            assert name is None, f"Should return None for path: {path}"


class TestAdvancedPathAnalysis:
    """Test advanced path analysis scenarios."""

    def test_complex_path_structures(self):
        """Test extraction from complex path structures."""
        complex_paths = [
            "openconfig-network-instance:network-instances/network-instance[name='default']/protocols/protocol[identifier='ISIS'][name='100']",
            "openconfig-interfaces:interfaces/interface[name='GigabitEthernet0/0/0/0']/subinterfaces/subinterface[index='0']/state",
            "openconfig-system:system/config/hostname",
        ]

        expected_models = [
            OpenConfigModel.NETWORK_INSTANCE,
            OpenConfigModel.INTERFACES,
            OpenConfigModel.SYSTEM,
        ]

        for path, expected_model in zip(complex_paths, expected_models):
            model = extract_model_from_path(path)
            assert model == expected_model, f"Failed for complex path: {path}"

    def test_path_with_special_characters(self):
        """Test paths with special characters and edge cases."""
        special_paths = [
            "openconfig-system:/system/config/hostname",
            "openconfig-interfaces@interfaces/interface[name='Eth0/0/0']",
            "openconfig-network-instance#network-instances/network-instance[name='VRF_A']",
        ]

        # The @ and # characters should not break the extraction
        for path in special_paths:
            model = extract_model_from_path(path)
            assert (
                model is not None
            ), f"Failed to extract model from path with special chars: {path}"

    def test_path_with_wildcards(self):
        """Test paths with wildcards and array indices."""
        wildcard_paths = [
            "openconfig-interfaces:interfaces/interface[name=*]/state",
            "openconfig-network-instance:network-instances/network-instance[name=*]/protocols/protocol[identifier=*]",
            "openconfig-system:system/*",
        ]

        expected_models = [
            OpenConfigModel.INTERFACES,
            OpenConfigModel.NETWORK_INSTANCE,
            OpenConfigModel.SYSTEM,
        ]

        for path, expected_model in zip(wildcard_paths, expected_models):
            model = extract_model_from_path(path)
            assert model == expected_model, f"Failed for wildcard path: {path}"

    def test_path_normalization(self):
        """Test that paths are properly normalized."""
        normalized_paths = [
            "  openconfig-system:/system/config  ",  # Leading/trailing spaces
            "\topenconfig-interfaces:interfaces/interface\n",  # Tab and newline
            "openconfig-network-instance:network-instances",  # No trailing slash
        ]

        for path in normalized_paths:
            model = extract_model_from_path(path)
            assert model is not None, f"Failed to normalize path: {repr(path)}"

    def test_invalid_path_handling(self):
        """Test handling of invalid or malformed paths."""
        invalid_paths = [
            "",  # Empty string
            "   ",  # Whitespace only
            "not-openconfig-model:something",  # Non-OpenConfig model
            "openconfig-:interfaces",  # Malformed model name
            "openconfig-unknown-model:something",  # Unknown model
        ]

        for path in invalid_paths:
            model = extract_model_from_path(path)
            assert model is None, f"Expected None for invalid path: {path}"


class TestMultipleModelsExtraction:
    """Test extraction of multiple models from path lists."""

    def test_extract_models_from_multiple_paths(self):
        """Test extraction from multiple paths."""
        paths = [
            "openconfig-system:/system/config",
            "openconfig-interfaces:interfaces/interface[name='eth0']",
            "openconfig-network-instance:network-instances/network-instance[name='default']",
        ]

        models = extract_models_from_paths(paths)
        expected_models = {
            OpenConfigModel.SYSTEM,
            OpenConfigModel.INTERFACES,
            OpenConfigModel.NETWORK_INSTANCE,
        }

        assert models == expected_models

    def test_extract_models_with_duplicates(self):
        """Test extraction with duplicate models."""
        paths = [
            "openconfig-system:/system/config",
            "openconfig-system:/system/state",
            "openconfig-interfaces:interfaces/interface[name='eth0']",
            "openconfig-interfaces:interfaces/interface[name='eth1']",
        ]

        models = extract_models_from_paths(paths)
        expected_models = {
            OpenConfigModel.SYSTEM,
            OpenConfigModel.INTERFACES,
        }

        assert models == expected_models
        assert len(models) == 2  # Should deduplicate

    def test_extract_models_with_invalid_paths(self):
        """Test extraction with mix of valid and invalid paths."""
        paths = [
            "openconfig-system:/system/config",
            "invalid-path",
            "openconfig-interfaces:interfaces/interface[name='eth0']",
            "",  # Empty path
            "openconfig-network-instance:network-instances/network-instance[name='default']",
        ]

        models = extract_models_from_paths(paths)
        expected_models = {
            OpenConfigModel.SYSTEM,
            OpenConfigModel.INTERFACES,
            OpenConfigModel.NETWORK_INSTANCE,
        }

        assert models == expected_models

    def test_extract_models_from_empty_list(self):
        """Test extraction from empty path list."""
        models = extract_models_from_paths([])
        assert models == set()


class TestPathUtilityFunctions:
    """Test utility functions for path analysis."""

    def test_is_openconfig_path(self):
        """Test OpenConfig path detection."""
        openconfig_paths = [
            "openconfig-system:/system",
            "openconfig-interfaces:interfaces",
            "openconfig-network-instance:network-instances",
        ]

        non_openconfig_paths = [
            "cisco-ios-xr:system",
            "ietf-interfaces:interfaces",
            "juniper-config:system",
            "invalid-path",
        ]

        for path in openconfig_paths:
            assert (
                is_openconfig_path(path) is True
            ), f"Expected True for: {path}"

        for path in non_openconfig_paths:
            assert (
                is_openconfig_path(path) is False
            ), f"Expected False for: {path}"

    def test_get_model_name_from_path(self):
        """Test model name extraction from paths."""
        test_cases = [
            ("openconfig-system:/system/config", "openconfig-system"),
            (
                "openconfig-interfaces:interfaces/interface[name='eth0']",
                "openconfig-interfaces",
            ),
            (
                "openconfig-network-instance:network-instances/network-instance[name='default']",
                "openconfig-network-instance",
            ),
            ("invalid-path", None),
            ("", None),
        ]

        for path, expected_name in test_cases:
            model_name = get_model_name_from_path(path)
            assert (
                model_name == expected_name
            ), f"Expected '{expected_name}' for path: {path}"

    def test_path_validation_edge_cases(self):
        """Test edge cases in path validation."""
        edge_cases = [
            (None, False),  # None input
            (123, False),  # Non-string input
            ([], False),  # List input
            ({}, False),  # Dict input
        ]

        for path, expected in edge_cases:
            result = is_openconfig_path(path)
            assert result == expected, f"Expected {expected} for input: {path}"


class TestPerformanceConsiderations:
    """Test performance-related aspects of path analysis."""

    def test_large_path_list_performance(self):
        """Test performance with large path lists."""
        # Generate a large list of paths
        large_path_list = [
            f"openconfig-system:/system/config/item-{i}" for i in range(1000)
        ]
        large_path_list.extend(
            [
                f"openconfig-interfaces:interfaces/interface[name='eth{i}']"
                for i in range(1000)
            ]
        )

        # This should complete quickly
        models = extract_models_from_paths(large_path_list)

        # Should deduplicate to just the unique models
        expected_models = {
            OpenConfigModel.SYSTEM,
            OpenConfigModel.INTERFACES,
        }

        assert models == expected_models

    def test_complex_path_parsing_performance(self):
        """Test performance with complex path structures."""
        complex_paths = [
            "openconfig-network-instance:network-instances/network-instance[name='VRF_A']/protocols/protocol[identifier='ISIS'][name='100']/isis/global/config/level-capability",
            "openconfig-interfaces:interfaces/interface[name='GigabitEthernet0/0/0/0']/subinterfaces/subinterface[index='0']/ipv4/addresses/address[ip='192.168.1.1']/config/prefix-length",
            "openconfig-system:system/processes/process[pid='1234']/state/memory-usage",
        ]

        for path in complex_paths:
            model = extract_model_from_path(path)
            assert model is not None, f"Failed to parse complex path: {path}"
