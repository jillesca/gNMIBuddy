# LLM Agent Implementation Prompts for Issue #10

## 🚨 **CRITICAL INSTRUCTIONS FOR ALL AGENTS**

### **Before Starting Any Phase:**

1. **READ THE FULL PLAN**: First, read issue #10 in the GitHub repository (jillesca/gNMIBuddy) to understand the complete implementation plan
2. **UPDATE PLAN STATUS**: Update the **second comment** in issue #10 from "old" to "new" where your specific phase is mentioned
3. **FOCUS ON YOUR PHASE ONLY**: Work exclusively on your assigned phase - do not perform work from other phases
4. **REPORT OPPORTUNITIES**: If you identify areas for improvement outside your phase, document them but do not implement them

### **After Completing Your Phase:**

1. **UPDATE ISSUE**: Add a new comment to issue #10 with a brief summary of your work (keep it concise)
2. **IDENTIFY YOURSELF**: **CRITICAL** - Always start your comment with your author identification (e.g., "_Implemented by: [Your Agent Name/ID]_")
3. **MARK PHASE COMPLETE**: Update the **third comment** in issue #10 to mark your phase as completed
4. **TEST VERIFICATION**: Ensure all tests pass using the specified testing patterns

---

## 📋 **Phase 1: Early Inventory Validation**

### **Your Mission:**

Implement early inventory validation in the `ops validate` command to detect configuration errors before attempting any operations.

### **Specific Tasks:**

1. **Modify `src/cmd/commands/ops/validate.py`**:

   - Add inventory path validation at the beginning of the `ops_validate` function
   - Use `get_inventory_path()` to validate inventory availability
   - Catch `FileNotFoundError` and handle it gracefully
   - Implement fail-fast behavior with proper error display

2. **Implementation Pattern:**

```python
# Add this logic at the start of ops_validate function
try:
    from src.inventory.file_handler import get_inventory_path
    inventory_path = get_inventory_path()
    logger.debug("Using inventory file: %s", inventory_path)
except FileNotFoundError as e:
    # Will use error_utils from Phase 2, but for now use basic error handling
    click.echo(f"Error: {e}", err=True)
    click.echo("─" * 50, err=True)
    click.echo("Command Help:", err=True)
    click.echo("─" * 50, err=True)
    click.echo(ctx.get_help(), err=True)
    click.echo("\n💡 Set NETWORK_INVENTORY environment variable or use --inventory option", err=True)
    sys.exit(1)
```

### **Testing Requirements:**

- **Use pytest CLI only**: `pytest tests/cmd/test_ops_validate_errors.py -v`
- **Never use VS Code integrated terminal** (it hangs)
- **Test with log file pattern**: Redirect command output to log files and verify contents
- Create test file: `tests/cmd/test_ops_validate_errors.py`

### **Success Criteria:**

- ✅ Command fails immediately when inventory is missing
- ✅ Error message is user-friendly and actionable
- ✅ Command help is displayed after error
- ✅ Exit code is 1 for configuration errors
- ✅ All tests pass using proper testing patterns
- ✅ **GitHub comment posted with proper author identification**

### **Files to Modify:**

- `src/cmd/commands/ops/validate.py` (primary)
- `tests/cmd/test_ops_validate_errors.py` (new test file)

---

## 📋 **Phase 2: Error Utils Creation**

### **Your Mission:**

Create reusable error handling utilities that provide consistent error display patterns across CLI commands.

### **Specific Tasks:**

1. **Create `src/cmd/commands/error_utils.py`**:

   - Implement `display_error_with_help(ctx, error_message, suggestion=None)` function
   - Follow the same pattern used by `inventory validate` command
   - Use Click's error output (`err=True`)
   - Include proper formatting with separators and suggestions

2. **Implementation Requirements:**

```python
#!/usr/bin/env python3
"""
Error handling utilities for CLI commands.
"""
import click
import sys

def display_error_with_help(ctx, error_message: str, suggestion: str = None):
    """
    Display error message with command help in consistent format.

    Args:
        ctx: Click context
        error_message: The error message to display
        suggestion: Optional helpful suggestion for the user
    """
    click.echo(f"Error: {error_message}", err=True)
    click.echo("─" * 50, err=True)
    click.echo("Command Help:", err=True)
    click.echo("─" * 50, err=True)
    click.echo(ctx.get_help(), err=True)

    if suggestion:
        click.echo(f"\n💡 {suggestion}", err=True)

    sys.exit(1)
```

