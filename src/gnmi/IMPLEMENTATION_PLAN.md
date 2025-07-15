# OpenConfig Capability Verification Implementation Plan

## Overview

This plan implements OpenConfig model capability verification for gNMIBuddy to ensure devices support the required `openconfig-network-instance` model with minimum version 1.3.0.

Original user request:

> my code has an external dependency, devices must support openconfig-network-instance and the code has been tested on 1.3.0 so equal or greater versions should work, however older versions I don't know. please help me to create a verification that should be done the ideally only the first time the gnmi client connects to the device, get the capabilities and review if the model is supported and the version. if the model is not supported at all, is not present, the client should return an ErrorResponse to the user that the model required is not avialable and tell the user which model and version onwards is supported. it should also print a log message and the script should stop, no more tries should continue. if the model is found but the version is older than the one I tested, it should inform the user is a form of log message to the screen and if possible somehow using the metada of the NetworkOperationResult object on #file:responses.py but not sure if thats possible. if the model and versions are supported, it should just log an entry informing the user that model and version are supported.

## Requirements Analysis

- **Required Model**: `openconfig-network-instance`
- **Minimum Version**: 1.3.0 (tested version)
- **Verification Timing**: First connection only (cached afterward)
- **Behavior on Failure**: Return ErrorResponse and stop execution
- **Behavior on Older Version**: Log warning and add to metadata
- **Behavior on Success**: Log success message

## Implementation Phases

### Phase 1: Core Capability Infrastructure

**Objective**: Create the foundation for capability checking

#### Tasks

1. **Create capability checker module** (`src/gnmi/capabilities.py`)

   - Implement `get_device_capabilities()` function
   - Parse gNMI capabilities response
   - Extract model names and versions
   - Handle capability request errors

2. **Create capability models** (`src/schemas/capabilities.py`)

   - Define `CapabilityInfo` dataclass
   - Define `ModelCapability` dataclass
   - Define capability-specific error types

3. **Create capability cache** (`src/utils/capability_cache.py`)

   - Implement in-memory cching per device

   - Cache successful verifications
   - Provide cache invalidation

#### Verification Criteria

- [ ] `get_device_capabilitie()` successfully retrieves capabilities

- [ ] Capability models are properly defined
- [ ] Cache stores and retrieves verification results
- [ ] Unit tests pass for all new components

#### Agent Prompt for Phase 1

```
You are implementing Phase 1 of the OpenConfig capability verification system.

TASKS:
1. Create `src/gnmi/capabilities.py` with:
   - `get_device_capabilities(device: Device) -> Union[SuccessResponse, ErrorResponse]`
   - Parse gNMI capabilities response to extract supported models and versions
   - Handle gRPC errors gracefully

2. Create `src/schemas/capabilities.py` with:
   - `CapabilityInfo` dataclass containing model name, version, and organization
   - `ModelCapability` dataclass for verification results
   - `CapabilityError` for capability-specific errors

3. Create `src/utils/capability_cache.py` with:
   - In-memory cache using device name as key
   - `is_device_verified(device_name: str) -> bool`
   - `cache_verification_result(device_name: str, result: bool)`
   - `invalidate_cache(device_name: str = None)`

VERIFICATION:
- Write unit tests for each component
- Test with actual device or mock gNMI responses
- Ensure proper error handling for network failures

- Document all public APIs

SCOPE: Do ot modify existing client.py or add integration yet.

```

### Phase 2: Capability Verification Logic

**Objective**: Implement the verification logic for openconfig-network-instance

#### Tasks

1. **Create version comparison utilities** (`src/utils/version_utils.py`)

   - Implement semantic version comparison
   - Handle version string parsing
   - Support different version formats

2. **Create verification service** (`src/services/capability_verification.py`)

   - Implement `verify_openconfig_network_instance()` function
   - Check model presence nd version

   - Generate appropriate responses and warnings
   - Handle edge cases (missing versions, malformed data)

3. **Enhance NetworkOperationResult metadata**
   - Add capability verification metadata fields
   - Include version warningsin metadata

#### Verification Criteria

- [ ] Version comparison works correctly (1.3.0 vs 1.2.9, 1.3.1, etc.)
- [ ] Verification service correctly identifies supported/unsupported devices
- [ ] Metadata properly reflects capability status
- [ ] Unit tests cover all version comparison scenarios

#### Agent Prompt for Phase 2

```
You are implementing Phase 2 of the OpenConfig capability verification system.

TASKS:
1. Create `src/utils/version_utils.py` with:
   - `compare_versions(version1: str, version2: str) -> int` (returns -1, 0, 1)
   - `parse_version_string(version: str) -> tuple` for semantic version parsing
   - Handle edge cases: missing versions, non-semantic versions

2. Create `src/services/capability_verification.py` with:
   - `verify_openconfig_network_instance(device: Device) -> Dict[str, Any]`
   - Check for "openconfig-network-instance" model presence
   - Verify version >= 1.3.0
   - Return verification result with warnings/errors

3. Enhance `NetworkOperationResult` metadata in `src/schemas/responses.py`:
   - Add `capability_verification` field to metadata
   - Include version warnings and compatibility info


VERIFICATION:
- Test version comparison with various version strings
- Test verfication with mock capability responses

- Ensure proper error messages for unsupported devices
- Test metadata enhancement

SCOPE: Focus on verification logic only, no integration with client yet.
```

### Phase 3: Client Integration

**Objective**: Integrate capability verification into the gNMI client

#### Tasks

1. **Enhance get_gnmi_data() function**

   - Add capability verification before first request
   - Use cache to avoid repeated checks
   - Handle verification filures gracefully

