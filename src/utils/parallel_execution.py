"""Utility functions for parallel execution of network commands."""

import concurrent.futures
from typing import Dict, Any, List, Callable

from src.utils.logging_config import get_logger
import src.inventory


def run_command_on_all_devices(
    command_func: Callable,
    *args,
    max_workers: int = 5,
) -> List[Dict[str, Any]]:
    """
    Run a command on all devices in the inventory concurrently.

    Args:
        command_func: Function to execute on each device
        *args: Arguments to pass to the command function
        max_workers: Maximum number of concurrent workers

    Returns:
        List of results from each device
    """
    logger = get_logger(__name__)
    # Initialize inventory if not already done
    src.inventory.InventoryManager.initialize()
    # Get the list of all devices
    devices_info = src.inventory.InventoryManager.list_devices()
    device_names = [device["name"] for device in devices_info["devices"]]

    results = []

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=max_workers
    ) as executor:
        # Create a dictionary of future: device_name
        future_to_device = {
            executor.submit(command_func, device_name, *args): device_name
            for device_name in device_names
        }

        # Process the completed futures as they complete
        for future in concurrent.futures.as_completed(future_to_device):
            device_name = future_to_device[future]
            try:
                result = future.result()
                results.append(result)
            except (ConnectionError, TimeoutError) as exc:
                logger.error(
                    "Network error for device %s: %s", device_name, exc
                )
                results.append(
                    {
                        "device": device_name,
                        "error": f"Network error: {str(exc)}",
                    }
                )
            except ValueError as exc:
                logger.error("Value error for device %s: %s", device_name, exc)
                results.append(
                    {
                        "device": device_name,
                        "error": f"Value error: {str(exc)}",
                    }
                )
            except Exception as exc:
                # Still catch unexpected exceptions as a fallback
                logger.error(
                    "Unexpected error for device %s: %s", device_name, exc
                )
                results.append(
                    {
                        "device": device_name,
                        "error": f"Unexpected error: {str(exc)}",
                    }
                )

    return results
