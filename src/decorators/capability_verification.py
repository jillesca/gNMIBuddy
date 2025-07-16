#!/usr/bin/env python3
"""
Capability verification decorator for gNMIBuddy.

Provides a decorator that can be applied to collector functions to ensure
devices support the required OpenConfig models before executing operations.
"""

import functools
import os
from typing import Any, Callable, Dict, Optional, TypeVar

from src.schemas.models import Device
from src.schemas.responses import (
    NetworkOperationResult,
    OperationStatus,
    ErrorResponse,
    add_capability_verification_to_metadata,
)
from src.services.capability_verification import (
    verify_openconfig_network_instance,
)
from src.utils.capability_cache import (
    is_device_verified,
    cache_verification_result,
    get_verification_result,
)
from src.logging.config import get_logger

logger = get_logger(__name__)

# Type variable for function return type
F = TypeVar("F", bound=Callable[..., Any])


def verify_capabilities(
    required_models: Optional[Dict[str, str]] = None,
    fail_on_unsupported: bool = True,
    add_to_metadata: bool = True,
) -> Callable[[F], F]:
    """
    Decorator to verify device capabilities before executing collector functions.

    This decorator ensures that devices support the required OpenConfig models
    before executing the decorated function. It uses caching to avoid repeated
    capability requests for the same device.

    Args:
        required_models: Dictionary of required models and their minimum versions
                        Default: {"openconfig-network-instance": "1.3.0"}
        fail_on_unsupported: Whether to fail if device doesn't support required models
                           If False, will add warning to metadata and continue
        add_to_metadata: Whether to add capability verification results to metadata

    Returns:
        Decorator function that wraps the original function

    Example:
        @verify_capabilities()
        def get_vpn_info(device: Device) -> NetworkOperationResult:
            # Function implementation
            pass

        @verify_capabilities(
            required_models={"openconfig-network-instance": "1.3.0"},
            fail_on_unsupported=False
        )
        def get_system_info(device: Device) -> NetworkOperationResult:
            # Function implementation
            pass
    """
    # Default to openconfig-network-instance if no models specified
    if required_models is None:
        required_models = {"openconfig-network-instance": "1.3.0"}

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger.debug(
                "Starting capability verification for function",
                extra={
                    "operation": "capability_verification",
                    "function": func.__name__,
                    "required_models": required_models,
                    "fail_on_unsupported": fail_on_unsupported,
                    "add_to_metadata": add_to_metadata,
                },
            )

            # Check if capability verification is disabled (useful for testing)
            if (
                os.environ.get(
                    "GNMIBUDDY_DISABLE_CAPABILITY_VERIFICATION", "0"
                )
                == "1"
            ):
                logger.debug(
                    "Capability verification disabled via environment variable",
                    extra={
                        "operation": "capability_verification",
                        "function": func.__name__,
                        "verification_disabled": True,
                        "env_var": "GNMIBUDDY_DISABLE_CAPABILITY_VERIFICATION",
                    },
                )
                return func(*args, **kwargs)

            # Extract device from arguments
            device = _extract_device_from_args(*args, **kwargs)
            if not device:
                logger.error(
                    "Could not extract device from function arguments",
                    extra={
                        "operation": "capability_verification",
                        "function": func.__name__,
                        "error_type": "device_extraction_failed",
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys()),
                    },
                )
                return _create_capability_error_result(
                    device=None,
                    operation_type=func.__name__,
                    error_message="Could not extract device from function arguments",
                )

            logger.debug(
                "Device extracted for capability verification",
                extra={
                    "operation": "capability_verification",
                    "function": func.__name__,
                    "device": device.name,
                    "device_ip": device.ip_address,
                    "device_nos": device.nos,
                },
            )

            # Check if device is already verified in cache
            if not is_device_verified(device.name):
                logger.info(
                    "Starting capability verification for device",
                    extra={
                        "operation": "capability_verification",
                        "function": func.__name__,
                        "device": device.name,
                        "device_ip": device.ip_address,
                        "required_models": required_models,
                        "cache_status": "not_verified",
                    },
                )

                # Currently only support openconfig-network-instance verification
                if "openconfig-network-instance" in required_models:
                    verification_result = verify_openconfig_network_instance(
                        device
                    )

                    if not verification_result.get("is_supported", False):
                        # Cache the failed verification
                        cache_verification_result(
                            device.name,
                            is_verified=False,
                            verification_result=verification_result,
                        )

                        logger.warning(
                            "Device capability verification failed",
                            extra={
                                "operation": "capability_verification",
                                "function": func.__name__,
                                "device": device.name,
                                "device_ip": device.ip_address,
                                "verification_result": verification_result,
                                "is_supported": False,
                                "fail_on_unsupported": fail_on_unsupported,
                            },
                        )

                        if fail_on_unsupported:
                            error_message = verification_result.get(
                                "error_message",
                                "Device does not support required OpenConfig models",
                            )
                            logger.error(
                                "Function execution blocked due to capability verification failure",
                                extra={
                                    "operation": "capability_verification",
                                    "function": func.__name__,
                                    "device": device.name,
                                    "device_ip": device.ip_address,
                                    "error_message": error_message,
                                    "verification_result": verification_result,
                                },
                            )
                            return _create_capability_error_result(
                                device=device,
                                operation_type=func.__name__,
                                error_message=error_message,
                                verification_result=verification_result,
                            )
                        else:
                            logger.warning(
                                "Continuing function execution despite capability verification failure",
                                extra={
                                    "operation": "capability_verification",
                                    "function": func.__name__,
                                    "device": device.name,
                                    "device_ip": device.ip_address,
                                    "fail_on_unsupported": False,
                                    "verification_result": verification_result,
                                },
                            )
                    else:
                        # Cache the successful verification
                        cache_verification_result(
                            device.name,
                            is_verified=True,
                            verification_result=verification_result,
                        )

                        # Log success or warning message
                        if verification_result.get("warning_message"):
                            logger.warning(
                                "Device capability verification successful with warnings",
                                extra={
                                    "operation": "capability_verification",
                                    "function": func.__name__,
                                    "device": device.name,
                                    "device_ip": device.ip_address,
                                    "warning_message": verification_result[
                                        "warning_message"
                                    ],
                                    "verification_result": verification_result,
                                },
                            )
                        else:
                            model_capability = verification_result.get(
                                "model_capability", {}
                            )
                            found_version = model_capability.get(
                                "found_version", "unknown"
                            )
                            logger.info(
                                "Device capability verification successful",
                                extra={
                                    "operation": "capability_verification",
                                    "function": func.__name__,
                                    "device": device.name,
                                    "device_ip": device.ip_address,
                                    "model": "openconfig-network-instance",
                                    "found_version": found_version,
                                    "verification_result": verification_result,
                                },
                            )
            else:
                logger.debug(
                    "Device already verified in cache",
                    extra={
                        "operation": "capability_verification",
                        "function": func.__name__,
                        "device": device.name,
                        "device_ip": device.ip_address,
                        "cache_status": "verified",
                    },
                )

            # Execute the original function
            try:
                logger.debug(
                    "Executing decorated function",
                    extra={
                        "operation": "capability_verification",
                        "function": func.__name__,
                        "device": device.name,
                        "device_ip": device.ip_address,
                    },
                )
                result = func(*args, **kwargs)

                # Add capability verification metadata if requested and result is NetworkOperationResult
                if add_to_metadata and isinstance(
                    result, NetworkOperationResult
                ):
                    cached_result = get_verification_result(device.name)
                    if cached_result:
                        add_capability_verification_to_metadata(
                            result, cached_result
                        )
                        logger.debug(
                            "Added capability verification metadata to result",
                            extra={
                                "operation": "capability_verification",
                                "function": func.__name__,
                                "device": device.name,
                                "device_ip": device.ip_address,
                                "metadata_added": True,
                            },
                        )

                logger.debug(
                    "Function execution completed successfully",
                    extra={
                        "operation": "capability_verification",
                        "function": func.__name__,
                        "device": device.name,
                        "device_ip": device.ip_address,
                        "result_status": (
                            result.status
                            if hasattr(result, "status")
                            else "unknown"
                        ),
                    },
                )
                return result

            except Exception as e:
                logger.error(
                    "Error executing decorated function",
                    extra={
                        "operation": "capability_verification",
                        "function": func.__name__,
                        "device": device.name,
                        "device_ip": device.ip_address,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )
                raise

        return wrapper  # type: ignore

    return decorator


def _extract_device_from_args(*args, **kwargs) -> Optional[Device]:
    """
    Extract Device object from function arguments.

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Device object if found, None otherwise
    """
    logger.debug(
        "Extracting device from function arguments",
        extra={
            "operation": "device_extraction",
            "args_count": len(args),
            "kwargs_keys": list(kwargs.keys()),
        },
    )

    # Check positional arguments
    for i, arg in enumerate(args):
        if isinstance(arg, Device):
            logger.debug(
                "Found device in positional arguments",
                extra={
                    "operation": "device_extraction",
                    "device": arg.name,
                    "device_ip": arg.ip_address,
                    "device_nos": arg.nos,
                    "position": i,
                },
            )
            return arg

    # Check keyword arguments
    for key, value in kwargs.items():
        if isinstance(value, Device):
            logger.debug(
                "Found device in keyword arguments",
                extra={
                    "operation": "device_extraction",
                    "device": value.name,
                    "device_ip": value.ip_address,
                    "device_nos": value.nos,
                    "key": key,
                },
            )
            return value
        # Common parameter names for device
        if key in ["device", "target_device", "device_obj"] and isinstance(
            value, Device
        ):
            logger.debug(
                "Found device in common parameter names",
                extra={
                    "operation": "device_extraction",
                    "device": value.name,
                    "device_ip": value.ip_address,
                    "device_nos": value.nos,
                    "key": key,
                },
            )
            return value

    logger.warning(
        "No device found in function arguments",
        extra={
            "operation": "device_extraction",
            "args_count": len(args),
            "kwargs_keys": list(kwargs.keys()),
        },
    )
    return None


def _create_capability_error_result(
    device: Optional[Device],
    operation_type: str,
    error_message: str,
    verification_result: Optional[Dict[str, Any]] = None,
) -> NetworkOperationResult:
    """
    Create a NetworkOperationResult for capability verification errors.

    Args:
        device: Device object (can be None)
        operation_type: Type of operation that failed
        error_message: Error message describing the failure
        verification_result: Optional verification result to add to metadata

    Returns:
        NetworkOperationResult with error status
    """
    logger.debug(
        "Creating capability error result",
        extra={
            "operation": "error_result_creation",
            "device": device.name if device else "unknown",
            "device_ip": device.ip_address if device else "unknown",
            "operation_type": operation_type,
            "error_message": error_message,
            "has_verification_result": verification_result is not None,
        },
    )

    error_response = ErrorResponse(
        type="CAPABILITY_VERIFICATION_FAILED",
        message=error_message,
        details={
            "operation_type": operation_type,
            "device_name": device.name if device else "unknown",
            "required_models": ["openconfig-network-instance"],
            "required_version": "1.3.0",
        },
    )

    result = NetworkOperationResult(
        device_name=device.name if device else "unknown",
        ip_address=device.ip_address if device else "unknown",
        nos=device.nos if device else "unknown",
        operation_type=operation_type,
        status=OperationStatus.FAILED,
        error_response=error_response,
    )

    # Add verification result to metadata if available
    if verification_result:
        add_capability_verification_to_metadata(result, verification_result)
        logger.debug(
            "Added verification result to error response metadata",
            extra={
                "operation": "error_result_creation",
                "device": device.name if device else "unknown",
                "device_ip": device.ip_address if device else "unknown",
                "operation_type": operation_type,
                "metadata_added": True,
            },
        )

    logger.info(
        "Created capability error result",
        extra={
            "operation": "error_result_creation",
            "device": device.name if device else "unknown",
            "device_ip": device.ip_address if device else "unknown",
            "operation_type": operation_type,
            "error_type": "CAPABILITY_VERIFICATION_FAILED",
            "status": "FAILED",
        },
    )

    return result
