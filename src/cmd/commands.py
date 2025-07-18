#!/usr/bin/env python3
"""Clean Click-based command implementations for gNMIBuddy CLI"""
import click
from src.logging.config import get_logger

logger = get_logger(__name__)


# Device group commands
@click.command()
@click.option("--device", required=True, help="Device name from inventory")
@click.option(
    "--detail", is_flag=True, help="Show detailed system information"
)
@click.pass_context
def device_info(ctx, device, detail):
    """Get system information from a network device"""
    logger.info("Getting system information for device: %s", device)
    from src.collectors.system import get_system_info
    from src.inventory.manager import InventoryManager

    # Get device object from inventory
    device_obj, success = InventoryManager.get_device(device)
    if not success:
        click.echo(f"Error: {device_obj.error}", err=True)
        raise click.Abort()

    return get_system_info(device_obj)


@click.command()
@click.option("--detail", is_flag=True, help="Show detailed profile analysis")
@click.pass_context
def device_profile(ctx, device, detail):
    """Get device profile information from a network device"""
    logger.info("Getting device profile for device: %s", device)
    from src.collectors.profile import get_device_profile
    from src.inventory.manager import InventoryManager

    # Get device object from inventory
    device_obj, success = InventoryManager.get_device(device)
    if not success:
        click.echo(f"Error: {device_obj.error}", err=True)
        raise click.Abort()

    return get_device_profile(device_obj)


@click.command()
@click.option(
    "--detail", is_flag=True, help="Show detailed device information"
)
@click.pass_context
def device_list(ctx, detail):
    """List all available devices in the inventory"""
    logger.info("Listing all available devices")
    from src.inventory.manager import InventoryManager

    inventory = InventoryManager.get_instance()
    devices = inventory.get_devices()

    if not devices:
        click.echo("No devices found in inventory.")
        return None

    if detail:
        for device_name, device_info in devices.items():
            click.echo(f"\nDevice: {device_name}")
            # Convert device object to dict-like display
            device_data = device_info.__dict__
            for key, value in device_data.items():
                click.echo(f"  {key}: {value}")
    else:
        click.echo("Available devices:")
        for device_name in devices.keys():
            click.echo(f"  - {device_name}")

    return devices


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
@click.pass_context
def network_routing(ctx, device, protocol, detail):
    """Get routing information from a network device"""
    logger.info("Getting routing information for device: %s", device)
    from src.collectors.routing import get_routing_info
    from src.inventory.manager import InventoryManager

    if protocol:
        logger.info("Filtering by protocol: %s", protocol)

    # Get device object from inventory
    device_obj, success = InventoryManager.get_device(device)
    if not success:
        click.echo(f"Error: {device_obj.error}", err=True)
        raise click.Abort()

    return get_routing_info(device_obj)


@click.command()
@click.option("--device", required=True, help="Device name from inventory")
@click.option(
    "--name", help="Filter by interface name (e.g., GigabitEthernet0/0/0/1)"
)
@click.option(
    "--detail", is_flag=True, help="Show detailed interface information"
)
@click.pass_context
def network_interface(ctx, device, name, detail):
    """Get interface information from a network device"""
    logger.info("Getting interface information for device: %s", device)
    from src.collectors.interfaces import get_interface_info

    # Create args-like object for compatibility with existing collectors
    class Args:
        def __init__(self):
            self.device = device
            self.name = name
            self.detail = detail

    args = Args()
    return get_interface_info(args)


@click.command()
@click.option("--device", required=True, help="Device name from inventory")
@click.option("--detail", is_flag=True, help="Show detailed MPLS information")
@click.pass_context
def network_mpls(ctx, device, detail):
    """Get MPLS information from a network device"""
    logger.info("Getting MPLS information for device: %s", device)
    from src.collectors.mpls import get_mpls_info

    # Create args-like object for compatibility with existing collectors
    class Args:
        def __init__(self):
            self.device = device
            self.detail = detail

    args = Args()
    return get_mpls_info(args)


@click.command()
@click.option("--device", required=True, help="Device name from inventory")
@click.option("--vrf", help="Filter by VRF name")
@click.option(
    "--detail", is_flag=True, help="Show detailed VPN/VRF information"
)
@click.pass_context
def network_vpn(ctx, device, vrf, detail):
    """Get VPN/VRF information from a network device"""
    logger.info("Getting VPN/VRF information for device: %s", device)
    from src.collectors.vpn import get_vpn_info

    # Create args-like object for compatibility with existing collectors
    class Args:
        def __init__(self):
            self.device = device
            self.vrf = vrf
            self.detail = detail

    args = Args()
    return get_vpn_info(args)


