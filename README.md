# 🧪 gNMIBuddy

A Python-based tool designed primarily for LLMs (Large Language Models) to retrieve network information from network devices using gNMI (gRPC Network Management Interface) and OpenConfig models. While optimized for AI integration, it also provides a full CLI interface for direct human operation.

## 📋 Overview

This tool implements Model Context Protocol ([MCP](https://modelcontextprotocol.io/introduction)) for seamless LLM connectivity while allowing network engineers to:

- 🔄 Retrieve routing information (`BGP`, `ISIS`, etc.)
- 🔌 Get interface details and status
- 🏷️ Collect MPLS and segment routing information
- 🔒 Access VPN/VRF configuration
- 📜 View device logs with filtering capabilities
- 📊 List all available devices in the inventory

The tool provides a structured JSON output that can be easily parsed by other tools or scripts.

## 🛠️ Installation

### Prerequisites

- 🐍 Python 3.13+
- 🖥️ Network devices with gNMI enabled
- 📊 Network devices **must** support `openconfig-network-instance:network-instances` YANG model
  - Only the `get_logs` function uses XR-specific 'show' command.

### Installing uv

This project requires `uv` primarily for MCP integration with LLMs. If you're only using the CLI interface without MCP, traditional pip installation is sufficient. To install `uv` check out [uv's official documentation](https://docs.astral.sh/uv/#installation).

For macOS, uv worked by using Homebrew: `brew install uv`.

### Setup

1. Install required dependencies:

   With uv (recommended):

   ```bash
   # this creates a virtual environment, installs the dependencies, and runs the cli_app.py
   # once the virtual environment is activated, you can run the cli_app.py without uv
   uv run cli_app.py
   ```

   Or with traditional pip (sufficient for CLI usage only):

   ```bash
   pip install -r requirements.txt
   python cli_app.py
   ```

2. Provide a JSON inventory file (see `host.json` or `sandbox.json` for examples)

### VSCode MCP Server Setup

To enable MCP integration with VSCode:

1. Create a `.vscode` directory in your project root
2. Add an `mcp.json` file with the following content:

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

Note: You can also configure this in VSCode user settings, but you'll need to use absolute paths as variable substitution won't work in that context.

### Claude MCP Setup

To enable MCP integration with Claude:

1. Open Claude settings by clicking the gear icon > Developer > Edit config
2. Add the following configuration (update paths to your actual locations):

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
           "NETWORK_INVENTORY": "/absolute/path/to/<your_inventory_file>.json"
         }
       }
     }
   }
   ```

## 💻 CLI Usage

The tool provides a user-friendly command-line interface:

```bash
# Using uv (required for MCP integration, optional for CLI usage)
uv run cli_app.py [GLOBAL OPTIONS] COMMAND [COMMAND OPTIONS]

# Using traditional Python
python cli_app.py [GLOBAL OPTIONS] COMMAND [COMMAND OPTIONS]
```

### Global Options

- `--device DEVICE_NAME`: Specify a single target device from the inventory
- `--all-devices`: Run the command on all devices in the inventory concurrently
  - `--max-workers N`: Maximum number of concurrent workers (default: 5)
- `--inventory PATH`: Path to a custom inventory JSON file
  - Or set environment variable: `export NETWORK_INVENTORY=path/to/your/inventory.json`
  - For testing, you can use the provided `sandbox.json`
- `--log-level {debug,info,warning,error}`: Set the logging level (default: info)

Note: You must use either `--device` OR `--all-devices`, not both.

### Available Commands

- 🔄 `routing`: Get routing information
- 🔌 `interface`: Get interface information
- 🏷️ `mpls`: Get MPLS and segment routing information
- 🔒 `vpn`: Get VPN/VRF configuration information
- 📜 `logging`: Get logs from the device
- 📋 `list-devices`: Show all available devices in the inventory
- ℹ️ `list-commands`: Display all available CLI commands and options

### Command Options

#### 🔄 routing

```bash
uv run cli_app.py --device DEVICE_NAME routing [OPTIONS]
```

- `--protocol PROTOCOL`: Filter by routing protocol (`bgp`, `isis`)
- `--detail`: Show detailed information

#### 🔌 interface

```bash
uv run cli_app.py --device DEVICE_NAME interface [OPTIONS]
```

- `--name INTERFACE_NAME`: Specific interface name (e.g., `GigabitEthernet0/0/0/0`)

#### 🏷️ mpls

```bash
uv run cli_app.py --device DEVICE_NAME mpls [OPTIONS]
```

- `--detail`: Show detailed information

#### 🔒 vpn

```bash
uv run cli_app.py --device DEVICE_NAME vpn [OPTIONS]
```

- `--vrf VRF_NAME`: Specific VRF name
- `--detail`: Show detailed information

#### 📜 logging

```bash
uv run cli_app.py --device DEVICE_NAME logging [OPTIONS]
```

- `--keywords KEYWORDS`: Filter logs by specific keywords

#### ℹ️ list-commands

```bash
uv run cli_app.py list-commands [OPTIONS]
```

- `--detailed`: Show detailed command information

### 📝 Examples

```bash
# Get routing information with BGP protocol details
uv run cli_app.py --device xrd-1 routing --protocol bgp --detail

# Get information for a specific interface
uv run cli_app.py --device xrd-2 interface --name GigabitEthernet0/0/0/0

# Get MPLS information with details
uv run cli_app.py --device xrd-1 mpls --detail

# Get VRF information for a specific VRF
uv run cli_app.py --device xrd-3 vpn --vrf default

# Get logs filtered by keyword
uv run cli_app.py --device xrd-2 logging --keywords "error"

# Run the same command on all devices
uv run cli_app.py --all-devices interface --name GigabitEthernet0/0/0/0

# List all available devices in inventory
uv run cli_app.py list-devices

# Get detailed help on available commands
uv run cli_app.py list-commands --detailed
```

## 🚧 Development Notes

- Add a capabitlity check to review if the mininum openconfig models are supported by the device.
  - Handle errors.
- Create an interface and encapsulation for what the parsers recieve and output
- Create a gnmi not found object. errors for not found feature confuses llms.
