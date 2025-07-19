#!/usr/bin/env python3
"""Device list command implementation"""
import click

from src.logging.config import get_logger
from src.cmd.cli_utils import output_result
from src.inventory.manager import InventoryManager
from src.cmd.commands.base import add_output_option, add_detail_option


@click.command()
@add_detail_option(help_text="Show detailed device information")
@add_output_option
@click.pass_context
def device_list(ctx, detail, output):
    """List all available devices in the inventory"""

    logger = get_logger(__name__)
    logger.info("Listing all available devices")

    inventory = InventoryManager.get_instance()
    devices = inventory.get_devices()

    if not devices:
        result = {
            "devices": [],
            "count": 0,
            "message": "No devices found in inventory",
        }
        output_result(result, output)
        return result

    if detail:
        # Create detailed device list
        device_list = []
        for device_name, device_info in devices.items():
            device_data = {"name": device_name}
            # Convert device object to dict-like display
            if hasattr(device_info, "__dict__"):
                device_data.update(device_info.__dict__)
            else:
                device_data["info"] = str(device_info)
            device_list.append(device_data)

        result = {
            "devices": device_list,
            "count": len(device_list),
            "detail": True,
        }
    else:
        # Create simple device list
        device_names = list(devices.keys())
        result = {
            "devices": device_names,
            "count": len(device_names),
            "detail": False,
        }

    output_result(result, output)
    return result
