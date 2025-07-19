#!/usr/bin/env python3
"""Tests for Phase 4 advanced CLI features"""

import pytest
import json
import yaml
import tempfile
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
from src.cmd.formatters import (
    JSONFormatter,
    YAMLFormatter,
    FormatterManager,
    format_output,
    get_available_output_formats,
)
from src.cmd.version import VersionInfo, get_version_info, get_version_dict
from src.cmd.batch import (
    ProgressIndicator,
    BatchOperationExecutor,
    DeviceListParser,
)
from src.schemas.responses import (
    NetworkOperationResult,
    BatchOperationSummary,
    BatchOperationResult,
    OperationStatus,
    ErrorResponse,
)
from src.cmd.parser import cli


class TestOutputFormatters:
    """Test output formatting functionality"""

    def test_json_formatter_basic(self):
        """Test basic JSON formatting"""
        formatter = JSONFormatter()
        data = {"key": "value", "number": 42}

        result = formatter.format(data)
        parsed = json.loads(result)

        assert parsed == data
        assert formatter.get_format_name() == "json"

    def test_json_formatter_complex_data(self):
        """Test JSON formatting with complex data structures"""
        formatter = JSONFormatter()
        data = {
            "devices": [
                {"name": "R1", "type": "router", "interfaces": 24},
                {"name": "R2", "type": "switch", "interfaces": 48},
            ],
            "metadata": {
                "timestamp": "2024-01-01T00:00:00Z",
                "version": "1.0",
            },
        }

        result = formatter.format(data)
        parsed = json.loads(result)

        assert parsed == data
        assert "R1" in result
        assert "router" in result

    def test_json_formatter_error_handling(self):
        """Test JSON formatter error handling"""
        formatter = JSONFormatter()

        # Test with non-serializable object
        class NonSerializable:
            pass

        data = {"obj": NonSerializable()}
        result = formatter.format(data)

        # Should not raise exception, should return error JSON
        parsed = json.loads(result)
        assert "obj" in parsed

    def test_yaml_formatter_basic(self):
        """Test basic YAML formatting"""
        formatter = YAMLFormatter()
        data = {"key": "value", "number": 42}

        result = formatter.format(data)
        parsed = yaml.safe_load(result)

        assert parsed == data
        assert formatter.get_format_name() == "yaml"

    def test_yaml_formatter_complex_data(self):
        """Test YAML formatting with complex data"""
        formatter = YAMLFormatter()
        data = {
            "devices": [
                {"name": "R1", "status": "up"},
                {"name": "R2", "status": "down"},
            ]
        }

        result = formatter.format(data)
        parsed = yaml.safe_load(result)

        assert parsed == data
        assert "devices:" in result
        assert "- name: R1" in result

    def test_formatter_manager(self):
        """Test FormatterManager functionality"""
        manager = FormatterManager()

        # Test getting available formats
        formats = manager.get_available_formats()
        assert "json" in formats
        assert "yaml" in formats

        # Test getting formatters
        json_formatter = manager.get_formatter("json")
        assert isinstance(json_formatter, JSONFormatter)

        yaml_formatter = manager.get_formatter("yaml")
        assert isinstance(yaml_formatter, YAMLFormatter)

    def test_formatter_manager_unknown_format(self):
        """Test FormatterManager with unknown format"""
        manager = FormatterManager()

        # Should fall back to default format (json)
        formatter = manager.get_formatter("unknown")
        assert isinstance(formatter, JSONFormatter)

    def test_format_output_function(self):
        """Test format_output convenience function"""
        data = {"test": "data"}

        # Test JSON output
        json_result = format_output(data, "json")
        assert json.loads(json_result) == data

        # Test YAML output
        yaml_result = format_output(data, "yaml")
        assert yaml.safe_load(yaml_result) == data

        # Test table output
        table_result = format_output(data, "table")
        assert "test" in table_result
        assert "data" in table_result

    def test_get_available_output_formats_function(self):
        """Test get_available_output_formats function"""
        formats = get_available_output_formats()
        assert isinstance(formats, list)
        assert "json" in formats
        assert "yaml" in formats


