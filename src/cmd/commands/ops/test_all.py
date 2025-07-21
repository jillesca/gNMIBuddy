#!/usr/bin/env python3
"""Ops test_all command implementation"""
import click
from src.cmd.commands.base import (
    execute_device_command,
    add_common_device_options,
    add_detail_option,
    CommandErrorProvider,
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
        command="ops test-all",
        alias="o test-all",
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


# Error provider instance for duck typing pattern
error_provider = CommandErrorProvider(
    command_name="test-all", group_name="ops"
)


def _get_command_help() -> str:
    return detailed_examples()


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
