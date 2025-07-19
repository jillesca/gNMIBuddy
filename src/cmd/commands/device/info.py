#!/usr/bin/env python3
"""Device info command implementation"""
import click

from src.cmd.commands.base import (
    execute_device_command,
    add_common_device_options,
)
from src.collectors.system import get_system_info


@click.command()
@add_common_device_options
@click.option(
    "--detail", is_flag=True, help="Show detailed system information"
)
@click.pass_context
def device_info(
    ctx, device, detail, output, devices, device_file, all_devices
):
    """Get system information from a network device

    \b
    Examples:
      gnmibuddy device info --device R1
      gnmibuddy device info --device PE1 --detail
      gnmibuddy device info --device R1 --output json
      gnmibuddy device info --device R1 --output yaml
      gnmibuddy device info --devices R1,R2,R3
      gnmibuddy device info --all-devices
      gnmibuddy d info --device R1  # Using alias
    """

    def operation_func(device_obj, **kwargs):
        return get_system_info(device_obj)

    return execute_device_command(
        ctx=ctx,
        device=device,
        devices=devices,
        device_file=device_file,
        all_devices=all_devices,
        output=output,
        operation_func=operation_func,
        operation_name="system information",
        detail=detail,
    )
