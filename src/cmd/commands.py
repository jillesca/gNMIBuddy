#!/usr/bin/env python3
"""Clean Click-based command implementations for gNMIBuddy CLI"""
import click
from src.logging.config import get_logger

logger = get_logger(__name__)


def _handle_inventory_error_in_command(error_msg: str):
    """
    Handle inventory-related errors with clear user guidance in command context

    Args:
        error_msg: The original error message
    """
    click.echo("\n❌ Inventory Error", err=True)
    click.echo("═" * 50, err=True)

    click.echo("\nThe inventory file is required but not found.", err=True)
    click.echo("\n💡 How to fix this:", err=True)
    click.echo("  1. Use --inventory option:", err=True)
    click.echo(
        "     gnmibuddy --inventory path/to/your/devices.json device info --device R1",
        err=True,
    )
    click.echo("\n  2. Or set environment variable:", err=True)
    click.echo(
        "     export NETWORK_INVENTORY=path/to/your/devices.json", err=True
    )
    click.echo("     gnmibuddy device info --device R1", err=True)

    click.echo("\n📁 Example inventory files:", err=True)
    click.echo("  • xrd_sandbox.json (in project root)", err=True)
    click.echo("  • Any JSON file with device definitions", err=True)


# Device group commands
@click.command()
@click.option("--device", help="Device name from inventory")
@click.option(
    "--detail", is_flag=True, help="Show detailed system information"
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "yaml"], case_sensitive=False),
    default="json",
    help="Output format (json, yaml)",
)
@click.option(
    "--devices", type=str, help="Comma-separated list of device names"
)
@click.option(
    "--device-file",
    type=click.Path(exists=True),
    help="Path to file containing device names (one per line)",
)
@click.option(
    "--all-devices",
    is_flag=True,
    help="Run command on all devices in inventory",
)
@click.pass_context
def device_info(
    ctx, device, detail, output, devices, device_file, all_devices
):
    """Get system information from a network device

    \b
    Examples:
      gnmibuddy device info --device R1
      gnmibuddy device info --device PE1 --detail
      gnmibuddy device info --device R1 --output json
      gnmibuddy device info --device R1 --output yaml
      gnmibuddy device info --devices R1,R2,R3
      gnmibuddy device info --all-devices
      gnmibuddy d info --device R1  # Using alias
    """
    from src.cmd.formatters import format_output
    from src.collectors.system import get_system_info
    from src.inventory.manager import InventoryManager
    from src.cmd.batch import DeviceListParser, BatchOperationExecutor

    # Handle batch operations
    batch_devices = []
    if all_devices:
        batch_devices = DeviceListParser.get_all_inventory_devices()
        if not batch_devices:
            click.echo("No devices found in inventory", err=True)
            raise click.Abort()
    elif devices:
        batch_devices = DeviceListParser.parse_device_list(devices)
    elif device_file:
        batch_devices = DeviceListParser.parse_device_file(device_file)

    if batch_devices:
        # Batch operation
        max_workers = getattr(ctx.obj, "max_workers", 5)
        executor = BatchOperationExecutor(max_workers=max_workers)

        def single_device_operation(device_name: str):
            device_obj, success = InventoryManager.get_device(device_name)
            if not success:
                raise Exception(f"Device not found: {device_obj.error}")
            return get_system_info(device_obj)

        click.echo(
            f"Executing batch operation on {len(batch_devices)} devices..."
        )
        summary = executor.execute_batch_operation(
            devices=batch_devices,
            operation_func=single_device_operation,
            show_progress=True,
        )

        # Format batch results
        batch_data = {
            "summary": {
                "total_devices": summary.total_devices,
                "successful": summary.successful,
                "failed": summary.failed,
                "success_rate": summary.success_rate,
                "execution_time": summary.execution_time,
            },
            "results": [
                {
                    "device": result.device_name,
                    "success": result.success,
                    "data": (
                        result.data.data
                        if result.success and hasattr(result.data, "data")
                        else result.data if result.success else None
                    ),
                    "error": result.error if not result.success else None,
                    "execution_time": result.execution_time,
                }
                for result in summary.results
            ],
        }

        # Output in requested format
        formatted_output = format_output(batch_data, output.lower())
        click.echo(formatted_output)

        return summary

    # Single device operation
    if not device:
        click.echo(
            "Error: --device is required for single device operations",
            err=True,
        )
        raise click.Abort()

    logger.info("Getting system information for device: %s", device)

    # Get device object from inventory
    try:
        device_obj, success = InventoryManager.get_device(device)
        if not success:
            click.echo(f"Error: {device_obj['error']}", err=True)
            raise click.Abort()
    except FileNotFoundError as e:
        # Handle inventory file not found with friendly error message
        error_msg = str(e)
        if "inventory file" in error_msg.lower():
            _handle_inventory_error_in_command(error_msg)
        else:
            click.echo(f"File not found: {error_msg}", err=True)
        raise click.Abort()

        # Get the data
    result = get_system_info(device_obj)

    # Format and display the output
    formatted_output = format_output(result, output.lower())
    click.echo(formatted_output)

    return None


