#!/usr/bin/env python3
"""Ops logs command implementation"""
import click
from src.collectors.logs import get_logs
from src.cmd.commands.base import execute_device_command
from src.cmd.commands.decorators import add_common_device_options
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


def ops_logs_examples() -> ExampleSet:
    """Build ops logs command examples with common patterns."""
    examples = ExampleBuilder.standard_command_examples(
        command=f"{CommandGroup.OPS.group_name} {Command.OPS_LOGS.command_name}",
        alias=f"o {Command.OPS_LOGS.command_name}",
        device="R1",
        detail_option=False,  # logs doesn't use detail flag
        batch_operations=True,
        output_formats=True,
        alias_examples=True,
    )

    # Add log-specific examples
    examples.add_advanced(
        command=f"uv run gnmibuddy.py {CommandGroup.OPS.group_name} {Command.OPS_LOGS.command_name} --device R1 --minutes 20",
        description="Specify time range",
    ).add_advanced(
        command=f"uv run gnmibuddy.py {CommandGroup.OPS.group_name} {Command.OPS_LOGS.command_name} --device R1 --keywords 'error|warning'",
        description="Filter logs by keywords",
    ).add_advanced(
        command=f"uv run gnmibuddy.py {CommandGroup.OPS.group_name} {Command.OPS_LOGS.command_name} --device R1 --show-all-logs",
        description="Show all available logs",
    ).add_advanced(
        command=f"uv run gnmibuddy.py o {Command.OPS_LOGS.command_name} --device R1 --minutes 5",
        description="Using alias with time filter",
    )

    return examples


def basic_usage() -> str:
    """Basic usage examples"""
    return ops_logs_examples().basic_only().to_string()


def detailed_examples() -> str:
    """Detailed examples"""
    return ops_logs_examples().for_help()


error_provider = CommandErrorProvider(Command.OPS_LOGS)
register_error_provider(Command.OPS_LOGS, error_provider)


def _get_command_help() -> str:
    return detailed_examples()


@register_command(Command.OPS_LOGS)
@click.command(help=_get_command_help())
@add_common_device_options
@click.option(
    "--keywords",
    type=str,
    help="Filter logs by keywords",
)
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
    keywords,
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
            device_obj,
            keywords=keywords,
            minutes=minutes,
            show_all_logs=show_all_logs,
        )

    return execute_device_command(
        ctx=ctx,
        device=device,
        devices=devices,
        device_file=device_file,
        all_devices=all_devices,
        output=output,
        operation_func=operation_func,
        operation_name="logs",
        keywords=keywords,
        minutes=minutes,
        show_all_logs=show_all_logs,
    )


if __name__ == "__main__":
    print(_get_command_help())
