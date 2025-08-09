#!/usr/bin/env python3
"""Ops validate command implementation"""
import time
import concurrent.futures
from typing import Dict, Any, List

import click

from src.cmd.commands.base import execute_device_command
from src.cmd.commands.decorators import add_common_device_options
from src.cmd.schemas.commands import Command, CommandGroup
from src.cmd.error_providers import CommandErrorProvider
from src.cmd.registries.command_registry import (
    register_command,
    register_error_provider,
)
from src.logging import get_logger
from src.schemas.responses import OperationStatus, NetworkOperationResult

# Import all collector functions
from src.collectors.system import get_system_info
from src.collectors.profile import get_device_profile
from src.collectors.interfaces import get_interfaces
from src.collectors.logs import get_logs
from src.collectors.mpls import get_mpls_info
from src.collectors.routing import get_routing_info
from src.collectors.vpn import get_vpn_info
from src.collectors.topology.neighbors import neighbors
from src.collectors.topology.network_topology import get_network_topology

from src.cmd.examples.example_builder import (
    ExampleBuilder,
    ExampleSet,
)

logger = get_logger(__name__)


DESCRIPTION = """\b
Validate all collector functions on network devices

\b
This is a development tool that tests all available collector functions
to verify they work correctly after code changes. It runs comprehensive
tests on system info, interfaces, routing, MPLS, VPN, topology, and more.

\b
Use this command to quickly validate that all functionality still works
after making changes to the codebase.

\b
CONCURRENCY BEHAVIOR:
- --max-workers: Controls how many devices to process simultaneously (default: 5)
- --per-device-workers: Controls how many tests to run per device simultaneously (default: 2)
- Total concurrent requests = max_workers × per_device_workers

\b
To avoid rate limiting:
- Use --per-device-workers 1 for strict sequential testing per device
- Use --max-workers 1 --per-device-workers 2 for moderate concurrency
"""


def ops_validate_examples() -> ExampleSet:
    """Build ops validate command examples with development focus."""
    examples = ExampleBuilder.standard_command_examples(
        command=f"{CommandGroup.OPS.group_name} {Command.OPS_VALIDATE.command_name}",
        alias=f"o {Command.OPS_VALIDATE.command_name}",
        device="R1",
        detail_option=True,
        batch_operations=True,
        output_formats=True,
        alias_examples=True,
    )

    # Add development-specific examples
    examples.add_advanced(
        command=f"uv run gnmibuddy.py {CommandGroup.OPS.group_name} {Command.OPS_VALIDATE.command_name} --device R1 --test-query full",
        description="Run comprehensive validation with all tests",
    ).add_advanced(
        command=f"uv run gnmibuddy.py {CommandGroup.OPS.group_name} {Command.OPS_VALIDATE.command_name} --all-devices --summary-only",
        description="Quick validation check across all devices",
    ).add_advanced(
        command=f"uv run gnmibuddy.py o {Command.OPS_VALIDATE.command_name} --device R1 --output yaml",
        description="Development validation with YAML output for easier reading",
    ).add_advanced(
        command=f"NETWORK_INVENTORY=./inventory.json uv run gnmibuddy.py {CommandGroup.OPS.group_name} {Command.OPS_VALIDATE.command_name} --devices R1,R2,R3 --summary-only",
        description="Batch validation with environment variable and summary output",
    )

    return examples


def basic_usage() -> str:
    """Basic usage examples"""
    return ops_validate_examples().basic_only().to_string()


def detailed_examples() -> str:
    """Detailed examples"""
    return f"{DESCRIPTION}\n{ops_validate_examples().for_help()}"


error_provider = CommandErrorProvider(Command.OPS_VALIDATE)
register_error_provider(Command.OPS_VALIDATE, error_provider)


def _get_command_help() -> str:
    return detailed_examples()


