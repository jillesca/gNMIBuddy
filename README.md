# 🧪 gNMIBuddy

An opinionated tool that retrieves essential network information from devices using gNMI and OpenConfig models. Designed primarily for LLMs with [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction) integration, it also provides a full CLI for direct use.

> **Opinionated by design:** gNMI and YANG expose overwhelming amounts of data with countless parameters. This tool provides what I consider the most relevant information for LLMs.

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

### Installation

Install `uv` package manager ([docs](https://docs.astral.sh/uv/#installation)):

```bash
# macOS
brew install uv
```

Run the application:

```bash
# Creates virtual environment, installs dependencies, and shows help
uv run gnmibuddy.py --help
```

### Basic Usage

```bash
# List available devices
uv run gnmibuddy.py device list

# Get system information from a device
uv run gnmibuddy.py device info --device xrd-1

# Get routing info from a device
uv run gnmibuddy.py network routing --device xrd-1 --protocol bgp

# Check all interfaces across all devices
uv run gnmibuddy.py --all-devices network interface
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
        "mcp[cli],pygnmi,networkx",
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
        "mcp[cli],pygnmi,networkx",
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
uv run --with "mcp[cli],pygnmi,networkx" \
mcp run mcp_server.py
```

> **Note:** Set the `NETWORK_INVENTORY` environment variable to your inventory file or you'll get errors.

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

## CLI Reference

### Command Structure

The CLI uses a hierarchical command structure organized into logical groups:

```bash
uv run gnmibuddy [GLOBAL_OPTIONS] <group> <command> [COMMAND_OPTIONS]
```

**Command Groups:**

- **`device`**: Device management and information
- **`network`**: Network protocol analysis
- **`topology`**: Network topology discovery
- **`ops`**: Operational tasks and testing
- **`manage`**: CLI and system management

### Global Options

- `--inventory PATH`: Custom inventory file (or set `NETWORK_INVENTORY` env var)

For complete options and detailed command information, use:

```bash
uv run gnmibuddy.py --help
uv run gnmibuddy.py <group> --help
uv run gnmibuddy.py <group> <command> --help
```

### Examples

```bash
# Device information commands
uv run gnmibuddy.py device info --device xrd-1
uv run gnmibuddy.py device profile --device xrd-2
uv run gnmibuddy.py device list

# Network protocol commands
uv run gnmibuddy.py network routing --device xrd-1 --protocol bgp --detail
uv run gnmibuddy.py network interface --device xrd-2 --name GigabitEthernet0/0/0/0
uv run gnmibuddy.py network mpls --device xrd-1 --detail
uv run gnmibuddy.py network vpn --device xrd-3 --vrf customer-a

# Topology commands
uv run gnmibuddy.py topology neighbors --device xrd-1
uv run gnmibuddy.py topology adjacency --device xrd-2

# Operational commands
uv run gnmibuddy.py ops logs --device xrd-2 --keywords "bgp|error"

# Run on all devices
uv run gnmibuddy.py --all-devices network interface
```

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

## 🚧 Development Notes

**Planned Improvements:**

- [ ] Capability check for minimum OpenConfig model support.
- [ ] Standardized processor interfaces and output formats.
- [ ] Device compatibility validation.
