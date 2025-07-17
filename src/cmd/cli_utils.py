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

python_version = get_python_version()
gnmibuddy_version = load_gnmibuddy_version()


def display_program_banner():
    """Display the program title, description, Python version, and gNMIBuddy version."""
    print(ASCII_TITLE)
    print(DESCRIPTION)
    print(f"\nPython Version: {python_version}")
    print(f"gNMIBuddy Version: {gnmibuddy_version}\n")
