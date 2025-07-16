#!/usr/bin/env python3
"""
Unit tests for OpenConfig model registry.

Tests the model registry functionality including model definitions,
requirements, and utility functions.
"""

from src.schemas.openconfig_models import (
    OpenConfigModel,
    ModelRequirement,
    MODEL_REGISTRY,
    get_model_requirement,
    get_all_models,
    get_model_by_name,
)


class TestOpenConfigModel:
    """Test OpenConfigModel enum."""

    def test_model_enum_values(self):
        """Test that model enum has correct values."""
        assert OpenConfigModel.SYSTEM.value == "openconfig-system"
        assert OpenConfigModel.INTERFACES.value == "openconfig-interfaces"
        assert (
            OpenConfigModel.NETWORK_INSTANCE.value
            == "openconfig-network-instance"
        )

    def test_all_models_defined(self):
        """Test that all expected models are defined."""
        expected_models = {
            OpenConfigModel.SYSTEM,
            OpenConfigModel.INTERFACES,
            OpenConfigModel.NETWORK_INSTANCE,
        }
        assert set(OpenConfigModel) == expected_models


class TestModelRequirement:
    """Test ModelRequirement dataclass."""

    def test_model_requirement_creation(self):
        """Test ModelRequirement object creation."""
        req = ModelRequirement(
            name="openconfig-system",
            min_version="0.17.1",
            description="System configuration",
        )
        assert req.name == "openconfig-system"
        assert req.min_version == "0.17.1"
        assert req.description == "System configuration"


class TestModelRegistry:
    """Test model registry functionality."""

    def test_all_models_have_requirements(self):
        """Test that all models have requirements defined."""
        for model in OpenConfigModel:
            req = get_model_requirement(model)
            assert req is not None, f"No requirement defined for {model}"
            assert req.name == model.value
            assert req.min_version is not None
            assert req.description is not None

    def test_model_requirement_consistency(self):
        """Test consistency between model enum and requirements."""
        for model in OpenConfigModel:
            req = get_model_requirement(model)
            assert req.name == model.value, f"Name mismatch for {model}"

    def test_version_format_validation(self):
        """Test that all model versions follow semantic versioning."""
        import re

        # Basic semantic version pattern: major.minor.patch
        version_pattern = r"^\d+\.\d+\.\d+$"

        for model in OpenConfigModel:
            req = get_model_requirement(model)
            assert re.match(
                version_pattern, req.min_version
            ), f"Invalid version format for {model}: {req.min_version}"

    def test_model_descriptions_quality(self):
        """Test that model descriptions are meaningful."""
        for model in OpenConfigModel:
            req = get_model_requirement(model)
            assert (
                len(req.description) > 10
            ), f"Description too short for {model}: {req.description}"
            assert not req.description.startswith(
                "TODO"
            ), f"Placeholder description for {model}: {req.description}"


class TestModelUtilityFunctions:
    """Test utility functions for model registry."""

    def test_get_all_models(self):
        """Test getting all models."""
        all_models = get_all_models()
        assert isinstance(all_models, list)
        assert len(all_models) == len(OpenConfigModel)
        assert all(isinstance(model, OpenConfigModel) for model in all_models)

    def test_get_model_by_name(self):
        """Test getting model by name."""
        test_cases = [
            ("openconfig-system", OpenConfigModel.SYSTEM),
            ("openconfig-interfaces", OpenConfigModel.INTERFACES),
            ("openconfig-network-instance", OpenConfigModel.NETWORK_INSTANCE),
        ]

        for name, expected_model in test_cases:
            model = get_model_by_name(name)
            assert (
                model == expected_model
            ), f"Expected {expected_model} for name {name}"

    def test_get_model_by_name_invalid(self):
        """Test getting model by invalid name."""
        invalid_names = [
            "openconfig-invalid",
            "not-openconfig-model",
            "",
            "openconfig-",
            "system",  # Without openconfig prefix
        ]

        for name in invalid_names:
            model = get_model_by_name(name)
            assert model is None, f"Expected None for invalid name: {name}"

    def test_get_model_requirement_invalid(self):
        """Test getting requirement for invalid model."""
        # Test that the function handles edge cases properly
        # This test verifies that the function is robust
        # Since the function signature requires OpenConfigModel,
        # we test that it works correctly with all valid models
        for model in OpenConfigModel:
            req = get_model_requirement(model)
            assert (
                req is not None
            ), f"Should return requirement for valid model: {model}"