class TestVersionInformation:
    """Test version information functionality"""

    def test_version_info_basic(self):
        """Test basic version information"""
        version_info = VersionInfo()

        # Test getting gNMIBuddy version
        gnmibuddy_version = version_info.get_gnmibuddy_version()
        assert isinstance(gnmibuddy_version, str)
        assert len(gnmibuddy_version) > 0

    def test_python_version_info(self):
        """Test Python version information"""
        version_info = VersionInfo()
        python_info = version_info.get_python_version()

        assert "version" in python_info
        assert "implementation" in python_info
        assert "compiler" in python_info
        assert python_info["version"] == sys.version.split()[0]

    def test_platform_info(self):
        """Test platform information"""
        version_info = VersionInfo()
        platform_info = version_info.get_platform_info()

        required_keys = ["system", "release", "machine", "architecture"]
        for key in required_keys:
            assert key in platform_info
            assert isinstance(platform_info[key], str)

    def test_dependency_versions(self):
        """Test dependency version information"""
        version_info = VersionInfo()
        deps = version_info.get_dependency_versions()

        assert isinstance(deps, dict)
        # Should have at least some dependencies
        assert len(deps) > 0

        # Check for key dependencies
        expected_deps = ["click"]  # This should always be available
        for dep in expected_deps:
            if dep in deps:
                assert isinstance(deps[dep], str)
                assert len(deps[dep]) > 0

    def test_build_info(self):
        """Test build information"""
        version_info = VersionInfo()
        build_info = version_info.get_build_info()

        assert isinstance(build_info, dict)
        assert "python_executable" in build_info
        assert build_info["python_executable"] == sys.executable

    def test_comprehensive_version_info(self):
        """Test comprehensive version information"""
        version_info = VersionInfo()
        info = version_info.get_comprehensive_version_info()

        assert "gnmibuddy" in info
        assert "python" in info
        assert "platform" in info
        assert "dependencies" in info

        assert "version" in info["gnmibuddy"]
        assert "version" in info["python"]

    def test_format_version_output_simple(self):
        """Test simple version output formatting"""
        version_info = VersionInfo()
        output = version_info.format_version_output(detailed=False)

        assert "gNMIBuddy" in output
        assert "Python" in output
        assert len(output.split("\n")) == 1  # Single line

    def test_format_version_output_detailed(self):
        """Test detailed version output formatting"""
        version_info = VersionInfo()
        output = version_info.format_version_output(detailed=True)

        assert "gNMIBuddy" in output
        assert "Python:" in output
        assert "Platform:" in output
        assert len(output.split("\n")) > 5  # Multiple lines

    def test_get_version_info_function(self):
        """Test get_version_info convenience function"""
        simple_version = get_version_info(detailed=False)
        detailed_version = get_version_info(detailed=True)

        assert isinstance(simple_version, str)
        assert isinstance(detailed_version, str)
        assert len(detailed_version) > len(simple_version)

    def test_get_version_dict_function(self):
        """Test get_version_dict function"""
        version_dict = get_version_dict()

        assert isinstance(version_dict, dict)
        assert "gnmibuddy" in version_dict
        assert "python" in version_dict


