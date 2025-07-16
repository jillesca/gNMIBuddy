#!/usr/bin/env python3
"""
Test migration helpers with current functionality.
"""

import pytest
from src.utils.migration_helpers import (
    validate_collector_migration,
    get_collector_model_requirements,
    check_backward_compatibility,
)
from src.schemas.models import Device
from src.schemas.responses import NetworkOperationResult, OperationStatus
from src.decorators.smart_capability_verification import verify_required_models


def test_validate_collector_migration():
    """Test validation of a properly migrated collector function."""

    @verify_required_models()
    def test_collector(device: Device) -> NetworkOperationResult:
        """Test collector function."""
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="test",
            status=OperationStatus.SUCCESS,
            data={},
        )

    result = validate_collector_migration(test_collector)

    assert result["function_name"] == "test_collector"
    assert result["is_valid"] is True
    assert len(result["issues"]) == 0
    print("✓ Collector migration validation test passed!")


def test_get_collector_model_requirements():
    """Test model requirement analysis."""

    def test_system_collector(device: Device) -> NetworkOperationResult:
        """Test system collector function."""
        # Simulate using openconfig-system paths
        path = "openconfig-system:/system"
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="test",
            status=OperationStatus.SUCCESS,
            data={},
        )

    result = get_collector_model_requirements(test_system_collector)

    assert result["function_name"] == "test_system_collector"
    assert result["confidence"] in ["high", "low", "unknown"]
    print("✓ Model requirements analysis test passed!")


def test_check_backward_compatibility():
    """Test backward compatibility check."""

    result = check_backward_compatibility()

    assert result["is_compatible"] is True
    assert "old_decorator_import" in result["tested_components"]
    assert "old_verification_service" in result["tested_components"]
    print("✓ Backward compatibility test passed!")


if __name__ == "__main__":
    test_validate_collector_migration()
    test_get_collector_model_requirements()
    test_check_backward_compatibility()
    print("All migration helper tests passed!")