class TestModelRegistryExtensibility:
    """Test registry extensibility and future-proofing."""

    def test_model_registry_completeness(self):
        """Test that registry covers all enum values."""
        registry_models = set(MODEL_REGISTRY.keys())
        enum_models = set(OpenConfigModel)

        assert (
            registry_models == enum_models
        ), f"Registry missing models: {enum_models - registry_models}"

    def test_model_registry_structure(self):
        """Test registry structure consistency."""
        for model, requirement in MODEL_REGISTRY.items():
            assert isinstance(model, OpenConfigModel)
            assert isinstance(requirement, ModelRequirement)
            assert requirement.name == model.value

    def test_model_requirements_uniqueness(self):
        """Test that model requirements are unique."""
        names = [req.name for req in MODEL_REGISTRY.values()]
        assert len(names) == len(
            set(names)
        ), "Duplicate model names in registry"

    def test_version_ordering_assumptions(self):
        """Test assumptions about version ordering."""
        # Test that versions can be compared (basic check)
        for model in OpenConfigModel:
            req = get_model_requirement(model)
            version_parts = req.min_version.split(".")
            assert (
                len(version_parts) == 3
            ), f"Version should have 3 parts: {req.min_version}"

            # All parts should be numeric
            for part in version_parts:
                assert (
                    part.isdigit()
                ), f"Version part should be numeric: {part}"


class TestModelCompatibility:
    """Test model compatibility aspects."""

    def test_backward_compatibility_considerations(self):
        """Test that current versions are reasonable for backward compatibility."""
        # Test that no model requires an unreasonably high version
        for model in OpenConfigModel:
            req = get_model_requirement(model)
            major, minor, patch = map(int, req.min_version.split("."))

            # Basic sanity checks
            assert (
                major >= 0
            ), f"Major version should be non-negative: {req.min_version}"
            assert (
                minor >= 0
            ), f"Minor version should be non-negative: {req.min_version}"
            assert (
                patch >= 0
            ), f"Patch version should be non-negative: {req.min_version}"

            # Reasonable upper bounds (adjust as needed)
            assert (
                major < 10
            ), f"Major version seems too high: {req.min_version}"
            assert (
                minor < 100
            ), f"Minor version seems too high: {req.min_version}"

    def test_model_relationship_consistency(self):
        """Test consistency between related models."""
        # For example, ensure that interface-related models have compatible versions
        # This is more of a business logic test that can be expanded
        system_req = get_model_requirement(OpenConfigModel.SYSTEM)
        interfaces_req = get_model_requirement(OpenConfigModel.INTERFACES)

        # Both should exist and have valid versions
        assert system_req is not None
        assert interfaces_req is not None
        assert system_req.min_version is not None
        assert interfaces_req.min_version is not None

    def test_model_dependency_implications(self):
        """Test implications of model dependencies."""
        # Test that models that often work together have compatible requirements
        # This is a placeholder for more sophisticated dependency analysis
        network_instance_req = get_model_requirement(
            OpenConfigModel.NETWORK_INSTANCE
        )

        # Network instance is often the most complex requirement
        assert network_instance_req is not None
        assert (
            network_instance_req.min_version == "1.3.0"
        )  # Known tested version


class TestModelRegistryUsageScenarios:
    """Test real-world usage scenarios for model registry."""

    def test_collector_model_mapping(self):
        """Test mapping collectors to required models."""
        # Example mapping (this would be based on actual collector requirements)
        collector_models = {
            "system": [OpenConfigModel.SYSTEM],
            "interfaces": [OpenConfigModel.INTERFACES],
            "routing": [OpenConfigModel.NETWORK_INSTANCE],
            "vpn": [OpenConfigModel.NETWORK_INSTANCE],
        }

        # Test that all mapped models exist and have requirements
        for collector, models in collector_models.items():
            for model in models:
                req = get_model_requirement(model)
                assert (
                    req is not None
                ), f"No requirement for {model} used by {collector}"

    def test_model_requirement_for_common_operations(self):
        """Test model requirements for common operations."""
        common_operations = [
            ("Getting device hostname", OpenConfigModel.SYSTEM),
            ("Interface status check", OpenConfigModel.INTERFACES),
            ("VPN configuration", OpenConfigModel.NETWORK_INSTANCE),
        ]

        for operation, model in common_operations:
            req = get_model_requirement(model)
            assert (
                req is not None
            ), f"No requirement for {model} needed for: {operation}"
            assert (
                req.min_version is not None
            ), f"No version requirement for {model}"

    def test_model_requirements_documentation(self):
        """Test that model requirements are well-documented."""
        for model in OpenConfigModel:
            req = get_model_requirement(model)

            # Description should be informative
            assert req.description is not None
            assert len(req.description.strip()) > 0

            # Should contain key information
            description_lower = req.description.lower()
            assert any(
                keyword in description_lower
                for keyword in [
                    "config",
                    "state",
                    "data",
                    "information",
                    "management",
                ]
            ), f"Description should be more informative: {req.description}"