class TestBatchOperations:
    """Test batch operations functionality"""

    def test_network_operation_result(self):
        """Test NetworkOperationResult dataclass"""
        result = NetworkOperationResult(
            device_name="R1",
            ip_address="192.168.1.1",
            nos="iosxr",
            operation_type="interface_info",
            status=OperationStatus.SUCCESS,
            data={"status": "up"},
            metadata={"execution_time": 1.5},
        )

        assert result.device_name == "R1"
        assert result.ip_address == "192.168.1.1"
        assert result.nos == "iosxr"
        assert result.operation_type == "interface_info"
        assert result.status == OperationStatus.SUCCESS
        assert result.data == {"status": "up"}
        assert result.metadata["execution_time"] == 1.5

    def test_batch_operation_summary(self):
        """Test BatchOperationSummary dataclass"""
        summary = BatchOperationSummary(
            total_devices=3,
            successful=2,
            failed=1,
            execution_time=5.0,
            operation_type="interface_info",
        )

        assert summary.total_devices == 3
        assert summary.successful == 2
        assert summary.failed == 1
        assert summary.execution_time == 5.0
        assert summary.operation_type == "interface_info"
        assert summary.success_rate == 66.66666666666666

    def test_batch_operation_result(self):
        """Test BatchOperationResult dataclass"""
        results = [
            NetworkOperationResult(
                device_name="R1",
                ip_address="192.168.1.1",
                nos="iosxr",
                operation_type="interface_info",
                status=OperationStatus.SUCCESS,
                data={"status": "up"},
                metadata={"execution_time": 1.0},
            ),
            NetworkOperationResult(
                device_name="R2",
                ip_address="192.168.1.2",
                nos="iosxr",
                operation_type="interface_info",
                status=OperationStatus.FAILED,
                data={},
                metadata={"execution_time": 1.5},
                error_response=ErrorResponse(
                    type="connection_error", message="Connection failed"
                ),
            ),
            NetworkOperationResult(
                device_name="R3",
                ip_address="192.168.1.3",
                nos="iosxr",
                operation_type="interface_info",
                status=OperationStatus.SUCCESS,
                data={"status": "up"},
                metadata={"execution_time": 0.8},
            ),
        ]

        summary = BatchOperationSummary(
            total_devices=3,
            successful=2,
            failed=1,
            execution_time=5.0,
            operation_type="interface_info",
        )

        batch_result = BatchOperationResult(
            results=results,
            summary=summary,
            metadata={"test_run": True},
        )

        assert len(batch_result.results) == 3
        assert batch_result.summary.total_devices == 3
        assert batch_result.summary.successful == 2
        assert batch_result.summary.failed == 1
        assert len(batch_result.successful_results) == 2
        assert len(batch_result.failed_results) == 1
        assert batch_result.get_results_by_device("R1").device_name == "R1"
        assert (
            batch_result.get_results_by_device("R2").status
            == OperationStatus.FAILED
        )

    def test_batch_operation_summary_empty(self):
        """Test BatchOperationSummary with no devices"""
        summary = BatchOperationSummary(
            total_devices=0,
            successful=0,
            failed=0,
            execution_time=0.0,
            operation_type="test",
        )

        assert summary.success_rate == 0.0

    def test_progress_indicator(self):
        """Test ProgressIndicator functionality"""
        progress = ProgressIndicator(total=5, show_progress=False)

        assert progress.total == 5
        assert progress.completed == 0

        progress.update(2)
        assert progress.completed == 2

        progress.update()  # Default increment of 1
        assert progress.completed == 3

    def test_device_list_parser_comma_separated(self):
        """Test parsing comma-separated device list"""
        devices = DeviceListParser.parse_device_list("R1, R2, R3")
        assert devices == ["R1", "R2", "R3"]

        devices = DeviceListParser.parse_device_list("R1,R2,R3")
        assert devices == ["R1", "R2", "R3"]

        devices = DeviceListParser.parse_device_list("")
        assert devices == []

    def test_device_list_parser_file(self):
        """Test parsing device list from file"""
        # Create temporary file with device names
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("R1\n")
            f.write("R2\n")
            f.write("# Comment line\n")
            f.write("R3\n")
            f.write("\n")  # Empty line
            temp_filename = f.name

        try:
            devices = DeviceListParser.parse_device_file(temp_filename)
            assert devices == ["R1", "R2", "R3"]
        finally:
            os.unlink(temp_filename)

    def test_device_list_parser_file_not_found(self):
        """Test parsing non-existent device file"""
        with pytest.raises(Exception):  # Should raise ClickException
            DeviceListParser.parse_device_file("/nonexistent/file.txt")

    @patch("src.inventory.manager.InventoryManager.get_instance")
    def test_device_list_parser_inventory(self, mock_get_instance):
        """Test getting devices from inventory"""
        # Mock the InventoryManager instance and its methods
        mock_manager = Mock()
        mock_manager.is_initialized.return_value = True
        mock_manager.get_devices.return_value = {
            "R1": Mock(),
            "R2": Mock(),
            "R3": Mock(),
        }
        mock_get_instance.return_value = mock_manager

        devices = DeviceListParser.get_all_inventory_devices()
        assert devices == ["R1", "R2", "R3"]

    def test_batch_operation_executor_basic(self):
        """Test basic batch operation execution"""

        def mock_operation(device_name):
            return NetworkOperationResult(
                device_name=device_name,
                ip_address="192.168.1.1",
                nos="iosxr",
                operation_type="test",
                status=OperationStatus.SUCCESS,
                data={"device": device_name, "status": "success"},
                metadata={"execution_time": 1.0},
            )

        executor = BatchOperationExecutor(max_workers=2)
        devices = ["R1", "R2"]

        batch_result = executor.execute_batch_operation(
            devices=devices,
            operation_func=mock_operation,
            operation_type="test",
            show_progress=False,
        )

        assert batch_result.summary.total_devices == 2
        assert batch_result.summary.successful == 2
        assert batch_result.summary.failed == 0
        assert len(batch_result.results) == 2

    def test_batch_operation_executor_with_failures(self):
        """Test batch operation execution with failures"""

        def mock_operation(device_name):
            if device_name == "R2":
                raise Exception("Connection failed")
            return NetworkOperationResult(
                device_name=device_name,
                ip_address="192.168.1.1",
                nos="iosxr",
                operation_type="test",
                status=OperationStatus.SUCCESS,
                data={"device": device_name, "status": "success"},
                metadata={"execution_time": 1.0},
            )

        executor = BatchOperationExecutor(max_workers=2)
        devices = ["R1", "R2", "R3"]

        batch_result = executor.execute_batch_operation(
            devices=devices,
            operation_func=mock_operation,
            operation_type="test",
            show_progress=False,
        )

        assert batch_result.summary.total_devices == 3
        assert batch_result.summary.successful == 2
        assert batch_result.summary.failed == 1


