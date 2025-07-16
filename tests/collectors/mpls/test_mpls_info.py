#!/usr/bin/env python3
"""
Unit tests for MPLS utility functions.
Tests logic without making actual gNMI requests.
"""

import pytest
from unittest.mock import MagicMock

from src.schemas.responses import NetworkOperationResult, OperationStatus
from src.schemas.models import Device


class TestMplsUtilityFunctions:
    """Test suite for MPLS utility functions."""

    def test_device_model_creation(self):
        """Test Device model creation for MPLS operations."""
        device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            nos="iosxr",
            username="admin",
            password="password",
        )

        assert device.name == "test-device"
        assert device.ip_address == "192.168.1.1"
        assert device.nos == "iosxr"

    def test_network_operation_result_creation(self):
        """Test NetworkOperationResult creation for MPLS operations."""
        result = NetworkOperationResult(
            device_name="test-device",
            ip_address="192.168.1.1",
            nos="iosxr",
            operation_type="mpls",
            status=OperationStatus.SUCCESS,
            data={"mpls_info": "test data"},
        )

        assert result.device_name == "test-device"
        assert result.operation_type == "mpls"
        assert result.status == OperationStatus.SUCCESS
        assert result.data["mpls_info"] == "test data"

    def test_operation_status_values(self):
        """Test OperationStatus enum values."""
        assert OperationStatus.SUCCESS is not None
        assert OperationStatus.FAILED is not None
        assert OperationStatus.FEATURE_NOT_AVAILABLE is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
