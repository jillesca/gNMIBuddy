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
            # Check if capability verification is disabled (useful for testing)
            if (
                os.environ.get(
                    "GNMIBUDDY_DISABLE_CAPABILITY_VERIFICATION", "0"
                )
                == "1"
            ):
                logger.debug(
                    "Capability verification disabled for function %s",
                    func.__name__,
                )
                return func(*args, **kwargs)

            # Extract device from arguments
            device = _extract_device_from_args(*args, **kwargs)
            if not device:
                logger.error(
                    "Could not extract device from arguments for function %s",
                    func.__name__,
                )
                return _create_capability_error_result(
                    device=None,
                    operation_type=func.__name__,
                    error_message="Could not extract device from function arguments",
                )

            # Check if device is already verified in cache
            if not is_device_verified(device.name):
                logger.info(
                    "Verifying capabilities for device: %s", device.name
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

                        if fail_on_unsupported:
                            error_message = verification_result.get(
                                "error_message",
                                "Device does not support required OpenConfig models",
                            )
                            logger.error(
                                "Device %s failed capability verification: %s",
                                device.name,
                                error_message,
                            )
                            return _create_capability_error_result(
                                device=device,
                                operation_type=func.__name__,
                                error_message=error_message,
                                verification_result=verification_result,
                            )
                        else:
                            logger.warning(
                                "Device %s does not support required models but continuing due to fail_on_unsupported=False",
                                device.name,
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
                                "Device %s: %s",
                                device.name,
                                verification_result["warning_message"],
                            )
                        else:
                            model_capability = verification_result.get(
                                "model_capability", {}
                            )
                            found_version = model_capability.get(
                                "found_version", "unknown"
                            )
                            logger.info(
                                "Device %s: openconfig-network-instance v%s verification successful",
                                device.name,
                                found_version,
                            )

            # Execute the original function
            try:
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

                return result

            except Exception as e:
                logger.error(
                    "Error executing function %s for device %s: %s",
                    func.__name__,
                    device.name,
                    str(e),
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
    # Check positional arguments
    for arg in args:
        if isinstance(arg, Device):
            return arg

    # Check keyword arguments
    for key, value in kwargs.items():
        if isinstance(value, Device):
            return value
        # Common parameter names for device
        if key in ["device", "target_device", "device_obj"] and isinstance(
            value, Device
        ):
            return value

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

    return result
