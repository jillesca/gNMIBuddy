# Agent Prompts: Issue #14 — Review if device supports models required

Use these prompts to guide LLM agents through a phased implementation of Issue #14. Each agent must:

- First, read the issue thread, especially the comment titled: “Implementation plan for ‘Review if device supports models required’ (Authored by GitHub Copilot)”.
- Also review the implementation plan on issue #14 for alignment.
- Work only on their assigned phase. No scope creep. If you identify improvements, add them as notes on the issue instead of implementing them.
- Do not use dictionaries to encapsulate related data and behavior. Use classes/dataclasses with methods for encapsulation and accessors.
- After finishing, add a short summary comment to issue #14 stating what you implemented and any relevant notes (keep it concise; do not restate the plan).
- When testing CLI, run with “uv run gnmibuddy.py …” and capture logs to a file for full output. For tests, run “pytest” via CLI.

Global engineering guardrails

- DRY, KISS, YAGNI, SOLID, modularity, readability (Zen of Python, Fowler refactoring).
- Prefer small files with single responsibility. Use directory hierarchy as proposed in the plan.
- Do not change public behavior beyond what the plan requires.
- Follow output flag conventions used by current CLI commands.

How to post your completion summary comment

- Keep it short. Example:
  - “Phase X complete: Implemented <module> with classes <A, B>. Added unit tests. CLI unaffected in this phase. Notes: <optional>.”

---

## Phase 0 — Context loading (read-only)

Prompt

- Read Issue #14 fully, focusing on the “Implementation plan … (Authored by GitHub Copilot)” comment.
- Read Issue #14 implementation plan.
- Skim the repo code paths mentioned in the plan to understand integration points (src/gnmi/client.py, src/gnmi/parameters.py, src/cmd/commands, collectors).
- Do not modify code in this phase.
- Post a brief comment on Issue #14 acknowledging context is understood and list any ambiguities found.

Verification

- None (read-only). Post the short comment.

---

## Phase 1 — Capabilities domain models (objects only)

Scope

- Create: src/gnmi/capabilities/models.py

Prompt

- Implement classes (no dicts-as-objects):
  - ModelIdentifier: name (str), version (str|None), organization (str|None). Methods: normalized_version(), matches(name: str) -> bool.
  - ModelRequirement: name (str), minimum_version (str|None). Methods: requires_version() -> bool.
  - DeviceCapabilities: models (list[ModelIdentifier]), encodings (list[str]), gnmi_version (str|None). Methods:
    - has_model(req: ModelRequirement, version_cmp: Callable) -> tuple[bool, bool] where returns (present, older_than_min).
    - supports_encoding(encoding: str, normalize: Callable) -> bool.
