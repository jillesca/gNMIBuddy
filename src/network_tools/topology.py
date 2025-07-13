#!/usr/bin/env python3
"""
Topology discovery module.
Provides functions for building and querying network topology graph.
"""
from typing import Dict, Any
from src.network_tools.topology.adjacency_dump import adjacency_dump
from src.network_tools.topology.neighbors import neighbors
from src.network_tools.topology.path import path
from src.network_tools.topology.segment import segment
from src.network_tools.topology.ip_adjacency_dump import ip_adjacency_dump


def adjacency_dump_cmd(device) -> Dict[str, Any]:
    edges = adjacency_dump()
    return {"device_name": device.name, "adjacencies": edges}


def neighbors_cmd(device) -> Dict[str, Any]:
    neighbors_list = neighbors(device)
    return {
        "device_name": device.name,
        "neighbors": neighbors_list,
    }


def path_cmd(device, target_device_name) -> Dict[str, Any]:
    if not target_device_name or not isinstance(target_device_name, str):
        raise ValueError(
            "Target device name must be provided for path computation."
        )
    path_result = path(device, target_device_name)
    return {"device_name": device.name, "path": path_result}


def segment_cmd(device, network) -> Dict[str, Any]:
    if not network or not isinstance(network, str):
        raise ValueError("Network segment must be provided for segment query.")
    segment_result = segment(network)
    return {
        "device_name": device.name,
        "segment": segment_result,
    }


def ip_adjacency_dump_cmd(device) -> Dict[str, Any]:
    connections = ip_adjacency_dump()
    return {
        "device_name": "all",
        "direct_connections": connections,
    }
