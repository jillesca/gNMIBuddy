#!/usr/bin/env python3
"""Network VPN command implementation"""
import click
from src.collectors.vpn import get_vpn_info
from src.cmd.commands.base import (
    execute_device_command,
    add_common_device_options,
    add_detail_option,
    CommandErrorProvider,
)

from src.cmd.examples.example_builder import (
    ExampleBuilder,
    ExampleSet,
)


def network_vpn_examples() -> ExampleSet:
    """Build network VPN command examples with common patterns."""
    # Start with standard network command examples
    examples = ExampleBuilder.network_command_examples(
        command="vpn",
        device="R1",
        detail_option=True,
        batch_operations=True,
        output_formats=True,
    )

    # Add VRF-specific examples
    examples.add_advanced(
        command="uv run gnmibuddy.py network vpn --device R1 --vrf-name CUSTOMER_A",
        description="Filter by specific VRF",
    ).add_advanced(
        command="uv run gnmibuddy.py n vpn --device R1 --vrf-name MGMT",
        description="Using alias with VRF filter",
    )

    return examples


def basic_usage() -> str:
    """Basic usage examples"""
    return network_vpn_examples().basic_only().to_string()


def detailed_examples() -> str:
    """Detailed examples"""
    return network_vpn_examples().for_help()


# Error provider instance for duck typing pattern
error_provider = CommandErrorProvider(command_name="vpn", group_name="network")


def _get_command_help() -> str:
    return detailed_examples()


@click.command(help=_get_command_help())
@add_common_device_options
@click.option("--vrf-name", help="Filter by VRF name (e.g., CUSTOMER_A)")
@add_detail_option(help_text="Show detailed VPN information")
@click.pass_context
def network_vpn(
    ctx, device, vrf_name, detail, output, devices, device_file, all_devices
):
    """Get VPN/VRF information from a network device"""

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


if __name__ == "__main__":
    print(_get_command_help())
