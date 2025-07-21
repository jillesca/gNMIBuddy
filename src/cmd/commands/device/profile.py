#!/usr/bin/env python3
"""Device profile command implementation"""
import click
from src.collectors.profile import get_device_profile
from src.cmd.commands.base import (
    execute_device_command,
    add_common_device_options,
    add_detail_option,
    CommandErrorProvider,
)

from src.cmd.examples.example_builder import (
    ExampleBuilder,
    ExampleSet,
)


def device_profile_examples() -> ExampleSet:
    """Build device profile command examples with common patterns."""
    return ExampleBuilder.standard_command_examples(
        command="device profile",
        alias="d profile",
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


# Error provider instance for duck typing pattern
error_provider = CommandErrorProvider(
    command_name="profile", group_name="device"
)


def _get_command_help() -> str:
    return detailed_examples()


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
