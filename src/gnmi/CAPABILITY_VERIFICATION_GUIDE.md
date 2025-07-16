# Capability Verification System Guide

## Overview

The capability verification system in gNMIBuddy ensures that network devices support the required OpenConfig models before attempting to collect data. This prevents errors and provides clear feedback about device compatibility.

## Multi-Model Support

The system now supports verification of multiple OpenConfig models simultaneously, allowing for more complex operations that require multiple schemas.

### Supported Models

| Model                         | Purpose                                       | Minimum Version |
| ----------------------------- | --------------------------------------------- | --------------- |
| `openconfig-system`           | System-level configuration and state data     | 0.17.1          |
| `openconfig-interfaces`       | Interface configuration and statistics        | 4.0.0           |
| `openconfig-network-instance` | Network instance configuration and state data | 1.3.0           |

## How It Works

### Automatic Verification

The system automatically verifies device capabilities when you run commands that require specific OpenConfig models:

```bash
# This command will automatically verify openconfig-network-instance capability
uv run gnmictl.py --inventory xrd_sandbox.json --device xrd-1 routing

# This command will verify openconfig-interfaces capability
uv run gnmictl.py --inventory xrd_sandbox.json --device xrd-1 interfaces

# This command will verify openconfig-system capability
uv run gnmictl.py --inventory xrd_sandbox.json --device xrd-1 system
```

### Verification Process

1. **Path Analysis**: The system analyzes gNMI paths to determine required models
2. **Multi-Model Detection**: Identifies all OpenConfig models needed for the operation
3. **Capability Query**: Queries the device for its supported gNMI models
4. **Model Search**: Searches for each required OpenConfig model
5. **Version Check**: Verifies each model version meets minimum requirements
6. **Caching**: Results are cached for performance optimization
7. **Execution**: If verification passes, the command proceeds; otherwise, it fails gracefully

### Smart Decorator

The `@verify_required_models` decorator automatically detects required models from function parameters:

```python
@verify_required_models()
def collect_routing_data(device: Device, gnmi_request: GnmiRequest):
    # Function automatically verified for openconfig-network-instance
    # based on paths in gnmi_request
    pass
```

## What to Expect

### Successful Verification

When a device supports the required model:

```
INFO | Device xrd-1: openconfig-network-instance v1.3.0 verification successful
INFO | Collecting routing information from device xrd-1
[Data collection proceeds...]
```

### Version Warnings

When a device has an older version that might still work:

```
WARNING | Device xrd-1: openconfig-network-instance v1.2.0 is older than required v1.3.0
WARNING | Proceeding with data collection but some features may not work
[Data collection proceeds with warning...]
```

### Model Not Found

When a device doesn't support the required model:

```
ERROR | Device xrd-1 does not support openconfig-network-instance model
ERROR | Available models: [list of supported models]
ERROR | Cannot proceed with routing data collection
```

### Network/Connection Issues

When there are connectivity problems:

```
ERROR | Failed to connect to device xrd-1: Connection refused
ERROR | Please check device connectivity and gNMI configuration
```

## Performance Characteristics

### First Request

- **Time**: ~2-3 seconds (includes capability query)
- **Network**: 1 gNMI capabilities request + data requests
- **Caching**: Results cached for 1 hour

### Subsequent Requests

- **Time**: ~1-2 seconds (uses cached results)
- **Network**: Only data requests (no capability query)
- **Caching**: Uses cached verification results

## Troubleshooting

### Common Issues

#### 1. Device Not Found in Inventory

```
ERROR | Device 'invalid-device' not found in inventory
```

**Solution**: Check your inventory file and ensure the device name is correct.

#### 2. Inventory File Not Found

```
ERROR | File not found: /path/to/inventory.json
```

**Solution**: Verify the inventory file path and ensure the file exists.

#### 3. gNMI Connection Failed

```
ERROR | Failed to connect to device: Connection refused
```

**Solution**:

- Check device IP address and port
- Verify gNMI is enabled on the device
- Check network connectivity
- Verify authentication credentials

#### 4. Model Not Supported

```
ERROR | Device does not support openconfig-network-instance model
```

**Solution**:

- Update device software to a version that supports OpenConfig
- Check if the device has the required model installed
- Use alternative collection methods if available

