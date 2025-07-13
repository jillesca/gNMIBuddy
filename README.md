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

- Python 3.13+
- Network devices with gNMI _enabled_ and `openconfig-network-instance` support
- Device inventory file (JSON format)

**Tested on:**

- **Platform:** cisco XRd Control Plane (`24.4.1.26I`)
- **OpenConfig:** `openconfig-network-instance` (`1.3.0`)

### Installation

Install `uv` package manager ([docs](https://docs.astral.sh/uv/#installation)):

```bash
# macOS
brew install uv
```

Run the application:

```bash
# Creates virtual environment, installs dependencies, and shows help
uv run cli_app.py --help
```

### Basic Usage

```bash
# List available devices
uv run cli_app.py list-devices

# Get routing info from a device
uv run cli_app.py --device xrd-1 routing --protocol bgp

# Check all interfaces across all devices
uv run cli_app.py --all-devices interface
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

Use the MCP inspector for testing:

```bash
npx @modelcontextprotocol/inspector \
uv run --with "mcp[cli],pygnmi,networkx" \
mcp run mcp_server.py
```

> **Note:** Set the `NETWORK_INVENTORY` environment variable or you'll get errors.

## 🧪 Testing with DevNet Sandbox

Don't have network devices? Use the [DevNet XRd Sandbox](https://devnetsandbox.cisco.com/DevNet/) with the included Ansible playbook:

```bash
# Enable gRPC on the DevNet XRd Sandbox
ANSIBLE_HOST_KEY_CHECKING=False \
uv run --with "paramiko,ansible" \
ansible-playbook ansible-helper/xrd_apply_config.yaml -i ansible-helper/hosts
```

Then test with the provided `xrd_sandbox.json` inventory file.

### Testing with AI Agents

Want to see how this MCP tool integrates with actual AI agents? Check out [sp_oncall](https://github.com/jillesca/sp_oncall) - a graph of agents that use gNMIBuddy to demonstrate real-world network operations scenarios.

## 💻 CLI Reference

### Global Options

Choose **one** target option:

- `--device DEVICE_NAME`: Single device from inventory
- `--inventory PATH`: Custom inventory file (or set `NETWORK_INVENTORY` env var)

Use the `--help` flag for detailed command options.

### Examples

```bash
# Routing with BGP details
uv run cli_app.py --device xrd-1 routing --protocol bgp --detail

# Specific interface
uv run cli_app.py --device xrd-2 interface --name GigabitEthernet0/0/0/0

# MPLS details
uv run cli_app.py --device xrd-1 mpls --detail

# VRF information
uv run cli_app.py --device xrd-3 vpn --vrf customer-a

# Filtered logs
uv run cli_app.py --device xrd-2 logging --keywords "bgp|error"

# Run on all devices
uv run cli_app.py --all-devices interface
```

## 🏗️ Architecture

### Schema Organization

gNMIBuddy uses a centralized schema approach for data contracts:

- **`src/schemas/`**: Contains all shared data models and response contracts
  - `models.py`: Device and inventory data models
  - `responses.py`: Network operation response schemas
  - `__init__.py`: Unified imports for all schemas

These schemas serve as contracts between different parts of the system, ensuring consistency across:

- CLI and API interfaces
- Network operation responses
- Error handling and status reporting
- MCP tool integration

## 🚧 Development Notes

**Planned Improvements:**

- [ ] Capability check for minimum OpenConfig model support
- [ ] Standardized parser interfaces and output formats
- [ ] Device compatibility validation
