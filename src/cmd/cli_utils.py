from src.utils.version_utils import load_gnmibuddy_version, get_python_version


ASCII_TITLE = r"""
 ▗▄▄▖▗▖  ▗▖▗▖  ▗▖▗▄▄▄▖▗▄▄▖ ▗▖ ▗▖▗▄▄▄ ▗▄▄▄▗▖  ▗▖
▐▌   ▐▛▚▖▐▌▐▛▚▞▜▌  █  ▐▌ ▐▌▐▌ ▐▌▐▌  █▐▌  █▝▚▞▘ 
▐▌▝▜▌▐▌ ▝▜▌▐▌  ▐▌  █  ▐▛▀▚▖▐▌ ▐▌▐▌  █▐▌  █ ▐▌  
▝▚▄▞▘▐▌  ▐▌▐▌  ▐▌▗▄█▄▖▐▙▄▞▘▝▚▄▞▘▐▙▄▄▀▐▙▄▄▀ ▐▌  
"""

DESCRIPTION = (
    "An opinionated tool that retrieves essential network information from devices using gNMI and OpenConfig models.\n"
    "Designed primarily for LLMs with Model Context Protocol (MCP) integration, it also provides a full CLI for direct use."
)

HELP: str = "Help: https://github.com/jillesca/gNMIBuddy"

python_version = get_python_version()
gnmibuddy_version = load_gnmibuddy_version()


def display_program_banner():
    """
    Display or return the program title, description, Python version, and gNMIBuddy version.
    Args:
        return_str (bool): If True, return the banner as a string. If False, print it.
    Returns:
        str: Banner string if return_str is True, else None.
    """
    banner = (
        f"{ASCII_TITLE}\n"
        f"{DESCRIPTION}\n"
        f"{HELP}\n"
        f"\nPython Version: {python_version}\n"
        f"gNMIBuddy Version: {gnmibuddy_version}\n"
    )
    return banner
