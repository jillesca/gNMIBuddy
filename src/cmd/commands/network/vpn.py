#!/usr/bin/env python3
"""Network VPN command implementation"""
import click
from src.collectors.vpn import get_vpn_info
from src.cmd.commands.base import (
    execute_device_command,
    add_common_device_options,
)


@click.command()
@add_common_device_options
@click.option("--vrf-name", help="Filter by VRF name (e.g., CUSTOMER_A)")
@click.option("--detail", is_flag=True, help="Show detailed VPN information")
@click.pass_context
def network_vpn(
    ctx, device, vrf_name, detail, output, devices, device_file, all_devices
):
    """Get VPN/VRF information from a network device

    \b
    Examples:
      uv run gnmibuddy.py network vpn --device R1
      uv run gnmibuddy.py network vpn --device R1 --vrf-name CUSTOMER_A
      uv run gnmibuddy.py network vpn --device R1 --detail
      uv run gnmibuddy.py network vpn --devices R1,R2,R3
      uv run gnmibuddy.py network vpn --all-devices
      uv run gnmibuddy.py n vpn --device R1  # Using alias
    """

    def operation_func(device_obj, **kwargs):
        return get_vpn_info(
            device_obj, vrf_name=vrf_name, include_details=detail
        )

    return execute_device_command(
        ctx=ctx,
        device=device,
        devices=devices,
        device_file=device_file,
        all_devices=all_devices,
        output=output,
        operation_func=operation_func,
        operation_name="VPN information",
        vrf_name=vrf_name,
        detail=detail,
    )