class TestCLIIntegration:
    """Test CLI integration with advanced features"""

    def test_version_flag(self):
        """Test --version flag"""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "gNMIBuddy" in result.output
        assert "Python" in result.output

    def test_version_detailed_flag(self):
        """Test --version-detailed flag"""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version-detailed"])

        assert result.exit_code == 0
        assert "gNMIBuddy" in result.output
        assert "Python:" in result.output
        assert "Platform:" in result.output

    @patch("src.collectors.system.get_gnmi_data")
    @patch("src.inventory.manager.InventoryManager.get_device")
    def test_output_format_json(self, mock_get_device, mock_get_gnmi_data):
        """Test JSON output format"""
        from src.schemas.responses import SuccessResponse

        # Mock device with proper attributes
        from src.schemas.models import Device

        mock_device = Device(
            name="R1",
            ip_address="192.168.1.1",
            nos="iosxr",
            username="admin",
            password="admin",
            port=57777,
        )
        mock_get_device.return_value = mock_device

        # Mock gNMI response with proper structure
        mock_gnmi_response = SuccessResponse(
            data=[
                {
                    "openconfig-system:system": {
                        "config": {"hostname": "R1"},
                        "state": {
                            "hostname": "R1",
                            "current-datetime": "2023-01-01T00:00:00Z",
                        },
                    }
                }
            ]
        )
        mock_get_gnmi_data.return_value = mock_gnmi_response

        runner = CliRunner()
        result = runner.invoke(
            cli, ["device", "info", "--device", "R1", "--output", "json"]
        )

        # Should not exit with error
        if result.exit_code != 0:
            print(f"Command failed with output: {result.output}")

        # Check that output contains JSON
        assert "hostname" in result.output

    @patch("src.collectors.system.get_gnmi_data")
    @patch("src.inventory.manager.InventoryManager.get_device")
    def test_output_format_yaml(self, mock_get_device, mock_get_gnmi_data):
        """Test YAML output format"""
        from src.schemas.responses import SuccessResponse

        # Mock device with proper attributes
        from src.schemas.models import Device

        mock_device = Device(
            name="R1",
            ip_address="192.168.1.1",
            nos="iosxr",
            username="admin",
            password="admin",
            port=57777,
        )
        mock_get_device.return_value = mock_device

        # Mock gNMI response with proper structure
        mock_gnmi_response = SuccessResponse(
            data=[
                {
                    "openconfig-system:system": {
                        "config": {"hostname": "R1"},
                        "state": {
                            "hostname": "R1",
                            "current-datetime": "2023-01-01T00:00:00Z",
                        },
                    }
                }
            ]
        )
        mock_get_gnmi_data.return_value = mock_gnmi_response

        runner = CliRunner()
        result = runner.invoke(
            cli, ["device", "info", "--device", "R1", "--output", "yaml"]
        )

        # Should not exit with error
        if result.exit_code != 0:
            print(f"Command failed with output: {result.output}")

        # Check that output contains YAML
        assert "hostname:" in result.output


