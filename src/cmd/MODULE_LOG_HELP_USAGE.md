# Module-Specific Logging Help

This document explains how to use the new `--module-log-help` option in gNMIBuddy for controlling logging verbosity at the module level.

## Overview

The `--module-log-help` option provides comprehensive help for the `--module-log-levels` feature, showing:

- Available modules for logging control
- Supported log levels
- Usage examples
- Common scenarios
- Validation of input format

## Usage

### Show Module Logging Help

```bash
uv run gnmibuddy.py --module-log-help
```

This will display:

- 📁 **Module Categories**: Organized list of all available modules
- 📊 **Log Levels**: Available levels (debug, info, warning, error) with descriptions
- 💡 **Usage Examples**: Practical examples for common use cases
- 🎯 **Common Scenarios**: Pre-configured examples for typical debugging situations

### Set Module-Specific Log Levels

```bash
# Basic usage - single module
uv run gnmibuddy.py --module-log-levels "gnmibuddy.collectors.interfaces=debug" device info --device R1

# Multiple modules
uv run gnmibuddy.py --module-log-levels "gnmibuddy.collectors=debug,pygnmi=error" device info --device R1

# Complex scenario
uv run gnmibuddy.py --log-level warning --module-log-levels "gnmibuddy.gnmi=debug,pygnmi=info" device info --device R1
```

## Available Modules

### Core Application

- `gnmibuddy` - Root application logger
- `gnmibuddy.api` - API layer
- `gnmibuddy.cli` - CLI components
- `gnmibuddy.mcp` - MCP server

### Data Collection

- `gnmibuddy.collectors` - All data collection modules
- `gnmibuddy.collectors.interfaces` - Interface data collection
- `gnmibuddy.collectors.routing` - Routing protocol data
- `gnmibuddy.collectors.mpls` - MPLS data collection
- `gnmibuddy.collectors.vpn` - VPN/VRF data collection
- `gnmibuddy.collectors.logs` - Device logs collection
- `gnmibuddy.collectors.system` - System information collection
- `gnmibuddy.collectors.topology` - Topology data collection
- `gnmibuddy.collectors.profile` - Device profile analysis

### Infrastructure

- `gnmibuddy.gnmi` - gNMI client operations
- `gnmibuddy.inventory` - Device inventory management
- `gnmibuddy.processors` - Data processing modules
- `gnmibuddy.services` - Service layer
- `gnmibuddy.utils` - Utility functions

### External Libraries

- `pygnmi` - PyGNMI library (external)
- `grpc` - gRPC library (external)
- `urllib3` - HTTP client library
- `asyncio` - Async I/O operations

## Log Levels

- **debug** - Detailed diagnostic information
- **info** - General operational information
- **warning** - Something unexpected happened but we can continue
- **error** - Serious problem that prevented operation completion

## Common Scenarios

### 🔍 Debugging Interface Issues

```bash
uv run gnmibuddy.py --log-level warning \
  --module-log-levels "gnmibuddy.collectors.interfaces=debug" \
  network interface --device R1
```

### 🔍 Debugging gNMI Connection Issues

```bash
uv run gnmibuddy.py --log-level warning \
  --module-log-levels "gnmibuddy.gnmi=debug,pygnmi=info" \
  device info --device R1
```

### 🔇 Minimal Noise (Production)

```bash
uv run gnmibuddy.py --log-level error \
  --module-log-levels "pygnmi=error,grpc=error" \
  device info --device R1
```

### 📈 Full Debug Mode

```bash
uv run gnmibuddy.py --log-level debug device info --device R1
```

### 🎛️ Granular Control

```bash
uv run gnmibuddy.py \
  --module-log-levels "gnmibuddy.collectors=debug,gnmibuddy.gnmi=info,pygnmi=warning" \
  network routing --device R1
```

## Validation

The system validates your module log level configuration:

### ✅ Valid Examples

```bash
--module-log-levels "gnmibuddy.collectors=debug"
--module-log-levels "gnmibuddy.collectors=debug,pygnmi=error"
--module-log-levels "gnmibuddy.gnmi=info,urllib3=warning"
```

### ❌ Invalid Examples

```bash
--module-log-levels "gnmibuddy.collectors=invalid_level"  # Invalid level
--module-log-levels "invalid_format"                      # Missing '='
```

When validation fails, you'll see:

```
❌ Invalid module log levels: Invalid log level 'invalid_level'. Available levels: debug, error, info, warning
💡 Use --module-log-help to see available modules and examples
```

## Integration with Other Options

### With Structured Logging

```bash
uv run gnmibuddy.py --structured-logging \
  --module-log-levels "gnmibuddy.collectors.interfaces=debug" \
  network interface --device R1
```

### With Batch Operations

```bash
uv run gnmibuddy.py --all-devices \
  --module-log-levels "gnmibuddy.collectors=info,pygnmi=error" \
  device info
```

## Implementation Details

The module logging help is implemented using a simplified approach for clarity and maintainability:

### Architecture

- `src/cmd/module_log_help.py` - Core functionality with simplified design
  - **HELP_TEMPLATE** - Single comprehensive template with all sections
  - **ModuleLogHelp** - Business logic with inline formatting
  - **Validation functions** - Input validation and error handling
- `src/cmd/parser.py` - CLI integration with validation
- `src/logging/config.py` - Logger name definitions from LoggerNames

### Design Philosophy

The implementation uses a simplified approach:

1. **Single template** - One comprehensive template with all sections
2. **Simple data structures** - Clean tuples and lists instead of complex dataclasses
3. **Direct formatting** - Inline formatting logic without multiple template layers
4. **Minimal abstraction** - Focus on clarity and simplicity over complex patterns

This ensures the code is easy to understand and maintain while providing comprehensive help functionality.

The system follows OpenTelemetry conventions for logger naming and is designed for easy integration with observability tools.

## Related Documentation

- [Full Logging Documentation](../logging/README.md)
- [Logging Implementation Details](../logging/IMPLEMENTATION.md)
- [CLI Design](./README.md)
