# Agent Prompts for Issue #2 Implementation

## Prerequisites for All Agents

**MANDATORY**: Before starting any work, you MUST read and understand the complete context from GitHub issue #2 comments, specifically:

1. **Original Issue Description**: <https://github.com/jillesca/gNMIBuddy/issues/2>
2. **Initial Implementation Plan**: First comment with detailed analysis and task breakdown
3. **Updated Implementation Plan**: Second comment with clarifications about ErrorResponse and data structures
4. **Critical Pattern Correction**: Third comment with mandatory coding patterns

**Key Requirements for ALL Agents:**

- ✅ **Use direct `isinstance(response, ErrorResponse)` checks** - NO wrapper functions
- ✅ **Use classes to encapsulate data** - NO dictionaries for data encapsulation
- ✅ **Return `data: {}` for both errors and legitimate empty results**
- ✅ **Use `status` field to distinguish**: `"failed"` for errors, `"success"` for legitimate empty
- ✅ **Use `metadata` field for context** about the scenario
- ✅ **Fail fast when ErrorResponse detected**
- ✅ **Work ONLY on your assigned phase** - report opportunities, don't implement them

**Final Step**: After completing your work, add a comment to GitHub issue #2 with a brief summary of what you implemented and any relevant notes.

---

## Task 1: Python Backend Developer - Fix VPN Info Error Handling

### Your Mission

Fix the `get_vpn_info` function in `/src/collectors/vpn.py` to properly handle `ErrorResponse` from gNMI operations and fail fast instead of returning successful empty results.

### Specific Requirements

- **File to modify**: `/src/collectors/vpn.py`
- **Focus**: The `get_vpn_info` function's handling of `get_non_default_vrf_names()` errors
- **Core Logic**: Check if `get_non_default_vrf_names()` encounters `ErrorResponse` from gNMI client
- **Error Pattern**: Use direct `isinstance(response, ErrorResponse)` checks
- **Data Encapsulation**: Use classes, not dictionaries, to encapsulate response data

### Expected Behavior Changes

```python
# Error case (authentication failed)
NetworkOperationResult(
    status=OperationStatus.FAILED,
    data={},  # Empty dict, not empty array
    error_response=ErrorResponse(...),
    metadata=SomeMetadataClass(message="Failed to discover VRFs due to gNMI error")
)

# Success case (no VRFs configured)
NetworkOperationResult(
    status=OperationStatus.SUCCESS,
    data={},  # Empty dict, not {"vrfs": []}
    metadata=SomeMetadataClass(message="No VRFs found", total_vrfs_on_device=0)
)
```

### Testing

- Test with authentication failures to verify error propagation
- Test with legitimate no-VRF scenarios to verify success response
- Run: `uv run gnmibuddy.py ops validate --device xrd-1` to verify behavior

### Constraints

- **ONLY** work on VPN info error handling
- **DO NOT** modify other functions or files beyond what's necessary
- **DO NOT** create wrapper utility functions like `has_gnmi_error()`
- **REPORT** any related issues you notice but don't fix them

---

## Task 2: Network Topology Specialist - Fix Topology Neighbors Error Handling

### Your Mission

Fix the `neighbors` function in `/src/collectors/topology/neighbors.py` to distinguish between legitimate device isolation and gNMI errors during topology building.

### Specific Requirements

- **Primary File**: `/src/collectors/topology/neighbors.py`
- **Secondary File**: May need to update `/src/collectors/topology/utils.py` for error propagation
- **Focus**: Detect when `_build_graph_ip_only()` encounters `ErrorResponse` during interface collection
- **Error Pattern**: Use direct `isinstance(response, ErrorResponse)` checks
- **Data Encapsulation**: Use classes, not dictionaries, to encapsulate response data

### Expected Behavior Changes