@click.command()
@click.option("--device", required=True, help="Device name from inventory")
@click.option("--detail", is_flag=True, help="Show detailed profile analysis")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "yaml"], case_sensitive=False),
    default="json",
    help="Output format (json, yaml)",
)
@click.pass_context
def device_profile(ctx, device, detail, output):
    """Get device profile information from a network device"""
    logger.info("Getting device profile for device: %s", device)
    from src.collectors.profile import get_device_profile
    from src.inventory.manager import InventoryManager
    from src.cmd.cli_utils import output_result

    # Get device object from inventory
    device_obj, success = InventoryManager.get_device(device)
    if not success:
        click.echo(f"Error: {device_obj['error']}", err=True)
        raise click.Abort()

    result = get_device_profile(device_obj)
    output_result(result, output)
    return result


@click.command()
@click.option(
    "--detail", is_flag=True, help="Show detailed device information"
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "yaml"], case_sensitive=False),
    default="json",
    help="Output format (json, yaml)",
)
@click.pass_context
def device_list(ctx, detail, output):
    """List all available devices in the inventory"""
    logger.info("Listing all available devices")
    from src.inventory.manager import InventoryManager
    from src.cmd.cli_utils import output_result

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


# Network group commands
@click.command()
@click.option("--device", required=True, help="Device name from inventory")
@click.option(
    "--protocol",
    type=click.Choice(["bgp", "isis", "ospf"]),
    help="Filter by routing protocol",
)
@click.option(
    "--detail", is_flag=True, help="Show detailed routing information"
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "yaml"], case_sensitive=False),
    default="json",
    help="Output format (json, yaml)",
)
@click.pass_context
def network_routing(ctx, device, protocol, detail, output):
    """Get routing information from a network device

    \b
    Examples:
      gnmibuddy network routing --device R1
      gnmibuddy network routing --device R1 --protocol bgp
      gnmibuddy network routing --device R1 --detail
      gnmibuddy network routing --device R1 --output yaml
      gnmibuddy n routing --device R1  # Using alias
    """
    logger.info("Getting routing information for device: %s", device)
    from src.collectors.routing import get_routing_info
    from src.inventory.manager import InventoryManager
    from src.cmd.cli_utils import output_result

    # Get device object from inventory
    device_obj, success = InventoryManager.get_device(device)
    if not success:
        click.echo(f"Error: {device_obj['error']}", err=True)
        raise click.Abort()

    result = get_routing_info(device_obj)
    output_result(result, output)
    return result


@click.command()
@click.option("--device", required=True, help="Device name from inventory")
@click.option(
    "--name", help="Filter by interface name (e.g., GigabitEthernet0/0/0/1)"
)
@click.option(
    "--detail", is_flag=True, help="Show detailed interface information"
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "yaml"], case_sensitive=False),
    default="json",
    help="Output format (json, yaml)",
)
@click.pass_context
def network_interface(ctx, device, name, detail, output):
    """Get interface information from a network device

    \b
    Examples:
      gnmibuddy network interface --device R1
      gnmibuddy network interface --device R1 --name GigabitEthernet0/0/0/1
      gnmibuddy network interface --device R1 --detail
      gnmibuddy network interface --device R1 --output yaml
      gnmibuddy n interface --device R1  # Using alias
    """
    logger.info("Getting interface information for device: %s", device)
    from src.collectors.interfaces import get_interfaces
    from src.inventory.manager import InventoryManager
    from src.cmd.cli_utils import output_result

    # Get device object from inventory
    device_obj, success = InventoryManager.get_device(device)
    if not success:
        click.echo(f"Error: {device_obj['error']}", err=True)
        raise click.Abort()

    result = get_interfaces(device_obj, interface=name)
    output_result(result, output)
    return result


