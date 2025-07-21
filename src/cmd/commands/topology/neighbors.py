#!/usr/bin/env python3
"""Topology neighbors command implementation"""
import click

from src.inventory.manager import InventoryManager
from src.cmd.commands.base import (
    add_common_device_options,
)
from src.cmd.schemas import Command, CommandGroup
from src.cmd.error_providers import CommandErrorProvider
from src.cmd.registries.command_registry import (
    register_command,
    register_error_provider,
)
from src.schemas.models import DeviceErrorResult
from src.logging.config import get_logger
from src.collectors.topology.neighbors import neighbors

from src.cmd.examples.example_builder import (
    ExampleBuilder,
    ExampleSet,
)

logger = get_logger(__name__)


def topology_neighbors_examples() -> ExampleSet:
    """Build topology neighbors command examples with common patterns."""
    return ExampleBuilder.standard_command_examples(
        command=f"{CommandGroup.TOPOLOGY.group_name} {Command.TOPOLOGY_NEIGHBORS.command_name}",
        alias=f"t {Command.TOPOLOGY_NEIGHBORS.command_name}",
        device="R1",
        detail_option=True,
        batch_operations=True,
        output_formats=True,
        alias_examples=True,
    )


def basic_usage() -> str:
    """Basic usage examples"""
    return topology_neighbors_examples().basic_only().to_string()


def detailed_examples() -> str:
    """Detailed examples"""
    return topology_neighbors_examples().for_help()


error_provider = CommandErrorProvider(Command.TOPOLOGY_NEIGHBORS)
register_error_provider(Command.TOPOLOGY_NEIGHBORS, error_provider)


def _get_command_help() -> str:
    return detailed_examples()


@register_command(Command.TOPOLOGY_NEIGHBORS)
@click.command(help=_get_command_help())
@click.option("--device", required=True, help="Device name from inventory")
@add_common_device_options
@click.pass_context
def topology_neighbors(ctx, device, output):
    """Get topology neighbors information"""
    logger.info("Getting topology neighbors for device: %s", device)

    # Get device object from inventory
    device_obj = InventoryManager.get_device(device)
    if isinstance(device_obj, DeviceErrorResult):
        click.echo(f"Error: {device_obj.msg}", err=True)
        raise click.Abort()

    # Call the topology neighbors collector function
    result = neighbors(device_obj)

    # Format and return the result
    from src.cmd.formatters import format_output

    formatted_output = format_output(result, output.lower())
    click.echo(formatted_output)
    return result


if __name__ == "__main__":
    print(_get_command_help())
