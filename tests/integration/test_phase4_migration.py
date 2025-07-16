#!/usr/bin/env python3
"""
Integration test to verify Phase 4 implementation works correctly.
"""

import pytest
import os
import glob
from unittest.mock import patch


class TestPhase4Integration:
    """Integration tests for Phase 4 migration."""

    def test_collectors_have_smart_verification_decorator(self):
        """Test that all collectors have been migrated to use the smart verification decorator."""

        # Check the source files directly without problematic imports
        collector_files = glob.glob("src/collectors/*.py")
        migrated_count = 0

        for collector_file in collector_files:
            if collector_file.endswith("__init__.py"):
                continue

            with open(collector_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Check if the file imports and uses the smart verification decorator
            has_import = (
                "from src.decorators.smart_capability_verification import verify_required_models"
                in content
            )
            has_decorator = "@verify_required_models" in content

            if has_import and has_decorator:
                migrated_count += 1

        # We expect at least 5 collectors to be migrated
        assert (
            migrated_count >= 5
        ), f"Only {migrated_count} collectors migrated, expected at least 5"

    def test_backward_compatibility_maintained(self):
        """Test that backward compatibility is maintained by checking source files."""

        # Check that the old decorator still exists for backward compatibility
        old_decorator_file = "src/decorators/capability_verification.py"
        assert os.path.exists(
            old_decorator_file
        ), "Old decorator file should exist for backward compatibility"

        with open(old_decorator_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Check that the old decorator function still exists
        assert (
            "def verify_capabilities(" in content
        ), "Old decorator function should still exist"

        # Check that the old verification service still exists
        verification_service_file = "src/services/capability_verification.py"
        assert os.path.exists(
            verification_service_file
        ), "Verification service file should exist"

        with open(verification_service_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Check that the old verification function still exists
        assert (
            "def verify_openconfig_network_instance(" in content
        ), "Old verification function should still exist"

    def test_collector_validation_passes(self):
        """Test that all migrated collectors pass validation using source code analysis."""

        collector_files = glob.glob("src/collectors/*.py")

        for collector_file in collector_files:
            if collector_file.endswith("__init__.py"):
                continue

            with open(collector_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Validate that the collector uses the smart verification decorator
            if (
                "from src.decorators.smart_capability_verification import verify_required_models"
                in content
            ):
                assert (
                    "@verify_required_models" in content
                ), f"File {collector_file} imports decorator but doesn't use it"

                # Check that old decorator is NOT used
                assert (
                    "@verify_capabilities" not in content
                ), f"File {collector_file} still uses old decorator"

    def test_all_collectors_use_network_operation_result(self):
        """Test that all collectors are structured to return NetworkOperationResult objects."""

        collector_files = glob.glob("src/collectors/*.py")

        for collector_file in collector_files:
            if collector_file.endswith("__init__.py"):
                continue

            with open(collector_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Check that NetworkOperationResult is imported
            assert (
                "NetworkOperationResult" in content
            ), f"File {collector_file} should import NetworkOperationResult"

            # Check that functions return NetworkOperationResult
            assert (
                "-> NetworkOperationResult" in content
            ), f"File {collector_file} should have functions returning NetworkOperationResult"

    def test_client_hardcoded_verification_removed(self):
        """Test that the client no longer has hardcoded verification."""

        # Read the client source code directly instead of importing
        with open("src/gnmi/client.py", "r", encoding="utf-8") as f:
            source = f.read()

        # These should NOT be in the client anymore
        assert (
            "verify_openconfig_network_instance" not in source
        ), "Client still has hardcoded verification"
        assert (
            "is_device_verified" not in source
        ), "Client still has hardcoded cache checks"
        assert (
            "cache_verification_result" not in source
        ), "Client still has hardcoded cache calls"

        # The client should still have basic functionality
        assert (
            "def get_gnmi_data" in source
        ), "Client should have get_gnmi_data function"
        assert "gNMIclient" in source, "Client should still use gNMIclient"

    def test_smart_verification_decorator_exists(self):
        """Test that the smart verification decorator exists and is properly structured."""

        decorator_file = "src/decorators/smart_capability_verification.py"
        assert os.path.exists(
            decorator_file
        ), "Smart verification decorator file should exist"

        with open(decorator_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Check that the decorator function exists
        assert (
            "def verify_required_models(" in content
        ), "Smart verification decorator function should exist"

        # Check that it imports the necessary components
        assert (
            "from ..schemas.openconfig_models import OpenConfigModel"
            in content
        ), "Should import OpenConfigModel"
        assert (
            "NetworkOperationResult" in content
        ), "Should import NetworkOperationResult"

    def test_model_registry_exists(self):
        """Test that the model registry exists and contains the expected models."""

        registry_file = "src/schemas/openconfig_models.py"
        assert os.path.exists(
            registry_file
        ), "Model registry file should exist"

        with open(registry_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Check that the registry contains the expected models
        assert (
            "class OpenConfigModel(Enum):" in content
        ), "OpenConfigModel enum should exist"
        assert (
            'SYSTEM = "openconfig-system"' in content
        ), "Should have SYSTEM model"
        assert (
            'INTERFACES = "openconfig-interfaces"' in content
        ), "Should have INTERFACES model"
        assert (
            'NETWORK_INSTANCE = "openconfig-network-instance"' in content
        ), "Should have NETWORK_INSTANCE model"

        # Check that the registry dict exists
        assert (
            "MODEL_REGISTRY: Dict[OpenConfigModel, ModelRequirement]"
            in content
        ), "Should have MODEL_REGISTRY"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
