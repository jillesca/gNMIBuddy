#!/usr/bin/env python3
"""Output formatting system for CLI with support for multiple formats"""
import json
import yaml
from typing import Any, Dict, List
from abc import ABC, abstractmethod
from io import StringIO
from dataclasses import is_dataclass, asdict
from enum import Enum
from src.logging.config import get_logger

logger = get_logger(__name__)


class OutputFormatter(ABC):
    """Abstract base class for output formatters"""

    @abstractmethod
    def format(self, data: Any, **kwargs) -> str:
        """Format data according to the formatter's rules"""
        pass

    @abstractmethod
    def get_format_name(self) -> str:
        """Get the name of this format"""
        pass


class JSONFormatter(OutputFormatter):
    """JSON output formatter with pretty printing"""

    def format(self, data: Any, indent: int = 2, **kwargs) -> str:
        """Format data as pretty-printed JSON"""
        try:
            # Convert complex objects to dictionary representation
            serializable_data = self._make_serializable(data)
            return json.dumps(
                serializable_data,
                indent=indent,
                ensure_ascii=False,
                default=str,
            )
        except Exception as e:
            logger.error("Error formatting JSON output: %s", e)
            return json.dumps(
                {"error": f"JSON formatting failed: {str(e)}"}, indent=indent
            )

    def _make_serializable(self, obj: Any) -> Any:
        """Convert complex objects to JSON-serializable format"""
        if is_dataclass(obj):
            # Convert dataclass to dict, then recursively process the result
            data_dict = asdict(obj)
            return self._make_serializable(data_dict)
        elif isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, dict):
            return {
                key: self._make_serializable(value)
                for key, value in obj.items()
            }
        elif isinstance(obj, (list, tuple)):
            return [self._make_serializable(item) for item in obj]
        else:
            return obj

    def get_format_name(self) -> str:
        return "json"


class YAMLFormatter(OutputFormatter):
    """YAML output formatter"""

    def format(self, data: Any, **kwargs) -> str:
        """Format data as YAML"""
        try:
            # Convert complex objects to dictionary representation
            serializable_data = self._make_serializable(data)
            output = StringIO()
            yaml.dump(
                serializable_data,
                output,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
                indent=2,
            )
            return output.getvalue()
        except Exception as e:
            logger.error("Error formatting YAML output: %s", e)
            return f"error: YAML formatting failed: {str(e)}\n"

    def _make_serializable(self, obj: Any) -> Any:
        """Convert complex objects to YAML-serializable format"""
        if is_dataclass(obj):
            # Convert dataclass to dict, then recursively process the result
            data_dict = asdict(obj)
            return self._make_serializable(data_dict)
        elif isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, dict):
            return {
                key: self._make_serializable(value)
                for key, value in obj.items()
            }
        elif isinstance(obj, (list, tuple)):
            return [self._make_serializable(item) for item in obj]
        else:
            return obj

    def get_format_name(self) -> str:
        return "yaml"