2. **Update error handling**

   - Add capability-specific error responses
   - Enhance logging for capability issues
   - Provide clear user feedback

3. **Create verification decoator/wrapper**

   - Implement `@verify_capabilities` decorator
   - Apply to relevant collector functions
   - Ensure single verification per device

#### Verification Criteria

- [ ] First gNMI request triggers capability verification
- [ ] Subsequent requests use cached results
- [ ] Capability failures return appropriate ErrorResponse
- [ ] Logging messages are clear and actionable
- [ ] No performance impact on verified devices

#### Agent Prompt for Phase 3

```
You are implementing Phase 3 of the OpenConfig capability verification system.

TASKS:
1. Modify `src/gnmi/client.py`:
   - Add capability verification to `get_gnmi_data()` function
   - Check cache first, then verify if needed
   - Return ErrorResponse if verification fails
   - Add version warnings to metadata if older version detected

2. Update error handling in `src/gnmi/error_handlers.py`:
   - Add `handle_capability_error()` function
   - Create appropriate error responses for capability failures
   - Include clear messages about required model and version

3. Create `src/decorators/capability_verification.py`:
   - Implement `@verify_capabilities` decorator

   - Apply to collector functions that need openconfig-network-instance
   - Ensure single verification per device per session


VERIFICATION:
- Test with devices that support openconfig-network-instance 1.3.0+
- Test with devices that don't support the model
- Test with devices that have older versions
- Verify logging messages are clear
- Test cache functionality

SCOPE: Focus on integration with existing client code.
```

### Phase 4: Testing and Documentation

**Objective**: Ensure robust testing and clear documentation

#### Tasks

1. **Create comprehensive test suite**

   - Unit tests for all ne components

   - Integration tests with mock devices
   - Edge case testing (network failures, malformed responses)
   - Performance testing (cache efficiency)

2. **Update documentation**

   - Add capability requiremets to README

   - Document new error scenarios
   - Update troubleshooting guide
   - Add example responses

3. **Create compatibility matrix**
   - Document tested device/version combinations
   - Add compatibility checking guidance
   - Update minimum requirements

#### Verification Criteria

- [ ] All tests pass including edge cases
- [ ] Documentation is comprehensive and clear
- [ ] Performance benchmarks meet expectations
- [ ] Error messages are user-friendly

#### Agent Prompt for Phase 4

```
You are implementing Phase 4 of the OpenConfig capability verification system.

TASKS:
1. Create comprehensive test suite in `tests/gnmi/`:
   - `test_capabilities.py` for capability checking
   - `test_version_utils.py` for version comparison
   - `test_capability_verification.py` for verification service
   - `test_client_integration.py` for client integration
   - Mock gNMI responses for testing

2. Update documentation:
   - Add capability requirements to README.md
   - Document new error types and troubleshooting
   - Update CLI help text with compatibility info
   - Add example error responses

3. Create `COMPATIBILITY.md`:
   - Document tested device/version combinations
   - Add compatibility matrix
   - Provide troubleshooting guide for capability issues

VERIFICATION:
- Run full test suite and ensure 100% pass rate
- Test documentation with fresh users
- Verify error messages are actionable
- Test with actual devices if possible

SCOPE: Focus on testing and documentation, no new functionality.
```

## Implementation Files Structure

```
src/
├── gnmi/
│   ├── capabilities.py           # New: Capability checking
│   ├── client.py                 # Modified: Add verification
│   └── error_handlers.py         # Modified: Add capability errors
├── schemas/
│   ├── capabilities.py           # New: Capability models
│   └── responses.py              # Modified: Add metadata fields
├── services/

│   └── capability_verification.py # New: Verification logic
├── utils/
│   ├── capability_cache.py       # New: Verification cache
│   └── version_utils.py          # New: Version comparison
├── decorators/

│   └── capability_verification.py # New: Verification decorator
tests/
├── gnmi/
│   ├── test_capabilities.py      # New: Capability tests
│   ├── testclient_integration.py # New: Integration tests

│   └── test_version_utils.py     # New: Version tests
└── services/
    └── test_capability_verification.py # New: Verification tests
```

## Risk Assessment

### High Risk

- **Network latency**: Capability requests add overhead to first connection
- **Device compatibility**: Some devices may not support capabilities properly
- **Version parsing**: Different vendors may use different version formats

### Medium Risk

- **Cache invalidation**: Need to handle device restarts/reconfigurations
- **Error handling**: Must gracefully handle partial capability responses
- **Performance**: Cache must be efficient for high-frequency operations

### Low Risk

- **Testing complexity**: Comprehensive testing requires multiple device types
- **Documentation**: Keeping compatibility matrix up-to-date

## Success Metrics

1. **Functionality**: 100% of unsupported devices correctly identified
2. **Performance**: < 500ms additional latency for first connection
3. **Reliability**: Zero false positives/negatives in capability detection
4. **Usability**: Clear error messages help users resolve issues quickly
5. **Maintainability**: New device support can be added without code changes

## Rollout Strategy

1. **Phase 1-2**: Internal testing with known devices
2. **Phase 3**: Integration testing with DevNet sandbox
3. **Phase 4**: Documentation and community testing
4. **Production**: Feature flag controlled rollout

## Agent Coordination

Each phase should be implemented by a separate agent or can be tackled sequentially. Agents should:

1. **Review prior phases** before starting their work
2. **Run verification criteria** before marking phase complete
3. **Document any deviations** from the plan
4. **Provide clear handoff** to next phase

The implementation should be backwards compatible and not break existing functionality.
