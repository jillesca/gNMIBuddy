# Commands Module Structure

This directory contains the modular command implementations for gNMIBuddy CLI. Each command is implemented in its own file, organized by command groups.

## Directory Structure

```
commands/
├── __init__.py              # Base utilities exports
├── base.py                  # Common command utilities
├── README.md               # This documentation
├── device/                 # Device management commands
│   ├── __init__.py
│   ├── info.py            # `gnmibuddy device info`
│   ├── profile.py         # `gnmibuddy device profile`
│   └── list.py            # `gnmibuddy device list`
├── network/               # Network protocol commands
│   ├── __init__.py
│   ├── routing.py         # `gnmibuddy network routing`
│   ├── interface.py       # `gnmibuddy network interface`
│   ├── mpls.py           # `gnmibuddy network mpls`
│   └── vpn.py            # `gnmibuddy network vpn`
├── topology/              # Network topology commands
│   ├── __init__.py
│   ├── adjacency.py       # `gnmibuddy topology adjacency`
│   └── neighbors.py       # `gnmibuddy topology neighbors`
├── ops/                   # Operational commands
│   ├── __init__.py
│   ├── logs.py           # `gnmibuddy ops logs`
│   └── validate.py       # `gnmibuddy ops validate`
└── manage/                # Management commands
    ├── __init__.py
    └── log_level.py       # `gnmibuddy manage log-level`
```

## Benefits of This Structure

1. **Easier Navigation**: Each command has its own file, making it easy to find and modify specific functionality
2. **Better Organization**: Commands are grouped logically by their domain (device, network, topology, etc.)
3. **Reduced Code Duplication**: Common patterns are abstracted in `base.py`
4. **Easier Testing**: Each command can be tested independently
5. **Scalability**: Adding new commands is simple - just create a new file and register it

## Adding a New Command

To add a new command, follow these steps:

### 1. Create the Command File

Create a new file in the appropriate group directory (e.g., `src/cmd/commands/network/new_command.py`):

```python
#!/usr/bin/env python3
"""New command implementation"""
import click
from src.collectors.new_collector import get_new_data  # Your collector
from src.cmd.commands.base import execute_device_command, add_common_device_options


@click.command()
@add_common_device_options
@click.option("--custom-option", help="A custom option for this command")
@click.pass_context
def network_new_command(ctx, device, custom_option, output, devices, device_file, all_devices):
    """Description of what this command does

    \b
    Examples:
      uv run gnmibuddy.py network new-command --device R1
      uv run gnmibuddy.py network new-command --device R1 --custom-option value
      uv run gnmibuddy.py n new-command --device R1  # Using alias
    """
    def operation_func(device_obj, **kwargs):
        return get_new_data(device_obj, custom_option=custom_option)

    return execute_device_command(
        ctx=ctx,
        device=device,
        devices=devices,
        device_file=device_file,
        all_devices=all_devices,
        output=output,
        operation_func=operation_func,
        operation_name="new data",
        custom_option=custom_option
    )
```

### 2. Update the Group's **init**.py

Add your command to the appropriate group's `__init__.py` file:

```python
# In src/cmd/commands/network/__init__.py
from .new_command import network_new_command

__all__ = [
    # ... existing commands ...
    "network_new_command",
]
```

### 3. Register the Command

Add the command registration in `src/cmd/groups.py` in the `register_commands()` function:

```python
from src.cmd.commands.network import network_new_command  # Add import

# In register_commands function:
network.add_command(network_new_command, "new-command")
```

That's it! Your command is now available as `gnmibuddy network new-command`.

## Base Utilities

The `base.py` module provides common utilities that reduce code duplication:

### `execute_device_command()`

This function handles the common pattern of device commands including:

- Single device vs batch operations
- Inventory management
- Error handling
- Output formatting

### Atomic Decorators

The base module provides atomic decorators that can be combined for flexible option management:

#### `@add_output_option`

Adds the standard output format option:

- `--output` / `-o`: Output format (json, yaml)

#### `@add_detail_option(help_text="Show detailed information")`

Adds a detail flag option with customizable help text:

- `--detail`: Boolean flag for detailed output

#### `@add_device_selection_options`

Adds device selection options:

- `--device`: Single device name
- `--devices`: Comma-separated device list
- `--device-file`: File with device names
- `--all-devices`: Run on all devices

### `add_common_device_options`

A convenience decorator that combines `@add_output_option` and `@add_device_selection_options` for backward compatibility.

### Decorator Usage Examples

**For commands that need all common options:**

```python
@add_common_device_options
@add_detail_option("Show detailed interface information")
def network_interface(...):
```

**For commands that only need output formatting:**

```python
@add_output_option
@add_detail_option("Show detailed device information")
def device_list(...):
```

**For commands with custom device requirements:**

```python
@click.option("--device", required=True, help="Device name from inventory")
@add_detail_option("Show detailed topology information")
@add_output_option
def topology_neighbors(...):
```

### `handle_inventory_error_in_command()`

Provides user-friendly error messages for inventory-related issues.

## Command Registration

Commands are registered in `src/cmd/groups.py` using the `register_commands()` function. This function:

1. Imports all command implementations
2. Adds them to their respective Click groups
3. Makes them available through the CLI

The registration happens automatically when the CLI starts up.

## Testing Commands

Each command can be tested independently. Example test structure:

```python
# tests/cmd/commands/test_device_info.py
def test_device_info_single_device(mock_inventory):
    """Test device info command with single device"""
    # Test implementation

def test_device_info_batch_devices(mock_inventory):
    """Test device info command with multiple devices"""
    # Test implementation
```
