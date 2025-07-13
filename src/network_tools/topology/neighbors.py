from src.schemas.models import Device
from src.schemas.responses import NetworkOperationResult, ErrorResponse
from .utils import _build_graph_ip_only


def neighbors(device: Device) -> NetworkOperationResult:
    """
    List direct neighbors of a device.

    Args:
        device: Device object from inventory

    Returns:
        NetworkOperationResult: Response object containing neighbor information
    """
    try:
        topology_graph = _build_graph_ip_only()
        device_name = device.name
        neighbor_list = []

        if device_name not in topology_graph:
            return NetworkOperationResult(
                device_name=device.name,
                ip_address=device.ip_address,
                nos=device.nos,
                operation_type="topology_neighbors",
                status="success",
                data={"neighbors": []},
                metadata={
                    "message": f"No neighbors found for device {device_name}",
                    "device_in_topology": False,
                },
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

        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="topology_neighbors",
            status="success",
            data={"neighbors": neighbor_list},
            metadata={
                "neighbor_count": len(neighbor_list),
                "device_in_topology": True,
            },
        )

    except (KeyError, ValueError, TypeError) as e:
        error_response = ErrorResponse(
            type="TOPOLOGY_ERROR",
            message=f"Error retrieving neighbors for {device.name}: {str(e)}",
        )
        return NetworkOperationResult(
            device_name=device.name,
            ip_address=device.ip_address,
            nos=device.nos,
            operation_type="topology_neighbors",
            status="failed",
            error_response=error_response,
        )
