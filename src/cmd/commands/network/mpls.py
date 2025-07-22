#!/usr/bin/env python3
"""Network MPLS command implementation"""
import click
from src.collectors.mpls import get_mpls_info
from src.cmd.commands.base import execute_device_command
from src.cmd.commands.decorators import (
    add_common_device_options,
    add_detail_option,
)
from src.cmd.registries.command_registry import (
    register_command,
    register_error_provider,
)

from src.cmd.schemas.commands import Command
from src.cmd.error_providers import CommandErrorProvider

from src.cmd.examples.example_builder import (
    ExampleBuilder,
    ExampleSet,
)


def network_mpls_examples() -> ExampleSet:
    """Build network MPLS command examples with common patterns."""
    return ExampleBuilder.network_command_examples(
        command=Command.NETWORK_MPLS.command_name,
        device="R1",
        detail_option=True,
        batch_operations=True,
        output_formats=True,
    )


def basic_usage() -> str:
    """Basic usage examples"""
    return network_mpls_examples().basic_only().to_string()


def detailed_examples() -> str:
    """Detailed examples"""
    return network_mpls_examples().for_help()


error_provider = CommandErrorProvider(Command.NETWORK_MPLS)
register_error_provider(Command.NETWORK_MPLS, error_provider)


def _get_command_help() -> str:
    return detailed_examples()


@register_command(Command.NETWORK_MPLS)
@click.command(help=_get_command_help())
@add_common_device_options
@add_detail_option("Show detailed MPLS information")
@click.pass_context
def network_mpls(
    ctx, device, detail, output, devices, device_file, all_devices
):
    """Get MPLS information from a network device"""

    def operation_func(device_obj, **kwargs):
        return get_mpls_info(device_obj, include_details=detail)

    return execute_device_command(
        ctx=ctx,
        device=device,
        devices=devices,
        device_file=device_file,
        all_devices=all_devices,
        output=output,
        operation_func=operation_func,
        operation_name="MPLS information",
        detail=detail,
    )


if __name__ == "__main__":
    print(_get_command_help())
