#!/usr/bin/env python3
"""Ops logs command implementation"""
import click
from src.collectors.logs import get_logs
from src.cmd.commands.base import (
    execute_device_command,
    add_common_device_options,
)


@click.command()
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
    """Get log information from a network device

    \b
    Examples:
      uv run gnmibuddy.py ops logs --device R1
      uv run gnmibuddy.py ops logs --device R1 --minutes 20
      uv run gnmibuddy.py ops logs --device R1 --show-all-logs
      uv run gnmibuddy.py ops logs --devices R1,R2,R3
      uv run gnmibuddy.py ops logs --all-devices
      uv run gnmibuddy.py o logs --device R1  # Using alias
    """

    def operation_func(device_obj, **kwargs):
        return get_logs(
            device_obj, minutes=minutes, show_all_logs=show_all_logs
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
        minutes=minutes,
        show_all_logs=show_all_logs,
    )
