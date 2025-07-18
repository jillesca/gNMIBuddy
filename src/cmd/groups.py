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

    Run 'gnmibuddy device COMMAND --help' for more information on a specific command.
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


# Group registry for easy access
COMMAND_GROUPS = {
    "device": device,
    "network": network,
    "topology": topology,
    "ops": ops,
    "manage": manage,
}


def get_group_for_command(command_name: str) -> str:
    """Get the group name for a given command name"""
    command_mappings = {
        # Device group
        "system": "device",
        "deviceprofile": "device",
        "device-profile": "device",
        "list-devices": "device",
        # Network group
        "routing": "network",
        "interface": "network",
        "mpls": "network",
        "vpn": "network",
        # Topology group
        "topology-adjacency": "topology",
        "topology-neighbors": "topology",
        # Ops group
        "logging": "ops",
        "test-all": "ops",
        # Manage group
        "log-level": "manage",
        "list-commands": "manage",
    }

    return command_mappings.get(
        command_name, "device"
    )  # Default to device group


def get_new_command_name(old_name: str) -> str:
    """Map old command names to new hierarchical names"""
    name_mappings = {
        # Device group mappings
        "system": "info",
        "deviceprofile": "profile",
        "device-profile": "profile",  # This should also map to profile
        "list-devices": "list",
        # Network group mappings
        "routing": "routing",
        "interface": "interface",
        "mpls": "mpls",
        "vpn": "vpn",
        # Topology group mappings
        "topology-adjacency": "adjacency",
        "topology-neighbors": "neighbors",
        # Ops group mappings
        "logging": "logs",
        "test-all": "test-all",
        # Manage group mappings
        "log-level": "log-level",
        "list-commands": "list-commands",
    }

    return name_mappings.get(old_name, old_name)
