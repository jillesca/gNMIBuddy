#!/usr/bin/env python3
"""Device list command implementation"""
import click

from src.logging import get_logger
from src.cmd.formatters import format_output
from src.inventory.manager import InventoryManager
from src.schemas.models import DeviceListCommandResult
from src.cmd.commands.decorators import (
    add_detail_option,
    add_output_option,
)
from src.cmd.schemas import Command, CommandGroup
from src.cmd.error_providers import CommandErrorProvider
from src.cmd.registries.command_registry import (
    register_command,
    register_error_provider,
)

from src.cmd.examples.example_builder import (
    ExampleBuilder,
    ExampleSet,
)


def device_list_examples() -> ExampleSet:
    """Build device list command examples with common patterns."""
    examples = ExampleBuilder.simple_command_examples(
        command=f"{CommandGroup.DEVICE.group_name} {Command.DEVICE_LIST.command_name}",
        description="List all devices in inventory",
    )

    # Add device list specific examples
    examples.add_advanced(
        command=f"uv run gnmibuddy.py {CommandGroup.DEVICE.group_name} {Command.DEVICE_LIST.command_name} --detail",
        description="Show detailed device information",
    ).add_advanced(
        command=f"uv run gnmibuddy.py d {Command.DEVICE_LIST.command_name} --output json",
        description="Output as JSON with alias",
    )

    return examples


def basic_usage() -> str:
    """Basic usage examples"""
    return device_list_examples().basic_only().to_string()


def detailed_examples() -> str:
    """Detailed examples"""
    return device_list_examples().for_help()


def _get_command_help() -> str:
    return detailed_examples()


error_provider = CommandErrorProvider(Command.DEVICE_LIST)
register_error_provider(Command.DEVICE_LIST, error_provider)


@register_command(Command.DEVICE_LIST)
@click.command(help=_get_command_help())
@add_detail_option(help_text="Show detailed device information")
@add_output_option
@click.pass_context
def device_list(ctx, detail, output):
    """List all available devices in the inventory"""

    logger = get_logger(__name__)
    logger.info("Listing all available devices")

    # Use the list_devices method instead of direct access to get_devices
    try:
        device_list_result = InventoryManager.list_devices()
    except FileNotFoundError as e:
        # Handle inventory not found error gracefully
        from src.cmd.commands.base import handle_inventory_error_in_command

        handle_inventory_error_in_command(str(e))
        raise click.Abort()

    if not device_list_result.devices:
        result = DeviceListCommandResult(
            devices=[],
            count=0,
            detail=detail,
            message="No devices found in inventory",
        )
        formatted_output = format_output(result, output.lower())
        click.echo(formatted_output)
        return result

    if detail:
        result = DeviceListCommandResult(
            devices=device_list_result.devices,
            count=len(device_list_result.devices),
            detail=detail,
        )
        formatted_output = format_output(result, output.lower())
        click.echo(formatted_output)
        return result

    result = DeviceListCommandResult(
        devices=[device.name for device in device_list_result.devices],
        count=len(device_list_result.devices),
        detail=detail,
    )
    formatted_output = format_output(result, output.lower())
    click.echo(formatted_output)
    return result


if __name__ == "__main__":
    print(_get_command_help())
