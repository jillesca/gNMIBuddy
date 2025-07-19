#!/usr/bin/env python3
"""Network MPLS command implementation"""
import click
from src.collectors.mpls import get_mpls_info
from src.cmd.commands.base import (
    execute_device_command,
    add_common_device_options,
    add_detail_option,
)


@click.command()
@add_common_device_options
@add_detail_option("Show detailed MPLS information")
@click.pass_context
def network_mpls(
    ctx, device, detail, output, devices, device_file, all_devices
):
    """Get MPLS information from a network device

    \b
    Examples:
      uv run gnmibuddy.py network mpls --device R1
      uv run gnmibuddy.py network mpls --device R1 --detail
      uv run gnmibuddy.py network mpls --devices R1,R2,R3
      uv run gnmibuddy.py network mpls --all-devices
      uv run gnmibuddy.py n mpls --device R1  # Using alias
    """

    def operation_func(device_obj, **kwargs):
        return get_mpls_info(device_obj, include_details=detail)

    return execute_device_command(
        ctx=ctx,
        device=device,
        devices=devices,
        device_file=device_file,
        all_devices=all_devices,
        output=output,
        operation_func=operation_func,
        operation_name="MPLS information",
        detail=detail,
    )
