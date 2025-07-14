#### Agent Prompt for Phase 1

You are tasked with updating the base parser classes to remove the {"response": response.data} wrapper pattern.

TASK OVERVIEW:

- Modify base parser classes to accept List[Dict[str, Any]] directly instead of expecting a wrapper
- Update extract_data methods to work with raw gNMI data
- Ensure backward compatibility during transition

FILES TO MODIFY:

- src/parsers/base.py
- src/parsers/interfaces/parser_interface.py
- src/parsers/protocols/parser_interface.py
- src/parsers/logs/parser_interface.py

SPECIFIC CHANGES:

1. In base.py, update the extract_data method signature and implementation to work with List[Dict[str, Any]] directly
2. In parser_interface.py files, remove the logic that expects and extracts from {"response": ...} structure
3. Update docstrings to reflect the new data format expectations
4. Ensure the parse() method correctly calls extract_data with the new format

SUCCESS CRITERIA:

- Base classes accept gNMI data directly without wrapper
- extract_data methods work with List[Dict[str, Any]]
- No breaking changes to public parse() method signatures
- All parser base classes are consistent

VERIFICATION:
Run these commands to verify the changes work:

```bash
python -m pytest tests/parsers/ -k "test_base" -v
```

Do not modify any concrete parser implementations yet - only the base classes.

#### Agent Prompt for Phase 2

You are tasked with updating network tools functions to pass gNMI response data directly to parsers.

TASK OVERVIEW:

- Remove the {"response": response.data} wrapper pattern from network tools
- Pass response.data directly to parser functions
- Use more descriptive variable names (gnmi_data instead of data_for_parsing)

FILES TO MODIFY:

- src/network_tools/interfaces_info.py
- src/network_tools/routing_info.py
- src/network_tools/vpn_info.py
- src/network_tools/logging.py

SPECIFIC CHANGES:

1. Replace `data_for_parsing = {"response": response.data}` with `gnmi_data = response.data`
2. Pass `gnmi_data` directly to parser functions
3. Update variable names throughout for clarity
4. Ensure error handling still works correctly

EXAMPLE TRANSFORMATION:
Before:

```python
data_for_parsing = {}
if isinstance(response, SuccessResponse):
    if response.data:
        data_for_parsing = {"response": response.data}

parsed_result = parse_single_interface_data(data_for_parsing)
```

After:

```python
gnmi_data = []
if isinstance(response, SuccessResponse):
    if response.data:
        gnmi_data = response.data

parsed_result = parse_single_interface_data(gnmi_data)
```

SUCCESS CRITERIA:

- All network tools pass response.data directly to parsers
- No more {"response": ...} wrapper creation
- Variable names are descriptive (gnmi_data, not data_for_parsing)
- Error handling and empty data checks work correctly

VERIFICATION:
Run these commands to verify the changes work:

```bash
python -m pytest tests/network_tools/ -k "test_interface" -v
python -m pytest tests/network_tools/ -k "test_routing" -v
```

Do not modify parser implementations yet - only the network tools functions.

#### Agent Prompt for Phase 3A (System and Device Profile Parsers)

You are tasked with updating system and device profile parsers to work with direct gNMI data instead of wrapped data.

TASK OVERVIEW:

- Remove {"response": ...} extraction logic from parsers
- Update parsers to work directly with List[Dict[str, Any]] gNMI data
- Ensure all parser methods handle the new data format correctly

FILES TO MODIFY:

- src/parsers/system_info_parser.py
- src/parsers/deviceprofile_parser.py

SPECIFIC CHANGES:

1. Remove any logic that checks for or extracts "response" key from input data
2. Update extract_data and transform_data methods to work with List[Dict[str, Any]] directly
3. Update any internal methods that expected wrapped data format
4. Ensure docstrings reflect the new data format

EXAMPLE TRANSFORMATION:
Before:

```python
def parse(self, data: Dict[str, Any]) -> Dict[str, Any]:
    if "response" in data and data["response"]:
        return self._parse_openconfig_data(data)
    return {"parse_error": "Unsupported data format"}
```

