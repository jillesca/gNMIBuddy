import logging
from .utils import _build_graph_ip_only

logger = logging.getLogger(__name__)


def ip_adjacency_dump(device: str) -> list:
    """
    Return the full IP-only direct connection list of the topology graph (no ISIS).
    Each connection represents a direct L3 IP connectivity between two devices.
    """
    try:
        logger.debug("Building IP topology graph for device: %s", device)
        topology_graph = _build_graph_ip_only()

        if topology_graph is None:
            logger.warning("Topology graph is None")
            return []

        logger.debug(
            "Topology graph has %d nodes and %d edges",
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

        logger.debug("Found %d direct connections", len(direct_connections))
        return direct_connections

    except (KeyError, ValueError, TypeError, AttributeError) as e:
        logger.error("Error in ip_adjacency_dump: %s", str(e))
        return []
