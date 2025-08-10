from dataclasses import dataclass
from collections import defaultdict
from typing import Dict, Any, List, Union, Optional

import networkx as nx

from src.logging import get_logger
from src.inventory.manager import InventoryManager
from src.collectors.routing import get_routing_info
from src.collectors.interfaces import get_interfaces
from src.schemas.models import Device, DeviceErrorResult
from src.schemas.responses import OperationStatus, ErrorResponse
from src.utils.parallel_execution import run_command_on_all_devices
from src.processors.topology_processor import extract_interface_subnets

logger = get_logger(__name__)


@dataclass
class TopologyBuildResult:
    """
    Result of topology building operation containing both the graph and error information.

    Attributes:
        graph: NetworkX graph representing the topology
        has_errors: Whether errors occurred during interface collection
        error_devices: List of device names that encountered errors
        total_devices: Total number of devices processed
        error_response: First ErrorResponse encountered, if any
    """

    graph: nx.Graph
    has_errors: bool
    error_devices: List[str]
    total_devices: int
    error_response: Optional[ErrorResponse] = None


def build_ip_only_graph_from_interface_results(interface_results) -> nx.Graph:
    logger.debug(
        "Building IP graph from %d interface results", len(interface_results)
    )

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

    logger.debug(
        "Found %d unique devices from interface results", len(all_devices)
    )

    # Add all devices as nodes before processing edges, in input order
    for device in sorted(
        all_devices, key=lambda x: device_order.get(x, float("inf"))
    ):
        topology_graph.add_node(device)

    logger.debug(
        "Added %d nodes to topology graph", topology_graph.number_of_nodes()
    )

    ip_subnet_entries = extract_interface_subnets(interface_results)
    logger.debug("Extracted %d IP subnet entries", len(ip_subnet_entries))

    mgmt_names = {"MgmtEth0/RP0/CPU0/0"}
    ip_subnet_entries = [
        entry
        for entry in ip_subnet_entries
        if entry["interface"] not in mgmt_names
    ]
    logger.debug(
        "After filtering management interfaces: %d subnet entries",
        len(ip_subnet_entries),
    )

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

    logger.debug(
        "Grouped interfaces into %d unique networks",
        len(network_to_interface_entries),
    )

    connections_added = 0
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
            connections_added += 1

            logger.debug(
                "Added connection %d: %s (%s) <-> %s (%s) on network %s",
                connections_added,
                source_endpoint["device"],
                source_endpoint["interface"],
                target_endpoint["device"],
                target_endpoint["interface"],
                network,
            )

    logger.debug(
        "Final topology graph: %d nodes, %d edges",
        topology_graph.number_of_nodes(),
        topology_graph.number_of_edges(),
    )

    return topology_graph


def _build_graph_ip_only(max_workers: int = 10) -> TopologyBuildResult:

    logger.debug("Getting device list from inventory")
    device_list_result = InventoryManager.list_devices()
    device_objs = device_list_result.devices
    device_names = [d.name for d in device_objs]
    logger.debug("Found %d devices: %s", len(device_names), str(device_names))

    logger.debug("Running interface commands on all devices")
    raw_interface_results = run_command_on_all_devices(
        _get_interface, max_workers=max_workers
    )
    logger.debug("Got %d interface results", len(raw_interface_results))

    interface_results = [
        dict(result, device=result.get("device_name", device_name))
        for device_name, result in zip(device_names, raw_interface_results)
    ]

    # Track errors and devices that encountered them
    success_count = 0
    error_count = 0
    error_devices = []
    first_error_response = None

    for i, result in enumerate(interface_results):
        device_name = device_names[i]
        if isinstance(result, dict):
            if "error" in result:
                error_count += 1
                error_devices.append(device_name)
                # Capture the first error response for fail-fast behavior
                if first_error_response is None:
                    error_message = result.get("error", "Unknown error")
                    first_error_response = ErrorResponse(
                        type="gNMIException", message=error_message
                    )
                    logger.debug(
                        "Captured first ErrorResponse from device %s: %s",
                        device_name,
                        error_message,
                    )
            elif "feature_not_found" in result:
                # Feature not found is not considered an error for topology building
                pass
            else:
                success_count += 1
        logger.debug(
            "Device %s: %s - keys: %s",
            device_names[i],
            type(result).__name__,
            (
                str(list(result.keys()))
                if isinstance(result, dict)
                else "not a dict"
            ),
        )

    logger.debug(
        "Interface collection summary - success: %d, errors: %d",
        success_count,
        error_count,
    )

    # Determine if we have significant errors that should cause fail-fast
    total_devices = success_count + error_count
    has_errors = error_count > 0

    if total_devices > 0 and error_count > 0:
        error_percentage = (error_count / total_devices) * 100
        if error_percentage >= 25:  # Warn if 25% or more failed
            logger.warning(
                "High interface collection failure rate: %d/%d devices failed (%.1f%%) - topology may be incomplete",
                error_count,
                total_devices,
                error_percentage,
            )

    logger.debug("Building graph from interface results")
    graph = build_ip_only_graph_from_interface_results(interface_results)
    logger.debug(
        "Built graph with %d nodes and %d edges",
        graph.number_of_nodes(),
        graph.number_of_edges(),
    )

    return TopologyBuildResult(
        graph=graph,
        has_errors=has_errors,
        error_devices=error_devices,
        total_devices=total_devices,
        error_response=first_error_response,
    )


def _get_interface(device: str) -> dict:
    logger.debug("Getting interface info for device %s", device)

    device_obj = _get_device_or_error_dict(device)
    if not isinstance(device_obj, Device):
        logger.debug(
            "Device %s: error getting device object: %s",
            device,
            str(device_obj),
        )
        return device_obj

    interface_response = get_interfaces(device_obj)
    logger.debug(
        "Device %s: interface response type: %s",
        device,
        type(interface_response).__name__,
    )

    # Handle NetworkOperationResult
    if hasattr(interface_response, "status"):
        if interface_response.status == OperationStatus.SUCCESS:
            # Return the data from NetworkOperationResult
            result = interface_response.data.copy()
            result["device_name"] = device
            logger.debug("Device %s: successful interface collection", device)
            return result
        elif (
            interface_response.status == OperationStatus.FEATURE_NOT_AVAILABLE
        ):
            feature_response = interface_response.feature_not_found_response
            logger.debug("Device %s: feature not available", device)
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
            logger.debug("Device %s: interface collection failed", device)
            logger.error(
                "Failed to collect interfaces from %s for topology building: %s",
                device,
                (
                    interface_response.error_response.message
                    if interface_response.error_response
                    else "Unknown error"
                ),
            )
            return {
                "error": (
                    interface_response.error_response.message
                    if interface_response.error_response
                    else "Unknown error"
                ),
                "device_name": device,
            }

    # Fallback for unexpected response type
    logger.debug("Device %s: unexpected response type", device)
    return {
        "error": "Unexpected response from get_interface_information",
        "device_name": device,
    }


def _get_device_or_error_dict(
    device_name: str,
) -> Union[Device, Dict[str, str]]:
    device_obj_result = InventoryManager.get_device(device_name)
    if not isinstance(device_obj_result, DeviceErrorResult):
        return device_obj_result
    return {"error": device_obj_result.msg, "device_name": device_name}


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
