#!/usr/bin/env python3
"""
Inventory validation command implementation.
Provides CLI interface for validating inventory files.
"""

import sys
from typing import Optional

import click

from src.logging import get_logger
from src.schemas.responses import ValidationStatus
from src.inventory.validator import InventoryValidator
from src.inventory.file_handler import get_inventory_path
from src.cmd.schemas.command import Command
from src.cmd.registries.command_registry import register_command
from src.cmd.formatters import make_serializable, print_formatted_output

# Setup module logger
logger = get_logger(__name__)


def _get_command_help() -> str:
    """
    Get help text for the inventory validate command.

    Returns:
        Help text string
    """
    return """Validate inventory file format and schema.

This command performs comprehensive validation of inventory files including:

\b
- JSON format validation
- Schema compliance checking  
- IP address format validation (IPv4/IPv6, no CIDR)
- Network OS enum value validation
- Required field presence checking
- Optional field type validation
- Duplicate device name detection

The command supports multiple output formats for different use cases:

\b
- table: Human-readable format (default)
- json: Machine-readable format for CI/CD pipelines  
- yaml: Alternative structured format

Exit codes:

\b
- 0: Validation passed (no errors found)
- 1: Validation failed (errors found)

Examples:

\b
  gnmibuddy inventory validate
  gnmibuddy inventory validate --inventory /path/to/inventory.json
  gnmibuddy inventory validate --output json
  gnmibuddy i validate --output yaml"""


@register_command(Command.INVENTORY_VALIDATE)
@click.command(help=_get_command_help())
@click.option(
    "--inventory",
    help="Path to inventory file (overrides environment variable)",
    type=click.Path(
        exists=False
    ),  # Don't check existence here, let our resolver handle it
)
@click.option(
    "--output",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format (default: table)",
)
@click.pass_context
def inventory_validate(
    ctx: click.Context, inventory: Optional[str], output: str
) -> None:
    """
    Validate inventory file format and schema.

    Args:
        ctx: Click context object
        inventory: Optional path to inventory file
        output: Output format (table, json, yaml)
    """
    logger.debug("Starting inventory validation command")

    try:
        # Get the inventory file path
        if inventory:
            inventory_file = inventory
            logger.debug(
                "Using inventory file from command line: %s", inventory_file
            )
        else:
            try:
                inventory_file = get_inventory_path()
                logger.debug(
                    "Using inventory file from environment/default: %s",
                    inventory_file,
                )
            except FileNotFoundError as e:
                # Show error and help, similar to how device commands handle errors
                click.echo(f"Error: {e}", err=True)
                click.echo("─" * 50, err=True)
                click.echo("Command Help:", err=True)
                click.echo("─" * 50, err=True)
                click.echo(ctx.get_help(), err=True)
                sys.exit(1)

        # Create validator and run validation
        validator = InventoryValidator()
        result = validator.validate_inventory_file(inventory_file)

        # Display results based on output format
        if output == "table":
            _display_table_format(result)
        elif output in ["json", "yaml"]:
            # Use the existing formatter system for structured output
            serializable_result = make_serializable(result)
            print_formatted_output(serializable_result, output)

        # Set exit code based on validation result
        if result.status == ValidationStatus.FAILED:
            logger.debug("Validation failed, exiting with code 1")
            sys.exit(1)
        else:
            logger.debug("Validation passed, exiting with code 0")
            sys.exit(0)

    except Exception as e:
        logger.error("Error during inventory validation: %s", e)
        click.echo(f"Error: Inventory validation failed: {e}", err=True)
        sys.exit(1)


def _display_table_format(result) -> None:
    """
    Display validation results in human-readable table format.

    Args:
        result: ValidationResult object
    """
    # Header
    click.echo("Inventory Validation Results")
    click.echo("============================")
    click.echo(f"File: {result.file_path}")
    click.echo(f"Status: {str(result.status)}")
    click.echo(f"Total Devices: {result.total_devices}")
    click.echo(f"Valid Devices: {result.valid_devices}")
    click.echo(f"Invalid Devices: {result.invalid_devices}")
    click.echo()

    if result.status == ValidationStatus.PASSED:
        click.echo("✅ All devices passed validation!")
    else:
        click.echo("❌ Validation failed with the following errors:")
        click.echo("-------")

        for error in result.errors:
            # Format error message based on whether it's device-specific or file-level
            if error.device_name:
                error_line = f"Device {error.device_name}"
                if error.device_index is not None:
                    error_line += f" [index: {error.device_index}]"
                if error.field:
                    error_line += f" (field: {error.field})"
                error_line += f": {error.message}"
            else:
                error_line = f"File-level error: {error.message}"

            click.echo(error_line)

            if error.suggestion:
                click.echo(f"  → Suggestion: {error.suggestion}")
            click.echo()
