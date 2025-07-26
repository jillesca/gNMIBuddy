# MCP Environment Variables

This document describes the environment variables available for configuring logging in the gNMIBuddy MCP server.

## Global Logging Environment Variables

These environment variables work for both CLI and MCP server:

### `GNMIBUDDY_LOG_LEVEL`

**Description**: Set the global logging level  
**Values**: `debug`, `info`, `warning`, `error`  
**Default**: `info`  
**Example**: `GNMIBUDDY_LOG_LEVEL=debug`

### `GNMIBUDDY_MODULE_LEVELS`

**Description**: Set module-specific log levels  
**Format**: `module1=level1,module2=level2`  
**Example**: `GNMIBUDDY_MODULE_LEVELS="gnmibuddy.collectors=debug,pygnmi=error"`

**Available modules**:

- `gnmibuddy.collectors` - All data collection modules
- `gnmibuddy.collectors.vpn` - VPN/VRF data collection
- `gnmibuddy.collectors.interfaces` - Interface data collection
- `gnmibuddy.collectors.routing` - Routing protocol data
- `gnmibuddy.gnmi` - gNMI client operations
- `gnmibuddy.services` - Service layer
- `gnmibuddy.processors` - Data processing modules
- `pygnmi` - External pygnmi library
- `grpc` - External gRPC library

### `GNMIBUDDY_STRUCTURED_LOGGING`

**Description**: Enable structured JSON logging  
**Values**: `true`, `false`, `1`, `0`, `yes`, `no`, `on`, `off`  
**Default**: `false`  
**Example**: `GNMIBUDDY_STRUCTURED_LOGGING=true`

### `GNMIBUDDY_LOG_FILE`

**Description**: Custom log file path  
**Default**: `logs/gnmibuddy.log`  
**Example**: `GNMIBUDDY_LOG_FILE=/var/log/gnmibuddy.log`

### `GNMIBUDDY_EXTERNAL_SUPPRESSION_MODE`

**Description**: External library suppression mode  
**Values**: `cli`, `mcp`, `development`  
**Default**: `cli`  
**Example**: `GNMIBUDDY_EXTERNAL_SUPPRESSION_MODE=mcp`

## MCP-Specific Environment Variables

These are specific to the MCP server:

### `GNMIBUDDY_MCP_TOOL_DEBUG`

**Description**: Enable debug logging for all MCP tools  
**Values**: `true`, `false`, `1`, `0`, `yes`, `no`, `on`, `off`  
**Default**: `false`  
**Example**: `GNMIBUDDY_MCP_TOOL_DEBUG=true`

**When enabled, sets debug level for**:

- `gnmibuddy.mcp.tools.get_vpn_info`
- `gnmibuddy.mcp.tools.get_devices`
- `gnmibuddy.mcp.tools.get_interface_info`
- `gnmibuddy.mcp.tools.get_routing_info`
- `gnmibuddy.mcp.tools.get_mpls_info`
- `gnmibuddy.mcp.tools.get_logs`
- `gnmibuddy.mcp.tools.get_device_profile_api`
- `gnmibuddy.mcp.tools.get_system_info`
- `gnmibuddy.mcp.tools.get_network_topology_api`
- `gnmibuddy.mcp.tools.get_topology_neighbors`

## Usage Examples

### Basic MCP Server with Debug Logging

```bash
export GNMIBUDDY_LOG_LEVEL=info
export GNMIBUDDY_MCP_TOOL_DEBUG=true
export GNMIBUDDY_MODULE_LEVELS="gnmibuddy.collectors.vpn=debug"
uv run mcp run mcp_server.py
```

### Quiet MCP Server (Production)

```bash
export GNMIBUDDY_LOG_LEVEL=warning
export GNMIBUDDY_MODULE_LEVELS="pygnmi=error,grpc=error"
export GNMIBUDDY_EXTERNAL_SUPPRESSION_MODE=mcp
uv run mcp run mcp_server.py
```

### Debug Specific Tool Issues

```bash
export GNMIBUDDY_LOG_LEVEL=info
export GNMIBUDDY_MODULE_LEVELS="gnmibuddy.mcp.tools.get_vpn_info=debug,gnmibuddy.collectors.vpn=debug"
uv run mcp run mcp_server.py
```

### CLI with Same Environment Variables

```bash
export GNMIBUDDY_LOG_LEVEL=debug
export GNMIBUDDY_MODULE_LEVELS="gnmibuddy.collectors=debug,pygnmi=warning"
python gnmibuddy.py --device xrd-1 vpn
```

## Environment Variable Priority

Environment variables serve as **defaults** and can be overridden by:

1. **CLI arguments** (highest priority) - `--log-level`, `--module-log-levels`
2. **Environment variables** (medium priority)
3. **Code defaults** (lowest priority)

## Troubleshooting

### No Log Output

Check that `GNMIBUDDY_LOG_LEVEL` is set to an appropriate level:

```bash
export GNMIBUDDY_LOG_LEVEL=debug
```

### Too Much Noise

Suppress external libraries:

```bash
export GNMIBUDDY_MODULE_LEVELS="pygnmi=error,grpc=error,urllib3=error"
```

### MCP Tool Not Logging

Enable MCP tool debug mode:

```bash
export GNMIBUDDY_MCP_TOOL_DEBUG=true
```

### Logs Not Going to stderr

For MCP servers, ensure suppression mode is set correctly:

```bash
export GNMIBUDDY_EXTERNAL_SUPPRESSION_MODE=mcp
```

## Integration with MCP Clients

When using gNMIBuddy with MCP clients like Claude Desktop or Cline:

1. **Set environment variables** in your shell before starting the MCP client
2. **Use quiet settings** for production: `GNMIBUDDY_LOG_LEVEL=warning`
3. **Enable debug** for troubleshooting: `GNMIBUDDY_MCP_TOOL_DEBUG=true`
4. **Logs appear in client** as [error] messages (because they go to stderr)

The MCP client will show gNMIBuddy logs prefixed with your server name, like:

```
2025-07-26 11:35:56 [error] user-gNMIBuddy: 2025-07-26 11:35:56 | INFO | gnmibuddy.collectors.vpn | Discovered 1 VRFs on device xrd-1
```
