from src.schemas.models import Device
from src.schemas.responses import (
    ErrorResponse,
    OperationStatus,
    NetworkOperationResult,
)

from .utils import _build_graph_ip_only
from src.logging import get_logger

logger = get_logger(__name__)


def neighbors(device: Device) -> NetworkOperationResult:
    """
    List direct neighbors of a device.

    Args:
        device: Device object from inventory

    Returns:
        NetworkOperationResult: Response object containing neighbor information
    """
    logger.debug("Getting neighbors for device %s", device.name)

    try:
        topology_result = _build_graph_ip_only()
        logger.debug(
            "Topology graph built with %d nodes",
            (
                topology_result.graph.number_of_nodes()
                if topology_result.graph
                else 0
            ),
        )

        device_name = device.name

        # Check if ErrorResponse was encountered during topology building
        if topology_result.has_errors and topology_result.error_response:
            logger.error(
                "Failed to build topology due to gNMI errors: %s",
                topology_result.error_response.message,
            )
            return NetworkOperationResult(
                device_name=device.name,
                ip_address=device.ip_address,
                nos=device.nos.value,
                operation_type="topology_neighbors",
                status=OperationStatus.FAILED,
                data={},
                error_response=topology_result.error_response,
                metadata={
                    "message": "Failed to build topology due to gNMI errors",
                    "device_in_topology": False,
                },
            )

        topology_graph = topology_result.graph
        neighbor_list = []

        if device_name not in topology_graph:
            logger.warning(
                "Device %s not found in topology graph - check interface collection",
                device_name,
            )
            return NetworkOperationResult(
                device_name=device.name,
                ip_address=device.ip_address,
                nos=device.nos.value,
                operation_type="topology_neighbors",
                status=OperationStatus.SUCCESS,
                data={},
                metadata={
                    "message": f"No neighbors found for device {device_name}",
                    "device_in_topology": False,
                    "isolation_reason": "legitimate",
                },
            )

        logger.debug(
            "Device %s found in topology, getting neighbors", device_name
        )
        for neighbor_device in topology_graph.neighbors(device_name):
            neighbor_list.append(
                {
                    "neighbor": neighbor_device,
                    "attributes": topology_graph.get_edge_data(
                        device_name, neighbor_device
                    ),
                }
            )

        if len(neighbor_list) == 0:
            logger.warning(
                "Device %s has no neighbors - device may be isolated",
                device_name,
            )

        logger.debug(
            "Found %d neighbors for device %s", len(neighbor_list), device_name
        )

        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos.value,
            operation_type="topology_neighbors",
            status=OperationStatus.SUCCESS,
            data={"neighbors": neighbor_list},
            metadata={
                "message": f"Found {len(neighbor_list)} neighbors for device {device_name}",
                "device_in_topology": True,
                "neighbor_count": len(neighbor_list),
            },
        )

    except (KeyError, ValueError, TypeError) as e:
        logger.error(
            "Error retrieving neighbors for %s: %s", device.name, str(e)
        )
        logger.debug("Exception details: %s", str(e), exc_info=True)
        error_response = ErrorResponse(
            type="TOPOLOGY_ERROR",
            message=f"Error retrieving neighbors for {device.name}: {str(e)}",
        )
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos.value,
            operation_type="topology_neighbors",
            status=OperationStatus.FAILED,
            data={},
            error_response=error_response,
            metadata={
                "message": "Error occurred during neighbor discovery",
                "device_in_topology": False,
            },
        )