# Topology group commands
@click.command()
@click.option("--device", required=True, help="Device name from inventory")
@click.option(
    "--detail", is_flag=True, help="Show detailed adjacency information"
)
@click.pass_context
def topology_adjacency(ctx, device, detail):
    """Get IP adjacency topology information"""
    logger.info("Getting IP adjacency topology for device: %s", device)
    from src.collectors.topology import get_topology_ip_adjacency

    # Create args-like object for compatibility with existing collectors
    class Args:
        def __init__(self):
            self.device = device
            self.detail = detail

    args = Args()
    return get_topology_ip_adjacency(args)


@click.command()
@click.option("--device", required=True, help="Device name from inventory")
@click.option(
    "--detail", is_flag=True, help="Show detailed neighbor information"
)
@click.pass_context
def topology_neighbors(ctx, device, detail):
    """Get topology neighbors information"""
    logger.info("Getting topology neighbors for device: %s", device)
    from src.collectors.topology.neighbors import get_topology_neighbors

    # Create args-like object for compatibility with existing collectors
    class Args:
        def __init__(self):
            self.device = device
            self.detail = detail

    args = Args()
    return get_topology_neighbors(args)


# Ops group commands
@click.command()
@click.option("--device", required=True, help="Device name from inventory")
@click.option(
    "--minutes",
    type=int,
    default=5,
    help="Get logs from the last N minutes (default: 5)",
)
@click.option(
    "--show-all-logs",
    is_flag=True,
    help="Show all available logs (raw format)",
)
@click.pass_context
def ops_logs(ctx, device, minutes, show_all_logs):
    """Get logging information from a network device"""
    logger.info("Getting logging information for device: %s", device)
    from src.collectors.logs import get_logging_info

    # Create args-like object for compatibility with existing collectors
    class Args:
        def __init__(self):
            self.device = device
            self.minutes = minutes
            self.show_all_logs = show_all_logs

    args = Args()
    return get_logging_info(args)


@click.command()
@click.option("--device", required=True, help="Device name from inventory")
@click.option(
    "--test-query", is_flag=True, help="Test if the device responds to queries"
)
@click.pass_context
def ops_test_all(ctx, device, test_query):
    """Test all available APIs on the specified device"""
    logger.info("Testing all APIs for device: %s", device)

    # List of all test functions
    test_functions = [
        (
            "routing",
            lambda: network_routing.callback(ctx, device, None, False),
        ),
        (
            "interface",
            lambda: network_interface.callback(ctx, device, None, False),
        ),
        ("mpls", lambda: network_mpls.callback(ctx, device, False)),
        ("vpn", lambda: network_vpn.callback(ctx, device, None, False)),
        ("system", lambda: device_info.callback(ctx, device, False)),
        ("profile", lambda: device_profile.callback(ctx, device, False)),
        ("logs", lambda: ops_logs.callback(ctx, device, 5, False)),
        (
            "topology-adjacency",
            lambda: topology_adjacency.callback(ctx, device, False),
        ),
        (
            "topology-neighbors",
            lambda: topology_neighbors.callback(ctx, device, False),
        ),
    ]

    results = {}
    for test_name, test_func in test_functions:
        try:
            logger.info(f"Testing {test_name} command...")
            result = test_func()
            results[test_name] = {
                "status": "success",
                "data": result,
            }
            click.echo(f"✓ {test_name}: Success")
        except Exception as e:
            logger.error(f"Error testing {test_name}: {e}")
            results[test_name] = {
                "status": "error",
                "error": str(e),
            }
            click.echo(f"✗ {test_name}: Failed - {e}")

    return results


# Management group commands
@click.command()
@click.option(
    "--detail", is_flag=True, help="Show detailed command information"
)
@click.pass_context
def manage_list_commands(ctx, detail):
    """List all available commands and their options"""
    logger.info("Displaying all available commands")
    from src.cmd.display import display_all_commands

    display_all_commands(detailed=detail)
    return None


@click.group()
@click.pass_context
def manage_log_level(ctx):
    """Manage logging levels for the CLI"""
    pass


@manage_log_level.command()
@click.pass_context
def show(ctx):
    """Show current log levels"""
    from src.logging.config import LoggingConfig

    current_levels = LoggingConfig.get_current_levels()
    click.echo("Current log levels:")
    for module, level in current_levels.items():
        click.echo(f"  {module}: {level}")


@manage_log_level.command()
@click.argument("module")
@click.argument(
    "level", type=click.Choice(["debug", "info", "warning", "error"])
)
@click.pass_context
def set(ctx, module, level):
    """Set log level for a module"""
    from src.logging.config import LoggingConfig

    LoggingConfig.set_module_level(module, level)
    click.echo(f"Set {module} log level to {level}")


@manage_log_level.command()
@click.pass_context
def reset(ctx):
    """Reset all modules to default log levels"""
    from src.logging.config import LoggingConfig

    LoggingConfig.reset_to_defaults()
    click.echo("Reset all log levels to defaults")
