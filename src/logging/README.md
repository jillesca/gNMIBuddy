# gNMIBuddy Logging System

A modern, modular logging system built following the Zen of Python principles and Martin Fowler's refactoring best practices.

## 🎯 Overview

This refactored logging system provides:

- **Type-safe configuration** using data classes and enums
- **Modular architecture** with single-responsibility components
- **OpenTelemetry compatibility** for observability
- **External library suppression** with configurable strategies
- **MCP server integration** with context-aware logging
- **Operation tracking** with automatic timing and context
- **Dynamic level management** at runtime

## 🏗️ Architecture

```
src/logging/
├── core/              # Fundamental types and data structures
│   ├── enums.py       # LogLevel, SuppressionMode enums
│   ├── models.py      # Configuration data classes
│   ├── logger_names.py # Centralized logger naming
│   └── formatter.py   # OTel-compatible formatters
├── config/            # Configuration components
│   ├── environment.py # Environment variable reading
│   ├── configurator.py # Main logging configuration
│   └── file_utils.py  # Log file path management
├── suppression/       # External library noise reduction
│   ├── external.py    # Core suppression functionality
│   └── strategies.py  # CLI/MCP/Development strategies
├── mcp/               # MCP server integration
│   ├── config.py      # MCP-specific configuration
│   └── context_logger.py # FastMCP context integration
├── decorators/        # Operation tracking
│   └── operation.py   # @log_operation decorator
├── utils/             # Utilities and helpers
│   ├── dynamic.py     # Runtime logger management
│   └── convenience.py # Main API functions
├── examples/          # Usage demonstrations
│   └── demo.py        # Comprehensive examples
└── docs/              # Documentation
    └── README.md      # Architecture overview
```

## 🚀 Quick Start

### Basic Configuration

```python
from src.logging import configure_logging, get_logger

# Configure logging
logger = configure_logging(log_level="info")

# Get a module logger
module_logger = get_logger(__name__)
module_logger.info("Hello from the new logging system!")
```

### Advanced Configuration

```python
from src.logging import LoggingConfigurator, LogLevel

# Advanced configuration with type safety
LoggingConfigurator.configure(
    global_level="info",
    module_levels={
        "gnmibuddy.collectors": "debug",
        "pygnmi": "error"
    },
    enable_structured=True,
    external_suppression_mode="mcp"
)
```

### Module-Specific Levels

```python
from src.logging import set_module_level, get_module_levels

# Runtime level changes
set_module_level("gnmibuddy.collectors.interfaces", "debug")

# Check current levels
current_levels = get_module_levels()
print(current_levels)
```

## 📊 Core Components

### Enums for Type Safety

```python
from src.logging.core import LogLevel, SuppressionMode

# Type-safe log levels
level = LogLevel.DEBUG
mode = SuppressionMode.MCP
```

### Data Classes Replace Dictionaries

```python
from src.logging.core import LoggingConfiguration, ModuleLevelConfiguration

# Structured configuration with validation
config = LoggingConfiguration(
    global_level=LogLevel.INFO,
    module_levels=ModuleLevelConfiguration.from_string_dict({
        "gnmibuddy.collectors": "debug"
    }),
    enable_structured=True
)
```

### Strategy Pattern for Suppression

```python
from src.logging.suppression import setup_mcp_suppression

# Context-appropriate suppression
setup_mcp_suppression()       # For MCP servers
setup_cli_suppression()       # For CLI tools
setup_development_suppression()  # For debugging
```

## 🎨 Logger Naming Convention

All loggers follow a hierarchical naming structure:

```
gnmibuddy                      # Root application
├── gnmibuddy.collectors       # Data collection
│   ├── gnmibuddy.collectors.interfaces
│   ├── gnmibuddy.collectors.routing
│   └── gnmibuddy.collectors.vpn
├── gnmibuddy.gnmi            # gNMI operations
├── gnmibuddy.mcp             # MCP server
└── gnmibuddy.utils           # Utilities
```

Use `LoggerNames` constants to avoid typos:

```python
from src.logging import LoggerNames

# Type-safe logger names
collectors_level = LoggerNames.COLLECTORS
interfaces_level = LoggerNames.INTERFACES
```

## 🔧 Operation Tracking

Automatic operation logging with timing and context:

```python
from src.logging import log_operation, get_logger

logger = get_logger(__name__)

@log_operation("get_device_interfaces")
def get_interfaces(device, interface=None):
    logger.info(f"Processing {device}")
    # Function implementation...
    return result
```

Output:

```
2025-01-15 10:30:00 | DEBUG | gnmibuddy.collectors | Starting get_device_interfaces | device=xrd-1
2025-01-15 10:30:01 | DEBUG | gnmibuddy.collectors | Completed get_device_interfaces | device=xrd-1 duration_ms=850.23
```

