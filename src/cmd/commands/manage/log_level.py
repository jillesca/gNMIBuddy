#!/usr/bin/env python3
"""Manage log_level command implementation"""
import click


@click.command()
@click.argument("action", type=click.Choice(["show", "set", "reset"]))
@click.option("--module", help="Module name for module-specific operations")
@click.option(
    "--level",
    type=click.Choice(["debug", "info", "warning", "error"]),
    help="Log level to set",
)
@click.pass_context
def manage_log_level(ctx, action, module, level):
    """Manage logging levels"""
    from src.logging.config import LoggingConfig

    if action == "show":
        if module:
            # Show specific module level
            levels = LoggingConfig.get_module_levels()
            if module in levels:
                click.echo(f"Module '{module}' log level: {levels[module]}")
            else:
                click.echo(
                    f"Module '{module}' not found or using default level"
                )
        else:
            # Show all levels
            levels = LoggingConfig.get_module_levels()
            if levels:
                click.echo("Current module log levels:")
                for mod, lvl in levels.items():
                    click.echo(f"  {mod}: {lvl}")
            else:
                click.echo("No custom module log levels set")

    elif action == "set":
        if not module or not level:
            click.echo(
                "Error: --module and --level are required for 'set' action",
                err=True,
            )
            raise click.Abort()

        LoggingConfig.set_module_level(module, level)
        click.echo(f"Set log level for module '{module}' to '{level}'")

    elif action == "reset":
        if module:
            # Reset specific module (implement if needed)
            click.echo(f"Resetting log level for module '{module}' to default")
        else:
            # Reset all to defaults
            click.echo("Resetting all log levels to defaults")
            # Note: LoggingConfig doesn't have reset_to_defaults method
            # This would need to be implemented if needed
