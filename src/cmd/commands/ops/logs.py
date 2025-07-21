#!/usr/bin/env python3
"""Ops logs command implementation"""
import click
from src.collectors.logs import get_logs
from src.cmd.commands.base import (
    execute_device_command,
    add_common_device_options,
    CommandErrorProvider,
)

from src.cmd.examples.example_builder import (
    ExampleBuilder,
    ExampleSet,
)


def ops_logs_examples() -> ExampleSet:
    """Build ops logs command examples with common patterns."""
    examples = ExampleBuilder.standard_command_examples(
        command="ops logs",
        alias="o logs",
        device="R1",
        detail_option=False,  # logs doesn't use detail flag
        batch_operations=True,
        output_formats=True,
        alias_examples=True,
    )

    # Add log-specific examples
    examples.add_advanced(
        command="uv run gnmibuddy.py ops logs --device R1 --minutes 20",
        description="Specify time range",
    ).add_advanced(
        command="uv run gnmibuddy.py ops logs --device R1 --show-all-logs",
        description="Show all available logs",
    ).add_advanced(
        command="uv run gnmibuddy.py o logs --device R1 --minutes 5",
        description="Using alias with time filter",
    )

    return examples


def basic_usage() -> str:
    """Basic usage examples"""
    return ops_logs_examples().basic_only().to_string()


def detailed_examples() -> str:
    """Detailed examples"""
    return ops_logs_examples().for_help()


# Error provider instance for duck typing pattern
error_provider = CommandErrorProvider(command_name="logs", group_name="ops")


def _get_command_help() -> str:
    return detailed_examples()


@click.command(help=_get_command_help())
@add_common_device_options
@click.option(
    "--minutes",
    type=int,
    default=10,
    help="Number of minutes of logs to retrieve",
)
@click.option(
    "--show-all-logs", is_flag=True, help="Show all available log entries"
)
@click.pass_context
def ops_logs(
    ctx,
    device,
    minutes,
    show_all_logs,
    output,
    devices,
    device_file,
    all_devices,
):
    """Get log information from a network device"""

    def operation_func(device_obj, **kwargs):
        return get_logs(
            device_obj, minutes=minutes, show_all_logs=show_all_logs
        )

    # TODO: Chech if show_all_logs exists in the device
    return execute_device_command(
        ctx=ctx,
        device=device,
        devices=devices,
        device_file=device_file,
        all_devices=all_devices,
        output=output,
        operation_func=operation_func,
        operation_name="logs",
        minutes=minutes,
        show_all_logs=show_all_logs,
    )


if __name__ == "__main__":
    print(_get_command_help())
