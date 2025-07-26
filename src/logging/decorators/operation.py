#!/usr/bin/env python3
"""
Operation tracking decorator.

This module provides the log_operation decorator for automatic
operation logging with timing and context tracking.
"""

import functools
from datetime import datetime
from typing import Optional, Callable, Any


def log_operation(
    operation_name: str, device_name: Optional[str] = None
) -> Callable:
    """
    Decorator to log function execution with OTel-compatible operation tracking.

    Provides automatic operation start/completion logging, duration tracking,
    error handling with context, and device name extraction.

    Args:
        operation_name: Name of the operation being performed
        device_name: Optional device name for context

    Returns:
        Decorated function with automatic logging

    Example:
        @log_operation("get_device_interfaces")
        def get_interfaces(device, interface=None):
            # Implementation...
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Import here to avoid circular imports
            from ..utils.dynamic import get_logger

            logger = get_logger(func.__module__)
            start_time = datetime.now()

            # Extract device name from args if not provided
            actual_device_name = device_name
            if not actual_device_name and args:
                actual_device_name = _extract_device_name_from_args(args)

            # Build logging context
            extra_context = {
                "operation": operation_name,
                "function": func.__name__,
            }

            if actual_device_name:
                extra_context["device_name"] = actual_device_name

            # Log operation start
            logger.debug("Starting %s", operation_name, extra=extra_context)

            try:
                # Execute the function
                result = func(*args, **kwargs)

                # Calculate duration and log success
                duration = (datetime.now() - start_time).total_seconds() * 1000
                extra_context["duration_ms"] = round(duration, 2)

                logger.debug(
                    "Completed %s", operation_name, extra=extra_context
                )
                return result

            except Exception as e:
                # Calculate duration and log failure
                duration = (datetime.now() - start_time).total_seconds() * 1000
                extra_context["duration_ms"] = round(duration, 2)
                extra_context["error"] = str(e)

                logger.error(
                    "Failed %s",
                    operation_name,
                    extra=extra_context,
                    exc_info=True,
                )
                raise

        return wrapper

    return decorator


def _extract_device_name_from_args(args: tuple) -> Optional[str]:
    """
    Extract device name from function arguments.

    Looks for common patterns in network function arguments
    to automatically extract device context.

    Args:
        args: Function arguments tuple

    Returns:
        Device name if found, None otherwise
    """
    for arg in args:
        # Check for device objects with name attribute
        if hasattr(arg, "name"):
            return str(arg.name)

        # Check for device objects with hostname attribute
        if hasattr(arg, "hostname"):
            return str(arg.hostname)

        # Check for device dictionaries
        if isinstance(arg, dict):
            for key in ["name", "hostname", "device_name", "device"]:
                if key in arg:
                    return str(arg[key])

    return None