After:

```python
def parse(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
    if data:
        return self._parse_openconfig_data(data)
    return {"parse_error": "No data provided"}
```

SUCCESS CRITERIA:

- Parsers accept List[Dict[str, Any]] directly
- No more "response" key extraction logic
- All internal methods work with new data format
- Parser output format remains unchanged

VERIFICATION:
Run these commands to verify the changes work:

```bash
python -m pytest tests/network_tools/system_info/ -v
python -m pytest tests/network_tools/deviceprofile/ -v
```

Focus only on system_info_parser.py and deviceprofile_parser.py in this phase.

#### Agent Prompt for Phase 3B (Interface Parsers)

You are tasked with updating interface parsers to work with direct gNMI data instead of wrapped data.

TASK OVERVIEW:

- Remove {"response": ...} extraction logic from interface parsers
- Update parsers to work directly with List[Dict[str, Any]] gNMI data
- Ensure interface parsing logic handles the new data format correctly

FILES TO MODIFY:

- src/parsers/interfaces/single_interface_parser.py
- src/parsers/interfaces/data_formatter.py

SPECIFIC CHANGES:

1. Update function signatures to accept List[Dict[str, Any]] instead of Dict with "response" key
2. Remove any logic that extracts from data["response"]
3. Update internal data extraction logic to work with gNMI data directly
4. Ensure all helper functions work with new format

EXAMPLE TRANSFORMATION:
Before:

```python
def parse_single_interface_data(raw_interface_data: Dict[str, Any]) -> Dict[str, Any]:
    response_data = raw_interface_data.get("response", [])
    # Process response_data...
```

After:

```python
def parse_single_interface_data(gnmi_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Process gnmi_data directly...
```

SUCCESS CRITERIA:

- Interface parsers accept List[Dict[str, Any]] directly
- No more "response" key extraction logic
- All helper functions work with new data format
- Interface parsing output format remains unchanged

VERIFICATION:
Run these commands to verify the changes work:

```bash
python -m pytest tests/network_tools/interfaces/ -v
python -c "
from src.parsers.interfaces.single_interface_parser import parse_single_interface_data
print('Interface parser function signature updated successfully')
"
```

Focus only on interface-related parsers in this phase.

#### Agent Prompt for Phase 3C (Protocol Parsers)

You are tasked with updating protocol parsers to work with direct gNMI data instead of wrapped data.

TASK OVERVIEW:

- Remove {"response": ...} extraction logic from protocol parsers
- Update parsers to work directly with List[Dict[str, Any]] gNMI data
- Ensure protocol parsing logic handles the new data format correctly

FILES TO MODIFY:

- src/parsers/protocols/bgp/config_parser.py
- src/parsers/protocols/mpls/mpls_parser.py
- src/parsers/protocols/isis/isis_parser.py
- src/parsers/protocols/vrf/vrf_parser.py
- src/parsers/protocols/vrf/cisco_iosxr_vrf_parser.py

SPECIFIC CHANGES:

1. Update function signatures to accept List[Dict[str, Any]] instead of Dict with "response" key
2. Remove logic that checks for "response" key: `if "response" in data and data["response"]:`
3. Update internal data extraction to work with gNMI data directly
4. Ensure all protocol-specific parsing logic works with new format

EXAMPLE TRANSFORMATION:
Before:

```python
def parse_bgp_data(data: Dict[str, Any]) -> Dict[str, Any]:
    if "response" in data and data["response"]:
        return _parse_openconfig_bgp(data)
    return {"parse_error": "Unsupported BGP data format"}
```

After:

```python
def parse_bgp_data(gnmi_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    if gnmi_data:
        return _parse_openconfig_bgp(gnmi_data)
    return {"parse_error": "No BGP data provided"}
```

SUCCESS CRITERIA:

- Protocol parsers accept List[Dict[str, Any]] directly
- No more "response" key checks or extraction
- All protocol parsing logic works with new data format
- Protocol parser output format remains unchanged

