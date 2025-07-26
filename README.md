# 🧪 gNMIBuddy

An _over-engineered_ and _opinionated_ tool that retrieves essential network information from devices using gNMI and OpenConfig models. Designed primarily for LLMs with [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction) integration, it also provides a full CLI for direct use.

> **Opinionated by design, over-engineered by passion.** gNMI and YANG expose overwhelming amounts of data with countless parameters. This tool provides what I consider the most relevant information for LLMs. And who doesn't enjoy building complicated solutions.

## 🎯 What It Does

Retrieve structured network data in JSON format:

- 🔄 **Routing**: BGP, ISIS protocols and neighbor states
- 🔌 **Interfaces**: Status, configuration, and statistics
- 🏷️ **MPLS**: Labels, forwarding tables, and segment routing
- 🔒 **VPN/VRF**: L3VPN configuration and route targets
- 📝 **Logs**: Filtered device logs with keyword search
- 🏠 **Topology**: Device profiles and network adjacencies

See the [API definition](/api.py) for all available APIs and options.

## ⚡ Quick Start

### Prerequisites

- Python `3.13+`
- Network devices with gNMI _enabled_.
- Device inventory file (JSON format).

### Device Compatibility Requirements

> [!IMPORTANT]
> gNMIBuddy requires devices to support specific OpenConfig models depending on the functionality used.

- **OpenConfig Models dependencies**

  - `openconfig-system` (`0.17.1`)
  - `openconfig-interfaces` (`4.0.0`)
  - `openconfig-network-instance` (`1.3.0`)

- **Tested on:**
  - **Platform:** cisco XRd Control Plane (`24.4.1.26I`)

> [!NOTE]
> The function to get logs from devices, only works on XR systems.

### Installation

