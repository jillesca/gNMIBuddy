#!/usr/bin/env python3
"""
Topology discovery module.
Provides functions for building and querying network topology graph.
"""
from src.network_tools.topology.adjacency_dump import adjacency_dump
from src.network_tools.topology.neighbors import neighbors
from src.network_tools.topology.path import path
from src.network_tools.topology.segment import segment
from src.network_tools.topology.ip_adjacency_dump import ip_adjacency_dump
from src.network_tools.responses import NetworkToolsResponse


# === Adapter Functions for API/CLI (explicit signatures, no *args) ===
def adjacency_dump_cmd(device):
    edges = adjacency_dump()
    return NetworkToolsResponse(
        success=True, device_name=device.name, raw_data={"adjacencies": edges}
    )


def neighbors_cmd(device):
    neighbors_list = neighbors(device)
    return NetworkToolsResponse(
        success=True,
        device_name=device.name,
        raw_data={"neighbors": neighbors_list},
    )


def path_cmd(device, target_device_name):
    if not target_device_name or not isinstance(target_device_name, str):
        raise ValueError(
            "Target device name must be provided for path computation."
        )
    path_result = path(device, target_device_name)
    return NetworkToolsResponse(
        success=True, device_name=device.name, raw_data={"path": path_result}
    )


def segment_cmd(device, network):
    if not network or not isinstance(network, str):
        raise ValueError("Network segment must be provided for segment query.")
    segment_result = segment(network)
    return NetworkToolsResponse(
        success=True,
        device_name=device.name,
        raw_data={"segment": segment_result},
    )


def ip_adjacency_dump_cmd(device):
    connections = ip_adjacency_dump()
    return NetworkToolsResponse(
        success=True,
        device_name="all",
        raw_data={"direct_connections": connections},
    )
