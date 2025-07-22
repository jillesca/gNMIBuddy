#!/usr/bin/env python3
"""
gNMI response parsing utilities.

This module provides robust parsing of gNMI responses with proper error
handling, validation, and structured data extraction.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from src.logging.config import get_logger

logger = get_logger(__name__)


@dataclass
class GnmiNotification:
    """Structured representation of a gNMI notification."""

    updates: List[Dict[str, Any]]
    timestamp: Optional[int] = None
    prefix: Optional[str] = None

    @property
    def has_data(self) -> bool:
        """Check if this notification contains any data updates."""
        return bool(self.updates)

    @property
    def update_count(self) -> int:
        """Get the number of updates in this notification."""
        return len(self.updates)


@dataclass
class ParsedGnmiResponse:
    """Structured representation of a parsed gNMI response."""

    notifications: List[GnmiNotification]

    @property
    def has_data(self) -> bool:
        """Check if response contains any meaningful data."""
        return any(
            notification.has_data for notification in self.notifications
        )

    @property
    def total_updates(self) -> int:
        """Get total number of updates across all notifications."""
        return sum(
            notification.update_count for notification in self.notifications
        )

    @property
    def first_notification(self) -> Optional[GnmiNotification]:
        """Get the first notification, if any."""
        return self.notifications[0] if self.notifications else None


class GnmiResponseValidator:
    """Validates gNMI response structure and content."""

    @staticmethod
    def validate_response_structure(response: Dict[str, Any]) -> bool:
        """
        Validate that response has expected gNMI structure.

        Args:
            response: Raw gNMI response dictionary

        Returns:
            True if structure is valid
        """
        if not isinstance(response, dict):
            logger.warning("gNMI response is not a dictionary")
            return False

        if "notification" not in response:
            logger.debug("gNMI response missing 'notification' field")
            return False

        notifications = response["notification"]
        if not isinstance(notifications, list):
            logger.warning("gNMI response 'notification' field is not a list")
            return False

        return True

    @staticmethod
    def validate_notification_structure(notification: Dict[str, Any]) -> bool:
        """
        Validate that a notification has expected structure.

        Args:
            notification: Single notification dictionary

        Returns:
            True if structure is valid
        """
        if not isinstance(notification, dict):
            logger.warning("gNMI notification is not a dictionary")
            return False

        # Updates are optional, but if present should be a list
        if "update" in notification:
            updates = notification["update"]
            if not isinstance(updates, list):
                logger.warning(
                    "gNMI notification 'update' field is not a list"
                )
                return False

        return True


class GnmiResponseParser:
    """Main parser for gNMI responses."""

    def __init__(self):
        self.validator = GnmiResponseValidator()

    def parse_response(
        self, response: Dict[str, Any]
    ) -> Optional[ParsedGnmiResponse]:
        """
        Parse a raw gNMI response into structured data.

        Args:
            response: Raw gNMI response dictionary

        Returns:
            Parsed response or None if parsing fails
        """
        if not self.validator.validate_response_structure(response):
            return None

        notifications = []
        raw_notifications = response.get("notification", [])

        for raw_notification in raw_notifications:
            notification = self._parse_notification(raw_notification)
            if notification:
                notifications.append(notification)

        return ParsedGnmiResponse(notifications=notifications)

    def _parse_notification(
        self, notification: Dict[str, Any]
    ) -> Optional[GnmiNotification]:
        """
        Parse a single notification.

        Args:
            notification: Raw notification dictionary

        Returns:
            Parsed notification or None if parsing fails
        """
        if not self.validator.validate_notification_structure(notification):
            return None

        # Extract updates (default to empty list if not present)
        updates = notification.get("update", [])
        if not isinstance(updates, list):
            logger.warning("Notification updates is not a list, skipping")
            return None

        # Extract optional fields
        timestamp = notification.get("timestamp")
        prefix = notification.get("prefix")

        # Validate timestamp if present
        if timestamp is not None and not isinstance(timestamp, (int, float)):
            logger.warning("Invalid timestamp type: %s", type(timestamp))
            timestamp = None

        return GnmiNotification(
            updates=updates,
            timestamp=int(timestamp) if timestamp is not None else None,
            prefix=str(prefix) if prefix is not None else None,
        )


# Factory function for easy usage
def parse_gnmi_response(
    response: Dict[str, Any],
) -> Optional[ParsedGnmiResponse]:
    """
    Parse gNMI response and return in legacy format for backward compatibility.


    Args:
        response: Raw gNMI response dictionary

    Returns:
        Parsed data in legacy format or None if no data
    """
    if not response:
        logger.debug("Empty gNMI response provided")
        return None

    parser = GnmiResponseParser()
    parsed = parser.parse_response(response)

    if not parsed:
        logger.debug("Failed to parse gNMI response structure")
        return None

    if not parsed.has_data:
        logger.debug("gNMI response contains no data updates")
        return None

    logger.debug(
        "Successfully parsed gNMI response with %d total updates",
        parsed.total_updates,
    )

    return parsed
