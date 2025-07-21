#!/usr/bin/env python3
"""Ops test_all command implementation"""
import click
from src.cmd.commands.base import (
    execute_device_command,
    add_common_device_options,
    add_detail_option,
)
from src.cmd.schemas.commands import Command, CommandGroup
from src.cmd.error_providers import CommandErrorProvider
from src.cmd.registries.command_registry import (
    register_command,
    register_error_provider,
)
from src.logging.config import get_logger

from src.cmd.examples.example_builder import (
    ExampleBuilder,
    ExampleSet,
)

logger = get_logger(__name__)


def ops_test_all_examples() -> ExampleSet:
    """Build ops test-all command examples with common patterns."""
    return ExampleBuilder.standard_command_examples(
        command=f"{CommandGroup.OPS.group_name} {Command.OPS_TEST_ALL.command_name}",
        alias=f"o {Command.OPS_TEST_ALL.command_name}",
        device="R1",
        detail_option=True,
        batch_operations=True,
        output_formats=True,
        alias_examples=True,
    )


def basic_usage() -> str:
    """Basic usage examples"""
    return ops_test_all_examples().basic_only().to_string()


def detailed_examples() -> str:
    """Detailed examples"""
    return ops_test_all_examples().for_help()


error_provider = CommandErrorProvider(Command.OPS_TEST_ALL)
register_error_provider(Command.OPS_TEST_ALL, error_provider)


def _get_command_help() -> str:
    return detailed_examples()


@register_command(Command.OPS_TEST_ALL)
@click.command(help=_get_command_help())
@add_common_device_options
@click.option(
    "--test-query",
    type=click.Choice(["basic", "full"]),
    default="basic",
    help="Type of test to run",
)
@click.pass_context
def ops_test_all(
    ctx, device, test_query, output, devices, device_file, all_devices
):
    """Test all APIs on a network device"""

    def operation_func(device_obj, **kwargs):
        # This is a placeholder implementation
        # TODO: Implement actual test-all functionality
        return {
            "device": (
                device_obj.name
                if hasattr(device_obj, "name")
                else str(device_obj)
            ),
            "test_type": test_query,
            "status": "completed",
        }

    return execute_device_command(
        ctx=ctx,
        device=device,
        devices=devices,
        device_file=device_file,
        all_devices=all_devices,
        output=output,
        operation_func=operation_func,
        operation_name="test-all",
        test_query=test_query,
    )


if __name__ == "__main__":
    print(_get_command_help())
