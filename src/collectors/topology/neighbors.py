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
        topology_graph = _build_graph_ip_only()
        logger.debug(
            "Topology graph built with %d nodes",
            topology_graph.number_of_nodes() if topology_graph else 0,
        )

        device_name = device.name
        neighbor_list = []

        if device_name not in topology_graph:
            logger.warning(
                "Device %s not found in topology graph - check interface collection",
                device_name,
            )
            return NetworkOperationResult(
                device_name=device.name,
                ip_address=device.ip_address,
                nos=device.nos,
                operation_type="topology_neighbors",
                status=OperationStatus.SUCCESS,
                data={"neighbors": []},
                metadata={
                    "message": f"No neighbors found for device {device_name}",
                    "device_in_topology": False,
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
            nos=device.nos,
            operation_type="topology_neighbors",
            status=OperationStatus.SUCCESS,
            data={"neighbors": neighbor_list},
            metadata={
                "neighbor_count": len(neighbor_list),
                "device_in_topology": True,
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
            nos=device.nos,
            operation_type="topology_neighbors",
            status=OperationStatus.FAILED,
            error_response=error_response,
        )
