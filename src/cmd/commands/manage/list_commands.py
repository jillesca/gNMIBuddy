#!/usr/bin/env python3
"""Manage list_commands command implementation"""
import click


@click.command()
@click.pass_context
def manage_list_commands(ctx):
    """List all available commands"""
    from src.cmd.groups import COMMAND_GROUPS

    click.echo("Available command groups and commands:")
    click.echo("=" * 50)

    for group_name, group in COMMAND_GROUPS.items():
        click.echo(f"\n{group_name.upper()} Commands:")
        click.echo("-" * 20)

        if hasattr(group, "commands") and group.commands:
            for cmd_name, cmd in group.commands.items():
                # Get the command description
                help_text = getattr(cmd, "help", "No description available")
                if help_text and len(help_text) > 60:
                    help_text = help_text[:60] + "..."
                click.echo(f"  {cmd_name:<20} {help_text}")
        else:
            click.echo("  No commands available")
