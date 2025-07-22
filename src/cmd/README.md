# gNMIBuddy CLI Module Documentation

This module provides the complete command-line interface for gNMIBuddy, built on the Click framework with a modular, extensible architecture.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Module Structure](#module-structure)
- [Core Components](#core-components)
- [How Components Work Together](#how-components-work-together)
- [Command Flow](#command-flow)
- [Adding New Commands](#adding-new-commands)
- [Error Handling System](#error-handling-system)
- [Template System](#template-system)
- [Development Guidelines](#development-guidelines)

## Architecture Overview

The CLI module follows several key design patterns:

- **Registry Pattern**: Commands and groups are registered dynamically
- **Template Pattern**: Consistent help and error messages using templates
- **Decorator Pattern**: Reusable option decorators for common functionality
- **Factory Pattern**: Output formatters for different output types
- **Context Pattern**: Dependency injection through CLI context
- **Command Pattern**: Each command is a separate, testable unit

### Design Principles

1. **Modularity**: Each command group has its own directory
2. **Consistency**: Common patterns through decorators and base utilities
3. **Extensibility**: Easy to add new commands and groups
4. **Testability**: Each command can be tested independently
5. **User Experience**: Rich help, examples, and error messages

## Module Structure

```plaintext
src/cmd/
├── __init__.py                    # Module exports
├── README.md                      # This documentation
│
├── Core Infrastructure/
├── parser.py                      # Main CLI entry point & Click group setup
├── context.py                     # CLI context and dependency injection
├── base.py                        # Legacy base classes (minimal usage)
├── cli_utils.py                   # CLI utilities and banner display
├── formatters.py                  # Output formatting (JSON, YAML)
├── display.py                     # Help display and command listing
├── batch.py                       # Batch operations and parallel execution
├── version.py                     # Version information display
├── module_log_help.py             # Module-specific logging help
│
├── Command Implementations/
├── commands/
│   ├── __init__.py               # Common utilities exports
│   ├── README.md                 # Command implementation guide
│   ├── base.py                   # Core command utilities
│   ├── decorators.py             # Command option decorators
│   ├── batch_operations.py       # Batch operation handling
│   │
│   ├── device/                   # Device management commands
│   │   ├── __init__.py
│   │   ├── info.py              # gnmibuddy device info
│   │   ├── profile.py           # gnmibuddy device profile
│   │   └── list.py              # gnmibuddy device list
│   │
│   ├── network/                  # Network protocol commands
│   │   ├── __init__.py
│   │   ├── routing.py           # gnmibuddy network routing
│   │   ├── interface.py         # gnmibuddy network interface
│   │   ├── mpls.py              # gnmibuddy network mpls
│   │   └── vpn.py               # gnmibuddy network vpn
│   │
│   ├── topology/                 # Network topology commands
│   │   ├── __init__.py
│   │   ├── neighbors.py         # gnmibuddy topology neighbors
│   │   └── network.py           # gnmibuddy topology network
│   │
│   └── ops/                      # Operational commands
│       ├── __init__.py
│       ├── logs.py              # gnmibuddy ops logs
│       └── validate.py          # gnmibuddy ops validate
│
├── Registration System/
├── registries/
│   ├── __init__.py
│   ├── command_registry.py       # Command registration and lookup
│   ├── group_registry.py         # Group registration and management
│   ├── coordinator.py            # Coordinates registration process
│   └── command_modules.py        # Module discovery utilities
│
├── Schema Definitions/
├── schemas/
│   ├── __init__.py
│   ├── command.py                # Individual command definitions
│   ├── command_group.py          # Command group definitions
│   └── commands.py               # Command metadata and registry
│
├── Error Handling/
├── error_handling/
│   ├── __init__.py
│   ├── click_integration.py      # Click exception handling
│   ├── handlers.py               # Error handler classes
│   └── templates.py              # Error message templates
│
├── Template System/
├── templates/
│   ├── __init__.py
│   ├── error_templates.py        # Error message templates
│   ├── help_templates.py         # Help message templates
│   └── usage_templates.py        # Usage message templates
│
├── Examples System/
├── examples/
│   └── example_builder.py        # Command example generation
│
├── Legacy/Error Providers/
├── error_providers.py            # Command-specific error providers
│
└── Documentation/
    └── improvement plan/          # Implementation and planning docs
        ├── CLI_IMPLEMENTATION_PLAN.md
        ├── CLI_IMPLEMENTATION_SUMMARY.md
        ├── Improvement_plan.md
        └── MODULE_LOG_HELP_USAGE.md
```

## Core Components

### 1. CLI Entry Point (`parser.py`)

The main entry point that:

- Sets up the root Click group with global options
- Configures logging from CLI options
- Handles inventory management
- Registers all command groups
- Provides version and help callbacks

```python
@click.group(invoke_without_command=True)
@click.option("--log-level", ...)
@click.option("--module-log-levels", ...)
@click.option("--inventory", ...)
def cli(ctx, ...):
    # Configure context and logging
    # Register command groups
```

### 2. Command Registration (`registries/`)

**CommandRegistry** (`command_registry.py`):

- Maintains mapping of Command enums to function implementations
- Handles error provider registration
- Provides command lookup functionality

**GroupRegistry** (`group_registry.py`):

- Creates Click groups for each CommandGroup enum
- Manages group aliases and help text
- Provides group lookup and validation

**RegistrationCoordinator** (`coordinator.py`):

- Orchestrates the registration process
- Imports command modules dynamically
- Registers commands with their groups
- Provides registration statistics

**CommandModules** (`command_modules.py`):

- Maintains the COMMAND_MODULES list for module discovery
- Provides utilities to get modules by group
- Single source of truth for which modules should be imported
- Must be updated when adding new commands

### 3. Schema System (`schemas/`)

**Command** (`command.py`):

- Enum defining all individual commands
- Maps command names to descriptions
- Provides command lookup utilities

**CommandGroup** (`command_group.py`):

- Enum defining command groups (device, network, topology, ops)
- Includes group names, aliases, titles, and descriptions
- Provides group resolution utilities

### 4. Command Implementation (`commands/`)

**Base Utilities** (`base.py`):

- `execute_device_command()`: Main orchestration function
- Error handling for device operations
- Integration with batch operations
- CommandErrorProvider base class

**Decorators** (`decorators.py`):

- `@add_common_device_options`: Standard device selection options
- `@add_output_option`: Output format selection
- `@add_detail_option`: Detail flag with custom help text
- `@add_device_selection_options`: Device selection with validation

**Batch Operations** (`batch_operations.py`):

- Parallel execution across multiple devices
- Progress reporting and error handling
- Integration with the base command execution flow

### 5. Error Handling (`error_handling/`)

- **Click Integration**: Handles Click exceptions gracefully
- **Error Handlers**: Provides user-friendly error messages
- **Templates**: Consistent error message formatting

### 6. Template System (`templates/`)

- **Error Templates**: Standardized error message formats
- **Help Templates**: Consistent help message structures
- **Usage Templates**: Common usage pattern messages

## How Components Work Together

### 1. Startup Flow

```plaintext
parser.py:cli()
    ↓
Configure CLI Context
    ↓
Register Command Groups (coordinator.py)
    ↓
Import Command Modules
    ↓
Register Commands with Groups
    ↓
Ready to Handle Commands
```

### 2. Command Execution Flow

```plaintext
User Input: gnmibuddy device info --device R1
    ↓
Click Routes to: device_info() function
    ↓
Decorators Apply: add_common_device_options
    ↓
Command Function Calls: execute_device_command()
    ↓
Device Resolution: InventoryManager.get_device()
    ↓
Operation Execution: operation_func(device_obj)
    ↓
Output Formatting: format_output()
    ↓
Display Result
```

### 3. Batch Operation Flow

```plaintext
User Input: gnmibuddy device info --all-devices
    ↓
execute_device_command() detects batch operation
    ↓
DeviceListParser.get_all_inventory_devices()
    ↓
execute_batch_operation()
    ↓
BatchOperationExecutor (parallel execution)
    ↓
Progress reporting and result collection
    ↓
Format and display batch results
```

### 4. Error Handling Flow

```plaintext
Exception Occurs
    ↓
Click Error Handler (error_handling/click_integration.py)
    ↓
Error Type Detection
    ↓
Template Selection (templates/error_templates.py)
    ↓
Context-Aware Error Message
    ↓
User-Friendly Display with Examples
```

## Command Flow

### Single Device Command

1. **Input Parsing**: Click parses command line arguments
2. **Option Validation**: Decorators validate device selection options
3. **Context Setup**: CLI context is populated with options
4. **Device Resolution**: Inventory manager resolves device name
5. **Operation Execution**: Collector function is called
6. **Result Processing**: Data is processed and formatted
7. **Output Display**: Formatted result is displayed to user

### Batch Command

1. **Batch Detection**: Multiple devices specified via --devices, --all-devices, etc.
2. **Device List Building**: Device names are resolved from various sources
3. **Parallel Execution**: BatchOperationExecutor runs operations in parallel
4. **Progress Reporting**: Real-time progress updates during execution
5. **Result Aggregation**: Results are collected into BatchOperationResult
6. **Summary Display**: Success/failure summary with details

## Adding New Commands

### Overview: Key Registration Steps

When adding a new command, you need to update **three critical files** for proper registration:

1. **`src/cmd/schemas/command.py`** - Define the command enum
2. **`src/cmd/schemas/commands.py`** - Register command with its group and properties
3. **`src/cmd/registries/command_modules.py`** - Add module path to COMMAND_MODULES list

Missing any of these steps will result in commands not being discovered or registered properly.

### Step 1: Define the Command

Add your command to `src/cmd/schemas/command.py`:

```python
class Command(Enum):
    # ... existing commands ...
    NETWORK_SECURITY = ("security", "Get security configuration and status")
```

### Step 2: Register Command in CommandRegistry

Add your command to the CommandRegistry in `src/cmd/schemas/commands.py`:

```python
def _initialize_commands(self):
    """Initialize with known commands using Command enum"""
    commands = [
        # ... existing commands ...

        # Add your new command here
        CommandInfo(
            command=Command.NETWORK_SECURITY,
            group=CommandGroup.NETWORK,
            supports_batch=True,        # Whether command supports --all-devices, --devices
            supports_detail=True,       # Whether command supports --detail flag
            requires_device=True,       # Whether command requires --device option
        ),
    ]
```

### Step 3: Add Module to Command Registry

Add your command module to the COMMAND_MODULES list in `src/cmd/registries/command_modules.py`:

```python
COMMAND_MODULES: List[str] = [
    # ... existing modules ...

    # Network commands
    "src.cmd.commands.network.routing",
    "src.cmd.commands.network.interface",
    "src.cmd.commands.network.mpls",
    "src.cmd.commands.network.vpn",
    "src.cmd.commands.network.security",  # Add your new module here

    # ... rest of modules ...
]
```

### Step 4: Create Command Implementation

Create `src/cmd/commands/network/security.py`:

```python
#!/usr/bin/env python3
"""Network security command implementation"""
import click
from src.collectors.security import get_security_info  # Your collector
from src.cmd.commands.base import execute_device_command
from src.cmd.commands.decorators import (
    add_common_device_options,
    add_detail_option,
)
from src.cmd.schemas.commands import Command
from src.cmd.error_providers import CommandErrorProvider
from src.cmd.registries.command_registry import (
    register_command,
    register_error_provider,
)

from src.cmd.examples.example_builder import (
    ExampleBuilder,
    ExampleSet,
)


def network_security_examples() -> ExampleSet:
    """Build network security command examples."""
    return ExampleBuilder.network_command_examples(
        command=Command.NETWORK_SECURITY.command_name,
        device="R1",
        detail_option=True,
        batch_operations=True,
        output_formats=True,
    )


def _get_command_help() -> str:
    return network_security_examples().for_help()


error_provider = CommandErrorProvider(Command.NETWORK_SECURITY)
register_error_provider(Command.NETWORK_SECURITY, error_provider)


@register_command(Command.NETWORK_SECURITY)
@click.command(help=_get_command_help())
@add_common_device_options
@click.option("--policy-type", help="Filter by security policy type")
@add_detail_option("Show detailed security information")
@click.pass_context
def network_security(
    ctx, device, policy_type, detail, output, devices, device_file, all_devices
):
    """Get security configuration from a network device"""

    def operation_func(device_obj, **kwargs):
        return get_security_info(device_obj, policy_type=policy_type, include_details=detail)

    return execute_device_command(
        ctx=ctx,
        device=device,
        devices=devices,
        device_file=device_file,
        all_devices=all_devices,
        output=output,
        operation_func=operation_func,
        operation_name="security information",
        policy_type=policy_type,
        detail=detail,
    )


if __name__ == "__main__":
    print(_get_command_help())
```

### Step 5: Update Group Exports

Add to `src/cmd/commands/network/__init__.py`:

```python
from .security import network_security

__all__ = [
    # ... existing exports ...
    "network_security",
]
```

### Step 6: Create Collector Function

Implement your collector in `src/collectors/security.py`:

```python
def get_security_info(device_obj, policy_type=None, include_details=False):
    """Collect security information from device"""
    # Your implementation here
    pass
```

### Step 7: Test the Command

The command is now automatically registered and available:

```bash
# Test basic functionality
uv run gnmibuddy.py network security --device R1

# Test with options
uv run gnmibuddy.py network security --device R1 --policy-type firewall --detail

# Test batch operations
uv run gnmibuddy.py network security --all-devices --output yaml
```

## Adding New Command Groups

If you need to create an entirely new command group (beyond device, network, topology, ops):

### Step 1: Define the Group

Add your group to `src/cmd/schemas/command_group.py`:

```python
class CommandGroup(Enum):
    # ... existing groups ...

    SECURITY = (
        "security",      # Full group name
        "s",            # Short alias
        "Security",     # Display title
        "Commands for security analysis and configuration",  # Description
    )
```

### Step 2: Create Group Directory

Create the directory structure:

```bash
mkdir src/cmd/commands/security
touch src/cmd/commands/security/__init__.py
```

### Step 3: Add Commands to New Group

Follow the "Adding New Commands" process above, but:

- Use `CommandGroup.SECURITY` in the CommandRegistry
- Create command files in `src/cmd/commands/security/`
- Add modules to COMMAND_MODULES with `"src.cmd.commands.security.command_name"`

### Step 4: Update Group Exports

Add exports in `src/cmd/commands/security/__init__.py`:

```python
from .scan import security_scan
from .audit import security_audit

__all__ = [
    "security_scan",
    "security_audit",
]
```

The new group will be automatically registered and available as:

- `gnmibuddy security <command>` (full name)
- `gnmibuddy s <command>` (alias)

## Advanced Command Features

### Custom Options and Validation

```python
@click.option(
    "--protocol",
    type=click.Choice(["bgp", "isis", "ospf"]),
    help="Filter by routing protocol",
)
@click.option(
    "--timeout",
    type=int,
    default=30,
    help="Operation timeout in seconds",
)
def my_command(ctx, device, protocol, timeout, ...):
    # Validation
    if timeout < 1 or timeout > 300:
        raise click.BadParameter("Timeout must be between 1 and 300 seconds")
```

### Custom Examples

```python
def my_command_examples() -> ExampleSet:
    """Build custom examples for my command."""
    examples = ExampleBuilder.network_command_examples(
        command="mycommand",
        device="R1",
        detail_option=True,
        batch_operations=True,
    )

    # Add command-specific examples
    examples.add_advanced(
        command="uv run gnmibuddy.py network mycommand --device R1 --protocol bgp",
        description="Filter by BGP protocol",
    ).add_advanced(
        command="uv run gnmibuddy.py n mycommand --all-devices --timeout 60",
        description="Extended timeout for all devices",
    )

    return examples
```

### Error Handling

The error provider is automatically configured, but you can customize it:

```python
class MyCommandErrorProvider(CommandErrorProvider):
    def get_custom_error_examples(self) -> ExampleSet:
        """Custom error examples for this command."""
        examples = ExampleSet("my_command_errors")
        examples.add_error_missing_device(
            command="uv run gnmibuddy.py network mycommand --device R1",
            description="Specify device for security check"
        )
        return examples
```

## Error Handling System

### Error Types Handled

1. **Click Exceptions**: Command line parsing errors
2. **Device Not Found**: Invalid device names
3. **Inventory Errors**: Missing or invalid inventory files
4. **Validation Errors**: Invalid option values
5. **Unexpected Arguments**: Positional arguments where options expected

### Error Message Features

- **User-Friendly**: Clear, actionable error messages
- **Context-Aware**: Relevant examples based on the command being used
- **Suggestions**: Alternative commands or options when applicable
- **Help Integration**: Automatic help display for command errors

### Adding Custom Error Handling

```python
from src.cmd.error_handling.templates import ErrorTemplates, TemplateData

@dataclass
class MyCustomErrorData(TemplateData):
    error_detail: str
    suggested_fix: str

# In your command implementation
try:
    result = risky_operation()
except MyCustomException as e:
    error_data = MyCustomErrorData(
        error_detail=str(e),
        suggested_fix="Try using --retry flag"
    )
    formatted_error = ErrorTemplates.format_custom_error(error_data)
    click.echo(formatted_error, err=True)
    raise click.Abort()
```

## Template System

### Available Templates

- **Error Templates**: Standardized error message formats
- **Help Templates**: Command help and usage information
- **Usage Templates**: Common usage patterns and examples

### Template Usage

```python
from src.cmd.templates.error_templates import ErrorTemplates, DeviceNotFoundData

data = DeviceNotFoundData(
    device="invalid_device",
    suggestions=["R1", "R2", "R3"],
    available_devices=inventory_manager.get_device_names()
)

error_message = ErrorTemplates.format_device_not_found_error(data)
click.echo(error_message, err=True)
```

### Creating Custom Templates

```python
from src.cmd.templates.error_templates import TemplateData

@dataclass
class MyTemplateData(TemplateData):
    field1: str
    field2: List[str]

class MyTemplates:
    MY_TEMPLATE = """❌ My Error Type
═══════════════════════════════════════════════════════════

{field1}

Available options:
{field2_list}

💡 How to fix this:
  Use one of the available options above"""

    @classmethod
    def format_my_error(cls, data: MyTemplateData) -> str:
        field2_list = "\n".join(f"  • {item}" for item in data.field2)
        return cls.MY_TEMPLATE.format(
            field1=data.field1,
            field2_list=field2_list
        )
```

## Development Guidelines

### Code Organization

1. **One command per file**: Each command gets its own implementation file
2. **Group by domain**: Commands organized by functional area (device, network, etc.)
3. **Consistent naming**: Follow the pattern `{group}_{command}.py` for files
4. **Proper imports**: Use relative imports within the cmd module

### Testing Strategy

1. **Unit Tests**: Test individual command functions
2. **Integration Tests**: Test command registration and CLI integration
3. **Error Testing**: Verify error handling and messages
4. **Example Testing**: Ensure examples work as documented

### Performance Considerations

1. **Lazy Loading**: Commands are only loaded when needed
2. **Parallel Execution**: Batch operations use ThreadPoolExecutor
3. **Progress Reporting**: Long-running operations show progress
4. **Resource Management**: Proper cleanup of connections and resources

### Documentation Standards

1. **Docstrings**: Every command function needs comprehensive docstrings
2. **Examples**: Rich examples using the ExampleBuilder system
3. **Help Text**: Clear, actionable help messages
4. **Error Messages**: User-friendly error messages with suggestions

### Best Practices

1. **Use Decorators**: Leverage existing decorators for common options
2. **Error Handling**: Always handle expected errors gracefully
3. **Validation**: Validate inputs and provide clear error messages
4. **Consistency**: Follow established patterns for similar functionality
5. **Testing**: Write tests for new commands and features

## Logging and Debugging

### Module-Specific Logging

The CLI module supports detailed logging configuration:

```bash
# Debug specific modules
uv run gnmibuddy.py --module-log-levels "gnmibuddy.cmd=debug,gnmibuddy.collectors=info" device info --device R1

# Show available modules and examples
uv run gnmibuddy.py --module-log-help
```

### Available Log Modules

- `gnmibuddy.cmd` - CLI components
- `gnmibuddy.cmd.commands` - Command implementations
- `gnmibuddy.cmd.registries` - Command registration
- `gnmibuddy.cmd.error_handling` - Error handling system

### Debugging Tips

1. **Use Debug Logging**: Enable debug logging for the cmd module when developing
2. **Check Registration**: Verify commands are properly registered
3. **Validate Examples**: Test that examples in help text actually work
4. **Error Message Testing**: Trigger error conditions to test error messages

---

This CLI module provides a robust, extensible foundation for the gNMIBuddy command-line interface. The modular design makes it easy to add new commands while maintaining consistency and providing excellent user experience.
