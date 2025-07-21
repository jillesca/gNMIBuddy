#!/usr/bin/env python3
"""Ops test_all command implementation"""
import time
import concurrent.futures
from typing import Dict, Any

import click

from src.cmd.commands.base import (
    execute_device_command,
    add_common_device_options,
)
from src.cmd.schemas.commands import Command, CommandGroup
from src.cmd.error_providers import CommandErrorProvider
from src.cmd.registries.command_registry import (
    register_command,
    register_error_provider,
)
from src.logging.config import get_logger
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
from src.collectors.topology.ip_adjacency_dump import ip_adjacency_dump

from src.cmd.examples.example_builder import (
    ExampleBuilder,
    ExampleSet,
)

logger = get_logger(__name__)


def ops_test_all_examples() -> ExampleSet:
    """Build ops test-all command examples with common patterns."""
    return ExampleBuilder.standard_command_examples(
        command=f"{CommandGroup.OPS.group_name} {Command.OPS_TEST_ALL.command_name}",
        alias=f"o {Command.OPS_TEST_ALL.command_name}",
        device="R1",
        detail_option=True,
        batch_operations=True,
        output_formats=True,
        alias_examples=True,
    )


def basic_usage() -> str:
    """Basic usage examples"""
    return ops_test_all_examples().basic_only().to_string()


def detailed_examples() -> str:
    """Detailed examples"""
    return ops_test_all_examples().for_help()


error_provider = CommandErrorProvider(Command.OPS_TEST_ALL)
register_error_provider(Command.OPS_TEST_ALL, error_provider)


def _get_command_help() -> str:
    return detailed_examples()


def _run_collector_tests(
    device_obj, test_query: str = "basic", include_data: bool = True
) -> Dict[str, Any]:
    """
    Run all collector function tests in parallel on a single device.

    Args:
        device_obj: Device object to test
        test_query: Type of test ("basic" or "full")
        include_data: Whether to include the full result data in output

    Returns:
        Dict containing test results, timing, and summary information
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
                "ip_adjacency_dump": lambda: ip_adjacency_dump(device_obj),
                "interfaces_detailed": lambda: get_interfaces(
                    device_obj, interface="GigabitEthernet0/0/0/1"
                ),
            }
        )

    # Run tests in parallel
    results = {}
    test_summary = {
        "total_tests": len(test_functions),
        "successful": 0,
        "failed": 0,
        "feature_not_available": 0,
        "test_type": test_query,
        "device_name": device_obj.name,
    }

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=len(test_functions)
    ) as executor:
        # Submit all tests
        future_to_test = {
            executor.submit(test_func): test_name
            for test_name, test_func in test_functions.items()
        }

        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_test):
            test_name = future_to_test[future]
            test_start_time = time.time()

            try:
                result = future.result(
                    timeout=30
                )  # 30 second timeout per test
                test_execution_time = time.time() - test_start_time

                # Analyze the result
                if isinstance(result, NetworkOperationResult):
                    if result.status == OperationStatus.SUCCESS:
                        status = "SUCCESS"
                        test_summary["successful"] += 1
                    elif (
                        result.status == OperationStatus.FEATURE_NOT_AVAILABLE
                    ):
                        status = "FEATURE_NOT_AVAILABLE"
                        test_summary["feature_not_available"] += 1
                    else:
                        status = "FAILED"
                        test_summary["failed"] += 1

                    test_result = {
                        "status": status,
                        "execution_time": round(test_execution_time, 3),
                        "operation_type": result.operation_type,
                        "data_size": (
                            len(str(result.data)) if result.data else 0
                        ),
                        "error_message": (
                            result.error_response.message
                            if result.error_response
                            else None
                        ),
                        "feature_message": (
                            result.feature_not_found_response.message
                            if result.feature_not_found_response
                            else None
                        ),
                    }

                    # Include the full result data if requested
                    if include_data:
                        test_result["result_data"] = {
                            "device_name": result.device_name,
                            "ip_address": result.ip_address,
                            "nos": result.nos,
                            "operation_type": result.operation_type,
                            "status": result.status.value,
                            "data": result.data,
                            "metadata": result.metadata,
                        }
                        if result.error_response:
                            test_result["result_data"]["error_response"] = {
                                "type": result.error_response.type,
                                "message": result.error_response.message,
                            }
                        if result.feature_not_found_response:
                            test_result["result_data"][
                                "feature_not_found_response"
                            ] = {
                                "feature_name": result.feature_not_found_response.feature_name,
                                "message": result.feature_not_found_response.message,
                            }

                    results[test_name] = test_result

                else:
                    # Handle non-NetworkOperationResult responses
                    status = "SUCCESS"
                    test_summary["successful"] += 1
                    test_result = {
                        "status": status,
                        "execution_time": round(test_execution_time, 3),
                        "operation_type": "unknown",
                        "data_size": len(str(result)) if result else 0,
                        "error_message": None,
                        "feature_message": None,
                    }

                    # Include the raw result data if requested
                    if include_data:
                        test_result["result_data"] = result

                    results[test_name] = test_result

            except concurrent.futures.TimeoutError:
                test_summary["failed"] += 1
                results[test_name] = {
                    "status": "TIMEOUT",
                    "execution_time": 30.0,
                    "operation_type": "timeout",
                    "data_size": 0,
                    "error_message": "Test timed out after 30 seconds",
                    "feature_message": None,
                }
                logger.warning(
                    "Test %s timed out for device %s",
                    test_name,
                    device_obj.name,
                )

            except Exception as e:
                test_execution_time = time.time() - test_start_time
                test_summary["failed"] += 1
                results[test_name] = {
                    "status": "ERROR",
                    "execution_time": round(test_execution_time, 3),
                    "operation_type": "error",
                    "data_size": 0,
                    "error_message": str(e),
                    "feature_message": None,
                }
                logger.error(
                    "Test %s failed for device %s: %s",
                    test_name,
                    device_obj.name,
                    str(e),
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
        "test_results": results,
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


@register_command(Command.OPS_TEST_ALL)
@click.command(help=_get_command_help())
@add_common_device_options
@click.option(
    "--test-query",
    type=click.Choice(["basic", "full"]),
    default="basic",
    help="Type of test to run",
)
@click.option(
    "--summary-only",
    is_flag=True,
    help="Show only test summary without full data",
)
@click.pass_context
def ops_test_all(
    ctx,
    device,
    test_query,
    summary_only,
    output,
    devices,
    device_file,
    all_devices,
):
    """Test all APIs on a network device"""

    # Include data by default, unless summary-only is requested
    include_data = not summary_only

    def operation_func(device_obj, **kwargs):
        logger.info(
            "Running %s test suite on device: %s", test_query, device_obj.name
        )
        return _run_collector_tests(device_obj, test_query, include_data)

    return execute_device_command(
        ctx=ctx,
        device=device,
        devices=devices,
        device_file=device_file,
        all_devices=all_devices,
        output=output,
        operation_func=operation_func,
        operation_name="test-all",
        test_query=test_query,
    )


if __name__ == "__main__":
    print(_get_command_help())
