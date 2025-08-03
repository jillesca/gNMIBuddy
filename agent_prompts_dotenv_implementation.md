# Agent Prompts for Dotenv (.env) Support Implementation

## Important Instructions for All Agents

**MANDATORY FIRST STEP:** Before starting any work, you MUST read the comprehensive implementation plan in issue #25 comment "Comprehensive Updated Implementation Plan for Dotenv (.env) Support" by GitHub Copilot. This comment contains all the detailed requirements and specifications you need to follow.

**Repository:** jillesca/gNMIBuddy  
**Issue:** #25 - add Dotenv (.env) support  
**Plan Location:** Comment "Comprehensive Updated Implementation Plan for Dotenv (.env) Support"

### Universal Requirements for All Agents

1. **Read the implementation plan first** - It contains crucial technical details and requirements
2. **Stay in your phase scope** - Don't work outside your assigned phase
3. **Use proper testing commands**: `uv run gnmibuddy.py ...` with output captured to log files
4. **Use pytest CLI** instead of integrated test terminal: `pytest tests/ -v`
5. **Report opportunities** - If you find areas for improvement, note them but don't implement
6. **Update issue when done** - Add a short summary as a new comment to issue #25 after completion
7. **Document obstacles** - Report any challenges in the issue thread

---

## Phase 1: Create Centralized Environment Management with Pydantic Settings

### Agent Prompt for Phase 1

You are tasked with implementing **Phase 1** of the dotenv (.env) support feature for the gNMIBuddy project.

**MANDATORY:** First read the complete implementation plan in issue #25 comment "Comprehensive Updated Implementation Plan for Dotenv (.env) Support" to understand all requirements and technical specifications.

**Your Phase 1 Responsibilities:**