def _run_collector_tests(
    device_obj,
    test_query: str = "basic",
    include_data: bool = True,
    max_workers: int = 5,
) -> Dict[str, Any]:
    """Run collector tests on a device and return a compact, non-duplicated report.

    The output format places each collector's result_data directly into a list at
    test_results.collectors, and embeds the per-device summary and metadata under
    test_results as well. This avoids repeating fields like operation_type or status
    at multiple levels.
    """
    start_time = time.time()

    # Define all collector tests
    test_functions = {
        "system_info": lambda: get_system_info(device_obj),
        "device_profile": lambda: get_device_profile(device_obj),
        "interfaces": lambda: get_interfaces(device_obj),
        "mpls_info": lambda: get_mpls_info(
            device_obj, include_details=(test_query == "full")
        ),
        "routing_info": lambda: get_routing_info(
            device_obj, include_details=(test_query == "full")
        ),
        "vpn_info": lambda: get_vpn_info(
            device_obj, include_details=(test_query == "full")
        ),
        "topology_neighbors": lambda: neighbors(device_obj),
    }

    # Add additional tests for full mode
    if test_query == "full":
        test_functions.update(
            {
                "logs": lambda: get_logs(
                    device_obj, minutes=5, show_all_logs=False
                ),
                "network_topology": lambda: get_network_topology(),
                "interfaces_detailed": lambda: get_interfaces(
                    device_obj, interface="GigabitEthernet0/0/0/1"
                ),
            }
        )

    collectors: List[Dict[str, Any]] = []
    test_summary = {
        "total_tests": len(test_functions),
        "successful": 0,
        "failed": 0,
        "feature_not_available": 0,
        "test_type": test_query,
        "device_name": device_obj.name,
    }

    # Use the smaller of max_workers or number of test functions to avoid unnecessary threads
    effective_max_workers = min(max_workers, len(test_functions))
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=effective_max_workers
    ) as executor:
        future_to_test = {
            executor.submit(test_func): test_name
            for test_name, test_func in test_functions.items()
        }

        for future in concurrent.futures.as_completed(future_to_test):
            test_name = future_to_test[future]

            try:
                result = future.result()

                if isinstance(result, NetworkOperationResult):
                    if result.status == OperationStatus.SUCCESS:
                        test_summary["successful"] += 1
                    elif (
                        result.status == OperationStatus.FEATURE_NOT_AVAILABLE
                    ):
                        test_summary["feature_not_available"] += 1
                    else:
                        test_summary["failed"] += 1

                    payload: Dict[str, Any] = {
                        "device_name": result.device_name,
                        "ip_address": result.ip_address,
                        "nos": result.nos,
                        "operation_type": result.operation_type,
                        "status": result.status.value,
                        "metadata": result.metadata,
                    }

                    if include_data:
                        payload["data"] = result.data

                    if result.error_response:
                        payload["error_response"] = {
                            "type": result.error_response.type,
                            "message": result.error_response.message,
                        }
                    if result.feature_not_found_response:
                        payload["feature_not_found_response"] = {
                            "feature_name": result.feature_not_found_response.feature_name,
                            "message": result.feature_not_found_response.message,
                        }

                    collectors.append(payload)
                else:
                    # Fallback for unexpected return types; don't fail the whole run
                    test_summary["successful"] += 1
                    payload: Dict[str, Any] = {
                        "device_name": device_obj.name,
                        "ip_address": getattr(device_obj, "ip_address", None),
                        "nos": getattr(device_obj, "nos", None),
                        "operation_type": test_name,
                        "status": OperationStatus.SUCCESS.value,
                        "metadata": {},
                    }
                    if include_data:
                        payload["data"] = result
                    collectors.append(payload)

            except (
                Exception
            ) as e:  # Keep minimal guard without duplicating logic
                logger.error(
                    "Collector %s failed for device %s: %s",
                    test_name,
                    device_obj.name,
                    str(e),
                )
                test_summary["failed"] += 1
                # Provide a compact error payload
                collectors.append(
                    {
                        "device_name": device_obj.name,
                        "ip_address": getattr(device_obj, "ip_address", None),
                        "nos": getattr(device_obj, "nos", None),
                        "operation_type": test_name,
                        "status": OperationStatus.FAILED.value,
                        "metadata": {},
                        "error_response": {
                            "type": "CollectorError",
                            "message": str(e),
                        },
                    }
                )

    total_execution_time = time.time() - start_time
    test_summary["total_execution_time"] = round(total_execution_time, 3)
    test_summary["success_rate"] = (
        round(
            (test_summary["successful"] / test_summary["total_tests"]) * 100, 2
        )
        if test_summary["total_tests"] > 0
        else 0.0
    )

    return {
        "test_results": {
            "collectors": collectors,
            "summary": test_summary,
            "metadata": {
                "device_name": device_obj.name,
                "device_ip": device_obj.ip_address,
                "device_nos": device_obj.nos,
                "test_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "test_mode": test_query,
                "include_data": include_data,
            },
        }
    }


@register_command(Command.OPS_VALIDATE)
@click.command(help=_get_command_help())
@add_common_device_options
@click.option(
    "--test-query",
    type=click.Choice(["basic", "full"]),
    default="basic",
    help="Type of validation to run",
)
@click.option(
    "--summary-only",
    is_flag=True,
    help="Show only validation summary without full data",
)
@click.option(
    "--per-device-workers",
    type=int,
    default=2,
    help="Maximum number of concurrent tests per device (default: 2, reduces rate limiting)",
)
@click.pass_context
def ops_validate(
    ctx,
    device,
    test_query,
    summary_only,
    per_device_workers,
    output,
    devices,
    device_file,
    all_devices,
):
    f"""{DESCRIPTION}
    """

    # Early inventory validation - FAIL FAST
    try:
        from src.inventory.file_handler import get_inventory_path

        inventory_path = get_inventory_path()
        logger.debug("Using inventory file: %s", inventory_path)
    except FileNotFoundError as e:
        from src.cmd.commands.error_utils import display_error_with_help

        display_error_with_help(
            ctx,
            str(e),
            "Set NETWORK_INVENTORY environment variable or use --inventory option",
        )

    # Include data by default, unless summary-only is requested
    include_data = not summary_only

    # Validate per_device_workers range
    if per_device_workers < 1:
        click.echo("Error: --per-device-workers must be at least 1", err=True)
        ctx.exit(1)
    elif per_device_workers > 10:
        click.echo(
            "Warning: --per-device-workers > 10 may cause rate limiting issues",
            err=True,
        )

    def operation_func(device_obj, **kwargs):
        logger.info(
            "Running %s validation suite on device: %s (concurrency: %d)",
            test_query,
            device_obj.name,
            per_device_workers,
        )
        return _run_collector_tests(
            device_obj, test_query, include_data, per_device_workers
        )

    return execute_device_command(
        ctx=ctx,
        device=device,
        devices=devices,
        device_file=device_file,
        all_devices=all_devices,
        output=output,
        operation_func=operation_func,
        operation_name="validate",
        test_query=test_query,
    )


if __name__ == "__main__":
    print(_get_command_help())
