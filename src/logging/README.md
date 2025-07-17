# gNMIBuddy Enhanced Logging Guide

This document explains the enhanced logging system in gNMIBuddy, which follows OpenTelemetry (OTel) best practices for observability-ready logging.

## Table of Contents

1. [Overview](#overview)
2. [Key Features](#key-features)
3. [Configuration](#configuration)
4. [CLI Usage](#cli-usage)
5. [Module-Specific Logging](#module-specific-logging)
6. [Structured Logging](#structured-logging)
7. [Operation Tracking](#operation-tracking)
8. [Dynamic Log Level Management](#dynamic-log-level-management)
9. [Integration with Observability Tools](#integration-with-observability-tools)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)

## Overview

The enhanced logging system provides:

- **Hierarchical logger naming** following OTel conventions
- **Module-specific log level control** to reduce noise
- **Structured JSON logging** for machine parsing
- **Operation tracking** with timing and context
- **Dynamic log level changes** at runtime
- **External library noise reduction**
- **Future OTel integration readiness**

## Key Features

### 1. Standardized Logger Names

All loggers follow a consistent naming convention:

```plaintext
gnmibuddy                          # Root application logger
├── gnmibuddy.api                  # API layer
├── gnmibuddy.cli                  # CLI components
├── gnmibuddy.mcp                  # MCP server
├── gnmibuddy.collectors           # Data collection modules
│   ├── gnmibuddy.collectors.interfaces
│   ├── gnmibuddy.collectors.routing
│   ├── gnmibuddy.collectors.mpls
│   ├── gnmibuddy.collectors.vpn
│   ├── gnmibuddy.collectors.logs
│   ├── gnmibuddy.collectors.system
│   ├── gnmibuddy.collectors.topology
│   └── gnmibuddy.collectors.profile
├── gnmibuddy.gnmi                 # gNMI client operations
├── gnmibuddy.inventory            # Device inventory
├── gnmibuddy.processors           # Data processors
├── gnmibuddy.services             # Service layer
├── gnmibuddy.utils                # Utilities
├── pygnmi                         # External pygnmi library
└── grpc                          # External gRPC library
```

### 2. Module-Specific Log Levels

Control logging verbosity per module:

```python
module_levels = {
    "gnmibuddy.collectors": "debug",        # Verbose for data collection
    "gnmibuddy.gnmi": "info",              # Normal for gNMI operations
    "pygnmi": "warning",                   # Minimal for external library
    "grpc": "error",                       # Only errors for gRPC
}
```

## Configuration

### Programmatic Configuration

```python
from src.logging.config import LoggingConfig, LoggerNames

# Basic configuration
LoggingConfig.configure(
    global_level="info",
    module_levels={
        LoggerNames.COLLECTORS: "debug",
        LoggerNames.PYGNMI: "warning",
    },
    enable_structured=False,
    enable_file_output=True,
)
```

### Environment-Based Configuration

The system automatically reads configuration from the CLI and applies appropriate settings.

## CLI Usage

### Basic Log Level Control

```bash
# Set global log level
python gbuddy.py --log-level debug --device xrd-1 interfaces

# Available levels: debug, info, warning, error
python gbuddy.py --log-level warning --device xrd-1 routing
```

### Module-Specific Logging

```bash
# Control specific modules
python gbuddy.py --log-level info \
  --module-log-levels "gnmibuddy.collectors=debug,pygnmi=error" \
  --device xrd-1 interfaces

# Multiple modules
python gbuddy.py --log-level info \
  --module-log-levels "gnmibuddy.collectors.interfaces=debug,gnmibuddy.gnmi=warning,pygnmi=error" \
  --device xrd-1 interfaces
```

### Structured Logging

```bash
# Enable JSON structured logging
python gbuddy.py --log-level info --structured-logging \
  --device xrd-1 interfaces

# Output example:
# {"timestamp": "2025-07-14T10:30:00.123", "level": "INFO", "logger": "gnmibuddy.collectors.interfaces", "message": "Getting interface information", "device_name": "xrd-1", "operation": "get_interfaces"}
```

### Runtime Log Level Management

```bash
# Show current log levels
python gbuddy.py --device xrd-1 log-level show

# Set log level for specific module
python gbuddy.py --device xrd-1 log-level set gnmibuddy.gnmi debug

# List available modules
python gbuddy.py --device xrd-1 log-level modules
```

## Module-Specific Logging

### Available Modules

| Module                            | Purpose                     | Recommended Level                              |
| --------------------------------- | --------------------------- | ---------------------------------------------- |
| `gnmibuddy.collectors.interfaces` | Interface data collection   | `debug` for troubleshooting                    |
| `gnmibuddy.collectors.routing`    | Routing protocol data       | `debug` for BGP/ISIS issues                    |
| `gnmibuddy.collectors.mpls`       | MPLS data collection        | `info` normally                                |
| `gnmibuddy.gnmi`                  | gNMI client operations      | `info` normally, `debug` for connection issues |
| `gnmibuddy.inventory`             | Device inventory management | `warning` normally                             |
| `pygnmi`                          | External pygnmi library     | `warning` or `error`                           |
| `grpc`                            | External gRPC library       | `error` only                                   |

### Common Scenarios

#### Debugging Interface Issues

```bash
python gbuddy.py --log-level warning \
  --module-log-levels "gnmibuddy.collectors.interfaces=debug" \
  --device xrd-1 interfaces
```

#### Debugging gNMI Connection Issues

```bash
python gbuddy.py --log-level warning \
  --module-log-levels "gnmibuddy.gnmi=debug,pygnmi=info" \
  --device xrd-1 system
```

#### Quiet Mode (Minimal Logging)

```bash
python gbuddy.py --log-level error \
  --module-log-levels "pygnmi=error,grpc=error" \
  --device xrd-1 interfaces
```

#### Verbose Mode (Full Debugging)

```bash
python gbuddy.py --log-level debug \
  --device xrd-1 interfaces
```

## Structured Logging

When `--structured-logging` is enabled, logs are output in JSON format suitable for log aggregation systems:

```json
{
  "timestamp": "2025-07-14T10:30:00.123456",
  "level": "INFO",
  "logger": "gnmibuddy.collectors.interfaces",
  "message": "Starting get_interfaces",
  "module": "interfaces",
  "function": "get_interfaces",
  "line": 42,
  "device_name": "xrd-1",
  "operation": "get_interfaces"
}
```

### OTel-Compatible Fields

The structured logs include fields that are compatible with OpenTelemetry:

- `timestamp`: ISO 8601 timestamp
- `level`: Log level
- `logger`: Logger name (service/component)
- `message`: Human-readable message
- `trace_id`: Trace ID (when available)
- `span_id`: Span ID (when available)
- `device_name`: Network device context
- `operation`: Operation being performed
- `duration_ms`: Operation duration

## Operation Tracking

The system includes automatic operation tracking using decorators:

```python
from src.logging.config import log_operation

@log_operation("get_device_interfaces")
def get_interfaces(device, interface=None):
    # Function implementation
    pass
```

This automatically logs:

- Operation start with context
- Operation completion with duration
- Operation failure with error details

Example output:

```
2025-07-14 10:30:00 | INFO     | gnmibuddy.collectors.interfaces | Starting get_interfaces | device_name=xrd-1
2025-07-14 10:30:01 | INFO     | gnmibuddy.collectors.interfaces | Completed get_interfaces | device_name=xrd-1 duration_ms=850.23
```

## Dynamic Log Level Management

### CLI Commands

```bash
# Show current module log levels
python gbuddy.py --device xrd-1 log-level show

# Set log level for a specific module
python gbuddy.py --device xrd-1 log-level set gnmibuddy.collectors.routing debug

# List all available modules for logging control
python gbuddy.py --device xrd-1 log-level modules
```

### Programmatic Control

```python
from src.logging.config import LoggingConfig

# Change log level at runtime
LoggingConfig.set_module_level("gnmibuddy.gnmi", "debug")

# Get current levels
current_levels = LoggingConfig.get_module_levels()
print(current_levels)
```

## Integration with Observability Tools

### Preparation for OpenTelemetry

The logging system is designed to integrate easily with OTel:

1. **Logger names** map to OTel service/component names
2. **Structured logs** include OTel-compatible fields
3. **Operation tracking** can be extended to spans
4. **Context propagation** is ready for trace correlation

### Log Aggregation

Structured logs can be sent to various systems:

- **ELK Stack**: Elasticsearch, Logstash, Kibana
- **Grafana Loki**: With Promtail or Grafana Agent
- **Splunk**: Universal forwarder
- **Cloud Services**: AWS CloudWatch, Azure Monitor, GCP Logging

### Example Grafana Loki Configuration

```yaml
# promtail configuration
clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: gnmibuddy
    static_configs:
      - targets:
          - localhost
        labels:
          job: gnmibuddy
          __path__: /path/to/gnmibuddy/logs/*.log
    pipeline_stages:
      - json:
          expressions:
            level: level
            logger: logger
            device_name: device_name
            operation: operation
```

## Best Practices

### 1. Module-Specific Levels

- Use `debug` only for modules you're actively troubleshooting
- Keep external libraries (`pygnmi`, `grpc`) at `warning` or `error`
- Use `info` as the default for application modules

### 2. Structured Logging

- Enable structured logging for production deployments
- Use structured logging when integrating with log aggregation systems
- Keep human-readable logging for development

### 3. Operation Context

- Always include device context in network operations
- Use the `@log_operation` decorator for timing critical operations
- Log operation parameters for debugging

### 4. Log Level Hierarchy

```
DEBUG   - Detailed diagnostic information
INFO    - General operational information
WARNING - Something unexpected happened but we can continue
ERROR   - Serious problem that prevented operation completion
```

### 5. Performance Considerations

- Avoid string formatting in debug logs when debug is disabled
- Use lazy evaluation: `logger.debug("Value: %s", expensive_function())`
- Be mindful of log volume in production

## Troubleshooting

### Common Issues

#### 1. Too Much Log Noise

**Problem**: Logs are too verbose, making it hard to find relevant information.

**Solution**:

```bash
# Reduce external library noise
python gbuddy.py --log-level info \
  --module-log-levels "pygnmi=error,grpc=error" \
  --device xrd-1 interfaces
```

#### 2. Missing Debug Information

**Problem**: Can't see detailed information for troubleshooting.

**Solution**:

```bash
# Enable debug for specific modules only
python gbuddy.py --log-level warning \
  --module-log-levels "gnmibuddy.collectors.interfaces=debug,gnmibuddy.gnmi=debug" \
  --device xrd-1 interfaces
```

#### 3. gNMI Connection Issues

**Problem**: Can't connect to devices, need detailed connection information.

**Solution**:

```bash
# Enable detailed gNMI and pygnmi logging
python gbuddy.py --log-level warning \
  --module-log-levels "gnmibuddy.gnmi=debug,pygnmi=info" \
  --device xrd-1 system
```

#### 4. Performance Debugging

**Problem**: Operations are slow, need timing information.

**Solution**:

```bash
# Enable structured logging to see operation timings
python gbuddy.py --log-level info --structured-logging \
  --device xrd-1 interfaces
```

### Debugging Specific Scenarios

#### BGP Issues

```bash
python gbuddy.py --log-level warning \
  --module-log-levels "gnmibuddy.collectors.routing=debug" \
  --device xrd-1 routing --protocol bgp
```

#### Interface State Issues

```bash
python gbuddy.py --log-level warning \
  --module-log-levels "gnmibuddy.collectors.interfaces=debug" \
  --device xrd-1 interfaces --interface GigabitEthernet0/0/0/0
```

#### Inventory Problems

```bash
python gbuddy.py --log-level warning \
  --module-log-levels "gnmibuddy.inventory=debug" \
  --device xrd-1 system
```

### Log File Locations

- **Default log file**: `logs/gnmibuddy.log`
- **Log rotation**: Implement using external tools (logrotate, etc.)
- **Structured logs**: Same file, JSON format when enabled

## Migration from Old Logging

### For Developers

Old pattern:

```python
import logging
logger = logging.getLogger(__name__)
```

New pattern:

```python
from src.logging.config import get_logger
logger = get_logger(__name__)
```

### Configuration Changes

Old way (manual configuration):

```python
logging.basicConfig(level=logging.INFO)
```

New way (centralized configuration):

```python
from src.logging.config import LoggingConfig
LoggingConfig.configure(global_level="info")
```

The enhanced logging system is backward compatible, so existing code will continue to work while you migrate to the new patterns.
