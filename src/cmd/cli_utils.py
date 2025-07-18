from src.utils.version_utils import load_gnmibuddy_version, get_python_version
import click
import functools


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


def output_option(f):
    """
    Decorator to add consistent --output option to Click commands.

    Usage:
        @click.command()
        @output_option
        def my_command(output, ...):
            # Command implementation
            result = get_data()
            output_result(result, output)
    """

    @click.option(
        "--output",
        "-o",
        type=click.Choice(["json", "yaml"], case_sensitive=False),
        default="json",
        help="Output format (json, yaml)",
    )
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)

    return wrapper


def output_result(data, output_format="json"):
    """
    Helper function to consistently format and output results.

    Args:
        data: The data to format and output
        output_format: The format to use ('json' or 'yaml')
    """
    from src.cmd.formatters import format_output

    if data is None:
        data = {"status": "no_data", "message": "No data available"}

    formatted_output = format_output(data, output_format.lower())
    click.echo(formatted_output)


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