class TableFormatter(OutputFormatter):
    """Table output formatter for structured data"""

    def format(self, data: Any, **kwargs) -> str:
        """Format data as a readable table"""
        try:
            if isinstance(data, dict):
                return self._format_dict_as_table(data)
            elif isinstance(data, list) and data:
                if isinstance(data[0], dict):
                    return self._format_list_of_dicts_as_table(data)
                else:
                    return self._format_simple_list_as_table(data)
            else:
                return str(data)
        except Exception as e:
            logger.error("Error formatting table output: %s", e)
            return f"Error: Table formatting failed: {str(e)}"

    def _format_dict_as_table(self, data: Dict[str, Any]) -> str:
        """Format a dictionary as a key-value table"""
        if not data:
            return "No data available"

        # Calculate column widths
        max_key_length = (
            max(len(str(key)) for key in data.keys()) if data else 0
        )
        max_value_length = (
            max(len(str(value)) for value in data.values()) if data else 0
        )

        # Create table format
        key_width = max(max_key_length, 10)
        value_width = max(max_value_length, 20)

        # Create header
        lines = []
        lines.append(f"{'Key':<{key_width}} | {'Value':<{value_width}}")
        lines.append("-" * (key_width + 3 + value_width))

        # Add data rows
        for key, value in data.items():
            # Handle complex values
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, default=str)
                if len(value_str) > 50:
                    value_str = value_str[:47] + "..."
            else:
                value_str = str(value)

            lines.append(
                f"{str(key):<{key_width}} | {value_str:<{value_width}}"
            )

        return "\n".join(lines)

    def _format_list_of_dicts_as_table(
        self, data: List[Dict[str, Any]]
    ) -> str:
        """Format a list of dictionaries as a table"""
        if not data:
            return "No data available"

        # Get all unique keys
        all_keys = set()
        for item in data:
            if isinstance(item, dict):
                all_keys.update(item.keys())

        if not all_keys:
            return "No data available"

        all_keys = sorted(all_keys)

        # Calculate column widths
        col_widths = {}
        for key in all_keys:
            max_width = len(str(key))
            for item in data:
                if isinstance(item, dict) and key in item:
                    value_str = str(item[key])
                    max_width = max(max_width, len(value_str))
            col_widths[key] = min(max_width, 30)  # Cap at 30 chars

        # Create header
        lines = []
        header = " | ".join(f"{key:<{col_widths[key]}}" for key in all_keys)
        lines.append(header)
        lines.append("-" * len(header))

        # Add data rows
        for item in data:
            if isinstance(item, dict):
                row_values = []
                for key in all_keys:
                    value = item.get(key, "")
                    value_str = str(value)
                    if len(value_str) > col_widths[key]:
                        value_str = value_str[: col_widths[key] - 3] + "..."
                    row_values.append(f"{value_str:<{col_widths[key]}}")
                lines.append(" | ".join(row_values))

        return "\n".join(lines)

    def _format_simple_list_as_table(self, data: List[Any]) -> str:
        """Format a simple list as a single-column table"""
        if not data:
            return "No data available"

        lines = []
        lines.append("Value")
        lines.append("-" * 20)
        for item in data:
            lines.append(str(item))

        return "\n".join(lines)

    def get_format_name(self) -> str:
        return "table"


class FormatterManager:
    """Manager for output formatters"""

    def __init__(self):
        self._formatters = {
            "json": JSONFormatter(),
            "yaml": YAMLFormatter(),
            "table": TableFormatter(),
        }
        self._default_format = "table"

    def get_formatter(self, format_name: str) -> OutputFormatter:
        """Get a formatter by name"""
        if format_name not in self._formatters:
            logger.warning(
                "Unknown format '%s', falling back to default '%s'",
                format_name,
                self._default_format,
            )
            format_name = self._default_format

        return self._formatters[format_name]

    def get_available_formats(self) -> List[str]:
        """Get list of available format names"""
        return list(self._formatters.keys())

    def format_output(
        self, data: Any, format_name: str = "table", **kwargs
    ) -> str:
        """Format data using the specified formatter"""
        formatter = self.get_formatter(format_name)
        return formatter.format(data, **kwargs)

    def set_default_format(self, format_name: str):
        """Set the default output format"""
        if format_name in self._formatters:
            self._default_format = format_name
        else:
            logger.warning(
                "Cannot set unknown format '%s' as default", format_name
            )


# Global formatter manager instance
formatter_manager = FormatterManager()


def format_output(data: Any, output_format: str = "table", **kwargs) -> str:
    """
    Convenience function to format output data

    Args:
        data: The data to format
        output_format: The format to use ('json', 'yaml', 'table')
        **kwargs: Additional formatting options

    Returns:
        Formatted string representation of the data
    """
    return formatter_manager.format_output(data, output_format, **kwargs)


def print_formatted_output(data: Any, output_format: str = "table", **kwargs):
    """
    Print formatted output to stdout

    Args:
        data: The data to format and print
        output_format: The format to use ('json', 'yaml', 'table')
        **kwargs: Additional formatting options
    """
    formatted_output = format_output(data, output_format, **kwargs)
    print(formatted_output)


def get_available_output_formats() -> List[str]:
    """Get list of available output formats"""
    return formatter_manager.get_available_formats()