```python
# Error case (gNMI errors during topology building)
NetworkOperationResult(
    status=OperationStatus.FAILED,
    data={},
    error_response=ErrorResponse(...),
    metadata=SomeMetadataClass(
        message="Failed to build topology due to gNMI errors",
        device_in_topology=False
    )
)

# Success case (legitimately isolated)
NetworkOperationResult(
    status=OperationStatus.SUCCESS,
    data={},
    metadata=SomeMetadataClass(
        message="No neighbors found for device",
        device_in_topology=False,
        isolation_reason="legitimate"
    )
)
```

### Key Logic

- Check if device exists in inventory but topology building failed due to `ErrorResponse`
- If `ErrorResponse` detected → fail fast with error status
- If device legitimately isolated → return success status
- Update `_build_graph_ip_only()` in utils.py if needed to propagate error information

### Testing

- Test with authentication failures during interface collection
- Test with legitimately isolated devices
- Run: `uv run gnmibuddy.py ops validate --device xrd-1` to verify behavior

### Constraints

- **ONLY** work on topology neighbors error handling
- **DO NOT** work on topology adjacency (that's Task 3)
- **REPORT** any related issues you notice but don't fix them

---

## Task 3: Network Topology Specialist - Implement Missing Topology Adjacency Function

### Your Mission

Create the missing `topology_adjacency` function and integrate it into the command structure and validate command.

### Specific Requirements

- **Files to create/modify**:
  - Create `/src/cmd/commands/topology/adjacency.py`
  - Update `/src/cmd/commands/topology/__init__.py`
  - Update `/src/cmd/commands/ops/validate.py`
- **Core Logic**: Wrap `get_network_topology()` with proper `ErrorResponse` detection
- **Error Pattern**: Use direct `isinstance(response, ErrorResponse)` checks
- **Data Encapsulation**: Use classes, not dictionaries, to encapsulate response data

### Expected Implementation

```python
# In adjacency.py - create command that wraps get_network_topology()
def ip_adjacency_dump_cmd(device_obj):
    # Implement ErrorResponse detection
    # Return NetworkOperationResult with proper error handling

# Error case
NetworkOperationResult(
    status=OperationStatus.FAILED,
    data={},
    error_response=ErrorResponse(...),
    metadata=SomeMetadataClass(
        scope="network-wide",
        message="Failed to build topology due to gNMI errors"
    )
)

# Success case (no connections found)
NetworkOperationResult(
    status=OperationStatus.SUCCESS,
    data={},
    metadata=SomeMetadataClass(
        total_connections=0,
        scope="network-wide",
        message="No topology connections discovered"
    )
)
```

### Integration Requirements

- Add function to validate.py test suite: `"topology_adjacency": lambda: ip_adjacency_dump_cmd(device_obj)`
- Ensure it's included in both basic and full validation modes
- Import appropriate functions from topology collectors

### Testing

- Test with network-wide topology building failures
- Test with legitimate empty topology scenarios
- Run: `uv run gnmibuddy.py ops validate --device xrd-1` to verify inclusion

### Constraints

- **ONLY** work on topology adjacency implementation and integration
- **DO NOT** modify topology neighbors (that's Task 2)
- **REPORT** any related issues you notice but don't fix them

---

## Task 4: CLI Developer - Update Validate Command

### Your Mission

Integrate the new `topology_adjacency` function into the validate command test suite.

### Specific Requirements

- **File to modify**: `/src/cmd/commands/ops/validate.py`
- **Task**: Add `topology_adjacency` test function to the validation test suite
- **Integration**: Ensure it works in both basic and full validation modes
- **Import**: Add necessary imports for the topology adjacency function

### Expected Changes

```python
# Add to test function dictionary
"topology_adjacency": lambda: ip_adjacency_dump_cmd(device_obj)

# Ensure proper imports
from src.cmd.commands.topology.adjacency import ip_adjacency_dump_cmd
```

### Testing

- Run: `uv run gnmibuddy.py ops validate --device xrd-1`
- Verify `topology_adjacency` appears in output
- Verify it handles both error and success scenarios correctly

### Constraints

- **ONLY** work on validate command integration
- **DO NOT** implement the adjacency function itself (that's Task 3)
- **COORDINATE** with Task 3 agent on function naming and import paths

---

## Task 5: Test Developer - Update Tests

### Your Mission

Create comprehensive tests for the modified functions focusing on `ErrorResponse` detection and fail-fast behavior.

### Specific Requirements

- **Focus**: Test `ErrorResponse` detection and proper error propagation
- **Files**: Create/update test files for:
  - VPN info error handling scenarios
  - Topology neighbors error propagation
  - Topology adjacency function
  - Validate command with all functions

### Key Test Scenarios

1. **ErrorResponse Detection**: Simulate gNMI authentication failures
2. **Data Structure Consistency**: Verify `data: {}` format
3. **Status Differentiation**: Verify correct status values
4. **Metadata Context**: Verify metadata provides clear context
5. **Fail-Fast Behavior**: Verify functions stop processing on errors

### Testing Strategy

- Use `pytest` CLI instead of integrated test terminal
- Test both error scenarios and legitimate empty data cases
- Mock `ErrorResponse` and `FeatureNotFoundResponse` objects
- Verify class-based data encapsulation (not dictionaries)

### Constraints

- **ONLY** work on testing the changes made by other agents
- **WAIT** for other agents to complete their implementations first
- **REPORT** any test failures or issues discovered

---

## Task 6: Documentation Specialist - Update Documentation

### Your Mission

Update documentation to reflect the new error handling patterns and the topology adjacency feature.

### Specific Requirements

- **Focus Areas**:
  - Document `ErrorResponse`-based error detection pattern
  - Explain uniform `data: {}` structure for both errors and empty results
  - Document metadata field usage for distinguishing scenarios
  - Document new topology adjacency command
  - Update API documentation for changed behavior

### Key Documentation Updates

- Error handling patterns and best practices
- Data structure conventions
- New topology adjacency command usage
- Metadata field semantics
- Status field meanings ("failed" vs "success")

### Constraints

- **ONLY** work on documentation updates
- **WAIT** for other agents to complete implementations first
- **COORDINATE** with other agents to understand exact changes made

---

## General Guidelines for All Agents

### Workflow

1. **Read issue comments 1-4** to understand full context
2. **Focus ONLY on your assigned task/phase**
3. **Use class-based data encapsulation** (mandatory requirement)
4. **Follow the direct `isinstance(response, ErrorResponse)` pattern**
5. **Test your changes thoroughly**
6. **Report any discovered issues without fixing them**
7. **Add summary comment to GitHub issue #2** when done

### Error Handling Pattern (MANDATORY)

```python
# ✅ CORRECT - Use direct isinstance checks
if isinstance(response, ErrorResponse):
    return SomeResultClass(
        status=OperationStatus.FAILED,
        data={},
        error_response=response,
        metadata=MetadataClass(message="Failed due to gNMI error")
    )

# ✅ CORRECT - Also check for FeatureNotFoundResponse
if isinstance(response, FeatureNotFoundResponse):
    # Handle feature not found scenario
```

### Data Structure Requirements

- **✅ DO**: Use classes to encapsulate data
- **✅ DO**: Return `data: {}` for both errors and legitimate empty
- **✅ DO**: Use `status` field to distinguish error vs success
- **✅ DO**: Use `metadata` field for additional context
- **❌ DON'T**: Use dictionaries for data encapsulation
- **❌ DON'T**: Create wrapper functions like `has_gnmi_error()`

### Reporting Issues

When you discover areas for improvement outside your task scope:

- **Document the issue clearly**
- **Explain why it needs attention**
- **Suggest the appropriate agent/task to handle it**
- **DO NOT implement the fix yourself**

### Success Criteria

Your task is complete when:

- ✅ Your specific requirements are implemented
- ✅ All tests pass for your changes
- ✅ Error handling follows the mandatory patterns
- ✅ Class-based data encapsulation is used
- ✅ You've added a summary comment to the GitHub issue
