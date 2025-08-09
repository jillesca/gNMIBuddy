#!/usr/bin/env python3
"""
Topology discovery module.
Provides functions for building and querying network topology graph.
"""
from src.schemas.responses import (
    NetworkOperationResult,
    ErrorResponse,
    OperationStatus,
)

from src.collectors.topology.path import path
from src.collectors.topology.segment import segment
from src.collectors.topology.neighbors import neighbors


def neighbors_cmd(device) -> NetworkOperationResult:
    """
    Get direct neighbors of a device using the topology graph.

    Args:
        device: Device object from inventory

    Returns:
        NetworkOperationResult: Response object containing neighbor information
    """
    return neighbors(device)


def path_cmd(device, target_device_name) -> NetworkOperationResult:
    if not target_device_name or not isinstance(target_device_name, str):
        error_response = ErrorResponse(
            type="INVALID_INPUT",
            message="Target device name must be provided for path computation.",
        )
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="topology_info",
            status=OperationStatus.FAILED,
            error_response=error_response,
        )

    try:
        path_result = path(device, target_device_name)
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="topology_info",
            status=OperationStatus.SUCCESS,
            data={"path": path_result},
        )
    except (KeyError, ValueError, TypeError) as e:
        error_response = ErrorResponse(
            type="TOPOLOGY_ERROR",
            message=f"Error computing path: {str(e)}",
        )
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="topology_info",
            status=OperationStatus.FAILED,
            error_response=error_response,
        )


def segment_cmd(device, network) -> NetworkOperationResult:
    if not network or not isinstance(network, str):
        error_response = ErrorResponse(
            type="INVALID_INPUT",
            message="Network segment must be provided for segment query.",
        )
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="topology_info",
            status=OperationStatus.FAILED,
            error_response=error_response,
        )

    try:
        segment_result = segment(network)
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="topology_info",
            status=OperationStatus.SUCCESS,
            data={"segment": segment_result},
        )
    except (KeyError, ValueError, TypeError) as e:
        error_response = ErrorResponse(
            type="TOPOLOGY_ERROR",
            message=f"Error retrieving segment: {str(e)}",
        )
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="topology_info",
            status=OperationStatus.FAILED,
            error_response=error_response,
        )