#### 5. Version Too Old

```
WARNING | Model version is older than required
```

**Solution**:

- Update device software
- Check if the older version actually works for your use case
- Consider the warning as informational if data collection succeeds

### Debug Information

For detailed troubleshooting, enable debug logging:

```bash
uv run gnmictl.py \
  --log-level DEBUG \
  --module-log-levels "gnmibuddy.gnmi.capabilities=DEBUG,gnmibuddy.services.capability_verification=DEBUG" \
  --inventory xrd_sandbox.json \
  --device xrd-1 \
  routing
```

This provides detailed information about:

- Capability query process
- Model search and matching
- Version comparison logic
- Caching behavior
- Error details

### Log Analysis

Key log messages to look for:

#### Successful Verification

```
INFO | Device xrd-1: openconfig-network-instance v1.3.0 verification successful
```

#### Version Issues

```
WARNING | Device xrd-1: openconfig-network-instance v1.2.0 is older than required v1.3.0
```

#### Model Not Found

```
ERROR | Device xrd-1 does not support openconfig-network-instance model
```

#### Cache Behavior

```
DEBUG | Cache hit for device: xrd-1, verified: True
DEBUG | No cache entry found for device: xrd-1
```

## Best Practices

### 1. Inventory Management

- Keep inventory files up to date
- Use descriptive device names
- Verify IP addresses and ports are correct

### 2. Error Handling

- Always check command exit codes
- Review error messages for actionable information
- Use debug logging for troubleshooting

### 3. Performance Optimization

- Cache results are automatically managed
- Avoid unnecessary repeated verification
- Use appropriate logging levels in production

### 4. Monitoring

- Monitor for version warning messages
- Track capability verification success rates
- Alert on repeated failures

## Integration with Automation

### Shell Scripts

```bash
#!/bin/bash
if uv run gnmictl.py --inventory inventory.json --device xrd-1 routing; then
    echo "Routing data collection successful"
else
    echo "Routing data collection failed - check device compatibility"
    exit 1
fi
```

### Python Integration

```python
import subprocess
import sys

def collect_routing_data(device_name):
    cmd = [
        "uv", "run", "gnmictl.py",
        "--inventory", "inventory.json",
        "--device", device_name,
        "routing"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Failed to collect routing data: {e.stderr}")
        return None
```

### CI/CD Integration

- Include capability verification in pre-deployment checks
- Use exit codes to determine pipeline success/failure
- Log verification results for audit purposes

## Advanced Configuration

### Custom Model Requirements

Future versions may support custom model requirements:

```json
{
  "model_requirements": {
    "openconfig-network-instance": {
      "min_version": "1.3.0",
      "required": true
    }
  }
}
```

### Cache Configuration

Cache settings can be adjusted:

- Cache TTL (default: 1 hour)
- Cache size limits
- Cache invalidation policies

## Support and Maintenance

### Updates

- Model requirements may change with software updates
- Check release notes for capability verification changes
- Update inventory files when devices are upgraded

### Monitoring

- Track verification success rates
- Monitor cache hit ratios
- Alert on model compatibility issues

### Documentation

- Keep this guide updated with your specific environment
- Document any custom model requirements
- Share troubleshooting procedures with your team

## FAQ

### Q: Why is the first request slower than subsequent ones?

A: The first request includes a capability query to the device, which is cached for one hour. Subsequent requests use the cached results and are faster.

### Q: What happens if a device is upgraded after verification?

A: The cache will expire after one hour, and the next request will re-verify capabilities automatically.

### Q: Can I disable capability verification?

A: Currently, capability verification is always enabled for commands that require specific models. This ensures data collection reliability.

### Q: How do I know which models my device supports?

A: Use debug logging to see all supported models, or check your device's OpenConfig documentation.

### Q: What if my device supports the model but data collection still fails?

A: This could indicate a model implementation issue. Check the device logs and consider reporting the issue to the device vendor.

## Version History

- **v1.0**: Initial capability verification system
- **v1.1**: Added caching for performance improvement
- **v1.2**: Enhanced error messages and troubleshooting
- **v1.3**: Added version warning system

---

For additional support, please refer to the main gNMIBuddy documentation or contact your system administrator.