@click.command()
@click.option("--device", required=True, help="Device name from inventory")
@click.option("--detail", is_flag=True, help="Show detailed MPLS information")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "yaml"], case_sensitive=False),
    default="json",
    help="Output format (json, yaml)",
)
@click.pass_context
def network_mpls(ctx, device, detail, output):
    """Get MPLS information from a network device"""
    logger.info("Getting MPLS information for device: %s", device)
    from src.collectors.mpls import get_mpls_info
    from src.inventory.manager import InventoryManager
    from src.cmd.cli_utils import output_result

    # Get device object from inventory
    device_obj, success = InventoryManager.get_device(device)
    if not success:
        click.echo(f"Error: {device_obj['error']}", err=True)
        raise click.Abort()

    result = get_mpls_info(device_obj, include_details=detail)
    output_result(result, output)
    return result


@click.command()
@click.option("--device", required=True, help="Device name from inventory")
@click.option("--vrf", help="Filter by VRF name (e.g., CUSTOMER_A)")
@click.option("--detail", is_flag=True, help="Show detailed VPN information")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "yaml"], case_sensitive=False),
    default="json",
    help="Output format (json, yaml)",
)
@click.pass_context
def network_vpn(ctx, device, vrf, detail, output):
    """Get VPN/VRF information from a network device"""
    logger.info("Getting VPN information for device: %s", device)
    from src.collectors.vpn import get_vpn_info
    from src.inventory.manager import InventoryManager
    from src.cmd.cli_utils import output_result

    # Get device object from inventory
    device_obj, success = InventoryManager.get_device(device)
    if not success:
        click.echo(f"Error: {device_obj['error']}", err=True)
        raise click.Abort()

    result = get_vpn_info(device_obj, vrf_name=vrf)
    output_result(result, output)
    return result


# Topology group commands
@click.command()
@click.option("--device", required=True, help="Device name from inventory")
@click.option(
    "--detail", is_flag=True, help="Show detailed topology information"
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "yaml"], case_sensitive=False),
    default="json",
    help="Output format (json, yaml)",
)
@click.pass_context
def topology_adjacency(ctx, device, detail, output):
    """Get IP adjacency topology information"""
    logger.info("Getting topology adjacency for device: %s", device)
    from src.inventory.manager import InventoryManager
    from src.cmd.cli_utils import output_result

    # Get device object from inventory
    device_obj, success = InventoryManager.get_device(device)
    if not success:
        click.echo(f"Error: {device_obj['error']}", err=True)
        raise click.Abort()

    # TODO: Implement actual topology adjacency collection
    result = {
        "device": device,
        "operation": "topology_adjacency",
        "status": "placeholder",
    }
    output_result(result, output)
    return result


@click.command()
@click.option("--device", required=True, help="Device name from inventory")
@click.option(
    "--detail", is_flag=True, help="Show detailed neighbor information"
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "yaml"], case_sensitive=False),
    default="json",
    help="Output format (json, yaml)",
)
@click.pass_context
def topology_neighbors(ctx, device, detail, output):
    """Get topology neighbors information"""
    logger.info("Getting topology neighbors for device: %s", device)
    from src.inventory.manager import InventoryManager
    from src.cmd.cli_utils import output_result

    # Get device object from inventory
    device_obj, success = InventoryManager.get_device(device)
    if not success:
        click.echo(f"Error: {device_obj['error']}", err=True)
        raise click.Abort()

    # TODO: Implement actual topology neighbors collection
    result = {
        "device": device,
        "operation": "topology_neighbors",
        "status": "placeholder",
    }
    output_result(result, output)
    return result