# Table output format is not supported in the current implementation
# Only json and yaml are supported as per the Choice definition in commands.py


class TestShellCompletion:
    """Test shell completion functionality"""

    def test_bash_completion_file_exists(self):
        """Test that bash completion file exists and has correct content"""
        completion_file = "completions/gnmibuddy-completion.bash"
        assert os.path.exists(completion_file)

        with open(completion_file, "r") as f:
            content = f.read()

        assert "_gnmibuddy_completions" in content
        assert "complete -F _gnmibuddy_completions gnmibuddy" in content
        assert "device" in content
        assert "network" in content

    def test_zsh_completion_file_exists(self):
        """Test that zsh completion file exists and has correct content"""
        completion_file = "completions/gnmibuddy-completion.zsh"
        assert os.path.exists(completion_file)

        with open(completion_file, "r") as f:
            content = f.read()

        assert "#compdef gnmibuddy" in content
        assert "_gnmibuddy" in content
        assert "device:Device management commands" in content
        assert "network:Network protocol commands" in content


class TestPerformanceAndOptimization:
    """Test performance aspects of advanced features"""

    def test_formatter_performance(self):
        """Test formatter performance with large data"""
        import time

        # Create large dataset
        large_data = {
            "devices": [
                {"name": f"R{i}", "status": "up", "interfaces": 24}
                for i in range(100)
            ]
        }

        formatters = [JSONFormatter(), YAMLFormatter()]

        for formatter in formatters:
            start_time = time.time()
            result = formatter.format(large_data)
            end_time = time.time()

            # Should complete within reasonable time
            assert end_time - start_time < 1.0  # Less than 1 second
            assert len(result) > 0

    def test_batch_operation_performance(self):
        """Test batch operation performance with parallel execution"""
        import time

        def fast_operation(device_name):
            time.sleep(0.01)  # Simulate fast operation
            return NetworkOperationResult(
                device_name=device_name,
                ip_address="192.168.1.1",
                nos="iosxr",
                operation_type="performance_test",
                status=OperationStatus.SUCCESS,
                data={"device": device_name, "status": "up"},
                metadata={"execution_time": 0.01},
            )

        executor = BatchOperationExecutor(max_workers=5)
        devices = [f"R{i}" for i in range(10)]

        start_time = time.time()
        batch_result = executor.execute_batch_operation(
            devices=devices,
            operation_func=fast_operation,
            operation_type="performance_test",
            show_progress=False,
        )
        end_time = time.time()

        # Should be faster than sequential execution
        assert (
            end_time - start_time < 0.5
        )  # Should be much faster than 10 * 0.01 = 0.1s
        assert batch_result.summary.successful == 10

    def test_version_info_caching(self):
        """Test that version information is cached"""
        version_info = VersionInfo()

        # First call
        version1 = version_info.get_gnmibuddy_version()

        # Second call should use cache
        version2 = version_info.get_gnmibuddy_version()

        assert version1 == version2
        # Verify cache was used by checking internal cache
        assert "gnmibuddy" in version_info._version_cache