1. Create a centralized environment management system using **Pydantic Settings** (not python-dotenv)
2. Create `src/config/environment.py` with a comprehensive settings class
3. Support ALL environment variables mentioned in the plan
4. Integrate with (don't replace) existing `src/logging/config/environment.py`
5. Implement proper environment variable precedence: CLI args > OS env vars > .env file > defaults

**Key Technical Requirements from the Plan:**

- Use Pydantic Settings BaseSettings class
- Support custom .env file paths via `_env_file` parameter
- Include all variables: `NETWORK_INVENTORY`, `GNMIBUDDY_*` variables, `GNMIBUDDY_MCP_TOOL_DEBUG`
- Graceful handling of missing .env files
- Type-safe approach with validation
- Container-friendly design

**Testing Requirements:**

- Test with existing `.env` file in project root
- Test graceful handling when `.env` file is missing
- Test that existing logging functionality still works
- Use command: `uv run gnmibuddy.py device info --device R1 2>&1 | tee test_output.log`

**Deliverables:**

1. New file: `src/config/environment.py` with GNMIBuddySettings class
2. Proper integration with existing logging environment system
3. Test the implementation thoroughly
4. Document any issues or improvement opportunities

**When Complete:**
Add a brief summary comment to issue #25 with:

- What you implemented
- Any challenges encountered
- Any improvement opportunities noted
- Confirmation that tests pass

---

## Phase 2: Add --env-file CLI Option and Update Existing Options

### Agent Prompt for Phase 2

You are responsible for **Phase 2** of the dotenv (.env) support implementation for gNMIBuddy.

**MANDATORY:** First read the complete implementation plan in issue #25 comment "Comprehensive Updated Implementation Plan for Dotenv (.env) Support" to understand all requirements.

**Your Phase 2 Responsibilities:**

1. Add new `--env-file` / `-e` CLI option following existing patterns
2. Update existing CLI options to use Click's `envvar` parameter for automatic fallback
3. Integrate with the Pydantic Settings class created in Phase 1
4. Ensure proper precedence: CLI args override env vars override .env file values

**Specific Tasks:**

1. **Examine existing CLI patterns** in `src/cmd/parser.py` to follow the same style
2. **Add new option:**

   ```python
   @click.option(
       "-e",
       "--env-file",
       type=str,
       help="Path to .env file for configuration (default: .env in project root)"
   )
   ```

3. **Update existing options** with envvar parameters:
   - `--inventory` → add `envvar='NETWORK_INVENTORY'`
   - `--log-level` → add `envvar='GNMIBUDDY_LOG_LEVEL'`
   - `--structured-logging` → add `envvar='GNMIBUDDY_STRUCTURED_LOGGING'`
4. **Remove manual environment assignments** like `os.environ["NETWORK_INVENTORY"] = inventory`
5. **Integrate with Phase 1's centralized settings**

**Testing Requirements:**

- Test CLI with environment variable fallback: `export NETWORK_INVENTORY=xrd_sandbox.json && uv run gnmibuddy.py device info --device R1`
- Test custom env file: `uv run gnmibuddy.py --env-file custom.env device info --device R1`
- Test precedence: CLI args should override env vars and .env file values
- Capture all output to log files for inspection

**Prerequisites:**

- Phase 1 must be completed (centralized environment management exists)
- The Pydantic Settings class should be available for integration

**When Complete:**
Add a brief summary comment to issue #25 with:

- CLI options added/updated
- Integration with Phase 1 completed
- Test results and precedence verification
- Any issues encountered

---

## Phase 3: Refactor Existing Environment Variable Usage

### Agent Prompt for Phase 3

You are assigned **Phase 3** of the dotenv (.env) support implementation for gNMIBuddy.

**MANDATORY:** First read the complete implementation plan in issue #25 comment "Comprehensive Updated Implementation Plan for Dotenv (.env) Support" for full context and requirements.

**Your Phase 3 Responsibilities:**

1. Replace scattered `os.environ.get()` calls with centralized Pydantic Settings
2. Update specific files that currently use direct environment variable access
3. Ensure integration with existing logging environment system (don't break it)
4. Maintain backward compatibility

**Files to Modify:**

- `src/inventory/file_handler.py` - Update `get_inventory_path()` function
- `mcp_server.py` - Use centralized environment management
- Any other files with direct `os.environ.get()` calls
- **Integrate with (don't replace)** `src/logging/config/environment.py`

**Key Requirements from the Plan:**

- Replace direct `os.environ.get("NETWORK_INVENTORY")` calls
- Update `get_inventory_path()` to use new centralized approach
- Update MCP server environment variable usage
- Preserve existing logging environment functionality
- Maintain existing error handling and logging behavior
- Ensure no crashes if .env file is missing

**Testing Requirements:**

- Test that inventory file loading still works: `uv run gnmibuddy.py device info --device R1`
- Test MCP server functionality with environment variables
- Test that logging environment variables still work properly
- Verify backward compatibility with existing workflows
- Run existing test suite: `pytest tests/ -v`

**Prerequisites:**

- Phase 1 completed (centralized environment management available)
- Phase 2 completed (CLI options updated)

**When Complete:**
Add a brief summary comment to issue #25 with:

- Files modified and what was changed
- Confirmation that existing functionality is preserved
- Test results showing backward compatibility
- Any challenges or improvement opportunities

---

## Phase 4: Integration and Testing

### Agent Prompt for Phase 4

You are responsible for **Phase 4** - the final integration and testing phase of the dotenv (.env) support implementation.

**MANDATORY:** First read the complete implementation plan in issue #25 comment "Comprehensive Updated Implementation Plan for Dotenv (.env) Support" to understand all testing requirements.

**Your Phase 4 Responsibilities:**

1. Perform comprehensive integration testing across all components
2. Test all environment variable precedence scenarios
3. Test container-ready scenarios and missing .env file handling
4. Verify all success criteria from the implementation plan are met
5. Run complete test suite and create additional integration tests

**Comprehensive Testing Checklist:**

**Environment Variable Loading:**

- [ ] Test `.env` file loading for ALL supported variables
- [ ] Test missing `.env` file (should not crash)
- [ ] Test custom `.env` file with `--env-file` option
- [ ] Test graceful handling of malformed `.env` files

**Precedence Testing:**

- [ ] CLI arguments override environment variables
- [ ] OS environment variables override `.env` file values
- [ ] `.env` file values used when no CLI args or OS env vars
- [ ] Default values used when nothing else specified

**CLI Integration Testing:**

```bash
# Test commands from the implementation plan:
export GNMIBUDDY_LOG_LEVEL=debug
export NETWORK_INVENTORY=xrd_sandbox.json
uv run gnmibuddy.py device info --device R1 2>&1 | tee test_output.log

# Test custom .env file
echo "GNMIBUDDY_LOG_LEVEL=warning" > test.env
echo "NETWORK_INVENTORY=xrd_sandbox.json" >> test.env
uv run gnmibuddy.py --env-file test.env device info --device R1 2>&1 | tee test_custom_env.log

# Test missing .env file (should not crash)
mv .env .env.backup
uv run gnmibuddy.py device info --device R1 2>&1 | tee test_no_env.log
mv .env.backup .env

# Test precedence (CLI should override env file)
uv run gnmibuddy.py --inventory different.json device info --device R1 2>&1 | tee test_precedence.log
```

**Component Integration:**

- [ ] MCP server environment loading works
- [ ] Inventory file handling uses centralized system
- [ ] Logging environment integration preserved
- [ ] All existing functionality still works

**Test Suite:**

- [ ] Run existing tests: `pytest tests/ -v`
- [ ] Create integration tests for environment scenarios
- [ ] Test container scenarios (if applicable)

**Success Criteria Verification:**

- [ ] Single centralized Pydantic Settings class implemented
- [ ] `.env` file support for ALL environment variables
- [ ] New `--env-file` CLI option working
- [ ] Click `envvar` parameters implemented
- [ ] No direct `os.environ.get()` calls remain (except centralized)
- [ ] Existing logging functionality preserved
- [ ] Graceful handling of missing `.env` files
- [ ] Container-friendly precedence working
- [ ] All tests passing

**Prerequisites:**

- All previous phases (1-3) must be completed
- All components should be integrated

**When Complete:**
Add a comprehensive summary comment to issue #25 with:

- All testing completed successfully
- Confirmation that success criteria are met
- Any remaining issues or recommendations
- Overall assessment of the implementation

---

## Summary Template for All Agents

When you complete your phase, add a comment to issue #25 using this template:

```
## Phase [X] Complete - [Phase Name]

**Completed Work:**
- [Brief bullet points of what was implemented]

**Testing Results:**
- [Key test results and confirmations]

**Issues/Challenges:**
- [Any obstacles encountered - or "None"]

**Improvement Opportunities:**
- [Any areas for future enhancement - or "None identified"]

**Status:** ✅ Phase [X] completed successfully
```

---

**Note:** Each agent should focus ONLY on their assigned phase and avoid implementing features from other phases. The implementation plan in issue #25 contains all the detailed technical specifications needed for successful implementation.