3. **Update Phase 1 Implementation**:
   - Modify `src/cmd/commands/ops/validate.py` to use the new error utils
   - Replace the basic error handling with `display_error_with_help()` call

### **Testing Requirements:**

- **Use pytest CLI only**: `pytest tests/cmd/test_error_utils.py -v`
- Test the error utility function independently
- Verify integration with ops validate command
- Create test file: `tests/cmd/test_error_utils.py`

### **Success Criteria:**

- ✅ Reusable error utility function created
- ✅ Consistent error display format implemented
- ✅ Integration with ops validate command works
- ✅ Error patterns match inventory validate command
- ✅ All tests pass
- ✅ **GitHub comment posted with proper author identification**

### **Files to Modify:**

- `src/cmd/commands/error_utils.py` (new file)
- `src/cmd/commands/ops/validate.py` (update to use error utils)
- `tests/cmd/test_error_utils.py` (new test file)

---

## 📋 **Phase 3: All-or-Nothing Batch Validation**

### **Your Mission:**

Implement comprehensive batch validation that ensures all specified devices can be accessed before starting any operations.

### **Specific Tasks:**

1. **Enhanced Device Resolution**:

   - Validate inventory access for ALL specified devices before operations begin
   - If ANY device cannot be resolved due to inventory issues, fail the entire operation
   - Implement all-or-nothing approach (no partial successes)

2. **Batch Operation Enhancement**:

   - Review `src/cmd/batch.py` if needed for early validation
   - Ensure batch operations don't start with "Executing batch operation on X devices..." when inventory is missing
   - Prevent the logging cascade that currently happens

3. **Implementation Strategy**:
   - Validate device list resolution early in the process
   - Check that all devices exist in inventory before attempting connections
   - Use fail-fast approach consistently

### **Testing Requirements:**

- **Use pytest CLI only**: Test various device list scenarios
- **Test edge cases**: Mixed valid/invalid devices, empty device lists, non-existent devices
- **Log file testing**: Verify that batch operation messages don't appear on configuration errors

### **Success Criteria:**

- ✅ All devices validated before any operations start
- ✅ Complete failure if any device has inventory issues
- ✅ No "Executing batch operation..." message on configuration errors
- ✅ Consistent fail-fast behavior
- ✅ All edge cases properly handled
- ✅ **GitHub comment posted with proper author identification**

### **Files to Modify:**

- `src/cmd/commands/ops/validate.py` (enhance device validation)
- `src/cmd/batch.py` (if needed for early validation)
- Update existing test files to cover new scenarios

---

## 📋 **Phase 4: Testing and Validation**

### **Your Mission:**

Create comprehensive test coverage for all error scenarios and ensure UX consistency across the implementation.

### **Specific Tasks:**

1. **Error Scenario Testing**:

   - Missing inventory file scenarios
   - Invalid inventory path scenarios
   - Empty device list scenarios
   - Mixed valid/invalid device scenarios

2. **UX Consistency Testing**:

   - Verify error message format matches inventory validate command
   - Ensure help display is consistent and complete
   - Verify proper exit codes (1 for errors, 0 for success)
   - Test that error messages are actionable

3. **Implementation Testing Pattern**:

```python
def test_ops_validate_missing_inventory_with_log_file():
    """Test that missing inventory shows error + help (using log file pattern)"""
    import subprocess
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        log_file = f.name

    try:
        # Run command and redirect output to log file
        result = subprocess.run([
            'uv', 'run', 'gnmibuddy.py', 'ops', 'validate',
            '--devices', 'device1,device2'
        ], capture_output=True, text=True, timeout=30)

        # Write both stdout and stderr to log file
        with open(log_file, 'w') as f:
            f.write("STDOUT:\n")
            f.write(result.stdout)
            f.write("\nSTDERR:\n")
            f.write(result.stderr)

        # Read and verify log file contents
        with open(log_file, 'r') as f:
            output = f.read()

        # Verify error handling
        assert result.returncode == 1
        assert "Error: No inventory file specified" in output
        assert "Command Help:" in output
        assert "💡" in output

    finally:
        # Cleanup
        if os.path.exists(log_file):
            os.unlink(log_file)
```

