#!/usr/bin/env python3
"""
MCP entry point for gNMIBuddy - Registers network tool functions as MCP tools.
Uses a decorator factory to register API functions without duplicating signatures and docstrings.
"""
import os
from functools import wraps
from typing import Optional

from mcp.server.fastmcp import FastMCP, Context

from src.logging import ExternalLibrarySuppressor

# Early environment suppression (before any gRPC imports)
from src.logging.suppression.external import SuppressionConfiguration

config = SuppressionConfiguration.create_default()
ExternalLibrarySuppressor.apply_suppression(config)

import api
from src.utils.version_utils import load_gnmibuddy_version, get_python_version
from src.cmd.formatters import make_serializable
from src.logging import (
    setup_mcp_logging,
    get_mcp_logger,
    read_mcp_environment_config,
)
from src.config.environment import get_settings


mcp_env_config = read_mcp_environment_config()
setup_mcp_logging(tool_debug_mode=mcp_env_config.get("tool_debug_mode", False))

mcp = FastMCP("gNMIBuddy")
logger = get_mcp_logger(__name__)

logger.std_logger.info("Started MCP server for gNMIBuddy")

settings = get_settings()
network_inventory = settings.get_network_inventory()
logger.std_logger.info("Network Inventory: %s", network_inventory)

gnmibuddy_version = load_gnmibuddy_version()
python_version = get_python_version()
logger.std_logger.info("Running gNMIBuddy version: %s", gnmibuddy_version)
logger.std_logger.info("Python version: %s", python_version)


def register_as_mcp_tool(func):
    """
    Decorator factory that creates an MCP tool wrapper for an API function.
    This preserves the original function's name, signature, docstring, and type hints.
    The wrapper automatically serializes the response and uses MCP context logging.

    Args:
        func: The API function to register as an MCP tool

    Returns:
        A decorated function that will be registered as an MCP tool
    """

    @mcp.tool()
    @wraps(
        func
    )  # This preserves docstring, name, and other function attributes
    async def wrapper(*args, ctx: Optional[Context] = None, **kwargs):
        tool_logger = get_mcp_logger(
            f"gnmibuddy.mcp.tools.{func.__name__}", ctx
        )

        try:
            await tool_logger.info("Executing tool: %s", func.__name__)
            await tool_logger.debug(
                "Arguments: args=%s, kwargs=%s", args, kwargs
            )

            result = func(*args, **kwargs)

            serialized_result = make_serializable(result)

            await tool_logger.info(
                "Tool '%s' completed successfully", func.__name__
            )

            return serialized_result

        except Exception as e:
            await tool_logger.error(
                "Tool '%s' failed: %s",
                func.__name__,
                str(e),
                exception=str(e),
                function=func.__name__,
                exception_type=type(e).__name__,
            )
            raise

    return wrapper


# Register all API functions as MCP tools
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
    logger.std_logger.info("Starting FastMCP server")
    mcp.run()


if __name__ == "__main__":
    main()
