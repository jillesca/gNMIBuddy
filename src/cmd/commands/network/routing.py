#!/usr/bin/env python3
"""Network routing command implementation"""
import click
from src.collectors.routing import get_routing_info
from src.cmd.commands.base import (
    execute_device_command,
    add_common_device_options,
)


@click.command()
@add_common_device_options
@click.option(
    "--protocol",
    type=click.Choice(["bgp", "isis", "ospf"]),
    help="Filter by routing protocol",
)
@click.option(
    "--detail", is_flag=True, help="Show detailed routing information"
)
@click.pass_context
def network_routing(
    ctx, device, protocol, detail, output, devices, device_file, all_devices
):
    """Get routing information from a network device

    \b
    Examples:
      uv run gnmibuddy.py network routing --device R1
      uv run gnmibuddy.py network routing --device R1 --protocol bgp
      uv run gnmibuddy.py network routing --device R1 --detail
      uv run gnmibuddy.py network routing --device R1 --output yaml
      uv run gnmibuddy.py network routing --devices R1,R2,R3
      uv run gnmibuddy.py network routing --all-devices
      uv run gnmibuddy.py n routing --device R1  # Using alias
    """

    def operation_func(device_obj, **kwargs):
        return get_routing_info(device_obj)

    return execute_device_command(
        ctx=ctx,
        device=device,
        devices=devices,
        device_file=device_file,
        all_devices=all_devices,
        output=output,
        operation_func=operation_func,
        operation_name="routing information",
        protocol=protocol,
        detail=detail,
    )
