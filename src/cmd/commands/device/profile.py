#!/usr/bin/env python3
"""Device profile command implementation"""
import click
from src.collectors.profile import get_device_profile
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


def device_profile_examples() -> ExampleSet:
    """Build device profile command examples with common patterns."""
    return ExampleBuilder.standard_command_examples(
        command=f"{CommandGroup.DEVICE.group_name} {Command.DEVICE_PROFILE.command_name}",
        alias=f"d {Command.DEVICE_PROFILE.command_name}",
        device="R1",
        detail_option=True,
        batch_operations=True,
        output_formats=True,
        alias_examples=True,
    )


def basic_usage() -> str:
    """Basic usage examples"""
    return device_profile_examples().basic_only().to_string()


def detailed_examples() -> str:
    """Detailed examples"""
    return device_profile_examples().for_help()


error_provider = CommandErrorProvider(Command.DEVICE_PROFILE)
register_error_provider(Command.DEVICE_PROFILE, error_provider)


def _get_command_help() -> str:
    return detailed_examples()


@register_command(Command.DEVICE_PROFILE)
@click.command(help=_get_command_help())
@add_common_device_options
@add_detail_option(help_text="Show detailed profile analysis")
@click.pass_context
def device_profile(
    ctx, device, detail, output, devices, device_file, all_devices
):
    """Get device profile information from a network device"""

    def operation_func(device_obj, **kwargs):
        return get_device_profile(device_obj)

    return execute_device_command(
        ctx=ctx,
        device=device,
        devices=devices,
        device_file=device_file,
        all_devices=all_devices,
        output=output,
        operation_func=operation_func,
        operation_name="device profile",
        detail=detail,
    )


if __name__ == "__main__":
    print(_get_command_help())
