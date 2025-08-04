# Agent Implementation Prompts for Issue 19: Remove Sensitive Data from get_devices

## Required Reading

**MANDATORY**: Before starting any work, read the "Implementation Plan for Issue 19: Remove Sensitive Data from get_devices" comment in GitHub issue #19. This comment contains the complete technical analysis, requirements, and implementation strategy that must be followed.

## General Requirements for All Agents

### Core Principles

- **Use classes, not dictionaries**: All data must be encapsulated in classes with proper methods for data access. Do NOT use dictionaries for data encapsulation.
- **Phase-specific work**: Only work on your assigned phase. Do not implement features from other phases.
- **Report opportunities**: If you identify areas for improvement outside your phase scope, document them in the issue comments.
- **Testing protocol**: Use `uv run gnmibuddy.py ... > log_file.txt 2>&1` and inspect log files. Use `pytest` from CLI, not integrated test terminal.
- **Documentation**: Add a concise work summary comment to issue #19 upon completion.

### Software Engineering Standards

- Follow DRY, KISS, YAGNI, and SOLID principles
- Prioritize readability and modularity
- Maintain backward compatibility
- Ensure no performance degradation

---

## Phase 1 Agent Prompt: Core Infrastructure

### Your Mission

You are responsible for creating the core sanitization infrastructure. Your work enables the other phases but does NOT include API integration or CLI updates.

### Required Reading

1. Read the complete implementation plan in issue #19 comment "Implementation Plan for Issue 19: Remove Sensitive Data from get_devices"
2. Examine the current `Device` class in `src/schemas/models.py`
3. Review the existing `InventoryManager` class in `src/inventory/manager.py`

### Your Specific Tasks

#### Task 1: Create Inventory Data Sanitizer Class (`src/inventory/sanitizer.py`)

Create a new module with a `DeviceDataSanitizer` class that:

- **Uses classes for data encapsulation** (no dictionaries for structured data)
- Provides methods for different sanitization levels
- Follows single responsibility principle
- Implements the sanitization logic for sensitive fields:
  - `password`: Replace with `"***"`
  - `path_cert`: Replace with `"***"` (if present)
  - `path_key`: Replace with `"***"` (if present)
- Preserves all other fields unchanged
- Provides a clean interface for future extensibility

#### Task 2: Enhance Device Model (`src/schemas/models.py`)

Add sanitization methods to the existing `Device` class:

- `to_device_info_safe()`: Returns sanitized device information using classes
- `to_device_info_with_auth()`: Returns full device information (for future internal use)
- Maintain the existing `to_device_info()` method unchanged
- Use proper class-based data structures in return values

#### Task 3: Update Inventory Manager (`src/inventory/manager.py`)

Add a new method to `InventoryManager`:

- `list_devices_safe()`: Returns sanitized device list using the sanitizer
- Keep existing `list_devices()` method completely unchanged
- Ensure the new method uses class-based data structures
- Follow the existing code patterns and error handling

### What You Must NOT Do

- Do not modify `api.py` (Phase 2 responsibility)
- Do not modify CLI commands (Phase 2 responsibility)
- Do not create tests (Phase 3 responsibility)
- Do not use dictionaries for structured data encapsulation

### Validation Criteria

- Sanitizer class properly redacts sensitive fields
- Device model methods return class-based structures
- InventoryManager has new safe listing method
- All existing functionality remains unchanged
- No breaking changes to existing APIs

### Completion Requirements

1. Test your changes: `uv run python -c "from src.inventory.sanitizer import DeviceDataSanitizer; print('Import successful')"`
2. Test Device model: `uv run python -c "from src.schemas.models import Device; d=Device(); print(hasattr(d, 'to_device_info_safe'))"`
3. Test InventoryManager: `uv run python -c "from src.inventory.manager import InventoryManager; print(hasattr(InventoryManager, 'list_devices_safe'))"`
4. Add a comment to issue #19 summarizing your work and any observations

---

## Phase 2 Agent Prompt: API Integration

### Your Mission

You are responsible for integrating the sanitization infrastructure into the API and CLI layers. You build upon Phase 1's work but do NOT create tests.

### Required Reading

1. Read the complete implementation plan in issue #19 comment "Implementation Plan for Issue 19: Remove Sensitive Data from get_devices"
2. Verify Phase 1 is complete by checking for:
   - `src/inventory/sanitizer.py` exists
   - `Device.to_device_info_safe()` method exists
   - `InventoryManager.list_devices_safe()` method exists

### Your Specific Tasks

#### Task 1: Update API Layer (`api.py`)

Modify the `get_devices()` function to:

- Use the sanitized data from `InventoryManager.list_devices_safe()`
- Maintain the exact same return type contract (`DeviceListResult`)
- Ensure MCP server automatically inherits the sanitized behavior
- Use class-based data structures throughout

#### Task 2: Update CLI Command (`src/cmd/commands/device/list.py`)

