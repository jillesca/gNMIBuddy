#!/usr/bin/env python3
"""
Error handling utilities for CLI commands.
"""
import click
import sys


from typing import Optional


def display_error_with_help(
    ctx, error_message: str, suggestion: Optional[str] = None
):
    """
    Display error message with command help in consistent format.

    Args:
        ctx: Click context
        error_message: The error message to display
        suggestion: Optional helpful suggestion for the user
    """
    click.echo(f"Error: {error_message}", err=True)
    click.echo("─" * 50, err=True)
    click.echo("Command Help:", err=True)
    click.echo("─" * 50, err=True)
    click.echo(ctx.get_help(), err=True)

    if suggestion:
        click.echo(f"\n💡 {suggestion}", err=True)

    sys.exit(1)
