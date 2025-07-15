import networkx as nx
from .utils import _build_graph_ip_only


def path(device, target_device_name: str) -> dict:
    """
    Compute shortest path between two devices.
    """
    topology_graph = _build_graph_ip_only()
    source_device_name = device.name if hasattr(device, "name") else device
    try:
        path_nodes = nx.shortest_path(
            topology_graph,
            source=source_device_name,
            target=target_device_name,
        )
        path_edges = []
        for idx in range(len(path_nodes) - 1):
            from_device, to_device = path_nodes[idx], path_nodes[idx + 1]
            path_edges.append(
                {
                    "source": from_device,
                    "target": to_device,
                    "attributes": topology_graph.get_edge_data(
                        from_device, to_device
                    ),
                }
            )
        return {"nodes": path_nodes, "edges": path_edges}
    except Exception as error:
        return {"error": str(error)}
