#!/usr/bin/env python3
"""Topology adjacency command implementation"""
import click

from src.cmd.commands.base import execute_device_command
from src.cmd.commands.decorators import add_common_device_options
from src.cmd.schemas import Command, CommandGroup
from src.cmd.error_providers import CommandErrorProvider
from src.cmd.registries.command_registry import (
    register_command,
    register_error_provider,
)
from src.logging import get_logger
from src.collectors.topology.network_topology import get_network_topology
from src.schemas.responses import (
    NetworkOperationResult,
    ErrorResponse,
    OperationStatus,
)
from src.schemas.metadata import TopologyAdjacencyMetadata

from src.cmd.examples.example_builder import (
    ExampleBuilder,
    ExampleSet,
)

logger = get_logger(__name__)


def ip_adjacency_dump_cmd(device) -> NetworkOperationResult:
    """
    Get the complete IP adjacency dump for the entire network topology.

    This function returns all direct IP connections in the network, not just for
    the specified device. The device parameter is used for interface compliance
    but the operation is network-wide.

    Args:
        device: Device object (used for interface compliance, but operation is network-wide)

    Returns:
        NetworkOperationResult: Response object containing all IP adjacencies in the network
                              with proper ErrorResponse detection and fail-fast behavior
    """
    logger.debug("Starting topology adjacency dump for network-wide analysis")

    try:
        # Get network topology with built-in ErrorResponse detection
        topology_result = get_network_topology()

        # Check if the topology building encountered ErrorResponse
        if isinstance(topology_result.error_response, ErrorResponse):
            logger.error(
                "Failed to build topology adjacency due to gNMI errors: %s",
                topology_result.error_response.message,
            )
            # Fail fast when ErrorResponse detected
            return NetworkOperationResult(
                device_name=device.name if device else "ALL_DEVICES",
                ip_address=device.ip_address if device else "0.0.0.0",
                nos=device.nos if device else "N/A",
                operation_type="topology_adjacency",
                status=OperationStatus.FAILED,
                data={},  # Empty dict as required
                error_response=topology_result.error_response,
                metadata=TopologyAdjacencyMetadata(
                    scope="network-wide",
                    message="Failed to build topology adjacency due to gNMI errors",
                ),
            )

        # If topology was successful, check if we have connections
        if topology_result.status == OperationStatus.SUCCESS:
            connections = topology_result.data.get("direct_connections", [])
            total_connections = len(connections)

            logger.info(
                "Topology adjacency completed: %d connections found",
                total_connections,
            )

            return NetworkOperationResult(
                device_name=device.name if device else "ALL_DEVICES",
                ip_address=device.ip_address if device else "0.0.0.0",
                nos=device.nos if device else "N/A",
                operation_type="topology_adjacency",
                status=OperationStatus.SUCCESS,
                data={},  # Empty dict for both error and legitimate empty as required
                metadata=TopologyAdjacencyMetadata(
                    total_connections=total_connections,
                    scope="network-wide",
                    message=(
                        "No topology connections discovered"
                        if total_connections == 0
                        else f"Topology adjacency analysis complete with {total_connections} connections"
                    ),
                ),
            )
        else:
            # Handle other failure cases from get_network_topology
            logger.error(
                "Network topology building failed with status: %s",
                topology_result.status,
            )
            return NetworkOperationResult(
                device_name=device.name if device else "ALL_DEVICES",
                ip_address=device.ip_address if device else "0.0.0.0",
                nos=device.nos if device else "N/A",
                operation_type="topology_adjacency",
                status=OperationStatus.FAILED,
                data={},  # Empty dict as required
                error_response=topology_result.error_response,
                metadata=TopologyAdjacencyMetadata(
                    scope="network-wide",
                    message="Failed to build topology adjacency due to network topology errors",
                ),
            )

    except Exception as e:
        logger.error("Unexpected error in topology adjacency: %s", str(e))
        logger.debug("Exception details: %s", str(e), exc_info=True)
        error_response = ErrorResponse(
            type="TOPOLOGY_ADJACENCY_ERROR",
            message=f"Error building topology adjacency: {str(e)}",
        )
        return NetworkOperationResult(
            device_name=device.name if device else "ALL_DEVICES",
            ip_address=device.ip_address if device else "0.0.0.0",
            nos=device.nos if device else "N/A",
            operation_type="topology_adjacency",
            status=OperationStatus.FAILED,
            data={},  # Empty dict as required
            error_response=error_response,
            metadata=TopologyAdjacencyMetadata(
                scope="network-wide",
                message="Unexpected error during topology adjacency analysis",
            ),
        )


def topology_adjacency_examples() -> ExampleSet:
    """Build topology adjacency command examples with common patterns."""
    return ExampleBuilder.standard_command_examples(
        command=f"{CommandGroup.TOPOLOGY.group_name} {Command.TOPOLOGY_ADJACENCY.command_name}",
        alias=f"t {Command.TOPOLOGY_ADJACENCY.command_name}",
        device="R1",
        detail_option=False,  # adjacency doesn't use detail flag
        batch_operations=True,
        output_formats=True,
        alias_examples=True,
    )


def basic_usage() -> str:
    """Basic usage examples"""
    return topology_adjacency_examples().basic_only().to_string()


def detailed_examples() -> str:
    """Detailed examples"""
    return topology_adjacency_examples().for_help()


error_provider = CommandErrorProvider(Command.TOPOLOGY_ADJACENCY)
register_error_provider(Command.TOPOLOGY_ADJACENCY, error_provider)


def _get_command_help() -> str:
    return detailed_examples()


@register_command(Command.TOPOLOGY_ADJACENCY)
@click.command(help=_get_command_help())
@add_common_device_options
@click.pass_context
def topology_adjacency(ctx, device, output, devices, device_file, all_devices):
    """Get complete network topology adjacency information"""

    def operation_func(device_obj, **kwargs):
        return ip_adjacency_dump_cmd(device_obj)

    return execute_device_command(
        ctx=ctx,
        device=device,
        devices=devices,
        device_file=device_file,
        all_devices=all_devices,
        output=output,
        operation_func=operation_func,
        operation_name="topology adjacency",
    )


if __name__ == "__main__":
    print(_get_command_help())
