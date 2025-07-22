#!/usr/bin/env python3
"""CLI utilities and banner display"""
from src.utils.version_utils import load_gnmibuddy_version, get_python_version


# ASCII art and banner templates - separated from logic for better readability
ASCII_TITLE = r"""
  ▗▄▄▖▗▖  ▗▖▗▖  ▗▖▗▄▄▄▖▗▄▄▖ ▗▖ ▗▖▗▄▄▄ ▗▄▄▄▗▖  ▗▖
 ▐▌   ▐▛▚▖▐▌▐▛▚▞▜▌  █  ▐▌ ▐▌▐▌ ▐▌▐▌  █▐▌  █▝▚▞▘ 
 ▐▌▝▜▌▐▌ ▝▜▌▐▌  ▐▌  █  ▐▛▀▚▖▐▌ ▐▌▐▌  █▐▌  █ ▐▌  
 ▝▚▄▞▘▐▌  ▐▌▐▌  ▐▌▗▄█▄▖▐▙▄▞▘▝▚▄▞▘▐▙▄▄▀▐▙▄▄▀ ▐▌  
"""

DESCRIPTION = (
    "An opinionated tool that retrieves essential network information from devices using gNMI and OpenConfig models.\n"
    "Designed primarily for LLMs with Model Context Protocol (MCP) integration, it also provides a full CLI."
)

HELP_URL = "Help: https://github.com/jillesca/gNMIBuddy"

PROGRAM_BANNER_TEMPLATE = """{ascii_title}
{description}
{help_url}

Python Version: {python_version}
gNMIBuddy Version: {gnmibuddy_version}
"""

# Cache version information to avoid repeated calls
python_version = get_python_version()
gnmibuddy_version = load_gnmibuddy_version()


def display_program_banner():
    """
    Display or return the program title, description, Python version, and gNMIBuddy version.

    Returns:
        str: Banner string
    """
    banner = PROGRAM_BANNER_TEMPLATE.format(
        ascii_title=ASCII_TITLE,
        description=DESCRIPTION,
        help_url=HELP_URL,
        python_version=python_version,
        gnmibuddy_version=gnmibuddy_version,
    )
    # Strip only trailing whitespace to preserve ASCII art leading spaces
    return banner.rstrip()