## 🌐 External Library Suppression

Three strategies for different contexts:

### CLI Strategy (Moderate)

```python
from src.logging.suppression import setup_cli_suppression
setup_cli_suppression()
# pygnmi: WARNING, grpc: WARNING
```

### MCP Strategy (Aggressive)

```python
from src.logging.suppression import setup_mcp_suppression
setup_mcp_suppression()
# pygnmi: ERROR, grpc: ERROR, logs to stderr
```

### Development Strategy (Minimal)

```python
from src.logging.suppression import setup_development_suppression
setup_development_suppression()
# pygnmi: INFO, grpc: WARNING (for debugging)
```

## 🖥️ MCP Server Integration

### Basic MCP Setup

```python
from src.logging.mcp import setup_mcp_logging

setup_mcp_logging(
    log_level="info",
    tool_debug_mode=False
)
```

### Context-Aware Logging

```python
from src.logging.mcp import get_mcp_logger

# In MCP tool functions
async def get_device_info(device_name: str, context: Context):
    logger = get_mcp_logger(__name__, context)

    await logger.info(f"Getting info for {device_name}")
    # Implementation...
```

### Environment Variables

```bash
# MCP-specific configuration
export GNMIBUDDY_MCP_TOOL_DEBUG=true
export GNMIBUDDY_EXTERNAL_SUPPRESSION_MODE=mcp
export GNMIBUDDY_LOG_LEVEL=info
```

## 📁 File Management

Sequential log files with smart numbering:

```bash
logs/
├── gnmibuddy_001.log  # First execution
├── gnmibuddy_002.log  # Second execution
└── gnmibuddy_003.log  # Latest execution
```

```python
from src.logging.config import LogFilePathGenerator

# Custom log file management
log_path = LogFilePathGenerator.get_next_log_file_path()
latest = LogFilePathGenerator.get_latest_log_file()
```

## 🔍 Structured Logging

OpenTelemetry-compatible JSON output:

```python
# Enable structured logging
configure_logging(log_level="info", structured=True)

# Results in JSON output:
{
  "timestamp": "2025-01-15T10:30:00.123456",
  "level": "INFO",
  "logger": "gnmibuddy.collectors.interfaces",
  "message": "Getting interface data",
  "device_name": "xrd-1",
  "operation": "get_interfaces",
  "duration_ms": 150.5
}
```

## 📈 Environment Configuration

All configuration can be controlled via environment variables:

```bash
# Global settings
export GNMIBUDDY_LOG_LEVEL=debug
export GNMIBUDDY_STRUCTURED_LOGGING=true

# Module-specific levels
export GNMIBUDDY_MODULE_LEVELS="gnmibuddy.collectors=debug,pygnmi=error"

# Suppression mode
export GNMIBUDDY_EXTERNAL_SUPPRESSION_MODE=mcp

# Custom log file
export GNMIBUDDY_LOG_FILE=/var/log/gnmibuddy.log
```

## 🧪 Examples

Run the comprehensive demo:

```bash
cd /Users/jillesca/DevNet/cisco_live/25clus/gNMIBuddy
python src/logging/examples/demo.py
```

The demo shows:

- Basic and advanced configuration
- Module-specific levels
- Structured logging
- Operation tracking
- Dynamic level changes
- Suppression strategies
- MCP integration examples

## 🎯 Key Benefits

### For Developers

- **Type safety**: Enums and data classes prevent configuration errors
- **Modular design**: Easy to understand and modify individual components
- **Clear interfaces**: Well-defined boundaries between modules
- **Comprehensive examples**: Learn by working examples

### For Operations

- **Runtime flexibility**: Change log levels without restarts
- **Context awareness**: Automatic device and operation tracking
- **Observability ready**: OTel-compatible structured logging
- **Noise reduction**: Configurable external library suppression

### For Maintenance

- **Single responsibility**: Each module has one clear purpose
- **Easy testing**: Isolated components with focused functionality
- **Clear documentation**: Every component thoroughly documented
- **Backward compatibility**: Smooth migration path

## 🔄 Migration from Old System

The refactored system maintains compatibility:

```python
# Old imports still work
from src.logging import configure_logging, get_logger, log_operation

# But new imports are cleaner
from src.logging import LoggingConfigurator, LogLevel, SuppressionMode
```

## 📚 Further Reading

- See `examples/demo.py` for comprehensive usage examples
- Check `docs/README.md` for detailed architecture information
- Review individual module docstrings for implementation details

---

_Built following the Zen of Python: "Beautiful is better than ugly. Explicit is better than implicit. Simple is better than complex."_