VERIFICATION:
Run these commands to verify the changes work:

```bash
python -m pytest tests/network_tools/protocols/ -v
python -c "
from src.parsers.protocols.bgp.config_parser import parse_bgp_data
from src.parsers.protocols.mpls.mpls_parser import parse_mpls_data
print('Protocol parser function signatures updated successfully')
"
```

Focus only on protocol-related parsers in this phase.

#### Agent Prompt for Phase 4

You are tasked with updating test files to work with the new direct gNMI data passing approach.

TASK OVERVIEW:

- Remove test logic that creates {"response": ...} wrapper structures
- Update tests to pass gNMI data directly to parsers
- Ensure all test assertions still work correctly
- Update test data files if needed

FILES TO MODIFY:

- tests/network_tools/deviceprofile/test_deviceprofile.py
- tests/network_tools/interfaces/test_single_interface_parser.py
- tests/network_tools/system_info/test_system_info_parser.py
- tests/network*tools/protocols/\*/test*\*.py
- Any other test files that use the old pattern

SPECIFIC CHANGES:

1. Replace `response_data = input_data["response"]` with direct data passing
2. Update parser calls to pass gNMI data directly instead of wrapped data
3. Update test data structures if they contain artificial "response" wrappers
4. Ensure test assertions match the new data flow

EXAMPLE TRANSFORMATION:
Before:

```python
def test_deviceprofile_pe():
    input_data = load_json("input_pe.json")
    expected = load_json("output_pe.json")
    parser = DeviceProfileParser()
    response_data = input_data["response"]  # Remove this
    result = parser.parse(response_data)
    assert result == expected
```

After:

```python
def test_deviceprofile_pe():
    gnmi_data = load_json("input_pe.json")  # Load gNMI data directly
    expected = load_json("output_pe.json")
    parser = DeviceProfileParser()
    result = parser.parse(gnmi_data)  # Pass gNMI data directly
    assert result == expected
```

SUCCESS CRITERIA:

- All tests pass gNMI data directly to parsers
- No more {"response": ...} wrapper creation in tests
- Test data files contain pure gNMI data format
- All existing test assertions still pass

VERIFICATION:
Run these commands to verify the changes work:

```bash
python -m pytest tests/network_tools/ -v
python -m pytest tests/parsers/ -v
```

Update test data files (JSON files) to contain direct gNMI data if they currently have wrapper structures.

#### Agent Prompt for Phase 5

You are tasked with final cleanup and documentation updates for the gNMI data refactoring.

TASK OVERVIEW:

- Search for any remaining {"response": ...} patterns in the codebase
- Update documentation to reflect the new data flow
- Ensure all variable names are descriptive and consistent
- Run comprehensive tests to verify everything works

TASKS:

1. Search the entire codebase for any remaining patterns:

   - `{"response":`
   - `data["response"]`
   - `response_data = input_data["response"]`
   - `data_for_parsing`

2. Update documentation files:

   - src/parsers/README.md: Update examples to show new data flow
   - Any inline comments that reference the old pattern

3. Standardize variable names:

   - Use `gnmi_data` for gNMI response data
   - Use `parsed_data` for parser output
   - Avoid generic names like `data_for_parsing`

4. Run comprehensive tests:

   ```bash
   python -m pytest tests/ -v
   python -m pytest tests/network_tools/ -v
   python -m pytest tests/parsers/ -v
   ```

SUCCESS CRITERIA:

- No remaining {"response": ...} wrapper patterns anywhere
- All tests pass
- Documentation reflects new data flow
- Variable names are consistent and descriptive
- Code is cleaner and more maintainable

VERIFICATION:
Run these search commands to ensure cleanup is complete:

```bash
grep -r "data_for_parsing" src/ tests/ || echo "No data_for_parsing found"
grep -r '{"response":' src/ tests/ || echo "No response wrapper found"
grep -r 'data\["response"\]' src/ tests/ || echo "No response extraction found"
```

If any patterns are found, fix them. Update any documentation that needs to reflect the new approach.
