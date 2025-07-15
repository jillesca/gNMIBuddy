#!/usr/bin/env python3
"""
Log filtering module.
Provides functions for filtering logs based on time and other criteria.
"""

import re
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from src.logging.config import get_logger

logger = get_logger(__name__)


def filter_logs(
    gnmi_data: List[Dict[str, Any]], show_all_logs: bool, filter_minutes: int
) -> Dict[str, Any]:
    """
    Filter logs based on time criteria and format them for display.

    Args:
        gnmi_data: List of gNMI response dictionaries containing log data
        show_all_logs: If True, return all logs without time filtering
        filter_minutes: Number of minutes to filter logs

    Returns:
        Dictionary with filtered logs in a standardized format
    """
    logs = []

    for response in gnmi_data:
        if "val" in response:
            log_content = response["val"]

            # Apply time filter if needed
            if not show_all_logs:
                log_content = filter_logs_by_time(
                    logs=log_content, minutes=filter_minutes
                )
                logger.debug(
                    "Applied time filter: last %s minutes", filter_minutes
                )

            # Always process the logs into the right format, even when not time-filtered
            if log_content.strip():
                # Split logs into lines for easier processing
                log_lines = log_content.strip().split("\n")

                # Add each log line to the list
                for line in log_lines:
                    if (
                        line
                        and not line.startswith("---")
                        and not line.startswith("===")
                        and "show logging" not in line
                    ):
                        logs.append({"message": line})

    # Create summary of log count
    summary = {"log_count": len(logs)}

    # Return structured format
    return {"logs": logs, "summary": summary}


def filter_logs_by_time(
    logs: str, minutes: int = 5, current_time: Optional[datetime] = None
) -> str:
    """
    Filter logs based on timestamp, keeping only recent logs.

    Args:
        logs: String containing log data
        minutes: Number of minutes to filter (keep logs newer than this)
        current_time: Reference time to use (defaults to current time)

    Returns:
        String with filtered logs
    """
    if not logs:
        return ""

    # Use provided time or current time as reference, ensure it's naive (no timezone)
    if current_time is None:
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)
    elif current_time.tzinfo is not None:
        # Convert to naive datetime if it has timezone info
        current_time = current_time.replace(tzinfo=None)

    # Time threshold
    time_threshold = current_time - timedelta(minutes=minutes)

    # Split logs into individual lines
    log_lines = logs.strip().split("\n")
    filtered_lines = []

    # Pattern to match timestamps in the logs
    # Format: RP/0/RP0/CPU0:Apr 23 12:52:06.929 UTC:
    timestamp_pattern = (
        r"RP/\d+/\w+/\w+:(\w+)\s+(\d+)\s+(\d+):(\d+):(\d+)\.(\d+)\s+UTC:"
    )

    # Current year for timestamp context
    current_year = current_time.year

    # Month name to number mapping
    month_dict = {
        "Jan": 1,
        "Feb": 2,
        "Mar": 3,
        "Apr": 4,
        "May": 5,
        "Jun": 6,
        "Jul": 7,
        "Aug": 8,
        "Sep": 9,
        "Oct": 10,
        "Nov": 11,
        "Dec": 12,
    }

    # Process each line
    for line in log_lines:
        # Skip header/footer lines or empty lines
        if (
            not line
            or line.startswith("---")
            or line.startswith("===")
            or "show logging" in line
        ):
            filtered_lines.append(line)
            continue

        match = re.search(timestamp_pattern, line)
        if match:
            try:
                # Extract timestamp components
                (
                    month_str,
                    day_str,
                    hour_str,
                    minute_str,
                    second_str,
                    msec_str,
                ) = match.groups()

                # Get month number
                month = month_dict.get(month_str, 1)

                # Handle year rollover (logs from last year)
                year = current_year
                if month > current_time.month:
                    year -= 1

                # Parse the log timestamp
                log_time = datetime(
                    year=year,
                    month=month,
                    day=int(day_str),
                    hour=int(hour_str),
                    minute=int(minute_str),
                    second=int(second_str),
                    microsecond=int(msec_str)
                    * 1000,  # Convert milliseconds to microseconds
                )

                # Add the line if it's recent enough
                if log_time >= time_threshold:
                    filtered_lines.append(line)
            except Exception as e:
                # If there are issues parsing, include the line and log the error
                logger.warning("Error parsing timestamp in log: %s", e)
                filtered_lines.append(line)
        else:
            # If no timestamp found, include the line
            filtered_lines.append(line)

    return "\n".join(filtered_lines)
