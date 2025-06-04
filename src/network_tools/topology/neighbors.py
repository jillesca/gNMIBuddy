from typing import Dict, Any, List
from .utils import _build_graph_ip_only


def neighbors(device) -> Dict[str, List[Dict[str, Any]]]:
    """
    List direct neighbors of a device.
    """
    topology_graph = _build_graph_ip_only()
    device_name = device.name if hasattr(device, "name") else device
    neighbor_list = []
    if device_name not in topology_graph:
        return {"neighbors": []}
    for neighbor_device in topology_graph.neighbors(device_name):
        neighbor_list.append(
            {
                "neighbor": neighbor_device,
                "attributes": topology_graph.get_edge_data(
                    device_name, neighbor_device
                ),
            }
        )
    return {"neighbors": neighbor_list}
