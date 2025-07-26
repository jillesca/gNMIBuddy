# MCP Configuration Examples

This directory contains ready-to-use configuration files for integrating gNMIBuddy with various MCP clients.

## File Naming Convention

- `{client}-uvx.json`: No installation required, runs directly from GitHub
- `{client}-dev.json`: For development setup with cloned repository

## Setup Instructions

### 1. Choose Your Approach

**Quick Start (Recommended)**: Use the `uvx` configurations - no need to clone the repository.

**Development**: Use the `dev` configurations if you plan to modify gNMIBuddy or want full control.

### 2. Copy Configuration

**VSCode**: Copy contents to `.vscode/mcp.json` in your project
**Cursor**: Copy contents to `.cursor/mcp.json` in your project  
**Claude Desktop**: Add contents to your Claude configuration file

### 3. Update Inventory Path

Replace `path/to/your_inventory.json` with the actual path to your network inventory file.

All configurations **must** use the `NETWORK_INVENTORY` environment variable to specifying the inventory path in the configuration file.

## Configuration Locations

### VSCode

```
your-project/
├── .vscode/
│   └── mcp.json
```

### Cursor

```
your-project/
├── .cursor/
│   └── mcp.json
```

### Claude Desktop

See Claude Docs.

## Testing

Use the MCP inspector to test your configuration:

```bash
# For uvx setup
NETWORK_INVENTORY=your_inventory.json \
npx @modelcontextprotocol/inspector \
uvx --from git+https://github.com/jillesca/gNMIBuddy.git gnmibuddy-mcp

# For development setup
NETWORK_INVENTORY=your_inventory.json \
npx @modelcontextprotocol/inspector \
uv run --with "mcp[cli],pygnmi,networkx,pyyaml" \
mcp run mcp_server.py
```
