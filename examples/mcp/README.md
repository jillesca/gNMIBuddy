# MCP Configuration Examples

This directory contains ready-to-use configuration files for integrating gNMIBuddy with various MCP clients.

## File Naming Convention

- `vscode-*.json`: VSCode-specific configuration (uses custom format)
- `mcp-standard-*.json`: Standard MCP specification format (works with Cursor, Claude Desktop, and other MCP-compliant clients)
- `*-uvx.json`: **Recommended** - No installation required, runs directly from GitHub
- `*-dev.json`: For development setup with cloned repository (testing local changes)

## Setup Instructions

### 1. Choose Your Approach

**🚀 Quick Start (Recommended)**: Use the `uvx` configurations - no need to clone the repository, always uses latest stable version.

**🛠️ Development**: Use the `dev` configurations if you need to test local changes or modifications to gNMIBuddy.

### 2. Copy Configuration

**VSCode**: Copy contents to `.vscode/mcp.json` in your project
**Other MCP Clients**: Use the `mcp-standard-*.json` files for any client following the MCP specification

### 3. Update Configuration

**For uvx configurations (`*-uvx.json`) - Recommended**:

- Update `NETWORK_INVENTORY` with the path to your network inventory file
- No other changes needed - runs automatically from GitHub

**For development configurations (`*-dev.json`)**:

- Set `cwd` to your gNMIBuddy project directory (where `pyproject.toml` is located)
- Update `NETWORK_INVENTORY` with the path to your network inventory file
- Requires local repository clone

All configurations **must** use the `NETWORK_INVENTORY` environment variable to specify the inventory path.

## Configuration Comparison

| **Feature**        | **uvx configs**       | **dev configs**         |
| ------------------ | --------------------- | ----------------------- |
| **Setup Required** | None                  | Clone repository        |
| **Local Changes**  | ❌ No                 | ✅ Yes                  |
| **Auto-Updates**   | ✅ Latest from GitHub | ❌ Manual pull required |
| **Startup Speed**  | Slower (downloads)    | Faster (local)          |
| **Best For**       | Production, testing   | Development, debugging  |

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

# For development setup (run from your gNMIBuddy project directory)
cd /path/to/your/gNMIBuddy && \
NETWORK_INVENTORY=your_inventory.json \
npx @modelcontextprotocol/inspector \
uv run --frozen gnmibuddy-mcp
```
