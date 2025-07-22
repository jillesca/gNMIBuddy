#!/usr/bin/env python3
"""
Retry handling logic for gNMI requests.

This module provides retry mechanisms with exponential backoff for handling
rate limiting and transient failures in gNMI operations.
"""
import time
import random
from typing import Callable, TypeVar, Optional
from src.schemas.models import Device
from src.logging.config import get_logger

logger = get_logger(__name__)

# Type variable for return type of functions being retried
T = TypeVar("T")


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        jitter_range: tuple[float, float] = (0.0, 0.5),
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter_range = jitter_range


class RateLimitDetector:
    """Detects rate limiting errors from various exception types."""

    RATE_LIMIT_KEYWORDS = [
        "exceeded requests limit",
        "rate limit",
        "too many requests",
        "request rate exceeded",
        "throttled",
    ]

    @classmethod
    def is_rate_limit_error(cls, error: Exception) -> bool:
        """
        Check if an error is related to rate limiting.

        Args:
            error: Exception to analyze

        Returns:
            True if this appears to be a rate limiting error
        """
        error_text = str(error).lower()

        # For gRPC errors, check the details method if available
        if hasattr(error, "details"):
            try:
                details = getattr(error, "details", lambda: str(error))()
                error_text = details.lower()
            except (AttributeError, TypeError):
                pass

        return any(
            keyword in error_text for keyword in cls.RATE_LIMIT_KEYWORDS
        )


class DelayCalculator:
    """Calculates retry delays with exponential backoff and jitter."""

    @staticmethod
    def calculate_delay(attempt: int, config: RetryConfig) -> float:
        """
        Calculate delay for retry attempt using exponential backoff with jitter.

        Args:
            attempt: Current attempt number (0-based)
            config: Retry configuration

        Returns:
            Delay in seconds before next retry
        """
        exponential_delay = config.base_delay * (2**attempt)

        # Cap the delay at max_delay
        exponential_delay = min(exponential_delay, config.max_delay)

        # Add jitter to prevent thundering herd
        jitter = random.uniform(config.jitter_range[0], config.jitter_range[1])

        return exponential_delay + jitter


class RetryLogger:
    """Handles logging for retry operations."""

    @staticmethod
    def log_retry_attempt(
        device: Device, attempt: int, max_retries: int, delay: float
    ) -> None:
        """
        Log retry attempt information.

        Args:
            device: Device being accessed
            attempt: Current attempt number (0-based)
            max_retries: Maximum number of retries
            delay: Delay before next attempt
        """
        logger.warning(
            "Rate limit detected on device '%s' (attempt %d/%d). "
            "Retrying in %.2fs...",
            device.name,
            attempt + 1,
            max_retries + 1,
            delay,
        )

    @staticmethod
    def log_retry_exhausted(device: Device, max_retries: int) -> None:
        """
        Log that retry attempts have been exhausted.

        Args:
            device: Device being accessed
            max_retries: Maximum number of retries that were attempted
        """
        logger.error(
            "Rate limit persists on device '%s' after %d attempts. "
            "Request failed permanently.",
            device.name,
            max_retries + 1,
        )

    @staticmethod
    def log_retry_success(device: Device, attempt: int) -> None:
        """
        Log successful retry.

        Args:
            device: Device being accessed
            attempt: Attempt number that succeeded (0-based)
        """
        if attempt > 0:
            logger.info(
                "Request succeeded on device '%s' after %d retries",
                device.name,
                attempt,
            )


class RetryHandler:
    """Main retry handler for gNMI operations."""

    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self.detector = RateLimitDetector()
        self.calculator = DelayCalculator()
        self.retry_logger = RetryLogger()

    def execute_with_retry(
        self,
        operation: Callable[[], T],
        device: Device,
        operation_name: str = "gNMI operation",
    ) -> T:
        """
        Execute an operation with retry logic for rate limiting.

        Args:
            operation: Function to execute (should raise exception on failure)
            device: Device being accessed
            operation_name: Name of operation for logging

        Returns:
            Result of the operation

        Raises:
            Exception: The last exception if all retries are exhausted
        """
        last_rate_limit_error = None

        for attempt in range(self.config.max_retries + 1):
            try:
                result = operation()
                self.retry_logger.log_retry_success(device, attempt)
                return result

            except Exception as error:
                if self.detector.is_rate_limit_error(error):
                    last_rate_limit_error = error

                    if attempt < self.config.max_retries:
                        delay = self.calculator.calculate_delay(
                            attempt, self.config
                        )
                        self.retry_logger.log_retry_attempt(
                            device, attempt, self.config.max_retries, delay
                        )
                        time.sleep(delay)
                        continue
                    else:
                        self.retry_logger.log_retry_exhausted(
                            device, self.config.max_retries
                        )
                        raise error
                else:
                    # Non-rate-limit error, don't retry
                    logger.debug(
                        "Non-retryable error in %s for device '%s': %s",
                        operation_name,
                        device.name,
                        str(error),
                    )
                    raise error

        # This should never be reached, but provide safety net
        if last_rate_limit_error:
            raise last_rate_limit_error

        raise RuntimeError(
            f"Unexpected state in retry logic for {operation_name}"
        )


# Convenience function for common use case
def with_retry(
    operation: Callable[[], T],
    device: Device,
    max_retries: int = 3,
    base_delay: float = 1.0,
) -> T:
    """
    Execute an operation with default retry configuration.

    Args:
        operation: Function to execute
        device: Device being accessed
        max_retries: Maximum retry attempts
        base_delay: Base delay for exponential backoff

    Returns:
        Result of the operation
    """
    config = RetryConfig(max_retries=max_retries, base_delay=base_delay)
    handler = RetryHandler(config)
    return handler.execute_with_retry(operation, device)
