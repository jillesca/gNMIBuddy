#!/usr/bin/env python3
"""Network interface command implementation"""
import click
from src.collectors.interfaces import get_interfaces
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


def network_interface_examples() -> ExampleSet:
    """Build network interface command examples with common patterns."""
    # Start with standard network command examples
    examples = ExampleBuilder.network_command_examples(
        command="interface",
        device="R1",
        detail_option=True,
        batch_operations=True,
        output_formats=True,
    )

    # Add interface-specific examples
    examples.add_advanced(
        command="uv run gnmibuddy.py network interface --device R1 --name GigabitEthernet0/0/0/1",
        description="Filter by specific interface",
    ).add_advanced(
        command="uv run gnmibuddy.py n interface --device R1 --name Gi0/0/0/1",
        description="Using alias with interface filter",
    )

    return examples


def basic_usage() -> str:
    """Basic usage examples"""
    return network_interface_examples().basic_only().to_string()


def detailed_examples() -> str:
    """Detailed examples"""
    return network_interface_examples().for_help()


# Custom error provider for interface-specific scenarios
class InterfaceErrorProvider(CommandErrorProvider):
    """Custom error provider for network interface command with interface-specific errors."""

    def __init__(self):
        super().__init__(command_name="interface", group_name="network")

    def get_missing_interface_name_examples(self) -> ExampleSet:
        """Get examples for missing --name option errors (interface-specific)."""
        examples = ExampleSet("interface_missing_name_errors")

        examples.add_error_missing_device(
            command="uv run gnmibuddy.py network interface --device R1 --name GigabitEthernet0/0/0/1",
            description="Specify interface name",
        )

        return examples

    def get_examples_for_error_type(
        self, error_type: str, **kwargs
    ) -> ExampleSet:
        """
        Override to handle interface-specific error types.
        """
        if error_type == "missing_interface_name":
            return self.get_missing_interface_name_examples()

        # Fall back to parent class for common error types
        return super().get_examples_for_error_type(error_type, **kwargs)


# Error provider instance for duck typing pattern - using custom provider
error_provider = InterfaceErrorProvider()


def _get_command_help() -> str:
    return detailed_examples()


@click.command(help=_get_command_help())
@add_common_device_options
@click.option(
    "--name", help="Filter by interface name (e.g., GigabitEthernet0/0/0/1)"
)
@add_detail_option(help_text="Show detailed interface information")
@click.pass_context
def network_interface(
    ctx, device, name, detail, output, devices, device_file, all_devices
):
    """Get interface information from a network device"""

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


if __name__ == "__main__":
    print(_get_command_help())
