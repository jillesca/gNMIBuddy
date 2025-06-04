from collections import defaultdict
from typing import Dict, Any, List, Union
import networkx as nx
from src.utils.parallel_execution import run_command_on_all_devices
from src.parsers.topology_parser import extract_interface_subnets
from src.network_tools.interfaces_info import get_interface_information
from src.network_tools.routing_info import get_routing_information
from src.inventory.models import Device
from src.inventory.manager import InventoryManager


# In-memory cache for the topology graph
_cached_graph = None


def build_ip_only_graph_from_interface_results(interface_results) -> nx.Graph:
    interface_results = [
        dict(result, device=result.get("device_name"))
        for result in interface_results
    ]
    topology_graph = nx.Graph()
    # Always add all devices as nodes, regardless of their interfaces or adjacencies
    all_devices = set()
    for interface_result in interface_results:
        if not isinstance(interface_result, dict):
            continue
        if (
            "error" in interface_result
            or "feature_not_found" in interface_result
        ):
            continue
        device_name = interface_result.get("device")
        if not device_name:
            continue
        all_devices.add(device_name)
    # Add all devices as nodes before processing edges
    for device in all_devices:
        topology_graph.add_node(device)
    ip_subnet_entries = extract_interface_subnets(interface_results)
    mgmt_names = {"MgmtEth0/RP0/CPU0/0"}
    ip_subnet_entries = [
        entry
        for entry in ip_subnet_entries
        if entry["interface"] not in mgmt_names
    ]
    network_to_interface_entries: Dict[str, List[Dict[str, Any]]] = (
        defaultdict(list)
    )
    for interface_entry in ip_subnet_entries:
        device = interface_entry.get("device") or interface_entry.get(
            "device_name"
        )
        if not device or not interface_entry.get("network"):
            continue
        interface_entry["device"] = device
        network_to_interface_entries[interface_entry["network"]].append(
            interface_entry
        )
    for network, interface_entry_list in network_to_interface_entries.items():
        if len(interface_entry_list) == 2:
            endpoint_a = interface_entry_list[0]
            endpoint_b = interface_entry_list[1]
            if (
                endpoint_a.get("interface") in mgmt_names
                or endpoint_b.get("interface") in mgmt_names
            ):
                continue
            node1, node2 = sorted([endpoint_a["device"], endpoint_b["device"]])
            topology_graph.add_edge(
                node1,
                node2,
                network=network,
                local_interface=endpoint_a["interface"],
                remote_interface=endpoint_b["interface"],
                local_ip=endpoint_a["ip"],
                remote_ip=endpoint_b["ip"],
            )
    return topology_graph


def _build_graph_ip_only(max_workers: int = 10) -> nx.Graph:
    from src.inventory.manager import InventoryManager

    device_objs = InventoryManager.list_devices()["devices"]
    device_names = [d["name"] for d in device_objs]
    interface_results = run_command_on_all_devices(
        _get_interface, max_workers=max_workers
    )

    interface_results = [
        dict(result, device=result.get("device_name", device_name))
        for device_name, result in zip(device_names, interface_results)
    ]
    return build_ip_only_graph_from_interface_results(interface_results)


def _get_interface(device: str) -> dict:
    device_obj = _get_device_or_error_dict(device)
    if not isinstance(device_obj, Device):
        return device_obj
    interface_response = get_interface_information(device_obj)
    if hasattr(interface_response, "to_dict"):
        response_dict = interface_response.to_dict()
        response_dict["device_name"] = device
        return response_dict
    return {
        "error": "Unexpected response from get_interface_information",
        "device_name": device,
    }


def _get_device_or_error_dict(
    device_name: str,
) -> Union[Device, Dict[str, str]]:
    device_obj_result, success = InventoryManager.get_device(device_name)
    if success and isinstance(device_obj_result, Device):
        return device_obj_result
    error_msg = (
        device_obj_result["error"]
        if isinstance(device_obj_result, dict) and "error" in device_obj_result
        else "Device not found"
    )
    return {"error": error_msg, "device_name": device_name}


def _get_isis(device) -> dict:
    routing_responses = get_routing_information(
        device, protocol="isis", include_details=True
    )
    if isinstance(routing_responses, list) and routing_responses:
        first_response = routing_responses[0]
        if hasattr(first_response, "to_dict"):
            return first_response.to_dict()
        return {"error": "Unexpected RoutingResponse object"}
    return {"error": "No ISIS routing information found"}