Modify the `device_list` function to:

- Use sanitized data for `--detail` output via `InventoryManager.list_devices_safe()`
- Keep existing behavior for non-detail output unchanged
- Maintain backward compatibility with existing output formats
- Use class-based data structures in processing

#### Task 3: Verify MCP Server Integration

Ensure that:

- MCP server automatically uses the updated `api.get_devices()` function
- No direct changes to `mcp_server.py` should be needed
- The sanitization flows through the existing registration mechanism

### What You Must NOT Do

- Do not modify the sanitizer logic (Phase 1 responsibility)
- Do not create tests (Phase 3 responsibility)
- Do not use dictionaries for structured data encapsulation
- Do not break existing CLI output formats

### Validation Criteria

- `api.get_devices()` returns sanitized data
- CLI `--detail` flag shows redacted sensitive information
- CLI non-detail output remains unchanged
- MCP server shows sanitized data
- All existing functionality preserved

### Completion Requirements

1. Test CLI: `uv run gnmibuddy.py device list --detail > test_output.txt 2>&1` and verify sensitive data is redacted
2. Test CLI basic: `uv run gnmibuddy.py device list > test_basic.txt 2>&1` and verify normal operation
3. Verify no passwords or certificate paths appear in output files
4. Add a comment to issue #19 summarizing your integration work and any observations

---

## Phase 3 Agent Prompt: Testing & Validation

### Your Mission

You are responsible for creating comprehensive tests to validate the sanitization functionality and ensure no regressions. You do NOT modify implementation code.

### Required Reading

1. Read the complete implementation plan in issue #19 comment "Implementation Plan for Issue 19: Remove Sensitive Data from get_devices"
2. Verify Phases 1 and 2 are complete by checking the implementation
3. Examine existing test patterns in `tests/` directory

### Your Specific Tasks

#### Task 1: Unit Tests for Sanitization Logic

Create tests in `tests/inventory/`:

- `test_sanitizer.py`: Test the `DeviceDataSanitizer` class
  - Test sensitive data redaction
  - Test non-sensitive data preservation
  - Test class-based data structures
  - Test edge cases (None values, empty strings)

#### Task 2: Device Model Tests

Extend existing tests in `tests/schemas/` or create new ones:

- Test `Device.to_device_info_safe()` method
- Test `Device.to_device_info_with_auth()` method
- Verify class-based return structures
- Test backward compatibility of existing methods

#### Task 3: Integration Tests for CLI Command

Create tests in `tests/cmd/commands/device/`:

- Test CLI `device list --detail` output redaction
- Test CLI `device list` basic output unchanged
- Test class-based data handling in CLI processing
- Verify no sensitive data leakage in any output format

#### Task 4: Integration Tests for MCP Server

Create tests in `tests/` directory:

- Test `api.get_devices()` returns sanitized data
- Test MCP server tool registration works with sanitized data
- Verify class-based data structures throughout
- Test that MCP inherits sanitization automatically

#### Task 5: Regression Testing

Create or extend existing tests:

- Verify all existing functionality still works
- Test performance has not degraded
- Test error handling remains intact
- Verify backward compatibility

### What You Must NOT Do

- Do not modify implementation code (sanitizer, API, or CLI)
- Do not use dictionaries for test data structures where classes are appropriate
- Do not skip testing of edge cases

### Validation Criteria

- All tests pass with `pytest` from CLI
- Sensitive data redaction properly tested
- No regressions in existing functionality
- Class-based data structures properly tested
- Both CLI and MCP paths tested

### Completion Requirements

1. Run full test suite: `uv run pytest tests/ -v > test_results.txt 2>&1`
2. Verify no sensitive data appears in any test outputs
3. Ensure test coverage includes both CLI and MCP paths
4. Validate that all tests use appropriate class-based structures
5. Add a comment to issue #19 summarizing your testing work, coverage achieved, and any findings

---

## Common Issue Resolution

### If Phase 1 is Incomplete

Phase 2 and 3 agents should:

1. Document the missing components in issue #19
2. Do not proceed until Phase 1 is complete
3. Tag the issue for Phase 1 completion

### If Phase 2 is Incomplete

Phase 3 agent should:

1. Document the missing integration in issue #19
2. Create tests only for completed components
3. Note which tests cannot be completed until Phase 2 is done

### Data Structure Requirements

- **Never use plain dictionaries** for structured data that should be encapsulated in classes
- **Always use class methods** for data access and manipulation
- **Follow existing code patterns** for class design and method naming
- **Maintain type safety** with proper class-based return types

### Emergency Contacts

If you encounter blocking issues:

1. Document the specific problem in issue #19 comments
2. Include error messages, logs, and attempted solutions
3. Tag the issue for human review
4. Do not work around architectural decisions without approval

---

_Remember: Each phase builds upon the previous one. Stick to your phase responsibilities and communicate clearly about any issues or opportunities you discover._
