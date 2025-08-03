# Environment Configuration Guide

This guide provides detailed information about gNMIBuddy's environment variable management system, including advanced configuration options and best practices.

## Overview

gNMIBuddy uses **Pydantic Settings** for centralized, type-safe environment variable management. The system supports multiple configuration sources with a clear precedence hierarchy.

## Environment Variable Precedence

gNMIBuddy follows a strict precedence order when loading configuration:

1. **CLI arguments** (highest priority)

   ```bash
   gnmibuddy --log-level debug --inventory custom.json device list
   ```

2. **Operating system environment variables**

   ```bash
   export GNMIBUDDY_LOG_LEVEL=debug
   export NETWORK_INVENTORY=custom.json
   gnmibuddy device list
   ```

3. **`.env` file values**

   ```bash
   # .env file
   GNMIBUDDY_LOG_LEVEL=debug
   NETWORK_INVENTORY=custom.json
   ```

4. **Default values** (lowest priority)

## .env File Configuration

### Default Behavior

- gNMIBuddy automatically looks for a `.env` file in the project root
- Missing `.env` files are handled gracefully (no errors)
- Malformed `.env` files are handled gracefully with warnings

### Custom .env Files

Use the `--env-file` option to specify custom environment files:

```bash
# Development environment
gnmibuddy --env-file .env.development device list

# Production environment
gnmibuddy --env-file .env.production device list

# Testing environment
gnmibuddy --env-file tests/.env device list
```

### Environment File Examples

#### Basic Configuration

```bash
# .env
NETWORK_INVENTORY=inventory/devices.json
GNMIBUDDY_LOG_LEVEL=info
```

#### Development Configuration

```bash
# .env.development
NETWORK_INVENTORY=dev_inventory.json
GNMIBUDDY_LOG_LEVEL=debug
GNMIBUDDY_STRUCTURED_LOGGING=true
GNMIBUDDY_EXTERNAL_SUPPRESSION_MODE=development
GNMIBUDDY_MCP_TOOL_DEBUG=true
```

#### Production Configuration

```bash
# .env.production
NETWORK_INVENTORY=/opt/gnmibuddy/inventory.json
GNMIBUDDY_LOG_LEVEL=warning
GNMIBUDDY_STRUCTURED_LOGGING=true
GNMIBUDDY_LOG_FILE=/var/log/gnmibuddy/gnmibuddy.log
GNMIBUDDY_EXTERNAL_SUPPRESSION_MODE=cli
```

## Supported Environment Variables

### Network Configuration

| Variable            | Description                        | Type  | Default | Example                   |
| ------------------- | ---------------------------------- | ----- | ------- | ------------------------- |
| `NETWORK_INVENTORY` | Path to device inventory JSON file | `str` | `None`  | `/path/to/inventory.json` |

### Logging Configuration

| Variable                              | Description                      | Type   | Default    | Example                               |
| ------------------------------------- | -------------------------------- | ------ | ---------- | ------------------------------------- |
| `GNMIBUDDY_LOG_LEVEL`                 | Global logging level             | `str`  | `info`     | `debug`, `info`, `warning`, `error`   |
| `GNMIBUDDY_MODULE_LEVELS`             | Module-specific log levels       | `str`  | `None`     | `src.cmd=warning,src.inventory=debug` |
| `GNMIBUDDY_LOG_FILE`                  | Custom log file path             | `str`  | Sequential | `/custom/path/gnmibuddy.log`          |
| `GNMIBUDDY_STRUCTURED_LOGGING`        | Enable JSON logging format       | `bool` | `false`    | `true`, `false`                       |
| `GNMIBUDDY_EXTERNAL_SUPPRESSION_MODE` | External library log suppression | `str`  | `cli`      | `cli`, `mcp`, `development`           |

### MCP Configuration

| Variable                   | Description               | Type   | Default | Example         |
| -------------------------- | ------------------------- | ------ | ------- | --------------- |
| `GNMIBUDDY_MCP_TOOL_DEBUG` | Enable MCP tool debugging | `bool` | `false` | `true`, `false` |
