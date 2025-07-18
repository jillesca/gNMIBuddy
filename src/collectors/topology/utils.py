from collections import defaultdict
from typing import Dict, Any, List, Union
import networkx as nx
from src.schemas.models import Device
from src.schemas.responses import OperationStatus
from src.inventory.manager import InventoryManager
from src.processors.topology_processor import extract_interface_subnets
from src.collectors.routing import get_routing_info
from src.utils.parallel_execution import run_command_on_all_devices
from src.collectors.interfaces import get_interfaces
from src.logging.config import get_logger

logger = get_logger(__name__)

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
    device_order = {}  # Track device order from input
    for i, interface_result in enumerate(interface_results):
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
        if device_name not in device_order:
            device_order[device_name] = i
    # Add all devices as nodes before processing edges, in input order
    for device in sorted(
        all_devices, key=lambda x: device_order.get(x, float("inf"))
    ):
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

            # Determine source/target based on device order in input
            device_a_order = device_order.get(
                endpoint_a["device"], float("inf")
            )
            device_b_order = device_order.get(
                endpoint_b["device"], float("inf")
            )

            if device_a_order < device_b_order:
                source_endpoint, target_endpoint = endpoint_a, endpoint_b
            elif device_a_order > device_b_order:
                source_endpoint, target_endpoint = endpoint_b, endpoint_a
            else:
                # Same device order (including self-loops), use original order
                source_endpoint, target_endpoint = endpoint_a, endpoint_b

            topology_graph.add_edge(
                source_endpoint["device"],
                target_endpoint["device"],
                network=network,
                local_interface=source_endpoint["interface"],
                remote_interface=target_endpoint["interface"],
                local_ip=source_endpoint["ip"],
                remote_ip=target_endpoint["ip"],
            )
    return topology_graph


def _build_graph_ip_only(max_workers: int = 10) -> nx.Graph:

    logger.debug("Getting device list from inventory")
    device_objs = InventoryManager.list_devices()["devices"]
    device_names = [d["name"] for d in device_objs]
    logger.debug("Found %d devices: %s", len(device_names), device_names)

    logger.debug("Running interface commands on all devices")
    raw_interface_results = run_command_on_all_devices(
        _get_interface, max_workers=max_workers
    )
    logger.debug("Got %d interface results", len(raw_interface_results))

    interface_results = [
        dict(result, device=result.get("device_name", device_name))
        for device_name, result in zip(device_names, raw_interface_results)
    ]

    # Log some details about the results
    for i, result in enumerate(interface_results):
        logger.debug(
            "Device %s: %s - keys: %s",
            device_names[i],
            type(result).__name__,
            list(result.keys()) if isinstance(result, dict) else "not a dict",
        )

    logger.debug("Building graph from interface results")
    graph = build_ip_only_graph_from_interface_results(interface_results)
    logger.debug(
        "Built graph with %d nodes and %d edges",
        graph.number_of_nodes(),
        graph.number_of_edges(),
    )

    return graph


def _get_interface(device: str) -> dict:
    device_obj = _get_device_or_error_dict(device)
    if not isinstance(device_obj, Device):
        return device_obj

    interface_response = get_interfaces(device_obj)

    # Handle NetworkOperationResult
    if hasattr(interface_response, "status"):
        if interface_response.status == OperationStatus.SUCCESS:
            # Return the data from NetworkOperationResult
            result = interface_response.data.copy()
            result["device_name"] = device
            return result
        elif (
            interface_response.status == OperationStatus.FEATURE_NOT_AVAILABLE
        ):
            feature_response = interface_response.feature_not_found_response
            return {
                "feature_not_found": (
                    feature_response.feature_name
                    if feature_response
                    else "unknown"
                ),
                "message": (
                    feature_response.message
                    if feature_response
                    else "Feature not available"
                ),
                "device_name": device,
            }
        else:  # failed
            return {
                "error": (
                    interface_response.error_response.message
                    if interface_response.error_response
                    else "Unknown error"
                ),
                "device_name": device,
            }

    # Fallback for unexpected response type
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
    routing_responses = get_routing_info(
        device, protocol="isis", include_details=True
    )
    if isinstance(routing_responses, list) and routing_responses:
        first_response = routing_responses[0]
        if isinstance(first_response, dict):
            return first_response
        return {"error": "Unexpected routing response format"}
    return {"error": "No ISIS routing information found"}
