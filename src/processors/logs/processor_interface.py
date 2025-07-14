#!/usr/bin/env python3
"""
Log processor interfaces.
Defines standard interfaces for processors that work with log data.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from src.processors.base import BaseProcessor


class LogProcessor(BaseProcessor):
    """
    Base class for log data processors.

    This class provides a consistent interface for extracting and transforming
    log data from network devices.
    """

    def transform_data(
        self, extracted_data: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        """
        Transform extracted log data into the final output format.

        Args:
            extracted_data: Data extracted from the gNMI response

        Returns:
            Transformed log data in the expected output format
        """
        result = {
            "timestamp": extracted_data.get("timestamp"),
            "logs": [],
            "summary": {"log_count": 0},
        }

        # Process the log data based on filter criteria
        logs = self.process_logs(extracted_data)

        # Apply additional filters if specified
        filtered_logs = self.apply_filters(logs)

        # Update the result with filtered logs
        result["logs"] = filtered_logs
        result["summary"]["log_count"] = len(filtered_logs)

        # Add filter information to the result
        result["filter_info"] = self.get_filter_info()

        return result

    def extract_data(self, gnmi_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract data from raw gNMI response data.

        This method processes the raw gNMI response data directly.
        Log data may come in different formats, so we handle both cases.

        Args:
            gnmi_data: Raw gNMI response data (list of update dictionaries)

        Returns:
            Structured data ready for log processing with 'items' key
        """
        return {"items": gnmi_data if gnmi_data else []}

    def process_data(self, gnmi_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process gNMI data through extraction and transformation."""
        extracted_data = self.extract_data(gnmi_data)
        return self.transform_data(extracted_data)

    def process_logs(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process extracted data into structured log entries.

        Args:
            data: Extracted data containing log information

        Returns:
            List of structured log entries
        """
        logs = []

        # Process each item in the extracted data
        for item in data.get("items", []):
            # Extract log entries based on the format
            # Implementation details should be provided by concrete classes
            _ = item  # Placeholder for processing item data

        return logs

    def apply_filters(
        self, logs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Apply filters to the list of logs.

        Args:
            logs: List of log entries to filter

        Returns:
            Filtered list of log entries
        """
        # Apply time-based filtering
        if not self.show_all_logs():
            logs = self.filter_by_time(logs, self.get_filter_minutes())

        # Apply keyword filtering if keywords are specified
        keywords = self.get_filter_keywords()
        if keywords:
            logs = self.filter_by_keywords(logs, keywords)

        return logs

    def filter_by_time(
        self, logs: List[Dict[str, Any]], minutes: int
    ) -> List[Dict[str, Any]]:
        """
        Filter logs based on timestamp, keeping only recent logs.

        Args:
            logs: List of log entries
            minutes: Number of minutes to filter (keep logs newer than this)

        Returns:
            Filtered list of log entries
        """
        if not logs or minutes <= 0:
            return logs

        # Get current time as reference
        current_time = datetime.now()
        time_threshold = current_time - timedelta(minutes=minutes)

        # Filter logs by timestamp
        return [
            log
            for log in logs
            if "timestamp" in log
            and self.parse_log_timestamp(log["timestamp"]) >= time_threshold
        ]

    def filter_by_keywords(
        self, logs: List[Dict[str, Any]], keywords: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Filter logs based on keywords.

        Args:
            logs: List of log entries
            keywords: List of keywords to filter by

        Returns:
            Filtered list of log entries
        """
        if not logs or not keywords:
            return logs

        # Convert keywords to lowercase for case-insensitive matching
        lower_keywords = [kw.lower() for kw in keywords]

        # Filter logs by keywords
        filtered_logs = []
        for log in logs:
            message = log.get("message", "").lower()
            if any(kw in message for kw in lower_keywords):
                filtered_logs.append(log)

        return filtered_logs

    def parse_log_timestamp(self, timestamp_str: str) -> datetime:
        """
        Parse a timestamp string into a datetime object.

        Args:
            timestamp_str: Timestamp string from log entry

        Returns:
            Parsed datetime object
        """
        # Default implementation - should be overridden by concrete classes
        # based on specific timestamp formats
        try:
            return datetime.fromisoformat(timestamp_str)
        except (ValueError, TypeError):
            # Return a very old date for entries that can't be parsed
            return datetime(1970, 1, 1)

    def show_all_logs(self) -> bool:
        """
        Check if all logs should be shown or filtered by time.

        Returns:
            True if all logs should be shown, False if time filtering should be applied
        """
        # Should be implemented by concrete classes
        return False

    def get_filter_minutes(self) -> int:
        """
        Get the number of minutes to use for time filtering.

        Returns:
            Number of minutes
        """
        # Should be implemented by concrete classes
        return 5  # Default to 5 minutes

    def get_filter_keywords(self) -> List[str]:
        """
        Get the keywords to use for filtering logs.

        Returns:
            List of keywords
        """
        # Should be implemented by concrete classes
        return []

    def get_filter_info(self) -> Dict[str, Any]:
        """
        Get information about the filters applied.

        Returns:
            Dictionary with filter information
        """
        return {
            "show_all": self.show_all_logs(),
            "minutes": (
                self.get_filter_minutes() if not self.show_all_logs() else None
            ),
            "keywords": self.get_filter_keywords() or None,
        }
