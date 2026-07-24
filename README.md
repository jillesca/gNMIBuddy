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
- 🏠 **Topology**: Device neighbors and network-wide topology analysis

See the [API definition](/api.py) for all available APIs and options.

## ⚡ Prerequisites

- Python `3.13+`
- `uv`, see the [docs](https://docs.astral.sh/uv/#installation) to install it.
  - `brew` is recommended for macOS users
- Network devices with gNMI _enabled_.

**Windows users**: The repo require a Unix-like environment. Use [WSL](https://docs.microsoft.com/en-us/windows/wsl/install).

### Device Compatibility

**Tested on:**

- Cisco XRd Control Plane (`24.4.1.26I`, `25.3.1`)

> [!NOTE]
> The `get_logs()` function only works on IOS-XR.

Devices **must** support gNMI and OpenConfig models listed below:

**OpenConfig Models dependencies**

- `openconfig-system >= 0.17.1`
- `openconfig-interfaces >= 3.0.0`
- `openconfig-network-instance >= 1.3.0`

> [!NOTE]
> If the required model for a function is not found, gNMIBuddy will return an error. If the model version is older than required, it will continue execution but warn the user about potential errors.

You can use the capabilities command to verify the supported models on a specific device. If you have many devices you can use the `--device` option.

```bash
uvx --from git+https://github.com/jillesca/gNMIBuddy.git \
gnmibuddy device capabilities --all-devices
```

### Device Inventory file

gNMIBuddy identifies devices by hostname and looks up their corresponding IP addresses and credentials from the inventory file.

> [!CAUTION]
> Without a device inventory file, gNMIBuddy cannot operate.

Provide device inventory via `--inventory PATH` or set `NETWORK_INVENTORY` env var.

> [!TIP]
> Store environment variables in a `.env` file.

The inventory must be a **JSON list** of `Device` objects with these required fields:

- `name`: Device hostname
- `ip_address`: IP for gNMI connections
- `nos`: Network OS identifier
  - `iosxr` only for now, use it even if you have other NOS. More will be added later.

Authentication (choose one method):

- Username/Password: Requires both `username` and `password` fields
- Certificate-based: Requires both `path_cert` and `path_key` fields

**Schema:** [`src/schemas/models.py`](src/schemas/models.py#L48) | **Example:** [`xrd_sandbox.json`](xrd_sandbox.json)

```json
[
  {
    "name": "xrd-1",
    "ip_address": "10.10.20.101",
    "nos": "iosxr",
    "username": "cisco",
    "password": "C1sco12345"
  },
  {
    "name": "xrd-2",
    "ip_address": "10.10.20.102",
    "nos": "iosxr",
    "path_cert": "/opt/certs/device.pem",
    "path_key": "/opt/certs/device.key"
  }
]
```

> [!TIP]
> Validate your inventory: Use `gnmibuddy inventory validate` to check your inventory file for proper format, valid IP addresses, required fields, and authentication configuration before running network commands.

## 🚀 Quick Start

### 🎯 Instant Testing with MCP Inspector

**Fastest way to try gNMIBuddy**:

```bash
# Replace `xrd_sandbox.json` with your actual inventory file
echo '#!/usr/bin/env bash' > /tmp/gnmibuddy-mcp-wrapper \
&& echo 'exec uvx --from git+https://github.com/jillesca/gNMIBuddy.git gnmibuddy-mcp "$@"' >> /tmp/gnmibuddy-mcp-wrapper \
&& chmod +x /tmp/gnmibuddy-mcp-wrapper \
&& NETWORK_INVENTORY=xrd_sandbox.json npx @modelcontextprotocol/inspector /tmp/gnmibuddy-mcp-wrapper
```

> [!TIP]
> No repo cloning, no MCP client setup required! If you don't have XRd, see [Testing with DevNet Sandbox](#testing-with-devnet-sandbox).

<details>
<summary><strong>🔌 Have an MCP Client? (VSCode, Cursor, Claude Desktop)</strong></summary>

**Recommended: No installation required** - runs directly from GitHub using `uvx`:

| **MCP Client**           | **Configuration**                                    |
| ------------------------ | ---------------------------------------------------- |
| **VSCode**               | [📋 Copy config](examples/mcp/vscode-uvx.json)       |
| **Standard MCP Clients** | [📋 Copy config](examples/mcp/mcp-standard-uvx.json) |

**For Development** - when you need to test local changes:

| **MCP Client**           | **Configuration**                                    |
| ------------------------ | ---------------------------------------------------- |
| **VSCode**               | [📋 Copy config](examples/mcp/vscode-dev.json)       |
| **Standard MCP Clients** | [📋 Copy config](examples/mcp/mcp-standard-dev.json) |

The "Standard MCP Clients" config works with any MCP client following the MCP specification (Cursor, Claude Desktop, etc.). VSCode uses a different format.

**Setup:**

- **uvx configs**: Update the `NETWORK_INVENTORY` path to your inventory file
- **dev configs**: Update the `NETWORK_INVENTORY` path and `cwd` to your local project directory

</details>

<details>
<summary><strong>🛠️ CLI Usage (Direct Tool Usage)</strong></summary>

**For CLI users** who want to use gNMIBuddy as a command-line tool:

### One-time execution

```bash
# Run directly without installation
uvx --from git+https://github.com/jillesca/gNMIBuddy.git gnmibuddy --help

# Example with commands
uvx --from git+https://github.com/jillesca/gNMIBuddy.git gnmibuddy --inventory your_inventory.json device list
```

### Install as a persistent tool

```bash
# Install the tool globally
uv tool install git+https://github.com/jillesca/gNMIBuddy.git

# Use it directly
gnmibuddy --help
gnmibuddy device info --device R1

# Uninstall when no longer needed
uv tool uninstall gnmibuddy

# To get updates
uv tool upgrade gnmibuddy
```

The `uvx` method automatically builds and runs the tool in an isolated environment without affecting your system.

</details>

## 🐳 Running as a Container

Build and run gNMIBuddy as a container image using the provided `Makefile` targets. The `Makefile` auto-detects Docker or Podman (Docker preferred); override with `CONTAINER_ENGINE=docker` or `CONTAINER_ENGINE=podman` if you need to force one.

Device inventory is provided at runtime as a mounted file.

```bash
# Build the image (no inventory needed)
make build

# Run it, mounting your inventory file read-only into the container
# or set the NETWORK_INVENTORY in a .env file
make run NETWORK_INVENTORY=/path/to/inventory.json

# Tail logs / stop the container
make logs
make stop
```

> [!TIP]
> Run `make help` for the rest of the targets (`restart`, `shell`, `clean`, `fresh`).

You can test it locally with the `modelcontextprotocol/inspector`.

```bash
npx @modelcontextprotocol/inspector --transport http --server-url http://0.0.0.0:8000/mcp
```

### Running on Kubernetes

The container expects a device inventory file at the path in the `NETWORK_INVENTORY` environment variable (`/app/inventory.json` by default). There's no bundled Kubernetes manifest — the exact mechanism depends on your cluster — but the requirement is generic:

- Build the image with any OCI-compatible builder (Docker, Buildah, Kaniko, `docker buildx`, your CI's own build step, etc.). The `Containerfile` is standard and carries no device-specific data, so the resulting image is safe to push to your registry.
- Store the inventory as a Kubernetes `Secret`.
- Mount that `Secret` as a volume on the pod at `/app/inventory.json` (or mount it elsewhere and point `NETWORK_INVENTORY` at that path via the pod's env).

## 📖 CLI Reference

```bash
# Clone and setup (one-time only)
git clone https://github.com/jillesca/gNMIBuddy.git && cd gNMIBuddy
# Install dependencies
uv sync --frozen --no-dev
```

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
  Provide device inventory via --inventory PATH, set NETWORK_INVENTORY env var, or use .env file (configurable with --env-file PATH)

Options:
  -h, --help            Show this message and exit
  -V, --version         Show version information
  --log-level LEVEL     Set logging level (debug, info, warning, error)
  --module-log-help     Show detailed module logging help
  --all-devices         Run on all devices concurrently
  --inventory PATH      Path to inventory JSON file
  -e, --env-file PATH   Path to .env file for configuration (default: .env in project root)
  --max-workers NUMBER  Maximum number of concurrent workers for batch operations (--all-devices, --devices, --device-file)

Commands:
  device (d)    Device Information
    capabilities Get gNMI capabilities from a network device
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
    adjacency    Get network-wide IP adjacency analysis for complete topology
    network      Get complete network topology information. Queries all devices in inventory.

  ops (o)       Operations
    logs         Retrieve and filter device logs
    validate     Validate all collector functions (development tool)

  inventory (i) Inventory Management
    validate     Validate inventory file format and schema

Examples:
  gnmibuddy.py device info --device R1
  gnmibuddy.py network routing --device R1
  gnmibuddy.py --all-devices device list
  gnmibuddy.py inventory validate --inventory inventory.json
  gnmibuddy.py --env-file production.env device list
  gnmibuddy.py --env-file dev.env --log-level debug device info --device R1

Run 'gnmibuddy.py COMMAND --help' for more information on a command.
```

## 🤖 Development

### Quick Testing with MCP Inspector

**Recommended: Use uvx (no repository clone needed)**:

```bash
# Replace `xrd_sandbox.json` with your actual inventory file
echo '#!/usr/bin/env bash' > /tmp/gnmibuddy-mcp-wrapper \
&& echo 'exec uvx --from git+https://github.com/jillesca/gNMIBuddy.git gnmibuddy-mcp "$@"' >> /tmp/gnmibuddy-mcp-wrapper \
&& chmod +x /tmp/gnmibuddy-mcp-wrapper \
&& NETWORK_INVENTORY=xrd_sandbox.json npx @modelcontextprotocol/inspector /tmp/gnmibuddy-mcp-wrapper
EOF
```

**For local development (testing uncommitted changes)**:

```bash
# Run from your gNMIBuddy project directory (where pyproject.toml is located)
cd /path/to/your/gNMIBuddy && \
NETWORK_INVENTORY=your_inventory.json \
npx @modelcontextprotocol/inspector \
uv run --frozen gnmibuddy-mcp
```

### MCP Client Configuration

Choose the approach that fits your needs:

| **Use Case**           | **VSCode**                                     | **Standard MCP Clients**                             |
| ---------------------- | ---------------------------------------------- | ---------------------------------------------------- |
| **Production/Testing** | [📋 Copy config](examples/mcp/vscode-uvx.json) | [📋 Copy config](examples/mcp/mcp-standard-uvx.json) |
| **Local Development**  | [📋 Copy config](examples/mcp/vscode-dev.json) | [📋 Copy config](examples/mcp/mcp-standard-dev.json) |

**Standard MCP Clients** config works with Cursor, Claude Desktop, and any other client following the MCP specification. VSCode requires a specific format.

**Configuration requirements:**

- **uvx configs**: Only update `NETWORK_INVENTORY` path to your inventory file
- **dev configs**: Update both `NETWORK_INVENTORY` path and `cwd` to your local project directory

## 🧪 Testing with DevNet Sandbox

Don't have network devices? Use the [DevNet XRd Sandbox](https://devnetsandbox.cisco.com/DevNet/), follow the instructions to bring up a segment routing network with gNMI configured.

Use the `xrd_sandbox.json` inventory file to connect to the XRd devices running in the DevNet Sandbox.

If gNMI is not enabled, you can enable it with the following commands:

```bash
# If you cloned the repo
# Enable gRPC on the DevNet XRd Sandbox
ANSIBLE_HOST_KEY_CHECKING=False \
uvx --from "ansible-core==2.19.2" --with "paramiko,ansible" \
ansible-playbook ansible-helper/xrd_apply_config.yaml -i ansible-helper/hosts
```

### Testing with AI Agents

Want to see how this MCP tool integrates with actual AI agents? Check out [sp_oncall](https://github.com/jillesca/sp_oncall) - a graph of agents that use gNMIBuddy to demonstrate real-world network operations scenarios.

## 📋 Response Format

gNMIBuddy provides structured, consistent responses for all network operations. The response format depends on whether you're targeting a single device or multiple devices.

### Single Device Operations

Single device operations return a `NetworkOperationResult` object with detailed information about the operation, including status, data, metadata, and error handling.

```python
@dataclass
class NetworkOperationResult:
    device_name: str
    ip_address: IPAddress
    nos: NetworkOS
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

gNMIBuddy supports environment variables for configuration, which work for both CLI and MCP server usage. Environment variables can be loaded from:

1. **Command line arguments** (highest priority)
2. **Operating system environment variables**
3. **`.env` files** (default: `.env` in project root)
4. **Default values** (lowest priority)

### .env File Support

gNMIBuddy automatically loads environment variables from a `.env` file in the project root. You can specify a custom `.env` file using the `--env-file` option:

```bash
# Use default .env file
gnmibuddy device list

# Use custom environment file
gnmibuddy --env-file production.env device list
```

Example:

```bash
# .env file

# Network configuration
NETWORK_INVENTORY=/path/to/inventory.json

# Logging configuration
GNMIBUDDY_LOG_LEVEL=debug
GNMIBUDDY_MODULE_LEVELS=src.cmd=warning,src.inventory=debug
GNMIBUDDY_STRUCTURED_LOGGING=true
GNMIBUDDY_LOG_FILE=/custom/log/path.log
GNMIBUDDY_EXTERNAL_SUPPRESSION_MODE=development

# MCP debugging
GNMIBUDDY_MCP_TOOL_DEBUG=true
```

### Global Configuration

| Variable                              | Description                                 | Values                              | Default                  |
| ------------------------------------- | ------------------------------------------- | ----------------------------------- | ------------------------ |
| `NETWORK_INVENTORY`                   | Device inventory file path                  | File path                           | -                        |
| `GNMIBUDDY_LOG_LEVEL`                 | Global log level                            | `debug`, `info`, `warning`, `error` | `info`                   |
| `GNMIBUDDY_MODULE_LEVELS`             | Module-specific log levels                  | `module1=debug,module2=warning`     | -                        |
| `GNMIBUDDY_LOG_FILE`                  | Custom log file path (overrides sequential) | File path                           | `logs/gnmibuddy_XXX.log` |
| `GNMIBUDDY_STRUCTURED_LOGGING`        | Enable JSON logging                         | `true`, `false`                     | `false`                  |
| `GNMIBUDDY_EXTERNAL_SUPPRESSION_MODE` | External library suppression                | `cli`, `mcp`, `development`         | `cli`                    |
| `GNMIBUDDY_MCP_TOOL_DEBUG`            | Enable MCP tool debugging                   | `true`, `false`                     | `false`                  |

**Sequential Log Files**: gNMIBuddy automatically creates numbered log files (`gnmibuddy_001.log`, `gnmibuddy_002.log`, etc.) for each execution in the `logs/` directory. The highest number is always the most recent run.

> [!NOTE]
> Environment variables serve as defaults and can be overridden by CLI arguments like `--log-level` and `--module-log-levels`.

For detailed environment configuration options and advanced usage, see [Environment Configuration Guide](src/config/README.md)

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
