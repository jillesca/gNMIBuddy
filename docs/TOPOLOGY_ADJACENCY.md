# Topology Adjacency Command Documentation

## Overview

The `topology adjacency` command provides network-wide IP adjacency analysis for complete topology understanding. This command was introduced in gNMIBuddy v0.1.0+ as part of comprehensive error handling improvements.

## Command Usage

### CLI Syntax

```bash
# Get network-wide topology adjacency analysis
uv run gnmibuddy.py topology adjacency --device <device-name>

# Example
uv run gnmibuddy.py topology adjacency --device xrd-1
```

### API Usage

```python
from api import get_topology_adjacency_api

# Get topology adjacency analysis
result = get_topology_adjacency_api("xrd-1")
```

## Command Behavior

### Network-Wide Scope

Unlike device-specific commands, topology adjacency performs a **network-wide analysis** that examines IP connections across the entire network infrastructure. The device parameter is used for interface compliance, but the operation scope is network-wide.

### Error Handling

The command implements robust error handling that distinguishes between:

1. **gNMI Errors**: Authentication failures, connectivity issues, gRPC server errors
2. **Legitimate Empty Topologies**: Networks with no discovered IP connections

## Response Format

### Success Response (Empty Network)

```json
{
  "device_name": "xrd-1",
  "ip_address": "10.10.20.101",
  "nos": "iosxr",
  "operation_type": "topology_adjacency",
  "status": "success",
  "data": {},
  "metadata": {
    "total_connections": 0,
    "scope": "network-wide",
    "message": "No topology connections discovered"
  }
}
```

### Success Response (Network With Connections)

```json
{
  "device_name": "xrd-1",
  "ip_address": "10.10.20.101",
  "nos": "iosxr",
  "operation_type": "topology_adjacency",
  "status": "success",
  "data": {},
  "metadata": {
    "total_connections": 5,
    "scope": "network-wide",
    "message": "Topology adjacency analysis complete with 5 connections"
  }
}
```

### Error Response (gNMI Authentication Failure)

```json
{
  "device_name": "xrd-1",
  "ip_address": "10.10.20.101",
  "nos": "iosxr",
  "operation_type": "topology_adjacency",
  "status": "failed",
  "data": {},
  "error_response": {
    "type": "gNMIException",
    "message": "GRPC ERROR Host: 10.10.20.101:57777, Error: authentication failed"
  },
  "metadata": {
    "scope": "network-wide",
    "message": "Failed to build topology adjacency due to gNMI errors"
  }
}
```

## Key Features

### 1. Fail-Fast Behavior

When gNMI errors are encountered during topology building (authentication failures, connectivity issues), the command immediately returns error status rather than potentially misleading empty results.

### 2. Uniform Data Structure

Both error responses and legitimate empty results return `data: {}` (empty dictionary). The distinction is made through:

- **`status` field**: `"failed"` for gNMI errors, `"success"` for legitimate empty
- **`error_response` field**: Present only for gNMI errors
- **`metadata` field**: Provides context about the scenario

### 3. Network-Wide Analysis

The command analyzes the complete network topology, not just connections from a single device. This provides a comprehensive view of network adjacencies.

### 4. Structured Metadata

The `metadata` field uses a plain dictionary to provide structured context:

- `scope`: Always "network-wide" for this command
- `message`: Human-readable description of the result
- `total_connections`: Number of IP connections discovered (when successful)

## Integration with Validate Command

The topology adjacency command is integrated into the `ops validate` test suite:

```bash
# Run validation including topology adjacency
uv run gnmibuddy.py ops validate --device xrd-1
```

The validate command now includes 8 total tests (increased from 7) with topology adjacency included in both basic and full validation modes.

## Error Scenarios and Troubleshooting

### Authentication Failures

**Symptom**: Command returns `status: "failed"` with gNMI authentication error

**Solution**:

- Verify device credentials in inventory file
- Check network connectivity to devices
- Ensure gNMI is enabled on target devices

### Network Unreachability

**Symptom**: Command returns `status: "failed"` with connection timeout errors

**Solution**:

- Verify IP addresses in inventory are correct
- Check network routing to devices
- Confirm gNMI port (typically 57777) is accessible

### Empty Topology Results

**Symptom**: Command returns `status: "success"` with `total_connections: 0`

**Expected When**:

- Network devices have no configured IP interfaces
- All devices are isolated (no inter-device connections)
- Management interfaces are excluded from topology

**Verify**: Check if this is legitimate network state vs configuration issue

## Best Practices

### For Users

1. **Check status field first** to distinguish between errors and legitimate empty results
2. **Use `metadata.message`** for human-readable context about the operation
3. **Review `total_connections`** in metadata to understand topology completeness
4. **Verify credentials and connectivity** when seeing `status: "failed"`

### For Developers

1. **Always check `isinstance(response, ErrorResponse)`** for error detection
2. **Use plain dictionary metadata** for structured metadata
3. **Return `data: {}`** for both errors and legitimate empty results
4. **Provide clear, actionable error messages** in metadata

## Related Commands

- `topology neighbors`: Get direct neighbors for a specific device
- `topology network`: Get complete network topology with full details
- `ops validate`: Run all collector functions including topology adjacency

## Version History

- **v0.1.0+**: Command introduced with comprehensive error handling
- **v0.1.0+**: Integrated into validate command test suite
- **v0.1.0+**: Implements uniform data structures and fail-fast behavior
