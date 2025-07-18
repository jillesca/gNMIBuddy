#!/usr/bin/env python3
"""Output formatting system for CLI with support for multiple formats"""
from enum import Enum
from io import StringIO
from typing import Any, List
from abc import ABC, abstractmethod
from dataclasses import is_dataclass, asdict

import json
import yaml

from src.logging.config import get_logger

logger = get_logger(__name__)


# Pure functions for data serialization
def make_serializable(obj: Any) -> Any:
    """
    Convert complex objects to JSON/YAML-serializable format.

    This is a pure function that recursively converts dataclasses, enums,
    and nested structures to basic Python types.
    """
    if is_dataclass(obj):
        # Convert dataclass to dict, then recursively process the result
        data_dict = asdict(obj)
        return make_serializable(data_dict)
    elif isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, dict):
        return {key: make_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [make_serializable(item) for item in obj]
    else:
        return obj


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
            serializable_data = make_serializable(data)
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

    def get_format_name(self) -> str:
        return "json"


class YAMLFormatter(OutputFormatter):
    """YAML output formatter"""

    def format(self, data: Any, **kwargs) -> str:
        """Format data as YAML"""
        try:
            serializable_data = make_serializable(data)
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

    def get_format_name(self) -> str:
        return "yaml"


class FormatterManager:
    """Manager for output formatters"""

    def __init__(self):
        self._formatters = {
            "json": JSONFormatter(),
            "yaml": YAMLFormatter(),
        }
        self._default_format = "json"

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
        self, data: Any, format_name: str = "json", **kwargs
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


def format_output(data: Any, output_format: str = "json", **kwargs) -> str:
    """
    Convenience function to format output data

    Args:
        data: The data to format
        output_format: The format to use ('json', 'yaml')
        **kwargs: Additional formatting options

    Returns:
        Formatted string representation of the data
    """
    return formatter_manager.format_output(data, output_format, **kwargs)


def print_formatted_output(data: Any, output_format: str = "json", **kwargs):
    """
    Print formatted output to stdout

    Args:
        data: The data to format and print
        output_format: The format to use ('json', 'yaml')
        **kwargs: Additional formatting options
    """
    formatted_output = format_output(data, output_format, **kwargs)
    print(formatted_output)


def get_available_output_formats() -> List[str]:
    """Get list of available output formats"""
    return formatter_manager.get_available_formats()
