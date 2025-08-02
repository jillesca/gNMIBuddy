# MCP Configuration Examples

This directory contains ready-to-use configuration files for integrating gNMIBuddy with various MCP clients.

## File Naming Convention

- `vscode-*.json`: VSCode-specific configuration (uses custom format)
- `mcp-standard-*.json`: Standard MCP specification format (works with Cursor, Claude Desktop, and other MCP-compliant clients)
- `*-uvx.json`: No installation required, runs directly from GitHub
- `*-dev.json`: For development setup with cloned repository

## Setup Instructions

### 1. Choose Your Approach

**Quick Start (Recommended)**: Use the `uvx` configurations - no need to clone the repository.

**Development**: Use the `dev` configurations if you plan to modify gNMIBuddy or want full control.

### 2. Copy Configuration

**VSCode**: Copy contents to `.vscode/mcp.json` in your project
**Other MCP Clients**: Use the `mcp-standard-*.json` files for any client following the MCP specification

### 3. Update Paths

Replace `path/to/mcp_server.py` with the path to the `mcp_server` file.

Replace `path/to/your_inventory.json` with the actual path to your network inventory file.

All configurations **must** use the `NETWORK_INVENTORY` environment variable to specifying the inventory path in the configuration file.

## Testing

Use the MCP inspector to test your configuration:

```bash
# uvx setup
# Replace `your_inventory.json` with your actual inventory file
echo '#!/usr/bin/env bash' > /tmp/gnmibuddy-mcp-wrapper \
&& echo 'exec uvx --from git+https://github.com/jillesca/gNMIBuddy.git gnmibuddy-mcp "$@"' >> /tmp/gnmibuddy-mcp-wrapper \
&& chmod +x /tmp/gnmibuddy-mcp-wrapper \
&& NETWORK_INVENTORY=your_inventory.json npx @modelcontextprotocol/inspector /tmp/gnmibuddy-mcp-wrapper
EOF

# For development setup
NETWORK_INVENTORY=your_inventory.json \
npx @modelcontextprotocol/inspector \
uv run --with "mcp[cli],pygnmi,networkx,pyyaml" \
mcp run mcp_server.py
```
