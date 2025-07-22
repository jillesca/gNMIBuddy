#!/usr/bin/env python3
"""
Command Module Registry

This module contains the centralized list of all command modules that need to be
imported by the registration coordinator. This serves as the single source of truth
for command module discovery and registration.

When adding new commands to the CLI system, follow these steps:

1. **Add to Command enum**: Add your command to the Command enum in
   `src/cmd/schemas/command.py` with command name and description:
   ```python
   MY_NEW_COMMAND = ("my-command", "Description of what it does")
   ```

2. **Register in CommandRegistry**: Add your command to the CommandRegistry in
   `src/cmd/schemas/commands.py` to specify its group and properties:
   ```python
   CommandInfo(
       command=Command.MY_NEW_COMMAND,
       group=CommandGroup.APPROPRIATE_GROUP,
       requires_device=True,  # or False for network-wide operations
   ),
   ```

3. **Create command module**: Create your command implementation file:
   `src/cmd/commands/group/command_name.py`

4. **Add to module registry**: Add the module path to COMMAND_MODULES list below:
   `"src.cmd.commands.group.command_name"`

5. **Registration happens automatically**: The registration coordinator will
   automatically discover and register your command with the CLI system.

The modules are organized by command groups for easier maintenance.
"""

from typing import List

# Central registry of all command modules that need to be imported
# for automatic command discovery and registration
COMMAND_MODULES: List[str] = [
    # Device commands - Commands for device management and information
    "src.cmd.commands.device.info",
    "src.cmd.commands.device.profile",
    "src.cmd.commands.device.list",
    # Network commands - Commands for network protocol analysis
    "src.cmd.commands.network.routing",
    "src.cmd.commands.network.interface",
    "src.cmd.commands.network.mpls",
    "src.cmd.commands.network.vpn",
    # Topology commands - Commands for topology discovery and analysis
    "src.cmd.commands.topology.neighbors",
    "src.cmd.commands.topology.network",
    # Operations commands - Commands for operational tasks and testing
    "src.cmd.commands.ops.logs",
    "src.cmd.commands.ops.test_all",
]


def get_command_modules() -> List[str]:
    """
    Get the list of all command modules that need to be imported.

    Returns:
        List of module paths as strings
    """
    return COMMAND_MODULES.copy()


def get_modules_by_group(group_name: str) -> List[str]:
    """
    Get command modules for a specific group.

    Args:
        group_name: The command group name (e.g., 'device', 'network', 'topology', 'ops')

    Returns:
        List of module paths for the specified group
    """
    prefix = f"src.cmd.commands.{group_name}."
    return [module for module in COMMAND_MODULES if module.startswith(prefix)]


def get_groups() -> List[str]:
    """
    Get all command groups that have registered modules.

    Returns:
        List of group names
    """
    groups = set()
    for module in COMMAND_MODULES:
        # Extract group name from module path like "src.cmd.commands.device.info"
        parts = module.split(".")
        if len(parts) >= 4 and parts[2] == "commands":
            groups.add(parts[3])
    return sorted(list(groups))
