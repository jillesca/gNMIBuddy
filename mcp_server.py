#!/usr/bin/env python3
"""
MCP entry point for gNMIBuddy - Registers network tool functions as MCP tools.
Uses a decorator factory to register API functions without duplicating signatures and docstrings.
"""
import os
import logging
from functools import wraps
from mcp.server.fastmcp import FastMCP

import api

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp")


mcp = FastMCP("gNMIBuddy")
logger.info("Started MCP server for gNMIBuddy")
logger.debug(f'Network Inventory: {os.environ.get("NETWORK_INVENTORY")}')


def register_as_mcp_tool(func):
    """
    Decorator factory that creates an MCP tool wrapper for an API function.
    This preserves the original function's name, signature, docstring, and type hints.

    Args:
        func: The API function to register as an MCP tool

    Returns:
        A decorated function that will be registered as an MCP tool
    """
    logger.debug(f"Calling MCP tool: {func.__name__} ")

    # Define a dynamic wrapper that preserves the original function's signature
    @mcp.tool()
    @wraps(
        func
    )  # This preserves docstring, name, and other function attributes
    def wrapper(*args, **kwargs):
        # Call the original function from the api module
        return func(*args, **kwargs)

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
register_as_mcp_tool(api.get_topology_ip_adjacency_dump)
register_as_mcp_tool(api.get_topology_neighbors)


def main():
    """Run the MCP server"""
    mcp.run()


if __name__ == "__main__":
    main()
