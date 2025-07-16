#!/usr/bin/env python3
"""
Unit tests for logging utility functions.
Tests logic without making actual gNMI requests.
"""

import pytest
from unittest.mock import MagicMock

from src.schemas.responses import NetworkOperationResult, OperationStatus
from src.schemas.models import Device


class TestLoggingFunctions:
    """Test suite for logging functionality."""

    def test_device_creation_for_logging(self):
        """Test Device model creation for logging operations."""
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

    def test_network_operation_result_for_logging(self):
        """Test NetworkOperationResult creation for logging operations."""
        result = NetworkOperationResult(
            device_name="test-device",
            ip_address="192.168.1.1",
            nos="iosxr",
            operation_type="logging",
            status=OperationStatus.SUCCESS,
            data={"logs": ["test log entry"]},
        )

        assert result.device_name == "test-device"
        assert result.operation_type == "logging"
        assert result.status == OperationStatus.SUCCESS
        assert result.data["logs"] == ["test log entry"]

    def test_operation_status_for_logging(self):
        """Test OperationStatus enum values for logging operations."""
        assert OperationStatus.SUCCESS is not None
        assert OperationStatus.FAILED is not None
        assert OperationStatus.FEATURE_NOT_AVAILABLE is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
