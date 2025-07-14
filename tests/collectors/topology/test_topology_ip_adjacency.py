import json
from src.collectors.topology.utils import (
    build_ip_only_graph_from_interface_results,
)


def graph_to_direct_connections(graph):
    """
    Convert a networkx.Graph to the direct_connections output format.
    """
    direct_connections = []
    for source_device, target_device, edge_attributes in graph.edges(
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


def test_ip_only_graph_and_output():
    # Load input and expected output
    with open(
        "tests/collectors/topology/topology_input.json", encoding="utf-8"
    ) as f:
        interface_results = json.load(f)
    with open(
        "tests/collectors/topology/topology_expected_output.json",
        encoding="utf-8",
    ) as f:
        expected_output = json.load(f)
    # Build graph and output using the actual production function
    graph = build_ip_only_graph_from_interface_results(interface_results)
    output = graph_to_direct_connections(graph)

    # Convert to set of tuples for order-insensitive comparison
    def conn_key(conn):
        a = conn["attributes"]
        return (
            conn["source"],
            conn["target"],
            a["network"],
            a["local_interface"],
            a["remote_interface"],
            a["local_ip"],
            a["remote_ip"],
        )

    expected_set = set(conn_key(c) for c in expected_output)
    actual_set = set(conn_key(c) for c in output)
    assert actual_set == expected_set
    # Optionally, check output structure
    for conn in output:
        assert "source" in conn
        assert "target" in conn
        assert "attributes" in conn
        for key in [
            "network",
            "local_interface",
            "remote_interface",
            "local_ip",
            "remote_ip",
        ]:
            assert key in conn["attributes"]