- Do not add external side effects. Keep types explicit and readable. Provide **repr**/**str** for developer clarity.
- Do not import pygnmi here. This is pure data/domain.

Constraints

- No dictionaries to encapsulate behavior; use classes and methods.

Verification

- Add minimal unit tests in tests/gnmi/capabilities/test_models.py for the objects’ basic behavior (constructors and method returns).

---

## Phase 2 — Version normalization and comparison

Scope

- Create: src/gnmi/capabilities/version.py

Prompt

- Implement NormalizedVersion class:
  - Accept common formats: semantic versions (e.g., 1.2.3), date-like (YYYY-MM-DD), or vendor strings.
  - Provide comparison operations (**, **lt**,**eq\_\_, etc.).
  - Provide from_string(s: str) -> NormalizedVersion and safe_compare(a: str|None, b: str|None) -> Optional[int].
  - Comparison rules: semver > date-like > raw lexicographic fallback; unknown returns None.
- Keep code small, readable, with docstrings and clear failure modes.

Verification

- Add tests in tests/gnmi/capabilities/test_version.py for parsing and comparisons.

---

## Phase 3 — In-memory repository

Scope

- Create: src/gnmi/capabilities/repository.py

Prompt

- Implement DeviceCapabilitiesRepository class with an in-memory cache keyed by a stable device key (e.g., f"{nos}:{ip}:{port}"). Methods:
  - make_key(device) -> str
  - get(device) -> DeviceCapabilities|None
  - set(device, caps: DeviceCapabilities) -> None
  - has(device) -> bool
  - clear() -> None
- No persistence beyond process lifetime.

Verification

- Add tests in tests/gnmi/capabilities/test_repository.py for keying, get/set/has/clear.

---

## Phase 4 — Capability service (fetch via Capabilities RPC)

Scope

- Create: src/gnmi/capabilities/service.py

Prompt

- Implement CapabilityService class with:
  - **init**(repo: DeviceCapabilitiesRepository)
  - get_or_fetch(device) -> DeviceCapabilities
  - \_fetch(device) -> DeviceCapabilities: build connection params using existing GnmiConnectionManager; open a pygnmi gNMIclient connection; call capabilities; normalize into DeviceCapabilities and ModelIdentifier objects.
- Map encodings from device to canonical forms (JSON_IETF → json_ietf, JSON → json, ASCII → ascii). Keep normalizer internal.
- Store result in repository; return cached on subsequent calls.
- Handle exceptions using existing error handling patterns (do not raise; let integrators convert errors if needed).

Verification

- Add tests in tests/gnmi/capabilities/test_service.py using mocks/stubs for gNMIclient to validate normalization and caching.

---

## Phase 5 — Request inspector (infer required models from paths)

Scope

- Create: src/gnmi/capabilities/inspector.py

Prompt

- Implement RequestInspector class with:
  - infer_requirements(paths: list[str]) -> list[ModelRequirement]
- Recognize the three top-level OpenConfig modules only:
  - openconfig-system → ModelRequirement(name="openconfig-system", minimum_version="0.17.1") when path starts with that module prefix.
  - openconfig-interfaces → … minimum_version="4.0.0".
  - openconfig-network-instance → … minimum_version="1.3.0".
- Handle patterns like "openconfig-system:/system" and "openconfig-system:system".
- Return unique requirements (no duplicates).

Verification

- Add tests in tests/gnmi/capabilities/test_inspector.py for typical and edge path variants.

---

## Phase 6 — Encoding policy

Scope

- Create: src/gnmi/capabilities/encoding.py

Prompt

- Implement EncodingPolicy class:
  - normalize(encoding: str|None) -> str|None (canonicalize to json_ietf/json/ascii; case-insensitive).
  - choose_supported(requested: str|None, supported: list[str]) -> tuple[str|None, bool]
    - If requested supported: return (requested, False)
    - Else attempt fallback order: json_ietf → json → ascii where present in supported; return (fallback, True) or (None, False) if none.
- No bytes fallback.

Verification

- Add tests in tests/gnmi/capabilities/test_encoding.py for normalization and fallback selection.

---

## Phase 7 — Capability checker (orchestration)

Scope

- Create: src/gnmi/capabilities/checker.py and src/gnmi/capabilities/errors.py

Prompt

- Implement in errors.py simple constants or an Enum for error types: MODEL_NOT_SUPPORTED and ENCODING_NOT_SUPPORTED.
- Implement CapabilityCheckResult class (in checker.py) with fields: success (bool), warnings (list[str]), selected_encoding (str|None), error_type (str|None), error_message (str|None). Provide simple helpers is_failure().
- Implement CapabilityChecker class with:
  - **init**(service: CapabilityService, version_cmp: Callable, encoding_policy: EncodingPolicy)
  - check(device, paths: list[str], requested_encoding: str|None) -> CapabilityCheckResult
    - Use RequestInspector to get requirements from paths.
    - Use service.get_or_fetch(device) to obtain DeviceCapabilities.
    - Validate encoding with EncodingPolicy; set selected_encoding; on none, return ENCODING_NOT_SUPPORTED failure.
    - For each requirement: use DeviceCapabilities.has_model(req, version_cmp).
      - If not present: return MODEL_NOT_SUPPORTED failure with a clear message stating missing model and required version.
      - If older_than_min: add a warning and continue.
    - On success: return success with warnings (if any) and selected_encoding.

Verification

- Add tests in tests/gnmi/capabilities/test_checker.py for missing model, older model (warning), unsupported encoding, fallback encoding, and all-good paths.

---

## Phase 8 — GnmiRequest: infer_models() method

Scope

- Modify: src/gnmi/parameters.py

Prompt

- Add an instance method infer_models(self) -> list[ModelRequirement] that calls RequestInspector.infer_requirements(self.path). Import only the type(s) needed and keep it thin.
- Do not change existing fields or constructor.

Verification

- Add tests in tests/gnmi/test_parameters_infer_models.py that create a GnmiRequest with paths and assert inferred requirements.

---

## Phase 9 — gNMI client preflight integration

Scope

- Modify: src/gnmi/client.py

Prompt

- In GnmiRequestExecutor.execute_request, before opening gNMIclient:
  - Instantiate CapabilityService (with a shared repository), EncodingPolicy, and CapabilityChecker (wire version comparator from NormalizedVersion and encoding normalizer).
  - Call request.infer_models() to get requirements; pass request.path and request.encoding into the checker.
  - If result is failure: return an ErrorResponse with type from errors.py and a clear message (do not call get()).
  - If result selected a fallback encoding: update a local copy of request with the selected encoding for this single call; do not mutate global state.
  - If warnings exist (older versions), log them at warning level and continue.
- Keep retry and error handling intact; do not alter public behavior when capabilities are satisfied.

Verification

- Add tests in tests/gnmi/test_client_capabilities_integration.py using mocks to simulate capabilities and assert early return on failures and fallback mutation only for the call.
- Manual smoke: run a simple CLI call and capture logs.

---

## Phase 10 — CLI command: device capabilities

Scope

- Create: src/cmd/commands/device/capabilities.py

Prompt

- Implement a new command under the device group (follow the structure and decorators used by device/info.py):
  - Name: capabilities
  - Behavior: fetch capabilities via CapabilityService, print:
    - Supported OpenConfig models (name and version)
    - Supported encoding formats (normalized names)
    - Validation result against the three minimums (meets/older/missing)
  - Follow existing output flag conventions of the CLI (respect --output json, etc.). Keep default formatting consistent with other device commands.
  - Reuse shared formatting utilities if available; otherwise produce clean, minimal output.

Verification

- Manual: run

  ```zsh
  uv run gnmibuddy.py device capabilities --device <NAME> --output json > /tmp/caps.json
  ```

  Inspect the JSON and logs to confirm supported encodings and model checks are present.

---

## Phase 11 — Test suite and quality gates

Scope

- Add/finish all unit tests from previous phases and ensure they run green.

Prompt

- Run tests from CLI:

  ```zsh
  pytest -q
  ```

- Fix any failures. Ensure type/lint (if configured) pass. Avoid flaky test dependencies.

Verification

- All tests green.

---

## Phase 12 — Minimal docs

Scope

- Update README or add a minimal docs note explaining the new CLI command and capability preflight at a high level.

Prompt

- Keep the docs short and focused; reference the CLI help examples.

Verification

- Build passes; CLI help displays the new command.

---

## Finalization (all phases)

- Post a short comment to Issue #14 summarizing what you implemented in your phase and any notable notes/risks. Keep it concise.
- If you found opportunities for improvement beyond your phase, add them as separate notes in the issue (do not implement them).
- Do not expand scope beyond your phase.

## Run and debug tips

- Prefer CLI over integrated terminals for reliability.
- Capture logs when running commands:

  ```zsh
  uv run gnmibuddy.py <command> ... 2>&1 | tee /tmp/gnmibuddy_run.log
  ```

- For network/device tests, verify credentials and sandbox connectivity first.
