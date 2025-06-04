#!/usr/bin/env python3
"""
Base parser module.
Defines common interfaces and base classes for all parsers to implement,
ensuring consistent behavior across different data types.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TypeVar, Generic, List

# Define type variables for input and output types
T_Input = TypeVar("T_Input", bound=Dict[str, Any])
T_Output = TypeVar("T_Output", bound=Dict[str, Any])


class BaseParser(Generic[T_Input, T_Output], ABC):
    """
    Abstract base class for all data parsers.

    This class defines the common interface that all parsers must implement,
    ensuring consistent behavior across different data types and sources.
    """

    @abstractmethod
    def parse(self, data: T_Input) -> T_Output:
        """
        Parse the input data and return structured output data.

        Args:
            data: Input data to parse

        Returns:
            Parsed and structured output data
        """
        pass

    @abstractmethod
    def extract_data(self, data: T_Input) -> Dict[str, Any]:
        """
        Extract relevant data from the input structure.

        This method handles the common pattern of extracting data from
        a "response" field or other standardized location in the input.

        Args:
            data: Input data to extract from

        Returns:
            Extracted data ready for processing
        """
        pass

    @abstractmethod
    def transform_data(self, extracted_data: Dict[str, Any]) -> T_Output:
        """
        Transform extracted data into the final output format.

        Args:
            extracted_data: Data extracted from the input

        Returns:
            Transformed data in the expected output format
        """
        pass

    @staticmethod
    def get_timestamp(data: Dict[str, Any]) -> Optional[int]:
        """
        Extract the timestamp from the input data.

        Args:
            data: Input data containing a possible timestamp

        Returns:
            Extracted timestamp or None if not available
        """
        return data.get("timestamp")


class NotFoundError(Exception):
    """Exception raised when a requested feature is not found in the data."""

    pass
