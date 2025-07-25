from src.schemas.responses import (
    ErrorResponse,
    OperationStatus,
    NetworkOperationResult,
)
from .utils import _build_graph_ip_only
from src.logging import get_logger, log_operation

logger = get_logger(__name__)


def get_network_topology() -> NetworkOperationResult:
    """
    Return the full IP-only direct connection list of the topology graph (no ISIS).
    Each connection represents a direct L3 IP connectivity between two devices.

    This function builds a complete network topology using all devices in the inventory.
    This is a network-wide operation that analyzes all devices to build the topology graph.

    Returns:
        NetworkOperationResult: Response object containing all direct IP connections in the network
    """
    try:
        logger.debug(
            "Building complete IP topology graph for all devices in inventory"
        )
        topology_graph = _build_graph_ip_only()
        logger.debug(
            "Topology graph build result: %s", type(topology_graph).__name__
        )

        if topology_graph is None:
            logger.warning("Topology graph is None")
            return NetworkOperationResult(
                device_name="ALL_DEVICES",
                ip_address="0.0.0.0",
                nos="N/A",
                operation_type="network_topology",
                status=OperationStatus.FAILED,
                data={"direct_connections": []},
                metadata={
                    "total_connections": 0,
                    "message": "Failed to build topology graph",
                    "scope": "network-wide",
                    "operation_note": "This operation analyzes all devices in inventory",
                },
            )

        logger.info(
            "Built network topology: %d devices, %d connections",
            topology_graph.number_of_nodes(),
            topology_graph.number_of_edges(),
        )

        direct_connections = []
        for (
            source_device,
            target_device,
            edge_attributes,
        ) in topology_graph.edges(data=True):
            direct_connections.append(
                {
                    "source": source_device,
                    "target": target_device,
                    "attributes": edge_attributes,
                }
            )

        logger.info(
            "Network topology complete: %d direct connections discovered",
            len(direct_connections),
        )

        # Warn if topology seems sparse (fewer connections than devices)
        device_count = topology_graph.number_of_nodes()
        if device_count > 0 and len(direct_connections) < device_count:
            logger.warning(
                "Sparse network topology detected: %d connections for %d devices - check device connectivity",
                len(direct_connections),
                device_count,
            )

        logger.debug(
            "Sample connections (first 3): %s",
            str(direct_connections[:3]) if direct_connections else "none",
        )

        return NetworkOperationResult(
            device_name="ALL_DEVICES",
            ip_address="0.0.0.0",
            nos="N/A",
            operation_type="network_topology",
            status=OperationStatus.SUCCESS,
            data={"direct_connections": direct_connections},
            metadata={
                "total_connections": len(direct_connections),
                "total_nodes": topology_graph.number_of_nodes(),
                "total_edges": topology_graph.number_of_edges(),
                "scope": "network-wide",
                "operation_note": "This operation analyzes all devices in inventory",
                "context_device": "network-wide",
            },
        )

    except (KeyError, ValueError, TypeError, AttributeError) as e:
        logger.error("Error in get_network_topology: %s", str(e))
        logger.debug("Exception details: %s", str(e), exc_info=True)
        error_response = ErrorResponse(
            type="TOPOLOGY_ERROR",
            message=f"Error building network topology: {str(e)}",
        )
        return NetworkOperationResult(
            device_name="ALL_DEVICES",
            ip_address="0.0.0.0",
            nos="N/A",
            operation_type="network_topology",
            status=OperationStatus.FAILED,
            error_response=error_response,
            metadata={
                "scope": "network-wide",
                "operation_note": "This operation analyzes all devices in inventory",
                "context_device": "network-wide",
            },
        )
