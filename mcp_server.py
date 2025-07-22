#!/usr/bin/env python3
"""
MCP entry point for gNMIBuddy - Registers network tool functions as MCP tools.
Uses a decorator factory to register API functions without duplicating signatures and docstrings.
"""
import os
import sys
import logging
from functools import wraps


from src.logging.external_suppression import ExternalLibrarySuppressor

ExternalLibrarySuppressor.setup_environment_suppression()

from mcp.server.fastmcp import FastMCP

import api
from src.utils.version_utils import load_gnmibuddy_version
from src.cmd.formatters import make_serializable
from src.logging import configure_logging, get_logger


def setup_mcp_logging():
    """Configure logging specifically for MCP server operation."""

    configure_logging(
        log_level="info",
        external_suppression_mode="mcp",  # Uses the most aggressive suppression
    )

    # For MCP servers, redirect all logging to stderr to keep stdout clean for JSON
    root_logger = logging.getLogger()

    # Remove all existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add stderr-only handler with clean format
    stderr_handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-30s | %(funcName)-20s:%(lineno)-4d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    stderr_handler.setFormatter(formatter)
    stderr_handler.setLevel(logging.INFO)

    root_logger.addHandler(stderr_handler)
    root_logger.setLevel(logging.DEBUG)


# Configure logging for MCP server
setup_mcp_logging()

logger = get_logger(__name__)


mcp = FastMCP("gNMIBuddy")
logger.info("Started MCP server for gNMIBuddy")
logger.debug("Network Inventory: %s", os.environ.get("NETWORK_INVENTORY"))


# Load and log gNMIBuddy version
gnmibuddy_version = load_gnmibuddy_version()
logger.info("Running gNMIBuddy version: %s", gnmibuddy_version)
logger.info("Python version: %s", sys.version)


def register_as_mcp_tool(func):
    """
    Decorator factory that creates an MCP tool wrapper for an API function.
    This preserves the original function's name, signature, docstring, and type hints.
    The wrapper automatically serializes the response to ensure MCP compatibility.

    Args:
        func: The API function to register as an MCP tool

    Returns:
        A decorated function that will be registered as an MCP tool
    """
    logger.debug("Registering MCP tool: %s", func.__name__)

    # Define a dynamic wrapper that preserves the original function's signature
    @mcp.tool()
    @wraps(
        func
    )  # This preserves docstring, name, and other function attributes
    def wrapper(*args, **kwargs):
        # Call the original function from the api module
        result = func(*args, **kwargs)

        serialized_result = make_serializable(result)

        logger.debug("MCP tool '%s' executed successfully", func.__name__)

        return serialized_result

    # Return the decorated function
    return wrapper


register_as_mcp_tool(api.get_routing_info)
register_as_mcp_tool(api.get_logs)
register_as_mcp_tool(api.get_interface_info)
register_as_mcp_tool(api.get_mpls_info)
register_as_mcp_tool(api.get_vpn_info)
register_as_mcp_tool(api.get_devices)
register_as_mcp_tool(api.get_device_profile_api)
register_as_mcp_tool(api.get_system_info)
register_as_mcp_tool(api.get_network_topology_api)
register_as_mcp_tool(api.get_topology_neighbors)


def main():
    """Run the MCP server"""
    mcp.run()


if __name__ == "__main__":
    main()
