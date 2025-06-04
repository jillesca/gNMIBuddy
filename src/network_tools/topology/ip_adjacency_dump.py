from .utils import _build_graph_ip_only


def ip_adjacency_dump(device: str) -> list:
    """
    Return the full IP-only direct connection list of the topology graph (no ISIS).
    Each connection represents a direct L3 IP connectivity between two devices.
    """
    topology_graph = _build_graph_ip_only()
    direct_connections = []
    for source_device, target_device, edge_attributes in topology_graph.edges(
        data=True
    ):
        direct_connections.append(
            {
                "source": source_device,
                "target": target_device,
                "attributes": edge_attributes,
            }
        )
    return direct_connections
