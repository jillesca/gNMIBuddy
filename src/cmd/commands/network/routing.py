#!/usr/bin/env python3
"""Network routing command implementation"""
import click
from src.collectors.routing import get_routing_info
from src.cmd.commands.base import execute_device_command
from src.cmd.commands.decorators import (
    add_common_device_options,
    add_detail_option,
)
from src.cmd.schemas.commands import Command
from src.cmd.error_providers import CommandErrorProvider
from src.cmd.registries.command_registry import (
    register_command,
    register_error_provider,
)

from src.cmd.examples.example_builder import (
    ExampleBuilder,
    ExampleSet,
)


def network_routing_examples() -> ExampleSet:
    """Build network routing command examples with common patterns."""
    return ExampleBuilder.network_command_examples(
        command=Command.NETWORK_ROUTING.command_name,
        device="R1",
        detail_option=True,
        batch_operations=True,
        output_formats=True,
    )


def basic_usage() -> str:
    """Basic usage examples"""
    return network_routing_examples().basic_only().to_string()


def detailed_examples() -> str:
    """Detailed examples"""
    return network_routing_examples().for_help()


error_provider = CommandErrorProvider(Command.NETWORK_ROUTING)
register_error_provider(Command.NETWORK_ROUTING, error_provider)


def _get_command_help() -> str:
    return detailed_examples()


@register_command(Command.NETWORK_ROUTING)
@click.command(help=_get_command_help())
@add_common_device_options
@click.option(
    "--protocol",
    type=click.Choice(["bgp", "isis", "ospf"]),
    help="Filter by routing protocol",
)
@add_detail_option(help_text="Show detailed routing information")
@click.pass_context
def network_routing(
    ctx, device, protocol, detail, output, devices, device_file, all_devices
):
    """Get routing information from a network device"""

    def operation_func(device_obj, **kwargs):
        return get_routing_info(
            device_obj, protocol=protocol, include_details=detail
        )

    return execute_device_command(
        ctx=ctx,
        device=device,
        devices=devices,
        device_file=device_file,
        all_devices=all_devices,
        output=output,
        operation_func=operation_func,
        operation_name="routing information",
        protocol=protocol,
        detail=detail,
    )


if __name__ == "__main__":
    print(_get_command_help())