# Ops group commands
@click.command()
@click.option("--device", required=True, help="Device name from inventory")
@click.option(
    "--minutes",
    type=int,
    default=10,
    help="Number of minutes of logs to retrieve",
)
@click.option(
    "--show-all-logs", is_flag=True, help="Show all available log entries"
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "yaml"], case_sensitive=False),
    default="json",
    help="Output format (json, yaml)",
)
@click.pass_context
def ops_logs(ctx, device, minutes, show_all_logs, output):
    """Get log information from a network device"""
    logger.info("Getting logs for device: %s", device)
    from src.collectors.logs import get_logs
    from src.inventory.manager import InventoryManager
    from src.cmd.cli_utils import output_result

    # Get device object from inventory
    device_obj, success = InventoryManager.get_device(device)
    if not success:
        click.echo(f"Error: {device_obj['error']}", err=True)
        raise click.Abort()

    result = get_logs(device_obj, minutes=minutes, show_all_logs=show_all_logs)
    output_result(result, output)
    return result


@click.command()
@click.option("--device", required=True, help="Device name from inventory")
@click.option(
    "--test-query",
    type=click.Choice(["basic", "full"]),
    default="basic",
    help="Type of test to run",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "yaml"], case_sensitive=False),
    default="json",
    help="Output format (json, yaml)",
)
@click.pass_context
def ops_test_all(ctx, device, test_query, output):
    """Test all APIs on a network device"""
    logger.info("Testing all APIs for device: %s", device)
    from src.cmd.cli_utils import output_result

    # This is a placeholder implementation
    # TODO: Implement actual test-all functionality
    result = {"device": device, "test_type": test_query, "status": "completed"}
    output_result(result, output)
    return result


# Management group commands
@click.command()
@click.pass_context
def manage_list_commands(ctx):
    """List all available commands"""
    from src.cmd.groups import COMMAND_GROUPS

    click.echo("Available command groups and commands:")
    click.echo("=" * 50)

    for group_name, group in COMMAND_GROUPS.items():
        click.echo(f"\n{group_name.upper()} Commands:")
        click.echo("-" * 20)

        if hasattr(group, "commands") and group.commands:
            for cmd_name, cmd in group.commands.items():
                # Get the command description
                help_text = getattr(cmd, "help", "No description available")
                if help_text and len(help_text) > 60:
                    help_text = help_text[:60] + "..."
                click.echo(f"  {cmd_name:<20} {help_text}")
        else:
            click.echo("  No commands available")


@click.command()
@click.argument("action", type=click.Choice(["show", "set", "reset"]))
@click.option("--module", help="Module name for module-specific operations")
@click.option(
    "--level",
    type=click.Choice(["debug", "info", "warning", "error"]),
    help="Log level to set",
)
@click.pass_context
def manage_log_level(ctx, action, module, level):
    """Manage logging levels"""
    from src.logging.config import LoggingConfig

    if action == "show":
        if module:
            # Show specific module level
            levels = LoggingConfig.get_module_levels()
            if module in levels:
                click.echo(f"Module '{module}' log level: {levels[module]}")
            else:
                click.echo(
                    f"Module '{module}' not found or using default level"
                )
        else:
            # Show all levels
            levels = LoggingConfig.get_module_levels()
            if levels:
                click.echo("Current module log levels:")
                for mod, lvl in levels.items():
                    click.echo(f"  {mod}: {lvl}")
            else:
                click.echo("No custom module log levels set")

    elif action == "set":
        if not module or not level:
            click.echo(
                "Error: --module and --level are required for 'set' action",
                err=True,
            )
            raise click.Abort()

        LoggingConfig.set_module_level(module, level)
        click.echo(f"Set log level for module '{module}' to '{level}'")

    elif action == "reset":
        if module:
            # Reset specific module (implement if needed)
            click.echo(f"Resetting log level for module '{module}' to default")
        else:
            # Reset all to defaults
            click.echo("Resetting all log levels to defaults")
            # Note: LoggingConfig doesn't have reset_to_defaults method
            # This would need to be implemented if needed
