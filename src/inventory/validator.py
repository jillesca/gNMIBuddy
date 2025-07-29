#!/usr/bin/env python3
"""
Inventory validation module.
Provides comprehensive validation for inventory files including schema, IP addresses, and network OS validation.
"""

import json
from ipaddress import ip_address, AddressValueError
from typing import List, Dict, Any, Optional, Set

from src.logging import get_logger
from src.schemas.models import Device, NetworkOS
from src.schemas.responses import (
    ValidationError,
    ValidationResult,
    ValidationStatus,
)
from src.inventory.file_handler import resolve_inventory_path

# Type alias for device inventory data from JSON
DeviceData = Dict[str, Any]

# Setup module logger
logger = get_logger(__name__)


class InventoryValidator:
    """
    Comprehensive inventory validation engine.

    Validates inventory files for proper JSON format, schema compliance,
    IP address formats, network OS values, and business rules.
    """

    def __init__(self):
        """Initialize the validator."""
        self.errors: List[ValidationError] = []

    def validate_inventory_file(self, file_path: str) -> ValidationResult:
        """
        Validate an inventory file comprehensively.

        Args:
            file_path: Path to the inventory JSON file

        Returns:
            ValidationResult with comprehensive validation results
        """
        logger.debug("Starting validation of inventory file: %s", file_path)

        # Reset errors for this validation run
        self.errors = []

        try:
            # Resolve the file path
            abs_path = resolve_inventory_path(file_path)
        except FileNotFoundError as e:
            # File path resolution failed, add error and return failed result
            self.errors.append(
                ValidationError(
                    device_name=None,
                    device_index=None,
                    field=None,
                    error_type="FILE_NOT_FOUND",
                    message=f"Inventory file not found: {file_path}",
                    suggestion="Check that the file path is correct and the file exists",
                )
            )
            return self._create_result(file_path, 0, 0)

        # Step 1: Validate JSON format and load content
        content = self._load_and_validate_json(abs_path)
        if content is None:
            # JSON parsing failed, errors already recorded
            return self._create_result(abs_path, 0, 0)

        # Step 2: Validate file structure (should be a list)
        if not self._validate_file_structure(content):
            return self._create_result(abs_path, 0, 0)

        # Step 3: Validate individual devices
        devices = content
        valid_count = self._validate_devices(devices)
        total_count = len(devices)

        # Step 4: Check for duplicate device names
        self._check_duplicate_names(devices)

        # Create final result
        result = self._create_result(abs_path, total_count, valid_count)

        logger.debug(
            "Validation completed: %s, Total: %d, Valid: %d, Invalid: %d, Errors: %d",
            result.status.value,
            total_count,
            valid_count,
            total_count - valid_count,
            len(self.errors),
        )

        return result

    def _load_and_validate_json(self, file_path: str) -> Optional[Any]:
        """
        Load and validate JSON format.

        Args:
            file_path: Absolute path to the JSON file

        Returns:
            Parsed JSON content or None if validation failed
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = json.load(file)
            logger.debug("JSON file loaded successfully: %s", file_path)
            return content
        except json.JSONDecodeError as e:
            logger.error("JSON parsing error in %s: %s", file_path, e)
            self.errors.append(
                ValidationError(
                    error_type="INVALID_JSON",
                    message=f"Invalid JSON format: {e}",
                    suggestion="Ensure the file contains valid JSON syntax",
                )
            )
            return None
        except FileNotFoundError:
            # This should not happen as resolve_inventory_path already checked,
            # but handle it just in case
            logger.error("File not found: %s", file_path)
            self.errors.append(
                ValidationError(
                    error_type="FILE_NOT_FOUND",
                    message=f"Inventory file not found: {file_path}",
                    suggestion="Ensure the file path is correct and the file exists",
                )
            )
            return None
        except Exception as e:
            logger.error("Error reading file %s: %s", file_path, e)
            self.errors.append(
                ValidationError(
                    error_type="FILE_READ_ERROR",
                    message=f"Error reading file: {e}",
                    suggestion="Check file permissions and try again",
                )
            )
            return None

    def _validate_file_structure(self, content: Any) -> bool:
        """
        Validate that the file contains a list of devices.

        Args:
            content: Parsed JSON content

        Returns:
            True if structure is valid, False otherwise
        """
        if not isinstance(content, list):
            logger.error(
                "Invalid file structure: expected list, got %s",
                type(content).__name__,
            )
            self.errors.append(
                ValidationError(
                    error_type="INVALID_STRUCTURE",
                    message=f"Invalid file structure: expected a list of devices, got {type(content).__name__}",
                    suggestion="Ensure the JSON file contains an array of device objects",
                )
            )
            return False

        if len(content) == 0:
            logger.warning("Empty device list in inventory file")
            self.errors.append(
                ValidationError(
                    error_type="EMPTY_INVENTORY",
                    message="Inventory file contains no devices",
                    suggestion="Add device entries to the inventory file",
                )
            )
            return False

        logger.debug(
            "File structure validation passed: %d devices found", len(content)
        )
        return True

    def _validate_devices(self, devices: List[DeviceData]) -> int:
        """
        Validate all devices in the inventory.

        Args:
            devices: List of device data dictionaries

        Returns:
            Number of valid devices
        """
        valid_count = 0

        for index, device_data in enumerate(devices):
            if self._validate_single_device(device_data, index):
                valid_count += 1

        logger.debug(
            "Device validation completed: %d/%d devices valid",
            valid_count,
            len(devices),
        )
        return valid_count

    def _validate_single_device(
        self, device_data: DeviceData, index: int
    ) -> bool:
        """
        Validate a single device entry.

        Args:
            device_data: Device data dictionary
            index: Position of device in the list (0-based)

        Returns:
            True if device is valid, False otherwise
        """
        if not isinstance(device_data, dict):
            logger.error(
                "Device at index %d is not a dictionary: %s",
                index,
                type(device_data).__name__,
            )
            self.errors.append(
                ValidationError(
                    device_index=index,
                    error_type="INVALID_DEVICE_TYPE",
                    message=f"Device at index {index} is not a dictionary: {type(device_data).__name__}",
                    suggestion="Ensure each device entry is a JSON object",
                )
            )
            return False

        device_name = device_data.get("name", f"<unnamed-device-{index}>")
        is_valid = True

        # Validate required fields first
        required_fields_valid = self._validate_required_fields(
            device_data, device_name, index
        )
        if not required_fields_valid:
            is_valid = False

        # Only validate optional fields if basic validation passed
        if required_fields_valid:
            if not self._validate_optional_fields(
                device_data, device_name, index
            ):
                is_valid = False

            # Validate authentication requirements
            if not self._validate_authentication(
                device_data, device_name, index
            ):
                is_valid = False

        # Try to create Device object only if all individual validations passed
        if is_valid:
            try:
                # Use the same conversion logic as the file handler
                converted_data = self._convert_device_data(device_data)
                Device(**converted_data)
                logger.debug(
                    "Device '%s' passed all validation checks", device_name
                )
            except Exception as e:
                logger.error(
                    "Device '%s' failed Device object creation: %s",
                    device_name,
                    e,
                )
                self.errors.append(
                    ValidationError(
                        device_name=device_name,
                        device_index=index,
                        error_type="DEVICE_CREATION_FAILED",
                        message=f"Failed to create Device object: {e}",
                        suggestion="Check all field values and types",
                    )
                )
                is_valid = False

        return is_valid

    def _validate_required_fields(
        self, device_data: DeviceData, device_name: str, index: int
    ) -> bool:
        """
        Validate required fields for a device.

        Args:
            device_data: Device data dictionary
            device_name: Name of the device (for error reporting)
            index: Position of device in the list

        Returns:
            True if all required fields are valid, False otherwise
        """
        required_fields = ["name", "ip_address", "nos"]
        is_valid = True

        for field in required_fields:
            if field not in device_data:
                logger.error(
                    "Device '%s': missing required field '%s'",
                    device_name,
                    field,
                )
                self.errors.append(
                    ValidationError(
                        device_name=device_name,
                        device_index=index,
                        field=field,
                        error_type="REQUIRED_FIELD",
                        message=f"Missing required field: {field}",
                        suggestion=f"Add the {field} field to the device configuration",
                    )
                )
                is_valid = False
                continue

            # Check for empty values
            value = device_data[field]
            if not value or (isinstance(value, str) and not value.strip()):
                logger.error(
                    "Device '%s': required field '%s' is empty",
                    device_name,
                    field,
                )
                self.errors.append(
                    ValidationError(
                        device_name=device_name,
                        device_index=index,
                        field=field,
                        error_type="EMPTY_REQUIRED_FIELD",
                        message=f"Required field '{field}' is empty",
                        suggestion=f"Provide a valid value for the {field} field",
                    )
                )
                is_valid = False
                continue

            # Field-specific validation
            if field == "ip_address":
                if not self._validate_ip_address(value, device_name, index):
                    is_valid = False
            elif field == "nos":
                if not self._validate_network_os(value, device_name, index):
                    is_valid = False
            elif field == "name":
                if not isinstance(value, str):
                    logger.error(
                        "Device '%s': name field must be a string, got %s",
                        device_name,
                        type(value).__name__,
                    )
                    self.errors.append(
                        ValidationError(
                            device_name=device_name,
                            device_index=index,
                            field=field,
                            error_type="INVALID_TYPE",
                            message=f"Name field must be a string, got {type(value).__name__}",
                            suggestion="Provide a string value for the device name",
                        )
                    )
                    is_valid = False

        return is_valid

    def _validate_optional_fields(
        self, device_data: DeviceData, device_name: str, index: int
    ) -> bool:
        """
        Validate optional fields if they are present.

        Args:
            device_data: Device data dictionary
            device_name: Name of the device (for error reporting)
            index: Position of device in the list

        Returns:
            True if all present optional fields are valid, False otherwise
        """
        is_valid = True

        # Port validation
        if "port" in device_data:
            port = device_data["port"]
            if not isinstance(port, int) or port < 1 or port > 65535:
                logger.error(
                    "Device '%s': invalid port value: %s", device_name, port
                )
                self.errors.append(
                    ValidationError(
                        device_name=device_name,
                        device_index=index,
                        field="port",
                        error_type="INVALID_PORT",
                        message=f"Invalid port value: {port}",
                        suggestion="Port must be an integer between 1 and 65535",
                    )
                )
                is_valid = False

        # Boolean field validation
        boolean_fields = ["skip_verify", "insecure"]
        for field in boolean_fields:
            if field in device_data and not isinstance(
                device_data[field], bool
            ):
                logger.error(
                    "Device '%s': field '%s' must be boolean, got %s",
                    device_name,
                    field,
                    type(device_data[field]).__name__,
                )
                self.errors.append(
                    ValidationError(
                        device_name=device_name,
                        device_index=index,
                        field=field,
                        error_type="INVALID_TYPE",
                        message=f"Field '{field}' must be boolean, got {type(device_data[field]).__name__}",
                        suggestion=f"Set {field} to true or false",
                    )
                )
                is_valid = False

        # Timeout validation
        if "gnmi_timeout" in device_data:
            timeout = device_data["gnmi_timeout"]
            if not isinstance(timeout, int) or timeout < 1:
                logger.error(
                    "Device '%s': invalid gnmi_timeout value: %s",
                    device_name,
                    timeout,
                )
                self.errors.append(
                    ValidationError(
                        device_name=device_name,
                        device_index=index,
                        field="gnmi_timeout",
                        error_type="INVALID_TIMEOUT",
                        message=f"Invalid gnmi_timeout value: {timeout}",
                        suggestion="gnmi_timeout must be a positive integer (seconds)",
                    )
                )
                is_valid = False

        # String field validation
        string_fields = [
            "username",
            "password",
            "path_cert",
            "path_key",
            "path_root",
            "override",
            "show_diff",
        ]
        for field in string_fields:
            if (
                field in device_data
                and device_data[field] is not None
                and not isinstance(device_data[field], str)
            ):
                logger.error(
                    "Device '%s': field '%s' must be string, got %s",
                    device_name,
                    field,
                    type(device_data[field]).__name__,
                )
                self.errors.append(
                    ValidationError(
                        device_name=device_name,
                        device_index=index,
                        field=field,
                        error_type="INVALID_TYPE",
                        message=f"Field '{field}' must be a string, got {type(device_data[field]).__name__}",
                        suggestion=f"Provide a string value for {field}",
                    )
                )
                is_valid = False

        # List field validation
        if "grpc_options" in device_data:
            grpc_options = device_data["grpc_options"]
            if grpc_options is not None and not isinstance(grpc_options, list):
                logger.error(
                    "Device '%s': grpc_options must be a list, got %s",
                    device_name,
                    type(grpc_options).__name__,
                )
                self.errors.append(
                    ValidationError(
                        device_name=device_name,
                        device_index=index,
                        field="grpc_options",
                        error_type="INVALID_TYPE",
                        message=f"grpc_options must be a list, got {type(grpc_options).__name__}",
                        suggestion="Provide a list of gRPC options",
                    )
                )
                is_valid = False

        return is_valid

    def _validate_ip_address(
        self, ip_str: str, device_name: str, index: int
    ) -> bool:
        """
        Validate IP address format using the ipaddress standard library.

        Args:
            ip_str: IP address string to validate
            device_name: Name of the device (for error reporting)
            index: Position of device in the list

        Returns:
            True if IP address is valid, False otherwise
        """
        if not isinstance(ip_str, str):
            logger.error(
                "Device '%s': IP address must be string, got %s",
                device_name,
                type(ip_str).__name__,
            )
            self.errors.append(
                ValidationError(
                    device_name=device_name,
                    device_index=index,
                    field="ip_address",
                    error_type="INVALID_TYPE",
                    message=f"IP address must be a string, got {type(ip_str).__name__}",
                    suggestion="Provide IP address as a string",
                )
            )
            return False

        try:
            # This validates both IPv4 and IPv6 addresses
            ip_address(ip_str)
            logger.debug(
                "Device '%s': IP address '%s' is valid", device_name, ip_str
            )
            return True
        except (AddressValueError, ValueError) as e:
            logger.error(
                "Device '%s': invalid IP address '%s': %s",
                device_name,
                ip_str,
                e,
            )
            self.errors.append(
                ValidationError(
                    device_name=device_name,
                    device_index=index,
                    field="ip_address",
                    error_type="INVALID_IP_FORMAT",
                    message=f"Invalid IP address format: '{ip_str}'",
                    suggestion="Provide valid IPv4 or IPv6 address without CIDR notation",
                )
            )
            return False

    def _validate_network_os(
        self, nos_value: str, device_name: str, index: int
    ) -> bool:
        """
        Validate network OS against NetworkOS enum values.

        Args:
            nos_value: Network OS string to validate
            device_name: Name of the device (for error reporting)
            index: Position of device in the list

        Returns:
            True if network OS is valid, False otherwise
        """
        if not isinstance(nos_value, str):
            logger.error(
                "Device '%s': nos field must be string, got %s",
                device_name,
                type(nos_value).__name__,
            )
            self.errors.append(
                ValidationError(
                    device_name=device_name,
                    device_index=index,
                    field="nos",
                    error_type="INVALID_TYPE",
                    message=f"nos field must be a string, got {type(nos_value).__name__}",
                    suggestion="Provide nos value as a string",
                )
            )
            return False

        try:
            NetworkOS(nos_value)
            logger.debug(
                "Device '%s': nos value '%s' is valid", device_name, nos_value
            )
            return True
        except ValueError:
            valid_values = [nos.value for nos in NetworkOS]
            logger.error(
                "Device '%s': invalid nos value '%s', valid values: %s",
                device_name,
                nos_value,
                valid_values,
            )
            self.errors.append(
                ValidationError(
                    device_name=device_name,
                    device_index=index,
                    field="nos",
                    error_type="INVALID_ENUM_VALUE",
                    message=f"Invalid network OS: '{nos_value}'. Must be one of: {valid_values}",
                    suggestion=f"Use one of the supported network OS values: {', '.join(valid_values)}",
                )
            )
            return False

    def _validate_authentication(
        self, device_data: DeviceData, device_name: str, index: int
    ) -> bool:
        """
        Validate authentication requirements for a device.

        gNMI clients require authentication via either:
        1. Username and password
        2. Client certificate and private key

        Args:
            device_data: Device data dictionary
            device_name: Name of the device (for error reporting)
            index: Position of device in the list

        Returns:
            True if authentication is properly configured, False otherwise
        """
        # Check for username/password authentication
        has_username = (
            "username" in device_data
            and device_data["username"]
            and device_data["username"].strip()
        )
        has_password = (
            "password" in device_data
            and device_data["password"]
            and device_data["password"].strip()
        )

        # Check for certificate-based authentication
        has_cert = (
            "path_cert" in device_data
            and device_data["path_cert"]
            and device_data["path_cert"].strip()
        )
        has_key = (
            "path_key" in device_data
            and device_data["path_key"]
            and device_data["path_key"].strip()
        )

        # Check for partial username/password authentication
        if (has_username and not has_password) or (
            has_password and not has_username
        ):
            missing_field = "password" if has_username else "username"
            logger.error(
                "Device '%s': incomplete username/password authentication - missing %s",
                device_name,
                missing_field,
            )
            self.errors.append(
                ValidationError(
                    device_name=device_name,
                    device_index=index,
                    field=missing_field,
                    error_type="INCOMPLETE_AUTHENTICATION",
                    message=f"Incomplete username/password authentication - missing {missing_field}",
                    suggestion="Provide both username and password for username/password authentication",
                )
            )
            return False

        # Check for partial certificate authentication
        if (has_cert and not has_key) or (has_key and not has_cert):
            missing_field = "path_key" if has_cert else "path_cert"
            logger.error(
                "Device '%s': incomplete certificate authentication - missing %s",
                device_name,
                missing_field,
            )
            self.errors.append(
                ValidationError(
                    device_name=device_name,
                    device_index=index,
                    field=missing_field,
                    error_type="INCOMPLETE_AUTHENTICATION",
                    message=f"Incomplete certificate authentication - missing {missing_field}",
                    suggestion="Provide both path_cert and path_key for certificate-based authentication",
                )
            )
            return False

        # Check for complete authentication methods
        has_userpass_auth = has_username and has_password
        has_cert_auth = has_cert and has_key

        # At least one authentication method must be present
        if not has_userpass_auth and not has_cert_auth:
            logger.error(
                "Device '%s': no valid authentication method configured",
                device_name,
            )
            self.errors.append(
                ValidationError(
                    device_name=device_name,
                    device_index=index,
                    error_type="MISSING_AUTHENTICATION",
                    message="No valid authentication method configured",
                    suggestion="Provide either username+password or path_cert+path_key for authentication",
                )
            )
            return False

        # Validate certificate files exist if certificate authentication is used
        if has_cert_auth:
            cert_path = device_data["path_cert"].strip()
            key_path = device_data["path_key"].strip()

            # Check certificate file exists
            if not self._validate_certificate_file_exists(
                cert_path, device_name, index, "path_cert"
            ):
                return False

            # Check key file exists
            if not self._validate_certificate_file_exists(
                key_path, device_name, index, "path_key"
            ):
                return False

        logger.debug(
            "Device '%s': authentication validation passed (userpass: %s, cert: %s)",
            device_name,
            has_userpass_auth,
            has_cert_auth,
        )
        return True

    def _check_duplicate_names(self, devices: List[DeviceData]) -> None:
        """
        Check for duplicate device names in the inventory.

        Args:
            devices: List of device data dictionaries
        """
        seen_names: Set[str] = set()
        name_indices: Dict[str, List[int]] = {}

        for index, device_data in enumerate(devices):
            if not isinstance(device_data, dict) or "name" not in device_data:
                continue  # Skip invalid devices (already handled)

            name = device_data["name"]
            if not isinstance(name, str):
                continue  # Skip invalid names (already handled)

            if name in seen_names:
                # Record all indices where this name appears
                if name not in name_indices:
                    name_indices[name] = []
                name_indices[name].append(index)
            else:
                seen_names.add(name)
                name_indices[name] = [index]

        # Report duplicates
        for name, indices in name_indices.items():
            if len(indices) > 1:
                logger.error(
                    "Duplicate device name '%s' found at indices: %s",
                    name,
                    indices,
                )
                for idx in indices:
                    self.errors.append(
                        ValidationError(
                            device_name=name,
                            device_index=idx,
                            field="name",
                            error_type="DUPLICATE_NAME",
                            message=f"Duplicate device name: '{name}' (also appears at indices {[i for i in indices if i != idx]})",
                            suggestion="Ensure each device has a unique name",
                        )
                    )

    def _validate_certificate_file_exists(
        self, file_path: str, device_name: str, index: int, field_name: str
    ) -> bool:
        """
        Validate that a certificate file exists and is readable.

        Args:
            file_path: Path to the certificate file
            device_name: Name of the device being validated
            index: Index of the device in the inventory
            field_name: Name of the field (path_cert or path_key)

        Returns:
            True if file exists and is readable, False otherwise
        """
        import os

        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(
                "Device '%s': certificate file not found at %s",
                device_name,
                file_path,
            )
            self.errors.append(
                ValidationError(
                    device_name=device_name,
                    device_index=index,
                    field=field_name,
                    error_type="CERTIFICATE_FILE_NOT_FOUND",
                    message=f"Certificate file not found: {file_path}",
                    suggestion=f"Ensure the {field_name} file exists and the path is correct",
                )
            )
            return False

        # Check if file is readable
        if not os.access(file_path, os.R_OK):
            logger.error(
                "Device '%s': certificate file is not readable at %s",
                device_name,
                file_path,
            )
            self.errors.append(
                ValidationError(
                    device_name=device_name,
                    device_index=index,
                    field=field_name,
                    error_type="CERTIFICATE_FILE_NOT_READABLE",
                    message=f"Certificate file is not readable: {file_path}",
                    suggestion=f"Check file permissions for {field_name}",
                )
            )
            return False

        logger.debug(
            "Device '%s': certificate file %s validation passed: %s",
            device_name,
            field_name,
            file_path,
        )
        return True

    def _convert_device_data(self, device_data: DeviceData) -> DeviceData:
        """
        Convert device data for validation (similar to file_handler conversion).

        Args:
            device_data: Raw device data from JSON

        Returns:
            Device data with enum conversions applied
        """
        converted_data = device_data.copy()

        # Convert nos string to NetworkOS enum if present
        if "nos" in converted_data and isinstance(converted_data["nos"], str):
            nos_value = converted_data["nos"]
            converted_data["nos"] = NetworkOS(nos_value)

        return converted_data

    def _create_result(
        self, file_path: str, total_devices: int, valid_devices: int
    ) -> ValidationResult:
        """
        Create validation result object.

        Args:
            file_path: Path to the validated file
            total_devices: Total number of devices
            valid_devices: Number of valid devices

        Returns:
            ValidationResult object
        """
        invalid_devices = total_devices - valid_devices
        status = (
            ValidationStatus.PASSED
            if len(self.errors) == 0
            else ValidationStatus.FAILED
        )

        return ValidationResult(
            status=status,
            total_devices=total_devices,
            valid_devices=valid_devices,
            invalid_devices=invalid_devices,
            errors=self.errors.copy(),
            file_path=file_path,
        )
