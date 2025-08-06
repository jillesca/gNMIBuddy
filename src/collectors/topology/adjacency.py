"""
Topology adjacency collector module.
Provides functions for retrieving network-wide topology adjacency information using gNMI.
"""

from src.schemas.models import DeviceErrorResult
from src.schemas.responses import (
    ErrorResponse,
    OperationStatus,
    NetworkOperationResult,
)
from src.inventory import get_device
from src.collectors.topology.network_topology import get_network_topology
from src.logging import get_logger

logger = get_logger(__name__)


def get_topology_adjacency(device_name: str) -> NetworkOperationResult:
    """
    Get network-wide IP adjacency analysis for complete topology understanding.

    This function performs a comprehensive network-wide topology adjacency analysis,
    providing insight into all IP connections across the entire network infrastructure.
    It uses robust error handling to distinguish between gNMI errors and legitimate
    empty topology scenarios.

    The function implements fail-fast behavior - if gNMI errors are encountered during
    topology building (such as authentication failures or connectivity issues), it
    immediately returns an error status rather than potentially misleading empty results.

    Key Features:
    - Network-wide scope (not limited to single device)
    - Robust ErrorResponse detection and fail-fast behavior
    - Uniform data structure for both errors and legitimate empty results
    - Clear status differentiation between failures and successful empty topologies
    - Structured metadata providing context about the operation

    Args:
        device_name: Name of the device in inventory (used for interface compliance,
                    operation is network-wide)

    Returns:
        NetworkOperationResult containing:
        - status: "failed" for gNMI errors, "success" for legitimate empty/populated
        - data: {} (empty dict for both error and success cases as per v0.1.0+ standard)
        - error_response: Present only when gNMI errors occurred
        - metadata: Context about operation scope, connection count, and result details

    Example Error Response (Authentication Failure):
        {
            "status": "failed",
            "data": {},
            "error_response": {
                "type": "gNMIException",
                "message": "GRPC ERROR Host: 10.10.20.101:57777, Error: authentication failed"
            },
            "metadata": {
                "scope": "network-wide",
                "message": "Failed to build topology adjacency due to gNMI errors"
            }
        }

    Example Success Response (Empty Network):
        {
            "status": "success",
            "data": {},
            "metadata": {
                "total_connections": 0,
                "scope": "network-wide",
                "message": "No topology connections discovered"
            }
        }
    """
    logger.debug("Getting topology adjacency for device %s", device_name)

    # Validate device exists in inventory
    device_result = get_device(device_name)
    if isinstance(device_result, DeviceErrorResult):
        logger.error("Device '%s' not found in inventory", device_name)
        return NetworkOperationResult(
            device_name=device_name,
            ip_address="0.0.0.0",
            nos="unknown",
            operation_type="topology_adjacency",
            status=OperationStatus.FAILED,
            data={},
            metadata={
                "scope": "network-wide",
                "message": f"Device '{device_name}' not found in inventory",
            },
        )

    logger.debug("Starting topology adjacency dump for network-wide analysis")

    try:
        # Get network topology with built-in ErrorResponse detection
        topology_result = get_network_topology()

        # Check if the topology building encountered ErrorResponse
        if isinstance(topology_result.error_response, ErrorResponse):
            logger.error(
                "Failed to build topology adjacency due to gNMI errors: %s",
                topology_result.error_response.message,
            )
            # Fail fast when ErrorResponse detected
            return NetworkOperationResult(
                device_name=device_result.name,
                ip_address=device_result.ip_address,
                nos=device_result.nos.value,
                operation_type="topology_adjacency",
                status=OperationStatus.FAILED,
                data={},  # Empty dict as required
                error_response=topology_result.error_response,
                metadata={
                    "scope": "network-wide",
                    "message": "Failed to build topology adjacency due to gNMI errors",
                },
            )

        # If topology was successful, check if we have connections
        if topology_result.status == OperationStatus.SUCCESS:
            connections = topology_result.data.get("direct_connections", [])
            total_connections = len(connections)

            logger.info(
                "Topology adjacency completed: %d connections found",
                total_connections,
            )

            return NetworkOperationResult(
                device_name=device_result.name,
                ip_address=device_result.ip_address,
                nos=device_result.nos.value,
                operation_type="topology_adjacency",
                status=OperationStatus.SUCCESS,
                data={},  # Empty dict for both error and legitimate empty as required
                metadata={
                    "total_connections": total_connections,
                    "scope": "network-wide",
                    "message": (
                        "No topology connections discovered"
                        if total_connections == 0
                        else f"Topology adjacency analysis complete with {total_connections} connections"
                    ),
                },
            )
        else:
            # Handle other failure cases from get_network_topology
            logger.error(
                "Topology building failed with status: %s",
                topology_result.status,
            )
            return NetworkOperationResult(
                device_name=device_result.name,
                ip_address=device_result.ip_address,
                nos=device_result.nos.value,
                operation_type="topology_adjacency",
                status=OperationStatus.FAILED,
                data={},
                metadata={
                    "scope": "network-wide",
                    "message": f"Topology building failed: {topology_result.status}",
                },
            )

    except Exception as e:
        logger.error(
            "Unexpected error during topology adjacency analysis: %s",
            str(e),
            exc_info=True,
        )
        return NetworkOperationResult(
            device_name=device_result.name,
            ip_address=device_result.ip_address,
            nos=device_result.nos.value,
            operation_type="topology_adjacency",
            status=OperationStatus.FAILED,
            data={},
            metadata={
                "scope": "network-wide",
                "message": f"Unexpected error during topology adjacency analysis: {str(e)}",
            },
        )
