#!/usr/bin/env python3
"""Network interface command implementation"""
import click
from src.collectors.interfaces import get_interfaces
from src.cmd.commands.base import (
    execute_device_command,
    add_common_device_options,
)


@click.command()
@add_common_device_options
@click.option(
    "--name", help="Filter by interface name (e.g., GigabitEthernet0/0/0/1)"
)
@click.option(
    "--detail", is_flag=True, help="Show detailed interface information"
)
@click.pass_context
def network_interface(
    ctx, device, name, detail, output, devices, device_file, all_devices
):
    """Get interface information from a network device

    \b
    Examples:
      gnmibuddy network interface --device R1
      gnmibuddy network interface --device R1 --name GigabitEthernet0/0/0/1
      gnmibuddy network interface --device R1 --detail
      gnmibuddy network interface --device R1 --output yaml
      gnmibuddy network interface --devices R1,R2,R3
      gnmibuddy network interface --all-devices
      gnmibuddy n interface --device R1  # Using alias
    """

    def operation_func(device_obj, **kwargs):
        return get_interfaces(device_obj, interface=name)

    return execute_device_command(
        ctx=ctx,
        device=device,
        devices=devices,
        device_file=device_file,
        all_devices=all_devices,
        output=output,
        operation_func=operation_func,
        operation_name="interface information",
        name=name,
        detail=detail,
    )
