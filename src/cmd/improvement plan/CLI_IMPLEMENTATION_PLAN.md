# gNMIBuddy CLI Improvement Implementation Plan

## Overview

An analysis on the existing gNMIBuddy CLI revealed that it has a flat command structure, which can be improved by implementing a hierarchical command structure. Review the [improvement plan](/src/cmd/improvement%20plan/Improvement_plan.md) for more context on the original request.

You can also find a summary of the implementation plan in [CLI_IMPLEMENTATION_SUMMARY.md](/src/cmd/improvement%20plan/CLI_IMPLEMENTATION_SUMMARY.md).

This plan implements the CLI improvements outlined in the improvement plan, restructuring the CLI from a flat command structure to a hierarchical, user-friendly interface. The implementation is divided into 5 phases, each with specific goals and test requirements.

## Phase 0: Framework Migration and Foundation Modernization

### Goals

1. Create a new implementation for the cli architecture.
2. Don't keep backwards compatibiltiy with the cmd module, however, the new architecture must work with the rest of the existings modules.
3. Migrate from argparse to Click framework for better CLI architecture
4. Implement proper dependency injection and service layer patterns
5. Create command objects that encapsulate behavior and data (following Martin Fowler's principles)
6. Establish type safety and validation throughout the CLI
7. Set up modern testing infrastructure with Click's testing utilities

### Success Criteria

- [ ] All existing commands migrated to Click framework
- [ ] Command classes follow object-oriented design principles
- [ ] Type hints and validation implemented throughout
- [ ] Dependency injection pattern established
- [ ] Test infrastructure modernized with Click testing utilities
- [ ] All existing functionality preserved during migration
- [ ] Performance improved or maintained

### Technical Implementation

**Framework Choice: Click**

- Mature, battle-tested framework used by major projects (Flask, Pip, etc.)
- Excellent support for nested commands and complex CLIs
- Superior testing utilities and documentation
- Better error handling and user experience
- Extensible plugin system

**Architecture Changes:**

- Replace `BaseCommand` with Click command groups and decorators
- Implement service layer pattern for business logic
- Create command context objects for dependency injection
- Establish clear separation between CLI layer and business logic

### Test Requirements

- Migration compatibility tests ensuring no functionality is lost
- Click-specific testing patterns implementation
- Type safety verification tests
- Performance benchmarking tests
- Integration tests for the new architecture

**Testing Instructions:**

- Use pytest CLI directly: `pytest tests/cmd/test_migration.py -v`
- DO NOT use VS Code integrated test terminal (it may hang)
- Save test output to file: `pytest tests/cmd/test_migration.py -v > test_output.log 2>&1`
- Test CLI compatibility: `uv run gnmibuddy.py --help > migration_test.log 2>&1`
- Verify all commands work: `uv run gnmibuddy.py routing --device R1 > routing_migration_test.log 2>&1`

### Expected Deliverables

1. Updated pyproject.toml with Click dependency
2. Migrated command structure using Click groups and decorators
3. Service layer implementation with dependency injection
4. Type-safe command interfaces with validation
5. Modern testing infrastructure with Click test utilities
6. Migration compatibility tests
7. Updated documentation for new architecture

---

## Phase 1: Hierarchical Command Structure Implementation

### Phase 1 Goals

1. Implement hierarchical command structure using Click's command groups
2. Create command grouping system (device, network, topology, ops, manage)
3. Update existing command names to follow consistent kebab-case naming
4. Implement nested command structure with proper organization

### Phase 1 Success Criteria

- [ ] Commands are properly organized into logical groups using Click groups
- [ ] All command names follow consistent kebab-case convention
- [ ] Nested command structure is implemented (e.g., `gnmibuddy device info`)
- [ ] All existing functionality works within the new hierarchical structure
- [ ] Commands are properly grouped by category
- [ ] Backward compatibility is maintained where possible

### Phase 1 Test Requirements

- CLI structure tests verify command grouping
- Command naming convention tests
- Backward compatibility tests
- Help system structure tests

**Testing Instructions:**

- Use pytest CLI directly: `pytest tests/cmd/test_cli_structure.py -v`
- DO NOT use VS Code integrated test terminal (it may hang)
- Save test output to file: `pytest tests/cmd/test_cli_structure.py -v > test_output.log 2>&1`
- Inspect the log file to verify all tests pass

### Phase 1 Expected Deliverables

1. Click-based command groups for hierarchical organization
2. Refactored commands using Click decorators and groups
3. Updated command names following kebab-case convention
4. Hierarchical command structure (device, network, topology, ops, manage)
5. CLI structure tests suite for Click-based commands
6. Updated documentation for new command structure

---

## Phase 2: Help System Enhancement and User Experience

### Goals

1. Implement grouped help system with progressive disclosure
2. Remove ASCII banner from subcommand help
3. Add usage examples to command help
4. Implement command aliases
5. Improve error messages with suggestions

### Success Criteria

- [ ] Help system shows commands grouped by category
- [ ] Banner only appears on top-level help
- [ ] Each command has usage examples in help text
- [ ] Command aliases work correctly
- [ ] Error messages provide helpful suggestions
- [ ] "Did you mean?" functionality for typos

### Test Requirements

- Help system output tests
- Command alias resolution tests
- Error message quality tests
- Usage example presence tests

**Testing Instructions:**

- Use pytest CLI directly: `pytest tests/cmd/test_help_system.py -v`
- DO NOT use VS Code integrated test terminal (it may hang)
- Save test output to file: `pytest tests/cmd/test_help_system.py -v > test_output.log 2>&1`
- Inspect the log file to verify all tests pass

### Expected Deliverables

1. Enhanced help formatter with command grouping
2. Command alias system
3. Improved error handling with suggestions
4. Usage examples for all commands
5. Help system tests suite

---

## Phase 3: Testing Infrastructure for CLI Design Compliance

### Goals

1. Create comprehensive test suite for CLI design compliance
2. Implement tests that verify command structure adherence
3. Create tests for help system consistency
4. Implement tests for naming conventions
5. Create automated checks for CLI best practices

### Success Criteria

- [ ] All commands follow the established hierarchical structure
- [ ] Help system consistency is automatically verified
- [ ] Naming conventions are enforced through tests
- [ ] CLI best practices are tested and enforced
- [ ] Future command additions are automatically validated

### Test Requirements

- CLI design compliance test suite
- Command structure validation tests
- Help system consistency tests
- Naming convention enforcement tests
- CLI best practices verification tests

**Testing Instructions:**

- Use pytest CLI directly: `pytest tests/cmd/ -v`
- DO NOT use VS Code integrated test terminal (it may hang)
- Save test output to file: `pytest tests/cmd/ -v > test_output.log 2>&1`
- Inspect the log file to verify all tests pass

### Expected Deliverables

1. Comprehensive CLI design compliance test suite
2. Automated command structure validation
3. Help system consistency checks
4. Naming convention enforcement
5. CLI best practices verification framework

---

## Phase 4: Advanced Features and Final Polish

### Goals

1. Implement output formatting options (json, table, yaml)
2. Add version flag and improved version information
3. Implement shell completion support
4. Add batch operations support
5. Final polish and optimization

### Success Criteria

- [ ] Multiple output formats work correctly
- [ ] Version information is comprehensive
- [ ] Shell completion works in common shells
- [ ] Batch operations are functional
- [ ] All CLI improvements are integrated seamlessly

### Test Requirements

- Output format tests
- Version information tests
- Shell completion tests
- Batch operation tests
- Integration tests for all features

**Testing Instructions:**

- Use pytest CLI directly: `pytest tests/cmd/test_advanced_features.py -v`
- DO NOT use VS Code integrated test terminal (it may hang)
- Save test output to file: `pytest tests/cmd/test_advanced_features.py -v > test_output.log 2>&1`
- Inspect the log file to verify all tests pass

### Expected Deliverables

1. Multiple output format support
2. Enhanced version information
3. Shell completion scripts
4. Batch operation functionality
5. Complete integration test suite

---

## LLM Agent Prompts

### Phase 0 Agent Prompt

````
You are a senior Python developer tasked with migrating the gNMIBuddy CLI from argparse to the Click framework. Your goal is to modernize the CLI architecture while maintaining all existing functionality and establishing a solid foundation for future improvements.

CURRENT STATE:
The CLI uses argparse with a custom BaseCommand class and has these commands: routing, interface, mpls, vpn, system, deviceprofile, topology-adjacency, topology-neighbors, logging, list-devices, list-commands, test-all, log-level

You must:
1. Create a new implementation for the cli architecture.
2. Don't keep backwards compatibiltiy with the cmd module, this must be a new, clean architecture that is not influence by the previous one. You can create new clases with new names/methods as you see fit. however, the new architecture must work with the rest of the existings modules.

TASKS:
1. Framework Migration
   - Replace argparse-based system with Click framework
   - Migrate all existing commands to Click command decorators
   - Maintain 100% backward compatibility for all existing functionality

2. Architecture Modernization
   - Implement service layer pattern for business logic separation
   - Create command context objects for dependency injection
   - Establish type safety with proper type hints throughout
   - Implement proper error handling using Click's built-in capabilities

3. Object-Oriented Design (Following Martin Fowler's Principles)
   - Create command classes that encapsulate behavior and data
   - Implement proper separation of concerns
   - Use composition over inheritance where appropriate
   - Apply dependency injection patterns

4. Testing Infrastructure
   - Set up Click's testing utilities (CliRunner)
   - Create compatibility tests ensuring no functionality is lost
   - Implement type safety verification tests
   - Add performance benchmarking tests

FILES TO MODIFY:
- pyproject.toml: Add Click dependency
- src/cmd/base.py: Replace BaseCommand with Click-based architecture
- src/cmd/parser.py: Migrate to Click's command system
- src/cmd/commands.py: Convert all commands to Click decorators
- tests/cmd/test_migration.py: Create migration compatibility tests
- src/cmd/context.py: Create command context system for dependency injection

SUCCESS CRITERIA:
- All existing CLI functionality works identically
- Commands maintain same interface and behavior
- Type safety is improved throughout
- Testing is more robust and maintainable
- Architecture follows modern best practices
- Performance is maintained or improved

TESTING AND EXECUTION:
- Run tests using pytest CLI: `pytest tests/cmd/test_migration.py -v > test_output.log 2>&1`
- DO NOT use VS Code integrated test terminal (it may hang)
- Test CLI compatibility: `uv run gnmibuddy.py --help > migration_test.log 2>&1`
- Verify all commands work: `uv run gnmibuddy.py routing --device R1 > routing_migration_test.log 2>&1`
- Test all existing commands: `uv run gnmibuddy.py list-commands > commands_test.log 2>&1`
- Save all command outputs to log files and inspect them afterward

EXPECTED CLICK STRUCTURE:
```python
import click

@click.group()
@click.pass_context
def cli(ctx):
    """gNMIBuddy CLI tool"""
    ctx.ensure_object(dict)

@cli.command()
@click.option('--device', required=True, help='Device name')
@click.option('--protocol', help='Routing protocol filter')
@click.option('--detail', is_flag=True, help='Show detailed information')
def routing(device, protocol, detail):
    """Get routing information from a network device"""
    # Implementation here
````

Focus on creating a solid, modern foundation that will support all future CLI improvements.

```

### Phase 1 Agent Prompt

```

You are a senior Python developer tasked with implementing a hierarchical command structure in the gNMIBuddy CLI using Click framework. Your goal is to organize the migrated commands into logical groups and create an intuitive command hierarchy.

PREREQUISITES:

- Phase 0 completed: CLI migrated to Click framework
- All commands working with Click decorators and groups
- Service layer and dependency injection established

CURRENT STATE:
The CLI commands are migrated to Click but still flat: routing, interface, mpls, vpn, system, device-profile, topology-adjacency, topology-neighbors, logging, list-devices, list-commands, test-all, log-level

TASKS:

1. Implement Command Groups
   Create Click command groups for logical organization:

   - device: system info, device-profile, list-devices
   - network: routing, interface, mpls, vpn
   - topology: topology-adjacency, topology-neighbors
   - ops: logging, test-all
   - manage: log-level, list-commands

2. Create Hierarchical Structure
   Transform flat commands into nested structure:

   - gnmibuddy device info --device R1 (was: system)
   - gnmibuddy device profile --device R1 (was: device-profile)
   - gnmibuddy device list (was: list-devices)
   - gnmibuddy network routing --device R1 (was: routing)
   - gnmibuddy network interface --device R1 (was: interface)
   - gnmibuddy topology neighbors --device R1 (was: topology-neighbors)
   - gnmibuddy ops logs --device R1 (was: logging)
   - gnmibuddy manage log-level show (was: log-level)

3. Maintain Backward Compatibility
   - Add aliases for old command names where possible
   - Ensure existing scripts continue to work
   - Document migration path for users

FILES TO MODIFY:

- src/cmd/commands.py: Organize commands into Click groups
- src/cmd/parser.py: Update main CLI group structure
- tests/cmd/test_cli_structure.py: Create hierarchical structure tests
- src/cmd/groups.py: Create command group definitions

SUCCESS CRITERIA:

- Commands are organized in logical hierarchical groups
- New nested command structure works properly
- All existing functionality preserved
- Backward compatibility maintained where possible
- Tests verify the new structure

TESTING AND EXECUTION:

- Run tests using pytest CLI: `pytest tests/cmd/test_cli_structure.py -v > test_output.log 2>&1`
- Test new hierarchical structure: `uv run gnmibuddy.py device --help > device_help.log 2>&1`
- Test nested commands: `uv run gnmibuddy.py device info --device R1 > device_info_test.log 2>&1`
- Test backward compatibility: `uv run gnmibuddy.py routing --device R1 > routing_compat_test.log 2>&1`
- Save all command outputs to log files and inspect them afterward

EXPECTED CLICK GROUP STRUCTURE:

```python
@click.group()
def cli():
    """gNMIBuddy CLI tool"""
    pass

@cli.group()
def device():
    """Device management commands"""
    pass

@device.command('info')
@click.option('--device', required=True, help='Device name')
def device_info(device):
    """Get system information from a network device"""
    # Implementation here

@cli.group()
def network():
    """Network protocol commands"""
    pass

@network.command('routing')
@click.option('--device', required=True, help='Device name')
def network_routing(device):
    """Get routing information from a network device"""
    # Implementation here
```

Focus on creating an intuitive, well-organized command hierarchy that follows CLI best practices.

```

### Phase 2 Agent Prompt

```

You are a UX-focused Python developer tasked with enhancing the gNMIBuddy CLI help system and user experience. Your goal is to create an intuitive, well-organized help system that follows CLI best practices.

PREREQUISITES:

- Phase 1 completed with hierarchical command structure
- Commands are grouped: device, network, topology, ops, manage

TASKS:

1. Enhanced Help System

   - Implement grouped help that shows commands organized by category
   - Remove ASCII banner from subcommand help (show only on main help)
   - Add progressive disclosure (group help → command help → detailed help)
   - Implement custom help formatter in src/cmd/display.py

2. Add Usage Examples

   - Add comprehensive usage examples to each command
   - Include common use cases and parameter combinations
   - Show examples in help text for each command

3. Implement Command Aliases

   - Add short aliases: d for device, n for network, t for topology, o for ops, m for manage
   - Implement alias resolution in parser
   - Document aliases in help system

4. Improve Error Messages

   - Implement "Did you mean?" functionality for typos
   - Add helpful suggestions for common mistakes
   - Provide context-aware error messages
   - Create error handler in src/cmd/error_handler.py

5. Create Help System Tests
   Create tests/cmd/test_help_system.py that verify:
   - Help output is properly grouped
   - Banner only appears on main help
   - Usage examples are present for all commands
   - Command aliases work correctly
   - Error messages provide helpful suggestions

FILES TO MODIFY:

- src/cmd/display.py: Enhanced help formatter
- src/cmd/parser.py: Add alias support and improved error handling
- src/cmd/error_handler.py: Create error handling system
- src/cmd/commands.py: Add usage examples to commands
- tests/cmd/test_help_system.py: Create help system tests

SUCCESS CRITERIA:

- Help system shows clean, organized output
- Banner clutter is eliminated from subcommands
- All commands have helpful usage examples
- Command aliases work seamlessly
- Error messages guide users effectively
- Tests verify help system quality

TESTING AND EXECUTION:

- Run tests using pytest CLI: `pytest tests/cmd/test_help_system.py -v > test_output.log 2>&1`
- DO NOT use VS Code integrated test terminal (it may hang)
- Test help system using: `uv run gnmibuddy.py --help > main_help.log 2>&1`
- Test group help: `uv run gnmibuddy.py device --help > device_help.log 2>&1`
- Test command help: `uv run gnmibuddy.py device info --help > device_info_help.log 2>&1`
- Test aliases: `uv run gnmibuddy.py d info --help > alias_test.log 2>&1`
- Test error messages: `uv run gnmibuddy.py invalid-command > error_test.log 2>&1`
- Save all outputs to log files and inspect them afterward

EXPECTED HELP OUTPUT:
$ gnmibuddy --help
[ASCII Banner]
Device Information:
device (d) Device management commands
Network Protocols:
network (n) Network protocol commands
Topology:
topology (t) Network topology commands
Operations:
ops (o) Operational commands
Management:
manage (m) Management commands

Focus on creating a smooth, intuitive user experience that guides users naturally through the CLI.

```

### Phase 3 Agent Prompt

```

You are a test automation specialist tasked with creating a comprehensive test suite for CLI design compliance. Your goal is to ensure that the gNMIBuddy CLI follows established design patterns and that future changes maintain these standards.

PREREQUISITES:

- Phase 1 and 2 completed
- CLI has hierarchical structure with enhanced help system
- Commands are grouped and have aliases

TASKS:

1. CLI Design Compliance Tests
   Create tests/cmd/test_cli_design_compliance.py with tests that verify:

   - All commands follow the established hierarchical structure
   - Command names use consistent kebab-case convention
   - All commands belong to appropriate groups
   - Command descriptions and help text meet quality standards

2. Help System Consistency Tests
   Create tests/cmd/test_help_consistency.py with tests that verify:

   - Help output format is consistent across all commands
   - Usage examples are present and properly formatted
   - Command grouping is displayed correctly
   - Banner appears only on main help

3. Command Structure Validation
   Create tests/cmd/test_command_structure.py with tests that verify:

   - All commands inherit from BaseCommand properly
   - Required attributes (name, help, description, group) are present
   - Command registration works correctly
   - Aliases are properly configured

4. Naming Convention Enforcement
   Create tests/cmd/test_naming_conventions.py with tests that verify:

   - All command names follow kebab-case convention
   - Group names are consistent
   - Aliases follow naming patterns
   - File and class names follow Python conventions

5. CLI Best Practices Verification
   Create tests/cmd/test_cli_best_practices.py with tests that verify:

   - Commands provide helpful error messages
   - Long-running commands have appropriate feedback
   - Output formatting is consistent
   - Command line parsing follows standards

6. Future-Proofing Tests
   Create tests that will catch violations when new commands are added:
   - Automatic validation of new commands
   - Integration with CI/CD pipeline
   - Comprehensive coverage reports

FILES TO CREATE:

- tests/cmd/test_cli_design_compliance.py
- tests/cmd/test_help_consistency.py
- tests/cmd/test_command_structure.py
- tests/cmd/test_naming_conventions.py
- tests/cmd/test_cli_best_practices.py
- tests/cmd/conftest.py: Test fixtures and utilities
- tests/cmd/test_utils.py: Test helper functions

SUCCESS CRITERIA:

- All CLI design patterns are automatically verified
- Tests catch violations early in development
- Future command additions are automatically validated
- Test coverage is comprehensive and maintainable
- Tests integrate well with existing test suite

TESTING AND EXECUTION:

- Run tests using pytest CLI: `pytest tests/cmd/ -v > test_output.log 2>&1`
- DO NOT use VS Code integrated test terminal (it may hang)
- Run specific test suites: `pytest tests/cmd/test_cli_design_compliance.py -v > compliance_test.log 2>&1`
- Test command structure: `pytest tests/cmd/test_command_structure.py -v > structure_test.log 2>&1`
- Test naming conventions: `pytest tests/cmd/test_naming_conventions.py -v > naming_test.log 2>&1`
- Verify CLI still works: `uv run gnmibuddy.py --help > final_cli_test.log 2>&1`
- Save all outputs to log files and inspect them afterward

EXAMPLE TEST STRUCTURE:

```python
def test_all_commands_have_proper_structure():
    """Test that all commands follow the established structure."""
    for command in get_all_commands():
        assert hasattr(command, 'name')
        assert hasattr(command, 'help')
        assert hasattr(command, 'group')
        assert command.name.replace('-', '').islower()

def test_command_names_follow_kebab_case():
    """Test that all command names use kebab-case convention."""
    for command in get_all_commands():
        assert re.match(r'^[a-z]+(-[a-z]+)*$', command.name)
```

Focus on creating tests that will maintain CLI quality as the codebase evolves.

```

### Phase 4 Agent Prompt


```

You are a senior Python developer tasked with implementing advanced CLI features and final polish for gNMIBuddy. Your goal is to add modern CLI capabilities and ensure the tool provides an excellent user experience.

PREREQUISITES:

- Phases 1-3 completed
- CLI has hierarchical structure, enhanced help system, and comprehensive tests

- Design compliance is enforced through automated tests

TASKS:

1. Output Formatting Options

   - Implement --output flag with choices: json, table, yaml
   - Add output formatters in src/cmd/formatters.py
   - Ensure all commands support multiple output formats
   - Add pretty-printing and proper formatting

2. Enhanced Version Information

   - Add --version flag (shorthand -V)
   - Display Python version, gNMIBuddy version, and dependencies
   - Add version information to help output
   - Include build information if available

3. Shell Completion Support

   - Implement bash completion in completions/gnmibuddy-completion.bash
   - Add zsh completion in completions/gnmibuddy-completion.zsh
   - Create completion generation command
   - Add installation instructions

4. Batch Operations Support

   - Implement --devices flag for multiple devices
   - Add support for device list files
   - Implement parallel execution for batch operations
   - Add progress indicators for long operations

5. Final Polish and Optimization

   - Optimize command loading and execution
   - Add performance monitoring
   - Improve error handling edge cases
   - Add comprehensive logging

6. Integration Tests
   Create tests/cmd/test_advanced_features.py with tests for:

   - Output formatting works correctly
   - Version information is accurate
   - Shell completion generates properly

   - Batch operations function correctly
   - Performance meets requirements

FILES TO MODIFY/CREATE:

- src/cmd/formatters.py: Output formatting system
- src/cmd/version.py: Enhanced version handling
- src/cmd/batch.py: Batch operations support
- completions/gnmibuddy-completion.bash: Bash completion

- completions/gnmibuddy-completion.zsh: Zsh completion
- tests/cmd/test_advanced_features.py: Advanced feature tests
- tests/cmd/test_integration.py: Full integration tests

SUCCESS CRITERIA:

- Multiple output formats work seamlessly
- Version information is comprehensive and accurate
- Shell completion works in bash and zsh

- Batch operations are efficient and reliable
- All features integrate well together
- Performance is optimized
- Tests verify all advanced features

TESTING AND EXECUTION:

- Run tests using pytest CLI: `pytest tests/cmd/test_advanced_features.py -v > test_output.log 2>&1`
- DO NOT use VS Code integrated test terminal (it may hang)
- Test output formatting: `uv run gnmibuddy.py device info --device R1 --output json > json_test.log 2>&1`
- Test version info: `uv run gnmibuddy.py --version > version_test.log 2>&1`
- Test batch operations: `uv run gnmibuddy.py device info --devices R1,R2 > batch_test.log 2>&1`
- Test shell completion: `bash completions/gnmibuddy-completion.bash > completion_test.log 2>&1`
- Run integration tests: `pytest tests/cmd/test_integration.py -v > integration_test.log 2>&1`
- Save all outputs to log files and inspect them afterward

EXPECTED ADVANCED FEATURES:

- Multiple output formats (json, table, yaml)

- Comprehensive version information
- Shell completion for bash and zsh
- Batch operations with parallel execution
- Enhanced error handling with suggestions
- Performance optimization

Focus on creating a polished, professional CLI tool that provides excellent user experience and follows modern CLI best practices.

````

---

## Testing Strategy for CLI Design Compliance

### Overview

Testing CLI design compliance requires verifying that the CLI follows established patterns and provides a consistent user experience. This is different from traditional unit testing as it focuses on design patterns, user experience, and structural consistency.

### Test Categories

#### 1. Structural Tests
Verify the basic structure and organization of the CLI:

```python
def test_command_hierarchy():
    """Test that commands are properly organized in hierarchy."""


def test_command_registration():
    """Test that all commands are registered correctly."""

def test_command_groups():
    """Test that commands belong to appropriate groups."""
````

#### 2. Naming Convention Tests

Enforce consistent naming patterns:

```python
def test_kebab_case_commands():
    """Test that all command names use kebab-case."""


def test_consistent_group_names():
    """Test that group names are consistent."""

def test_alias_patterns():
    """Test that aliases follow naming patterns."""
```

#### 3. Help System Tests

Verify the help system provides consistent, useful information:

```python
def test_help_output_format():

    """Test that help output follows consistent format."""

def test_usage_examples_present():
    """Test that all commands have usage examples."""

def test_command_grouping_display():
    """Test that commands are properly grouped in help."""
```

#### 4. User Experience Tests

Verify the CLI provides a good user experience:

```python
def test_error_message_quality():
    """Test that error messages are helpful and actionable."""

def test_command_aliases_work():
    """Test that command aliases function correctly."""

def test_progressive_disclosure():
    """Test that help system provides progressive disclosure."""
```

### Implementation Strategy

#### Using pytest for CLI Testing

```python
# tests/cmd/conftest.py
import pytest
from unittest.mock import Mock
from src.cmd.parser import create_parser

@pytest.fixture
def cli_parser():
    """Provide a CLI parser for testing."""
    return create_parser()

@pytest.fixture
def mock_device_response():
    """Mock device response for testing."""
    return {"status": "success", "data": {"device": "R1"}}

def get_all_commands():
    """Get all registered commands for testing."""
    # Implementation to discover all commands
    pass

def get_command_help(command_name):
    """Get help output for a specific command."""
    # Implementation to capture help output
    pass
```

#### Example Design Compliance Tests

```python
# tests/cmd/test_cli_design_compliance.py
import pytest
import re
from src.cmd.commands import COMMANDS

class TestCLIDesignCompliance:
    """Test suite for CLI design compliance."""

    def test_all_commands_have_required_attributes(self):
        """Test that all commands have required attributes."""
        for command_class in COMMANDS.values():
            command = command_class()
            assert hasattr(command, 'name')
            assert hasattr(command, 'help')
            assert hasattr(command, 'group')

    def test_command_names_follow_kebab_case(self):
        """Test that command names use kebab-case convention."""
        for command_class in COMMANDS.values():
            command = command_class()
            assert re.match(r'^[a-z]+(-[a-z]+)*$', command.name)

    def test_command_groups_are_valid(self):
        """Test that all commands belong to valid groups."""
        valid_groups = {'device', 'network', 'topology', 'ops', 'manage'}
        for command_class in COMMANDS.values():
            command = command_class()
            assert command.group in valid_groups

    def test_command_help_quality(self):
        """Test that command help text meets quality standards."""
        for command_class in COMMANDS.values():
            command = command_class()
            assert len(command.help) > 10
            assert not command.help.endswith('.')
```

### Summary

This testing strategy ensures that:

1. CLI structure is maintained as code evolves
2. User experience remains consistent
3. Design patterns are enforced automatically
4. New commands follow established conventions
5. Regressions are caught early

The tests run automatically in CI/CD and provide clear feedback when design compliance is violated.

---

## Critical Testing and Execution Instructions

### For All Phases - Testing Requirements

**Always use pytest CLI directly:**

```bash
pytest tests/cmd/test_*.py -v > test_output.log 2>&1
```

**Never use VS Code integrated test terminal** - it may hang or freeze.

**Always save test output to log files** and inspect them afterward to verify results.

### For All Phases - CLI Execution Requirements

**Always use `uv run` to execute the CLI:**

```bash
uv run gnmibuddy.py --help > cli_output.log 2>&1
```

**Never rely on terminal output directly** - it may get cut off or truncated.

**Always save CLI output to log files** and inspect them afterward.

### Verification Examples

**Testing Phase 0:**

```bash
pytest tests/cmd/test_migration.py -v > migration_test.log 2>&1
uv run gnmibuddy.py --help > cli_migration_help.log 2>&1
uv run gnmibuddy.py routing --device R1 > routing_migration_test.log 2>&1
```

**Testing Phase 1:**

```bash
pytest tests/cmd/test_cli_structure.py -v > test_output.log 2>&1
uv run gnmibuddy.py --help > cli_help.log 2>&1
uv run gnmibuddy.py device --help > device_help.log 2>&1
uv run gnmibuddy.py device info --device R1 > device_info_test.log 2>&1
```

**Testing Phase 2:**

```bash
pytest tests/cmd/test_help_system.py -v > test_output.log 2>&1
uv run gnmibuddy.py device info --help > command_help.log 2>&1
uv run gnmibuddy.py d info --help > alias_test.log 2>&1
```

**Testing Phase 3:**

```bash
pytest tests/cmd/ -v > all_tests.log 2>&1
uv run gnmibuddy.py --help > final_cli_check.log 2>&1
```

**Testing Phase 4:**

```bash
pytest tests/cmd/test_advanced_features.py -v > advanced_tests.log 2>&1
uv run gnmibuddy.py --version > version_test.log 2>&1
uv run gnmibuddy.py device info --device R1 --output json > json_test.log 2>&1
```

**Always inspect the log files** to verify everything works correctly before proceeding to the next phase.