### **Testing Requirements:**

- **ALWAYS use pytest CLI**: `pytest tests/cmd/ -v`
- **NEVER use VS Code integrated terminal** (it hangs from time to time)
- **Use log file redirection pattern** for CLI output testing
- **Test timeout**: Set 30-second timeout for subprocess calls

### **Success Criteria:**

- ✅ Comprehensive test coverage for all error scenarios
- ✅ UX consistency verification tests
- ✅ Proper testing patterns implemented
- ✅ All tests pass reliably
- ✅ Performance testing shows no degradation
- ✅ **GitHub comment posted with proper author identification**

### **Files to Create/Modify:**

- `tests/cmd/test_ops_validate_errors.py` (comprehensive error tests)
- `tests/cmd/test_error_patterns.py` (consistency tests)
- Update existing test files as needed

---

## 📋 **Phase 5: Final Integration and Documentation**

### **Your Mission:**

Ensure all components work together seamlessly and provide proper documentation for the implementation.

### **Specific Tasks:**

1. **Integration Testing**:

   - Test the complete workflow from start to finish
   - Verify that all phases work together correctly
   - Ensure no breaking changes to existing functionality

2. **Documentation Updates**:

   - Update command help text with better examples
   - Add inventory setup examples to ops validate help
   - Include environment variable usage examples

3. **Performance Verification**:
   - Ensure early validation doesn't impact command startup time
   - Verify that valid operations work exactly as before
   - Test memory usage and performance characteristics

### **Testing Requirements:**

- **End-to-end testing**: Test complete user workflows
- **Regression testing**: Ensure existing functionality unchanged
- **Performance testing**: Verify no performance degradation

### **Success Criteria:**

- ✅ All phases integrated successfully
- ✅ No breaking changes to existing functionality
- ✅ Documentation is updated and clear
- ✅ Performance characteristics maintained
- ✅ Complete test suite passes
- ✅ **GitHub comment posted with proper author identification**

### **Files to Review/Update:**

- All modified files from previous phases
- Documentation and help text
- Test suite comprehensive review

---

## 📋 **Universal Testing Guidelines**

### **Critical Testing Requirements:**

```bash
# ✅ CORRECT - Use pytest CLI directly
pytest tests/cmd/test_ops_validate_errors.py -v

# ❌ WRONG - Don't use VS Code integrated test terminal
# (it hangs from time to time)
```

### **CLI Output Testing Pattern:**

```bash
# ✅ CORRECT - Redirect output to log file and read contents
uv run gnmibuddy.py ops validate --devices device1,device2 > test_output.log 2>&1
# Then read and verify test_output.log contents

# ❌ WRONG - Don't rely on terminal output directly
# (terminal gets cut off and won't show all output)
```

### **Test File Template:**

Create test files that follow this pattern:

- Use subprocess with proper timeout (30 seconds)
- Redirect all output to temporary log files
- Read and verify log file contents
- Always clean up temporary files
- Assert proper exit codes and error messages

---

## 🎯 **Final Implementation Notes**

### **Remember:**

1. **Scope**: Only modify `ops validate` command, leave other commands unchanged
2. **Pattern**: Follow the same error handling pattern as `inventory validate` command
3. **Testing**: Always use pytest CLI and log file redirection
4. **Communication**: Update issue #10 with progress and completion status
5. **Quality**: Ensure all tests pass before marking phase complete

### **GitHub Comment Format Example:**

When posting completion comments to issue #10, use this format:

```markdown
# Phase [X] Complete - [Phase Name]

_Implemented by: [Your Agent Name/ID] - [Date]_

## Summary

[Brief 2-3 sentence summary of what was implemented]

## Key Changes

- [Bullet point of main change 1]
- [Bullet point of main change 2]

## Testing

- [Testing approach used]
- [Test results summary]

## Notes

[Any important considerations or recommendations for subsequent phases]
```

### **Success Indicators:**

- User sees friendly error message instead of logging cascade
- Command fails fast on configuration errors
- Help text appears automatically on errors
- Exit codes are correct (1 for errors)
- All tests pass using proper testing patterns
