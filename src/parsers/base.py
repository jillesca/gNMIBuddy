#!/usr/bin/env python3
"""
Base parser module.
Defines common interfaces and base classes for all parsers to implement,
ensuring consistent behavior across different data types.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TypeVar, Generic, List

# Define type variables for input and output types
T_Output = TypeVar("T_Output", bound=Dict[str, Any])


class BaseParser(Generic[T_Output], ABC):
    """
    Abstract base class for all data parsers.

    This class defines the common interface that all parsers must implement,
    ensuring consistent behavior across different data types and sources.
    """

    @abstractmethod
    def parse(self, gnmi_data: List[Dict[str, Any]]) -> T_Output:
        """
        Parse the input data and return structured output data.

        Args:
            gnmi_data: Raw gNMI response data (list of update dictionaries)

        Returns:
            Parsed and structured output data
        """
        ...

    def extract_data(
        self, gnmi_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract relevant data from the input structure.

        This method accepts the raw gNMI data directly from response.data.
        Subclasses can override this if they need special extraction logic.

        Args:
            gnmi_data: Raw gNMI response data (list of update dictionaries)

        Returns:
            Extracted data ready for processing
        """
        return gnmi_data if gnmi_data else []

    @abstractmethod
    def transform_data(
        self, extracted_data: List[Dict[str, Any]], **kwargs
    ) -> T_Output:
        """
        Transform extracted data into the final output format.

        Args:
            extracted_data: Data extracted from the input
            **kwargs: Additional parameters that specific parsers might need

        Returns:
            Transformed data in the expected output format
        """
        ...

    @staticmethod
    def get_timestamp(gnmi_data: List[Dict[str, Any]]) -> Optional[int]:
        """
        Extract the timestamp from the input data.

        Args:
            gnmi_data: Raw gNMI response data

        Returns:
            Extracted timestamp or None if not available
        """
        # Timestamp is now passed separately via SuccessResponse.timestamp
        # This method is kept for backward compatibility but may be deprecated
        _ = gnmi_data  # Suppress unused parameter warning
        return None


class NotFoundError(Exception):
    """Exception raised when a requested feature is not found in the data."""

    def __init__(self, message: str = "Feature not found in data") -> None:
        self.message = message
        super().__init__(self.message)
