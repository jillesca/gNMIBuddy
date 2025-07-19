#!/usr/bin/env python3
"""Command group definitions for hierarchical CLI structure"""
import click
from src.logging.config import get_logger

logger = get_logger(__name__)


# Custom context settings to enable -h shorthand
CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def device(ctx):
    """Device management commands

    Commands for managing and querying individual devices including
    system information, device profiles, and device listings.

    Run 'uv run gnmibuddy.py device COMMAND --help' for more information on a specific command.
    """
    pass


@click.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def network(ctx):
    """Network protocol commands

    Commands for querying network protocol information including
    routing, interfaces, MPLS, and VPN/VRF configurations.
    """
    pass


@click.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def topology(ctx):
    """Network topology commands

    Commands for discovering and analyzing network topology including
    neighbor relationships and adjacency information.
    """
    pass


@click.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def ops(ctx):
    """Operational commands

    Commands for operational tasks including logging, testing,
    and monitoring network devices.
    """
    pass


@click.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def manage(ctx):
    """Management commands

    Commands for managing the CLI tool itself including
    configuration, logging levels, and command listings.
    """
    pass


# Register commands with their groups
def register_commands():
    """Register all commands with their respective groups"""
    # Import commands
    from src.cmd.commands.device import (
        device_info,
        device_profile,
        device_list,
    )
    from src.cmd.commands.network import (
        network_routing,
        network_interface,
        network_mpls,
        network_vpn,
    )
    from src.cmd.commands.topology import (
        topology_adjacency,
        topology_neighbors,
    )
    from src.cmd.commands.ops import ops_logs, ops_test_all
    from src.cmd.commands.manage import manage_log_level

    # Register device commands
    device.add_command(device_info, "info")
    device.add_command(device_profile, "profile")
    device.add_command(device_list, "list")

    # Register network commands
    network.add_command(network_routing, "routing")
    network.add_command(network_interface, "interface")
    network.add_command(network_mpls, "mpls")
    network.add_command(network_vpn, "vpn")

    # Register topology commands
    topology.add_command(topology_adjacency, "adjacency")
    topology.add_command(topology_neighbors, "neighbors")

    # Register ops commands
    ops.add_command(ops_logs, "logs")
    ops.add_command(ops_test_all, "test-all")

    # Register manage commands
    manage.add_command(manage_log_level, "log-level")


# Group registry for easy access
COMMAND_GROUPS = {
    "device": device,
    "network": network,
    "topology": topology,
    "ops": ops,
    "manage": manage,
}
