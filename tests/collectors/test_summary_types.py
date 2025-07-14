#!/usr/bin/env python3

"""
Test module to diagnose type annotation issues in NetworkOperationResult response classes
"""

import sys

# Add src to path
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.schemas.responses import NetworkOperationResult, OperationStatus


def test_network_operation_result_structure():
    """Test to print out details of NetworkOperationResult structure"""

    # Create an instance of NetworkOperationResult to test
    result = NetworkOperationResult(
        device_name="test-device",
        ip_address="192.168.1.1",
        nos="iosxr",
        operation_type="mpls",
        status=OperationStatus.SUCCESS,
        data={"test": "data"},
        metadata={"timestamp": "2024-01-01"},
    )

    print(f"\nNetworkOperationResult structure inspection:")
    print(f"  device_name: {result.device_name}")
    print(f"  ip_address: {result.ip_address}")
    print(f"  nos: {result.nos}")
    print(f"  operation_type: {result.operation_type}")
    print(f"  status: {result.status}")
    print(f"  data type: {type(result.data).__name__}")
    print(f"  metadata type: {type(result.metadata).__name__}")
    print(f"  error_response: {result.error_response}")
    print(f"  feature_not_found_response: {result.feature_not_found_response}")

    # Test that the structure is consistent
    assert isinstance(result.data, dict), "data field should be a dictionary"
    assert isinstance(
        result.metadata, dict
    ), "metadata field should be a dictionary"
    assert isinstance(
        result.status, OperationStatus
    ), "status should be an OperationStatus enum"

    print("\nAll NetworkOperationResult structure tests passed!")


if __name__ == "__main__":
    test_network_operation_result_structure()
