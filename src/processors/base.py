#!/usr/bin/env python3
"""
Base processor module.
Defines common interfaces and base classes for all processors to implement,
ensuring consistent behavior across different data types.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TypeVar, Generic, List

# Define type variables for input and output types
T_Output = TypeVar("T_Output", bound=Dict[str, Any])


class BaseProcessor(Generic[T_Output], ABC):
    """
    Abstract base class for all data processors.

    This class defines the common interface that all processors must implement,
    ensuring consistent behavior across different data types and sources.
    """

    @abstractmethod
    def process_data(self, gnmi_data: List[Dict[str, Any]]) -> T_Output:
        """
        Process the input data and return structured output data.

        Args:
            gnmi_data: Raw gNMI response data (list of update dictionaries)

        Returns:
            Processed and structured output data
        """
        pass

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
        response_data = []
        for item in gnmi_data:
            response_data.append(item)
        return response_data

    @abstractmethod
    def transform_data(
        self, extracted_data: Dict[str, Any], **kwargs
    ) -> T_Output:
        """
        Transform extracted data into the final output format.

        Args:
            extracted_data: Data extracted from the input
            **kwargs: Additional keyword arguments for transformation

        Returns:
            Transformed output data in standard format
        """
        pass

    def get_timestamp(self, data: List[Dict[str, Any]]) -> Optional[int]:
        """
        Extract timestamp from gNMI response data.

        Args:
            data: Raw gNMI response data

        Returns:
            Timestamp if present, None otherwise
        """
        if data and len(data) > 0:
            first_item = data[0]
            if isinstance(first_item, dict) and "timestamp" in first_item:
                return first_item.get("timestamp")
        return None

    # Backward compatibility - maintain parse method but delegate to process_data
    def parse(self, gnmi_data: List[Dict[str, Any]]) -> T_Output:
        """
        Legacy method name for backward compatibility.
        Delegates to process_data method.
        """
        return self.process_data(gnmi_data)


class NotFoundError(Exception):
    """Exception raised when a requested feature is not found in the data."""

    def __init__(self, message: str = "Feature not found in the data"):
        self.message = message
        super().__init__(self.message)
