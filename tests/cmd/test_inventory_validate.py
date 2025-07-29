#!/usr/bin/env python3
"""
Integration tests for inventory validation command.

Tests the InventoryValidator integration and command logic
with various validation scenarios and output formats.
"""

import pytest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.inventory.validator import InventoryValidator
from src.cmd.commands.inventory.validate import _display_table_format
from src.schemas.responses import ValidationStatus


class TestInventoryValidateIntegration:
    """Test class for inventory validation integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = InventoryValidator()
        self.test_data_dir = (
            Path(__file__).parent.parent / "inventory" / "validation"
        )

    def test_validator_integration_with_valid_inventory(self):
        """Test validator integration with valid inventory file."""
        test_file = self.test_data_dir / "valid_inventory.json"
        result = self.validator.validate_inventory_file(str(test_file))

        assert result.status == ValidationStatus.PASSED
        assert result.total_devices == 3
        assert result.valid_devices == 3
        assert result.invalid_devices == 0
        assert len(result.errors) == 0

    def test_validator_integration_with_invalid_inventory(self):
        """Test validator integration with invalid inventory file."""
        test_file = self.test_data_dir / "invalid_json_format.json"
        result = self.validator.validate_inventory_file(str(test_file))

        assert result.status == ValidationStatus.FAILED
        assert result.total_devices == 0
        assert result.valid_devices == 0
        assert len(result.errors) == 1
        assert result.errors[0].error_type == "INVALID_JSON"

    def test_table_display_format_success(self):
        """Test table format display for successful validation."""
        test_file = self.test_data_dir / "valid_inventory.json"
        result = self.validator.validate_inventory_file(str(test_file))

        # Mock click.echo to capture output
        with patch(
            "src.cmd.commands.inventory.validate.click.echo"
        ) as mock_echo:
            _display_table_format(result)

            # Check that echo was called with expected content
            assert mock_echo.called
            # Get all the calls and their arguments
            all_calls = []
            for call in mock_echo.call_args_list:
                if call[0]:  # positional arguments
                    all_calls.append(call[0][0])
                else:  # keyword arguments
                    all_calls.append("")

            output = "\n".join(all_calls)

            assert "Status: PASSED" in output
            assert "Total Devices: 3" in output
            assert "Valid Devices: 3" in output
            assert "Invalid Devices: 0" in output
            assert "✅ All devices passed validation!" in output

    def test_table_display_format_with_errors(self):
        """Test table format display for failed validation."""
        test_file = self.test_data_dir / "invalid_ip_addresses.json"
        result = self.validator.validate_inventory_file(str(test_file))

        # Mock click.echo to capture output
        with patch(
            "src.cmd.commands.inventory.validate.click.echo"
        ) as mock_echo:
            _display_table_format(result)

            # Check that echo was called with expected content
            assert mock_echo.called
            # Get all the calls and their arguments
            all_calls = []
            for call in mock_echo.call_args_list:
                if call[0]:  # positional arguments
                    all_calls.append(call[0][0])
                else:  # keyword arguments
                    all_calls.append("")

            output = "\n".join(all_calls)

            assert "Status: FAILED" in output
            assert "❌ Validation failed" in output
            assert "Device xrd-" in output
            assert "→ Suggestion:" in output

    def test_validation_with_mixed_errors(self):
        """Test validation with multiple types of errors."""
        mixed_errors_inventory = [
            # Valid device
            {
                "name": "valid-device",
                "ip_address": "192.168.1.1",
                "nos": "iosxr",
                "username": "admin",
                "password": "secret123",
            },
            # Missing name
            {"ip_address": "192.168.1.2", "nos": "iosxr"},
            # Invalid IP
            {
                "name": "invalid-ip-device",
                "ip_address": "999.999.999.999",
                "nos": "iosxr",
            },
            # Invalid NOS
            {
                "name": "invalid-nos-device",
                "ip_address": "192.168.1.4",
                "nos": "invalid_nos",
            },
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as tmp:
            json.dump(mixed_errors_inventory, tmp, indent=2)
            tmp_path = tmp.name

        try:
            result = self.validator.validate_inventory_file(tmp_path)

            assert result.status == ValidationStatus.FAILED
            assert result.total_devices == 4
            assert result.valid_devices == 1  # Only the first device is valid
            assert result.invalid_devices == 3
            assert (
                len(result.errors) >= 3
            )  # At least one error per invalid device

            # Verify different error types are present
            error_types = [error.error_type for error in result.errors]
            assert len(set(error_types)) > 1  # Multiple different error types
        finally:
            os.unlink(tmp_path)

    def test_json_serialization_compatibility(self):
        """Test that validation results can be properly serialized."""
        from src.cmd.formatters import make_serializable

        test_file = self.test_data_dir / "invalid_nos_values.json"
        result = self.validator.validate_inventory_file(str(test_file))

        # Test that the result can be serialized
        serializable_result = make_serializable(result)

        # Should be able to convert to JSON without errors
        json_output = json.dumps(serializable_result, indent=2)

        # Verify the JSON contains expected structure
        parsed = json.loads(json_output)
        assert "status" in parsed
        assert "total_devices" in parsed
        assert "errors" in parsed

        # Verify error structure
        if parsed["errors"]:
            error = parsed["errors"][0]
            assert "error_type" in error
            assert "message" in error
            assert "suggestion" in error

    def test_realistic_inventory_validation(self):
        """Test comprehensive validation with realistic inventory structure."""
        realistic_inventory = [
            {
                "name": "router-core-01",
                "ip_address": "192.168.1.1",
                "port": 57400,
                "nos": "iosxr",
                "gnmi_timeout": 30,
                "username": "admin",
                "password": "admin123",
            },
            {
                "name": "router-edge-01",
                "ip_address": "2001:db8:1::1",
                "nos": "iosxr",
                "port": 57400,
                "gnmi_timeout": 60,
                "path_cert": "tests/certificates/device.pem",
                "path_key": "tests/certificates/device.key",
            },
            {
                "name": "router-access-01",
                "ip_address": "10.0.1.1",
                "nos": "iosxr",
                "username": "cisco",
                "password": "cisco123",
            },
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as tmp:
            json.dump(realistic_inventory, tmp, indent=2)
            tmp_path = tmp.name

        try:
            result = self.validator.validate_inventory_file(tmp_path)

            assert result.status == ValidationStatus.PASSED
            assert result.total_devices == 3
            assert result.valid_devices == 3
            assert result.invalid_devices == 0
            assert len(result.errors) == 0
        finally:
            os.unlink(tmp_path)

    def test_path_resolution_integration(self):
        """Test that the validation works with path resolution."""
        # Test with absolute path
        test_file = self.test_data_dir / "valid_inventory.json"
        result = self.validator.validate_inventory_file(str(test_file))

        assert result.status == ValidationStatus.PASSED
        assert str(test_file) in result.file_path

    def test_unicode_handling_in_validation(self):
        """Test that validation properly handles unicode content."""
        unicode_inventory = [
            {
                "name": "device-测试",
                "ip_address": "192.168.1.1",
                "nos": "iosxr",
                "username": "admin",
                "password": "admin123",
            },
            {
                "name": "device-café",
                "ip_address": "192.168.1.2",
                "nos": "iosxr",
                "path_cert": "tests/certificates/device.pem",
                "path_key": "tests/certificates/device.key",
            },
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp:
            json.dump(unicode_inventory, tmp, indent=2, ensure_ascii=False)
            tmp_path = tmp.name

        try:
            result = self.validator.validate_inventory_file(tmp_path)

            assert result.status == ValidationStatus.PASSED
            assert result.total_devices == 2
            assert result.valid_devices == 2
            assert result.invalid_devices == 0
            assert len(result.errors) == 0
        finally:
            os.unlink(tmp_path)

    def test_large_inventory_performance(self):
        """Test validation performance with larger inventory."""
        # Create a moderately large inventory for performance testing
        devices = []
        for i in range(100):
            device = {
                "name": f"device-{i:04d}",
                "ip_address": f"10.0.{i // 256}.{i % 256}",
                "nos": "iosxr",
                "username": "admin",
                "password": "admin123",
            }
            devices.append(device)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as tmp:
            json.dump(devices, tmp, indent=2)
            tmp_path = tmp.name

        try:
            result = self.validator.validate_inventory_file(tmp_path)

            assert result.status == ValidationStatus.PASSED
            assert result.total_devices == 100
            assert result.valid_devices == 100
            assert result.invalid_devices == 0
            assert len(result.errors) == 0
        finally:
            os.unlink(tmp_path)

    def test_comprehensive_error_scenarios(self):
        """Test comprehensive error detection across multiple scenarios."""
        error_scenarios = [
            # Test each major error category
            self.test_data_dir
            / "invalid_json_format.json",  # JSON syntax error
            self.test_data_dir
            / "missing_required_fields.json",  # Required field errors
            self.test_data_dir
            / "invalid_ip_addresses.json",  # IP format errors
            self.test_data_dir / "invalid_nos_values.json",  # NOS enum errors
            self.test_data_dir
            / "duplicate_names.json",  # Duplicate name errors
            self.test_data_dir
            / "invalid_optional_fields.json",  # Optional field errors
        ]

        total_error_types = set()

        for test_file in error_scenarios:
            if test_file.exists():
                result = self.validator.validate_inventory_file(str(test_file))
                assert result.status == ValidationStatus.FAILED

                # Collect all error types
                error_types = {error.error_type for error in result.errors}
                total_error_types.update(error_types)

        # Verify we've tested a comprehensive set of error types
        expected_error_types = {
            "INVALID_JSON",
            "REQUIRED_FIELD",
            "EMPTY_REQUIRED_FIELD",
            "INVALID_IP_FORMAT",
            "INVALID_ENUM_VALUE",
            "DUPLICATE_NAME",
            "INVALID_PORT",
            "INVALID_TYPE",
        }

        # Check that we've covered most major error types
        covered_types = total_error_types.intersection(expected_error_types)
        assert len(covered_types) >= 6  # Should cover most error scenarios


class TestInventoryValidateErrorHandling:
    """Test error handling and edge cases in validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = InventoryValidator()

    def test_validation_error_messages_quality(self):
        """Test that error messages are informative and actionable."""
        test_data_dir = (
            Path(__file__).parent.parent / "inventory" / "validation"
        )
        test_file = test_data_dir / "missing_required_fields.json"

        result = self.validator.validate_inventory_file(str(test_file))

        for error in result.errors:
            # Every error should have meaningful content
            assert len(error.message) > 10  # Reasonable message length
            assert len(error.suggestion) > 10  # Reasonable suggestion length
            assert error.error_type != ""  # Should have error type

            # Error messages should be professional
            assert not any(
                word in error.message.lower()
                for word in ["stupid", "dumb", "bad"]
            )

            # Suggestions should be actionable (contain action words)
            suggestion_lower = error.suggestion.lower()
            action_words = [
                "provide",
                "ensure",
                "check",
                "use",
                "add",
                "remove",
                "fix",
                "correct",
            ]
            assert any(word in suggestion_lower for word in action_words)

    def test_validation_result_consistency(self):
        """Test that validation results are internally consistent."""
        test_data_dir = (
            Path(__file__).parent.parent / "inventory" / "validation"
        )

        for test_file in test_data_dir.glob("*.json"):
            result = self.validator.validate_inventory_file(str(test_file))

            # Basic consistency checks
            assert (
                result.valid_devices + result.invalid_devices
                == result.total_devices
            )
            assert result.valid_devices >= 0
            assert result.invalid_devices >= 0
            assert result.total_devices >= 0

            # Status consistency
            if result.total_devices == 0 and len(result.errors) == 0:
                # Empty but valid case might not exist given current validator behavior
                pass
            elif len(result.errors) > 0:
                assert result.status == ValidationStatus.FAILED
            elif result.invalid_devices > 0:
                assert result.status == ValidationStatus.FAILED
            else:
                assert result.status == ValidationStatus.PASSED

    def test_error_context_information(self):
        """Test that errors provide sufficient context information."""
        test_data_dir = (
            Path(__file__).parent.parent / "inventory" / "validation"
        )
        test_file = test_data_dir / "invalid_ip_addresses.json"

        result = self.validator.validate_inventory_file(str(test_file))

        for i, error in enumerate(result.errors):
            # Device-level errors should have device context
            if error.device_name and error.device_name != "":
                assert error.device_index is not None
                assert error.device_index >= 0
                assert error.device_index < result.total_devices

            # Field-level errors should specify the field
            if error.field:
                assert len(error.field) > 0
                assert error.field in [
                    "name",
                    "ip_address",
                    "nos",
                    "port",
                    "gnmi_timeout",
                    "skip_verify",
                    "insecure",
                ]


if __name__ == "__main__":
    pytest.main([__file__])
