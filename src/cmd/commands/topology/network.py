#!/usr/bin/env python3
"""Network topology command implementation"""
import click

from src.cmd.commands.decorators import add_output_option
from src.cmd.schemas.commands import Command, CommandGroup
from src.cmd.error_providers import CommandErrorProvider
from src.cmd.registries.command_registry import (
    register_command,
    register_error_provider,
)
from src.cmd.examples.example_builder import (
    ExampleBuilder,
    ExampleSet,
)
from src.cmd.formatters import format_output
from src.logging import get_logger
from src.collectors.topology.network_topology import get_network_topology
from src.services.commands import run_network_wide


logger = get_logger(__name__)


def topology_network_examples() -> ExampleSet:
    """Build topology network command examples with common patterns."""
    examples = ExampleBuilder.simple_command_examples(
        command=f"{CommandGroup.TOPOLOGY.group_name} {Command.TOPOLOGY_NETWORK.command_name}",
        description="Get complete network topology. Queries all devices in inventory.",
    )

    # Add network topology specific examples
    examples.add_advanced(
        command=f"uv run gnmibuddy.py {CommandGroup.TOPOLOGY.group_name} {Command.TOPOLOGY_NETWORK.command_name} --output json",
        description="Output network topology as JSON",
    ).add_advanced(
        command=f"uv run gnmibuddy.py t {Command.TOPOLOGY_NETWORK.command_name}",
        description="Get network topology with alias",
    )

    return examples


def basic_usage() -> str:
    """Basic usage examples"""
    return topology_network_examples().basic_only().to_string()


def detailed_examples() -> str:
    """Detailed examples"""
    return topology_network_examples().for_help()


error_provider = CommandErrorProvider(Command.TOPOLOGY_NETWORK)
register_error_provider(Command.TOPOLOGY_NETWORK, error_provider)


def _get_command_help() -> str:
    return detailed_examples()


@register_command(Command.TOPOLOGY_NETWORK)
@click.command(help=_get_command_help())
@add_output_option
@click.pass_context
def topology_network(ctx, output):
    """Get complete network topology information for all devices"""

    logger.info("Getting complete network topology")

    # Call the network topology collector function (network-wide operation)
    result = run_network_wide(get_network_topology)

    formatted_output = format_output(result, output.lower())
    click.echo(formatted_output)
    return result


if __name__ == "__main__":
    print(_get_command_help())
