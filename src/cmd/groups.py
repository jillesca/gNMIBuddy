#!/usr/bin/env python3
"""Command groups for Click-based CLI"""

import click
from src.logging.config import get_logger

logger = get_logger(__name__)

# Context settings for click groups
CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])

# Command error provider registry for duck typing pattern
command_error_providers = {}


def register_error_provider(group_name: str, command_name: str, provider):
    """Register an error provider for a specific command."""
    key = f"{group_name}.{command_name}"
    command_error_providers[key] = provider
    logger.debug("Registered error provider for %s", key)


def get_error_provider(group_name: str, command_name: str):
    """Get error provider for a specific command using duck typing."""
    key = f"{group_name}.{command_name}"
    return command_error_providers.get(key)


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


# Register commands with their groups
def register_commands():
    """Register all commands with their respective groups"""
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

    # Register error providers (duck typing pattern)
    _register_error_providers()


def _register_error_providers():
    """Register error providers from command modules that have them."""
    # Device command error providers
    try:
        import src.cmd.commands.device.info as device_info_module

        if hasattr(device_info_module, "error_provider"):
            register_error_provider(
                "device", "info", device_info_module.error_provider
            )
    except (ImportError, AttributeError) as e:
        logger.debug("No error provider for device.info: %s", e)

    try:
        import src.cmd.commands.device.profile as device_profile_module

        if hasattr(device_profile_module, "error_provider"):
            register_error_provider(
                "device", "profile", device_profile_module.error_provider
            )
    except (ImportError, AttributeError) as e:
        logger.debug("No error provider for device.profile: %s", e)

    try:
        import src.cmd.commands.device.list as device_list_module

        if hasattr(device_list_module, "error_provider"):
            register_error_provider(
                "device", "list", device_list_module.error_provider
            )
    except (ImportError, AttributeError) as e:
        logger.debug("No error provider for device.list: %s", e)

    # Network command error providers
    try:
        import src.cmd.commands.network.routing as network_routing_module

        if hasattr(network_routing_module, "error_provider"):
            register_error_provider(
                "network", "routing", network_routing_module.error_provider
            )
    except (ImportError, AttributeError) as e:
        logger.debug("No error provider for network.routing: %s", e)

    try:
        import src.cmd.commands.network.interface as network_interface_module

        if hasattr(network_interface_module, "error_provider"):
            register_error_provider(
                "network", "interface", network_interface_module.error_provider
            )
    except (ImportError, AttributeError) as e:
        logger.debug("No error provider for network.interface: %s", e)

    try:
        import src.cmd.commands.network.mpls as network_mpls_module

        if hasattr(network_mpls_module, "error_provider"):
            register_error_provider(
                "network", "mpls", network_mpls_module.error_provider
            )
    except (ImportError, AttributeError) as e:
        logger.debug("No error provider for network.mpls: %s", e)

    try:
        import src.cmd.commands.network.vpn as network_vpn_module

        if hasattr(network_vpn_module, "error_provider"):
            register_error_provider(
                "network", "vpn", network_vpn_module.error_provider
            )
    except (ImportError, AttributeError) as e:
        logger.debug("No error provider for network.vpn: %s", e)

    # Topology command error providers
    try:
        import src.cmd.commands.topology.neighbors as topology_neighbors_module

        if hasattr(topology_neighbors_module, "error_provider"):
            register_error_provider(
                "topology",
                "neighbors",
                topology_neighbors_module.error_provider,
            )
    except (ImportError, AttributeError) as e:
        logger.debug("No error provider for topology.neighbors: %s", e)

    try:
        import src.cmd.commands.topology.adjacency as topology_adjacency_module

        if hasattr(topology_adjacency_module, "error_provider"):
            register_error_provider(
                "topology",
                "adjacency",
                topology_adjacency_module.error_provider,
            )
    except (ImportError, AttributeError) as e:
        logger.debug("No error provider for topology.adjacency: %s", e)

    # Ops command error providers
    try:
        import src.cmd.commands.ops.logs as ops_logs_module

        if hasattr(ops_logs_module, "error_provider"):
            register_error_provider(
                "ops", "logs", ops_logs_module.error_provider
            )
    except (ImportError, AttributeError) as e:
        logger.debug("No error provider for ops.logs: %s", e)

    try:
        import src.cmd.commands.ops.test_all as ops_test_all_module

        if hasattr(ops_test_all_module, "error_provider"):
            register_error_provider(
                "ops", "test-all", ops_test_all_module.error_provider
            )
    except (ImportError, AttributeError) as e:
        logger.debug("No error provider for ops.test-all: %s", e)

    logger.info("Registered %d error providers", len(command_error_providers))


# Group registry for easy access
COMMAND_GROUPS = {
    "device": device,
    "network": network,
    "topology": topology,
    "ops": ops,
}
