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
