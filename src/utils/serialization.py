#!/usr/bin/env python3
"""
Serialization utilities for converting complex objects to JSON-serializable format.

This module provides functions to handle dataclass objects, enums, and other
non-JSON-serializable types commonly used in gNMIBuddy responses.
"""

import json
from enum import Enum
from typing import Any, Dict
from dataclasses import is_dataclass, asdict

from src.logging.config import get_logger

logger = get_logger(__name__)


def convert_to_json_serializable(obj: Any) -> Any:
    """
    Convert complex objects (dataclasses, enums) to JSON-serializable format.

    This function handles:
    - Dataclass objects (converts to dictionaries)
    - Enum objects (converts to their values)
    - Nested structures (recursively processes dictionaries and lists)
    - Regular objects (passes through unchanged)

    Args:
        obj: Object to convert to JSON-serializable format

    Returns:
        JSON-serializable representation of the object
    """
    if is_dataclass(obj) and not isinstance(obj, type):
        # Convert dataclass to dict and recursively process all fields
        result = {}
        for field_name, field_value in asdict(obj).items():
            result[field_name] = convert_to_json_serializable(field_value)
        return result
    elif isinstance(obj, Enum):
        return obj.value  # Convert enum to its string/numeric value
    elif isinstance(obj, dict):
        return {
            key: convert_to_json_serializable(value)
            for key, value in obj.items()
        }
    elif isinstance(obj, (list, tuple)):
        return [convert_to_json_serializable(item) for item in obj]
    else:
        return obj


def to_json_dict(obj: Any) -> Dict[str, Any]:
    """
    Convert an object to a JSON-serializable dictionary.

    This is a convenience function that converts the object and ensures
    the result is a dictionary suitable for JSON serialization.

    Args:
        obj: Object to convert

    Returns:
        Dictionary representation suitable for JSON serialization
    """
    serializable_obj = convert_to_json_serializable(obj)

    # Ensure we return a dictionary by using json.loads(json.dumps())
    # This handles any edge cases in serialization
    try:
        return json.loads(json.dumps(serializable_obj))
    except (TypeError, ValueError) as e:
        logger.warning(
            "Failed to fully serialize object, returning basic conversion: %s",
            e,
        )
        return (
            serializable_obj
            if isinstance(serializable_obj, dict)
            else {"data": serializable_obj}
        )


def to_json_string(obj: Any, indent: int = 2) -> str:
    """
    Convert an object to a JSON string.

    Args:
        obj: Object to convert
        indent: Number of spaces for indentation (default: 2)

    Returns:
        JSON string representation of the object
    """
    serializable_obj = convert_to_json_serializable(obj)
    return json.dumps(serializable_obj, indent=indent)