Install `uv` package manager ([docs](https://docs.astral.sh/uv/#installation)):

```bash
# macOS
brew install uv
```

After cloning the project, sync dependencies:

```bash
uv sync --frozen --no-dev
```

This is needed only the first time you install the project.

## CLI Reference

```bash
❯ uv run gnmibuddy.py --help

  ▗▄▄▖▗▖  ▗▖▗▖  ▗▖▗▄▄▄▖▗▄▄▖ ▗▖ ▗▖▗▄▄▄ ▗▄▄▄▗▖  ▗▖
 ▐▌   ▐▛▚▖▐▌▐▛▚▞▜▌  █  ▐▌ ▐▌▐▌ ▐▌▐▌  █▐▌  █▝▚▞▘
 ▐▌▝▜▌▐▌ ▝▜▌▐▌  ▐▌  █  ▐▛▀▚▖▐▌ ▐▌▐▌  █▐▌  █ ▐▌
 ▝▚▄▞▘▐▌  ▐▌▐▌  ▐▌▗▄█▄▖▐▙▄▞▘▝▚▄▞▘▐▙▄▄▀▐▙▄▄▀ ▐▌

An opinionated tool that retrieves essential network information from devices using gNMI and OpenConfig models.
Designed primarily for LLMs with Model Context Protocol (MCP) integration, it also provides a full CLI.
Help: https://github.com/jillesca/gNMIBuddy

Python Version: 3.13.4
gNMIBuddy Version: 0.1.0
Usage:
  gnmibuddy.py [OPTIONS] COMMAND [ARGS]...

📋 Inventory Requirement:
  Provide device inventory via --inventory PATH or set NETWORK_INVENTORY env var

Options:
  -h, --help            Show this message and exit
  -V, --version         Show version information
  --log-level LEVEL     Set logging level (debug, info, warning, error)
  --module-log-help     Show detailed module logging help
  --all-devices         Run on all devices concurrently
  --inventory PATH      Path to inventory JSON file
  --max-workers NUMBER  Maximum number of concurrent workers for batch operations (--all-devices, --devices, --device-file)

Commands:
  device (d)    Device Information
    info         Get system information from a network device
    list         List all available devices in the inventory
    profile      Get device profile and role information

  network (n)   Network Protocols
    interface    Get interface status and configuration
    mpls         Get MPLS forwarding and label information
    routing      Get routing protocol information (BGP, ISIS, OSPF)
    vpn          Get VPN/VRF configuration and status

  topology (t)  Network Topology
    neighbors    Get direct neighbor information via LLDP/CDP
    network      Get complete network topology information. Queries all devices in inventory.

  ops (o)       Operations
    logs         Retrieve and filter device logs
    validate     Validate all collector functions (development tool)

Examples:
  gnmibuddy.py device info --device R1
  gnmibuddy.py network routing --device R1
  gnmibuddy.py --all-devices device list

Run 'gnmibuddy.py COMMAND --help' for more information on a command.
```

## 🤖 LLM Integration (MCP)

### VSCode Setup

Create `.vscode/mcp.json` in your project:

```json
{
  "servers": {
    "gNMIBuddy": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "mcp[cli],pygnmi,networkx,pyyaml",
        "mcp",
        "run",
        "${workspaceFolder}/mcp_server.py"
      ],
      "env": {
        "NETWORK_INVENTORY": "${workspaceFolder}/<your_inventory_file>.json"
      }
    }
  }
}
```

### Claude Desktop Setup

Add to Claude's configuration (Settings > Developer > Edit config):

```json
{
  "mcpServers": {
    "gNMIBuddy": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "mcp[cli],pygnmi,networkx,pyyaml",
        "mcp",
        "run",
        "/absolute/path/to/mcp_server.py"
      ],
      "env": {
        "NETWORK_INVENTORY": "/absolute/path/to/your_inventory.json"
      }
    }
  }
}
```

### Testing MCP

Use the MCP inspector for testing.

```bash
# Replace `xrd_sandbox.json` with your actual inventory file.
NETWORK_INVENTORY=xrd_sandbox.json \
npx @modelcontextprotocol/inspector \
uv run --with "mcp[cli],pygnmi,networkx,pyyaml" \
mcp run mcp_server.py
```

> [!IMPORTANT]
> For MCP set the `NETWORK_INVENTORY` environment variable to your inventory file or you'll get errors.

## 🧪 Testing with DevNet Sandbox

Don't have network devices? Use the [DevNet XRd Sandbox](https://devnetsandbox.cisco.com/DevNet/), follow the instructions to bring up a MPLS network with docker, then configure gNMI with the included Ansible playbook:

```bash
# Enable gRPC on the DevNet XRd Sandbox
ANSIBLE_HOST_KEY_CHECKING=False \
uv run --with "paramiko,ansible" \
ansible-playbook ansible-helper/xrd_apply_config.yaml -i ansible-helper/hosts
```

Then test with the provided `xrd_sandbox.json` inventory file.

### Testing with AI Agents

Want to see how this MCP tool integrates with actual AI agents? Check out [sp_oncall](https://github.com/jillesca/sp_oncall) - a graph of agents that use gNMIBuddy to demonstrate real-world network operations scenarios.
.

## 📋 Response Format

gNMIBuddy provides structured, consistent responses for all network operations. The response format depends on whether you're targeting a single device or multiple devices.

### Single Device Operations

Single device operations return a `NetworkOperationResult` object with detailed information about the operation, including status, data, metadata, and error handling.

```python
@dataclass
class NetworkOperationResult:
    device_name: str
    ip_address: str
    nos: str
    operation_type: str
    status: OperationStatus
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_response: Optional[ErrorResponse] = None
    feature_not_found_response: Optional[FeatureNotFoundResponse] = None
```

### Batch Operations

Batch operations (using `--all-devices`, `--devices`, or `--device-file`) return a `BatchOperationResult` object containing:

- **`results`**: A list of `NetworkOperationResult` objects, one for each device
- **`summary`**: Aggregate statistics about the batch operation
- **`metadata`**: Additional batch operation metadata

```python
@dataclass
class BatchOperationResult:
    results: List[NetworkOperationResult]  # One result per device
    summary: BatchOperationSummary
    metadata: Dict[str, Any] = field(default_factory=dict)
```

For more details, see the [response schema definition](src/schemas/responses.py).

## 🏗️ Architecture

### Schema Organization

gNMIBuddy uses a centralized schema approach for data contracts:

- **`src/schemas/`**: Contains all shared data models and response contracts.
- **`src/collectors/`**: Network telemetry data collectors following OpenTelemetry patterns.
- **`src/processors/`**: Data transformation processors following OpenTelemetry patterns.

These schemas serve as contracts between different parts of the system, ensuring consistency across:

- CLI and API interfaces.
- Network operation responses.
- Error handling and status reporting.
- MCP tool integration.

### Data Processing Pipeline

The application follows an OpenTelemetry-inspired architecture:

```text
Raw gNMI Data → Collector → Processor → Schema → Response
```

1. **Collectors** gather data from network devices via gNMI.
2. **Processors** transform raw data into structured, LLM-friendly formats.
3. **Schemas** ensure consistent data contracts across the system.
4. **Responses** provide standardized output for CLI, API, and MCP interfaces.

## ⚙️ Environment Variables

gNMIBuddy supports environment variables for configuration, which work for both CLI and MCP server usage.

### Global Configuration

| Variable                              | Description                                 | Values                              | Default                  |
| ------------------------------------- | ------------------------------------------- | ----------------------------------- | ------------------------ |
| `NETWORK_INVENTORY`                   | Device inventory file path                  | File path                           | -                        |
| `GNMIBUDDY_LOG_LEVEL`                 | Global log level                            | `debug`, `info`, `warning`, `error` | `info`                   |
| `GNMIBUDDY_MODULE_LEVELS`             | Module-specific log levels                  | `module1=debug,module2=warning`     | -                        |
| `GNMIBUDDY_LOG_FILE`                  | Custom log file path (overrides sequential) | File path                           | `logs/gnmibuddy_XXX.log` |
| `GNMIBUDDY_STRUCTURED_LOGGING`        | Enable JSON logging                         | `true`, `false`                     | `false`                  |
| `GNMIBUDDY_EXTERNAL_SUPPRESSION_MODE` | External library suppression                | `cli`, `mcp`, `development`         | `cli`                    |

**Sequential Log Files**: gNMIBuddy automatically creates numbered log files (`gnmibuddy_001.log`, `gnmibuddy_002.log`, etc.) for each execution in the `logs/` directory. The highest number is always the most recent run.

> [!NOTE]
> Environment variables serve as defaults and can be overridden by CLI arguments like `--log-level` and `--module-log-levels`.

For complete logging environment variable documentation, see [Logging README](src/logging/README.md)

## ⚙️ Batch Operations & Concurrency

gNMIBuddy supports running commands across multiple devices simultaneously with configurable concurrency controls to optimize performance while avoiding rate limiting.

### Batch Operation Options

**Device Selection:**

- `--device DEVICE`: Single device operation
- `--devices device1,device2,device3`: Comma-separated device list
- `--device-file path/to/devices.txt`: Device list from file (one per line)
- `--all-devices`: Run on all devices in inventory

**Concurrency Controls:**

- `--max-workers N`: Maximum concurrent devices to process (default: 5)
- `--per-device-workers N`: Maximum concurrent operations per device (default: varies by command)

### Understanding Concurrency Levels

gNMIBuddy operates with **two levels of concurrency**:

1. **Device-level concurrency** (`--max-workers`): How many devices to process simultaneously
2. **Per-device concurrency** (command-specific): How many operations to run simultaneously on each device

**Total concurrent requests = max_workers × per_device_operations**

### Examples

```bash
# Process 3 devices, 2 operations per device = 6 total requests
uv run gnmibuddy.py --max-workers 3 ops validate --devices xrd-1,xrd-2,xrd-3 --per-device-workers 2
```
