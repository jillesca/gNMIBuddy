#!/usr/bin/env python3
"""
Tests for the error handling functions in gnmi/error_handlers.py.
"""

import os
import sys
import re
import pytest
from unittest.mock import MagicMock, patch

# Add the project root to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
)

import grpc
from src.schemas.models import Device
from src.gnmi.error_handlers import (
    handle_timeout_error,
    handle_rpc_error,
    handle_connection_refused,
    handle_generic_error,
    _extract_feature_name,
    _log_error,
)
from src.schemas.responses import ErrorResponse, FeatureNotFoundResponse


class MockRpcError(grpc.RpcError):
    """Mock class for gRPC RpcError."""

    def __init__(self, code, details):
        self._code = code
        self._details = details

    def code(self):
        return self._code

    def details(self):
        return self._details


class Test_ErrorHandlers:
    """Test suite for gNMI error handlers."""

    def setup_method(self):
        """Setup test fixtures."""
        self.device = Device(
            name="test-device",
            ip_address="192.168.1.1",
            port=57400,
            username="admin",
            password="admin",
            nos="iosxr",
        )

    def test_handle_timeout_error(self):
        """Test the handle_timeout_error function."""
        result = handle_timeout_error(self.device)
        assert isinstance(result, ErrorResponse)
        assert result.type == "CONNECTION_TIMEOUT"
        assert "Connection timeout" in result.message
        assert self.device.name in result.message
        assert self.device.ip_address in result.message
        assert "error_class" in result.details

    def test_handle_connection_refused(self):
        """Test the handle_connection_refused function."""
        result = handle_connection_refused(self.device)
        assert isinstance(result, ErrorResponse)
        assert result.type == "CONNECTION_REFUSED"
        assert "Connection refused" in result.message
        assert self.device.name in result.message
        assert self.device.ip_address in result.message

    def test_handle_rpc_error_regular_error(self):
        """Test the handle_rpc_error function with a regular error."""
        error = MockRpcError(
            code=grpc.StatusCode.UNAVAILABLE, details="Service unavailable"
        )

        result = handle_rpc_error(self.device, error)
        assert isinstance(result, ErrorResponse)
        assert result.type == "GRPC_ERROR"
        assert "gRPC error" in result.message
        assert self.device.name in result.message
        assert error.code().name in result.message
        assert error.details() in result.message

    def test_handle_rpc_error_feature_not_found(self):
        """Test the handle_rpc_error function with a feature not found error."""
        feature_name = "bgp"
        error = MockRpcError(
            code=grpc.StatusCode.NOT_FOUND,
            details=f"Requested element(s) not found: '{feature_name}'",
        )

        result = handle_rpc_error(self.device, error)
        assert isinstance(result, FeatureNotFoundResponse)
        assert result.feature_name == feature_name
        assert feature_name in result.message
        assert self.device.name in result.message
        assert "code" in result.details
        assert "full_details" in result.details

    def test_handle_generic_error_regular_error(self):
        """Test the handle_generic_error function with a regular error."""
        error = ValueError("Invalid value")

        result = handle_generic_error(self.device, error)
        assert isinstance(result, ErrorResponse)
        assert result.type == "ValueError"
        assert str(error) in result.message

    def test_handle_generic_error_feature_not_found(self):
        """Test the handle_generic_error function with a feature not found error."""
        feature_name = "ospf"
        error = Exception(f"Element not found: '{feature_name}'")

        result = handle_generic_error(self.device, error)
        assert isinstance(result, FeatureNotFoundResponse)
        assert result.feature_name == feature_name
        assert "not found" in result.message.lower()
        assert self.device.name in result.message
        # The generic error handler creates an empty details dict
        assert isinstance(result.details, dict)

    def test_extract_feature_name(self):
        """Test the _extract_feature_name function."""
        # Test with standard gRPC pattern
        details = "Requested element(s) not found: 'bgp'"
        result = _extract_feature_name(details)
        assert result == "bgp"

        # Test with generic pattern
        details = "Error: not found: 'ospf'"
        result = _extract_feature_name(details)
        assert result == "ospf"

        # Test with no match
        details = "General error occurred"
        result = _extract_feature_name(details)
        assert result is None

        # Test with multiple matches (should return first)
        details = "Requested element(s) not found: 'bgp', not found: 'ospf'"
        result = _extract_feature_name(details)
        assert result == "bgp"

        # Test with comma-separated features
        details = "Requested element(s) not found: 'bgp, interfaces, global'"
        result = _extract_feature_name(details)
        assert result == "bgp, interfaces, global"
