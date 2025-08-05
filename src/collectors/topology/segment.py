from .utils import _build_graph_ip_only


def segment(network: str) -> dict:
    """
    List devices on the specified L3 segment.
    """
    topology_result = _build_graph_ip_only()
    topology_graph = topology_result.graph
    devices_on_segment = set()
    for source_device, target_device, edge_attributes in topology_graph.edges(
        data=True
    ):
        if (
            edge_attributes.get("type") == "ip"
            and edge_attributes.get("network") == network
        ):
            devices_on_segment.add(source_device)
            devices_on_segment.add(target_device)
    return {"segment": network, "devices": list(devices_on_segment)}
