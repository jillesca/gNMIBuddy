#!/usr/bin/env python3
"""Network interface command implementation"""
import click
from src.collectors.interfaces import get_interfaces
from src.cmd.commands.base import execute_device_command
from src.cmd.commands.decorators import (
    add_common_device_options,
    add_detail_option,
)
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


def network_interface_examples() -> ExampleSet:
    """Build network interface command examples with common patterns."""
    # Start with standard network command examples
    examples = ExampleBuilder.network_command_examples(
        command=Command.NETWORK_INTERFACE.command_name,
        device="R1",
        detail_option=True,
        batch_operations=True,
        output_formats=True,
    )

    # Add interface-specific examples
    examples.add_advanced(
        command=f"uv run gnmibuddy.py {CommandGroup.NETWORK.group_name} {Command.NETWORK_INTERFACE.command_name} --device R1 --name GigabitEthernet0/0/0/1",
        description="Filter by specific interface",
    ).add_advanced(
        command=f"uv run gnmibuddy.py n {Command.NETWORK_INTERFACE.command_name} --device R1 --name Gi0/0/0/1",
        description="Using alias with interface filter",
    )

    return examples


def basic_usage() -> str:
    """Basic usage examples"""
    return network_interface_examples().basic_only().to_string()


def detailed_examples() -> str:
    """Detailed examples"""
    return network_interface_examples().for_help()


error_provider = CommandErrorProvider(Command.NETWORK_INTERFACE)
register_error_provider(Command.NETWORK_INTERFACE, error_provider)


def _get_command_help() -> str:
    return detailed_examples()


@register_command(Command.NETWORK_INTERFACE)
@click.command(help=_get_command_help())
@add_common_device_options
@click.option(
    "--name", help="Filter by interface name (e.g., GigabitEthernet0/0/0/1)"
)
@add_detail_option(help_text="Show detailed interface information")
@click.pass_context
def network_interface(
    ctx, device, name, detail, output, devices, device_file, all_devices
):
    """Get interface information from a network device"""

    def operation_func(device_obj, **kwargs):
        return get_interfaces(device_obj, interface=name)

    return execute_device_command(
        ctx=ctx,
        device=device,
        devices=devices,
        device_file=device_file,
        all_devices=all_devices,
        output=output,
        operation_func=operation_func,
        operation_name="interface information",
        name=name,
        detail=detail,
    )


if __name__ == "__main__":
    print(_get_command_help())
