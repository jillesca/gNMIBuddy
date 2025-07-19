#!/usr/bin/env python3
"""Device profile command implementation"""
import click
from src.collectors.profile import get_device_profile
from src.cmd.commands.base import (
    execute_device_command,
    add_common_device_options,
)


@click.command()
@add_common_device_options
@click.option("--detail", is_flag=True, help="Show detailed profile analysis")
@click.pass_context
def device_profile(
    ctx, device, detail, output, devices, device_file, all_devices
):
    """Get device profile information from a network device

    \b
    Examples:
      uv run gnmibuddy.py device profile --device R1
      uv run gnmibuddy.py device profile --device R1 --detail
      uv run gnmibuddy.py device profile --devices R1,R2,R3
      uv run gnmibuddy.py device profile --all-devices
      uv run gnmibuddy.py d profile --device R1  # Using alias
    """

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
