#!/usr/bin/env python3
"""
Tests for the simplified routing functionality with metadata-based approach.
"""

import os
import sys
from unittest.mock import patch

# Add the project root to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
)

from src.collectors.routing import (
    get_routing_info,
    get_protocol_status,
    get_successful_protocols,
    get_failed_protocols,
    get_unavailable_protocols,
    get_protocol_error,
)
from src.schemas.responses import (
    NetworkOperationResult,
    OperationStatus,
    FeatureNotFoundResponse,
)
from src.schemas.models import Device


class TestSimplifiedRoutingFunctionality:
    """Test suite for simplified routing functionality."""

    def test_partial_success_bgp_not_configured_isis_configured(self):
        """Test scenario where BGP is not configured but ISIS is configured."""
        mock_device = Device(
            name="xrd-3",
            ip_address="10.10.20.103",
            nos="iosxr",
            port=57777,
            username="admin",
            password="admin",
        )

        # Mock BGP to return feature not found
        bgp_feature_not_found = FeatureNotFoundResponse(
            feature_name="bgp",
            message="Feature not found on device xrd-3: BGP not configured",
        )
        bgp_result = NetworkOperationResult(
            device_name=mock_device.name,
            ip_address=mock_device.ip_address,
            nos=mock_device.nos,
            operation_type="routing_info",
            status=OperationStatus.FEATURE_NOT_AVAILABLE,
            feature_not_found_response=bgp_feature_not_found,
        )

        # Mock ISIS to return success
        isis_data = {
            "detailed_data": {"isis_interfaces": []},
            "summary": {"enabled": True, "instance_count": 1},
        }
        isis_result = NetworkOperationResult(
            device_name=mock_device.name,
            ip_address=mock_device.ip_address,
            nos=mock_device.nos,
            operation_type="routing_info",
            status=OperationStatus.SUCCESS,
            data=isis_data,
        )

        with (
            patch(
                "src.collectors.routing._get_bgp_info", return_value=bgp_result
            ),
            patch(
                "src.collectors.routing._get_isis_info",
                return_value=isis_result,
            ),
        ):

            # Call the function to get all protocols
            response = get_routing_info(mock_device, protocol=None)

            # Verify overall response
            assert isinstance(response, NetworkOperationResult)
            assert response.status == OperationStatus.PARTIAL_SUCCESS
            assert response.device_name == "xrd-3"

            # Verify data contains only ISIS (successful protocol)
            routing_data = response.data["routing_protocols"]
            assert isinstance(routing_data, list)
            assert len(routing_data) == 1
            assert routing_data[0]["protocol"] == "isis"

            # Verify metadata
            assert response.metadata["successful_protocols"] == 1
            assert response.metadata["failed_protocols"] == 0
            assert response.metadata["feature_not_found_protocols"] == 1
            assert response.metadata["total_protocols"] == 2

            # Verify protocol statuses in metadata
            protocol_statuses = response.metadata["protocol_statuses"]
            assert protocol_statuses["bgp"] == "feature_not_available"
            assert protocol_statuses["isis"] == "success"

            # Verify protocol errors in metadata
            protocol_errors = response.metadata.get("protocol_errors", {})
            assert "bgp" in protocol_errors
            assert protocol_errors["bgp"]["type"] == "feature_not_found"

            # Test helper functions
            assert get_successful_protocols(response) == ["isis"]
            assert get_unavailable_protocols(response) == ["bgp"]
            assert get_failed_protocols(response) == []
            assert (
                get_protocol_status(response, "bgp") == "feature_not_available"
            )
            assert get_protocol_status(response, "isis") == "success"
            assert get_protocol_error(response, "bgp") is not None

    def test_helper_functions_with_metadata(self):
        """Test the helper functions with metadata approach."""
        # Create a mock response with mixed results
        mock_response = NetworkOperationResult(
            device_name="test-device",
            ip_address="10.0.0.1",
            nos="iosxr",
            operation_type="routing_info",
            status=OperationStatus.PARTIAL_SUCCESS,
            metadata={
                "protocol_statuses": {
                    "bgp": "feature_not_available",
                    "isis": "success",
                    "ospf": "failed",
                },
                "protocol_errors": {
                    "bgp": {
                        "type": "feature_not_found",
                        "message": "BGP not configured",
                    },
                    "ospf": {"type": "error", "message": "OSPF query failed"},
                },
            },
        )

        # Test helper functions
        assert get_successful_protocols(mock_response) == ["isis"]
        assert get_failed_protocols(mock_response) == ["ospf"]
        assert get_unavailable_protocols(mock_response) == ["bgp"]

        # Test protocol status
        assert (
            get_protocol_status(mock_response, "bgp")
            == "feature_not_available"
        )
        assert get_protocol_status(mock_response, "isis") == "success"
        assert get_protocol_status(mock_response, "ospf") == "failed"
        assert get_protocol_status(mock_response, "rip") is None

        # Test protocol errors
        bgp_error = get_protocol_error(mock_response, "bgp")
        assert bgp_error is not None
        assert bgp_error["type"] == "feature_not_found"
        assert bgp_error["message"] == "BGP not configured"

        ospf_error = get_protocol_error(mock_response, "ospf")
        assert ospf_error is not None
        assert ospf_error["type"] == "error"

        # No error for successful protocol
        assert get_protocol_error(mock_response, "isis") is None

    def test_all_protocols_successful(self):
        """Test scenario where all protocols are successful."""
        mock_device = Device(
            name="test-device",
            ip_address="10.0.0.1",
            nos="iosxr",
            port=57777,
            username="admin",
            password="admin",
        )

        # Mock both protocols to return success
        bgp_data = {"detailed_data": {}, "summary": {"enabled": True}}
        bgp_result = NetworkOperationResult(
            device_name=mock_device.name,
            ip_address=mock_device.ip_address,
            nos=mock_device.nos,
            operation_type="routing_info",
            status=OperationStatus.SUCCESS,
            data=bgp_data,
        )

        isis_data = {"detailed_data": {}, "summary": {"enabled": True}}
        isis_result = NetworkOperationResult(
            device_name=mock_device.name,
            ip_address=mock_device.ip_address,
            nos=mock_device.nos,
            operation_type="routing_info",
            status=OperationStatus.SUCCESS,
            data=isis_data,
        )

        with (
            patch(
                "src.collectors.routing._get_bgp_info", return_value=bgp_result
            ),
            patch(
                "src.collectors.routing._get_isis_info",
                return_value=isis_result,
            ),
        ):

            response = get_routing_info(mock_device, protocol=None)

            # Verify overall response
            assert response.status == OperationStatus.SUCCESS
            assert response.metadata["successful_protocols"] == 2
            assert response.metadata["failed_protocols"] == 0
            assert response.metadata["feature_not_found_protocols"] == 0
            assert len(response.data["routing_protocols"]) == 2

            # Verify no errors in metadata
            assert "protocol_errors" not in response.metadata

    def test_all_protocols_not_configured(self):
        """Test scenario where all protocols are not configured."""
        mock_device = Device(
            name="test-device",
            ip_address="10.0.0.1",
            nos="iosxr",
            port=57777,
            username="admin",
            password="admin",
        )

        # Mock both protocols to return feature not found
        bgp_not_found = FeatureNotFoundResponse(
            feature_name="bgp",
            message="BGP not configured",
        )
        bgp_result = NetworkOperationResult(
            device_name=mock_device.name,
            ip_address=mock_device.ip_address,
            nos=mock_device.nos,
            operation_type="routing_info",
            status=OperationStatus.FEATURE_NOT_AVAILABLE,
            feature_not_found_response=bgp_not_found,
        )

        isis_not_found = FeatureNotFoundResponse(
            feature_name="isis",
            message="ISIS not configured",
        )
        isis_result = NetworkOperationResult(
            device_name=mock_device.name,
            ip_address=mock_device.ip_address,
            nos=mock_device.nos,
            operation_type="routing_info",
            status=OperationStatus.FEATURE_NOT_AVAILABLE,
            feature_not_found_response=isis_not_found,
        )

        with (
            patch(
                "src.collectors.routing._get_bgp_info", return_value=bgp_result
            ),
            patch(
                "src.collectors.routing._get_isis_info",
                return_value=isis_result,
            ),
        ):

            response = get_routing_info(mock_device, protocol=None)

            # Verify overall response
            assert response.status == OperationStatus.FEATURE_NOT_AVAILABLE
            assert response.metadata["successful_protocols"] == 0
            assert response.metadata["feature_not_found_protocols"] == 2
            assert len(response.data["routing_protocols"]) == 0

            # Verify both protocols have errors
            protocol_errors = response.metadata.get("protocol_errors", {})
            assert "bgp" in protocol_errors
            assert "isis" in protocol_errors

    def test_single_protocol_query_not_configured(self):
        """Test querying a single protocol that is not configured."""
        mock_device = Device(
            name="test-device",
            ip_address="10.0.0.1",
            nos="iosxr",
            port=57777,
            username="admin",
            password="admin",
        )

        # Mock BGP to return feature not found
        bgp_not_found = FeatureNotFoundResponse(
            feature_name="bgp",
            message="BGP not configured",
        )
        bgp_result = NetworkOperationResult(
            device_name=mock_device.name,
            ip_address=mock_device.ip_address,
            nos=mock_device.nos,
            operation_type="routing_info",
            status=OperationStatus.FEATURE_NOT_AVAILABLE,
            feature_not_found_response=bgp_not_found,
        )

        with patch(
            "src.collectors.routing._get_bgp_info", return_value=bgp_result
        ):
            response = get_routing_info(mock_device, protocol="bgp")

            # Verify overall response
            assert response.status == OperationStatus.FEATURE_NOT_AVAILABLE
            assert response.metadata["successful_protocols"] == 0
            assert response.metadata["feature_not_found_protocols"] == 1
            assert response.metadata["total_protocols"] == 1
            assert len(response.data["routing_protocols"]) == 0

            # Verify protocol status and error
            assert (
                get_protocol_status(response, "bgp") == "feature_not_available"
            )
            assert get_protocol_error(response, "bgp") is not None
