#!/usr/bin/env python3
"""Device capabilities command implementation"""
import click

from src.cmd.commands.base import execute_device_command
from src.cmd.commands.decorators import add_common_device_options
from src.cmd.schemas import Command, CommandGroup
from src.cmd.error_providers import CommandErrorProvider
from src.cmd.registries.command_registry import (
    register_command,
    register_error_provider,
)
from src.collectors.capabilities import get_device_capabilities
from src.cmd.examples.example_builder import ExampleBuilder, ExampleSet

DESCRIPTION = """\b
Get gNMI capabilities from a network device.

By default, shows a focused summary of required OpenConfig models with status
(ok/older/not_supported/unknown), the device's gNMI version, and encodings.
Use --all-models to list every supported model and encoding.

When a model is older than required, a warning is shown and some collectors may
not work correctly. Consider updating the device's OpenConfig model/version.
"""


def device_capabilities_examples() -> ExampleSet:
    return ExampleBuilder.standard_command_examples(
        command=f"{CommandGroup.DEVICE.group_name} {Command.DEVICE_CAPABILITIES.command_name}",
        alias=f"d {Command.DEVICE_CAPABILITIES.command_name}",
        device="R1",
        detail_option=False,
        batch_operations=True,
        output_formats=True,
        alias_examples=True,
    )


def detailed_examples() -> str:
    return f"{DESCRIPTION}\n{device_capabilities_examples().for_help()}"


def _get_command_help() -> str:
    return detailed_examples()


error_provider = CommandErrorProvider(Command.DEVICE_CAPABILITIES)
register_error_provider(Command.DEVICE_CAPABILITIES, error_provider)


@register_command(Command.DEVICE_CAPABILITIES)
@click.command(help=_get_command_help())
@add_common_device_options
@click.option(
    "--all-models",
    is_flag=True,
    default=False,
    help="Show all supported models (by default only required models with status are shown)",
)
@click.pass_context
def device_capabilities(
    ctx, device, output, devices, device_file, all_devices, all_models
):
    """Get gNMI capabilities from a network device"""

    def operation_func(device_obj, **kwargs):
        # Pass flag positionally to avoid name mismatch across versions
        return get_device_capabilities(device_obj, all_models)

    return execute_device_command(
        ctx=ctx,
        device=device,
        devices=devices,
        device_file=device_file,
        all_devices=all_devices,
        output=output,
        operation_func=operation_func,
        operation_name="capabilities",
    )


if __name__ == "__main__":
    print(_get_command_help())
