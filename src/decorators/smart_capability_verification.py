#!/usr/bin/env python3
"""
Smart capability verification decorator for gNMIBuddy.

Provides an intelligent decorator that auto-detects required OpenConfig models
from GnmiRequest parameters and verifies device capabilities before executing
operations.
"""

import functools
import os
from typing import Any, Callable, Dict, Optional, Set, TypeVar

from ..schemas.models import Device
from ..schemas.openconfig_models import OpenConfigModel
from ..schemas.responses import (
    NetworkOperationResult,
    OperationStatus,
    ErrorResponse,
)
from ..schemas.verification_results import VerificationStatus
from ..services.capability_verification import verify_models


from ..gnmi.parameters import GnmiRequest

# from ..gnmi.error_handlers import (
#     handle_partial_verification_failure,
# )


# Temporary fix for hanging import
def handle_partial_verification_failure(
    device, failed_models, successful_models, operation_type
):
    """Temporary implementation to avoid import deadlock."""
    failed_model_names = [model.value for model in failed_models]
    error_message = f"Device {device.name} partial model verification failure for {operation_type}. Failed models: {failed_model_names}"

    error_response = ErrorResponse(
        type="PARTIAL_MODEL_VERIFICATION_FAILURE",
        message=error_message,
        details={
            "device_name": device.name,
            "failed_models": failed_model_names,
            "successful_models": [model.value for model in successful_models],
        },
    )

    return NetworkOperationResult(
        device_name=device.name,
        ip_address=device.ip_address,
        nos=device.nos,
        operation_type=operation_type,
        status=OperationStatus.FAILED,
        error_response=error_response,
    )


# from ..utils.capability_cache import (
#     get_model_verification_result,
#     cache_model_verification_result,
# )


# Temporary fix for hanging import
def get_model_verification_result(device_name, model):
    """Temporary implementation to avoid import deadlock."""
    return None  # Always cache miss for now


def cache_model_verification_result(
    device_name, model, result, ttl_minutes=None
):
    """Temporary implementation to avoid import deadlock."""
    pass  # No-op for now


# from ..logging.config import get_logger

# logger = get_logger(__name__)

# Temporary fix for hanging import - disable logging for now
from ..logging.config import get_logger

logger = get_logger(__name__)

# Type variable for function return type
F = TypeVar("F", bound=Callable[..., Any])


def verify_required_models(
    strict_mode: bool = True,
    required_models: Optional[Set[OpenConfigModel]] = None,
    add_to_metadata: bool = True,
) -> Callable[[F], F]:
    """
    Smart decorator to verify device capabilities before executing collector functions.

    This decorator automatically detects required OpenConfig models from GnmiRequest
    parameters and verifies that devices support them before executing the decorated
    function. It uses caching to avoid repeated capability requests for the same
    device-model combination.

    Args:
        strict_mode: Whether to fail if any required model is not supported
                    If False, will continue execution with partial model support
        required_models: Override auto-detection with specific set of models
                        If None, will auto-detect from GnmiRequest parameters
        add_to_metadata: Whether to add verification results to metadata

    Returns:
        Decorator function that wraps the original function

    Example:
        @verify_required_models()
        def get_vpn_info(device: Device, request: GnmiRequest) -> NetworkOperationResult:
            # Function implementation - models auto-detected from request.path
            pass

        @verify_required_models(
            strict_mode=False,
            required_models={OpenConfigModel.SYSTEM, OpenConfigModel.INTERFACES}
        )
        def get_mixed_info(device: Device, request: GnmiRequest) -> NetworkOperationResult:
            # Function implementation with explicit model requirements
            pass
    """

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
                    "Capability verification disabled for function",
                    extra={
                        "function": func.__name__,
                        "reason": "environment_variable_set",
                    },
                )
                return func(*args, **kwargs)

            # Extract device and GnmiRequest from arguments
            device = _extract_device_from_args(*args, **kwargs)
            gnmi_request = _extract_gnmi_request_from_args(*args, **kwargs)

            if not device:
                logger.error(
                    "Could not extract device from arguments for function",
                    extra={
                        "function": func.__name__,
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
                "Starting capability verification",
                extra={
                    "function": func.__name__,
                    "device_name": device.name,
                    "strict_mode": strict_mode,
                    "add_to_metadata": add_to_metadata,
                },
            )

            # Determine required models
            if required_models is not None:
                models_to_verify = required_models
                logger.debug(
                    "Using explicitly provided models",
                    extra={
                        "function": func.__name__,
                        "device_name": device.name,
                        "model_count": len(models_to_verify),
                        "models": [model.value for model in models_to_verify],
                    },
                )
            elif gnmi_request:
                models_to_verify = gnmi_request.get_required_models()
                logger.debug(
                    "Auto-detected models from gNMI request",
                    extra={
                        "function": func.__name__,
                        "device_name": device.name,
                        "model_count": len(models_to_verify),
                        "models": [model.value for model in models_to_verify],
                        "request_paths": gnmi_request.path,
                    },
                )
            else:
                logger.warning(
                    "No GnmiRequest found and no explicit models provided",
                    extra={
                        "function": func.__name__,
                        "device_name": device.name,
                    },
                )
                models_to_verify = set()

            # If no models required, proceed without verification
            if not models_to_verify:
                logger.debug(
                    "No OpenConfig models required, proceeding without verification",
                    extra={
                        "function": func.__name__,
                        "device_name": device.name,
                    },
                )
                return func(*args, **kwargs)

            # Check cache for each model
            cached_results = {}
            models_to_verify_fresh = set()

            logger.debug(
                "Checking cache for model verification results",
                extra={
                    "device_name": device.name,
                    "models_to_check": [
                        model.value for model in models_to_verify
                    ],
                },
            )

            for model in models_to_verify:
                cached_result = get_model_verification_result(
                    device.name, model
                )
                if cached_result:
                    cached_results[model] = cached_result
                    logger.debug(
                        "Using cached verification result",
                        extra={
                            "device_name": device.name,
                            "model": model.value,
                            "status": cached_result.status.value,
                        },
                    )
                else:
                    models_to_verify_fresh.add(model)
                    logger.debug(
                        "Model not in cache, will verify fresh",
                        extra={
                            "device_name": device.name,
                            "model": model.value,
                        },
                    )

            # Verify uncached models
            fresh_verification_result = None
            if models_to_verify_fresh:
                logger.info(
                    "Verifying capabilities for uncached models",
                    extra={
                        "device_name": device.name,
                        "fresh_model_count": len(models_to_verify_fresh),
                        "models": [
                            model.value for model in models_to_verify_fresh
                        ],
                    },
                )
                fresh_verification_result = verify_models(
                    device, models_to_verify_fresh
                )

                # Cache the fresh results
                for (
                    model,
                    result,
                ) in fresh_verification_result.model_results.items():
                    cache_model_verification_result(device.name, model, result)
                    logger.debug(
                        "Cached verification result",
                        extra={
                            "device_name": device.name,
                            "model": model.value,
                            "status": result.status.value,
                        },
                    )
            else:
                logger.debug(
                    "All models found in cache, no fresh verification needed",
                    extra={"device_name": device.name},
                )

            # Combine cached and fresh results
            all_results = {}
            all_results.update(cached_results)
            if fresh_verification_result:
                all_results.update(fresh_verification_result.model_results)

            logger.debug(
                "Combined verification results",
                extra={
                    "device_name": device.name,
                    "total_results": len(all_results),
                    "cached_results": len(cached_results),
                    "fresh_results": (
                        len(fresh_verification_result.model_results)
                        if fresh_verification_result
                        else 0
                    ),
                },
            )

            # Analyze results
            successful_models = set()
            failed_models = set()
            warning_models = set()

            for model, result in all_results.items():
                if result.status == VerificationStatus.SUPPORTED:
                    successful_models.add(model)
                elif result.status == VerificationStatus.VERSION_WARNING:
                    warning_models.add(model)
                    successful_models.add(model)  # Can still proceed
                else:
                    failed_models.add(model)

            logger.debug(
                "Verification analysis completed",
                extra={
                    "device_name": device.name,
                    "successful_models": len(successful_models),
                    "warning_models": len(warning_models),
                    "failed_models": len(failed_models),
                    "failed_model_list": [
                        model.value for model in failed_models
                    ],
                },
            )

            # Handle failures based on strict mode
            if failed_models:
                if strict_mode:
                    logger.error(
                        "Strict mode enabled - failing due to unsupported models",
                        extra={
                            "device_name": device.name,
                            "function": func.__name__,
                            "failed_models": [
                                model.value for model in failed_models
                            ],
                            "successful_models": [
                                model.value for model in successful_models
                            ],
                        },
                    )
                    return handle_partial_verification_failure(
                        device=device,
                        failed_models=failed_models,
                        successful_models=successful_models,
                        operation_type=func.__name__,
                    )
                else:
                    logger.warning(
                        "Continuing with partial model support",
                        extra={
                            "device_name": device.name,
                            "function": func.__name__,
                            "failed_models": [
                                model.value for model in failed_models
                            ],
                            "successful_models": [
                                model.value for model in successful_models
                            ],
                        },
                    )

            # Log successful verification
            if successful_models:
                logger.info(
                    "Successfully verified models",
                    extra={
                        "device_name": device.name,
                        "function": func.__name__,
                        "successful_models": [
                            model.value for model in successful_models
                        ],
                    },
                )

            # Log warnings
            if warning_models:
                logger.warning(
                    "Version warnings for models",
                    extra={
                        "device_name": device.name,
                        "function": func.__name__,
                        "warning_models": [
                            model.value for model in warning_models
                        ],
                    },
                )

            # Execute the original function
            logger.debug(
                "Executing original function after successful verification",
                extra={
                    "device_name": device.name,
                    "function": func.__name__,
                },
            )
            result = func(*args, **kwargs)

            # Add verification metadata if requested
            if add_to_metadata and isinstance(result, NetworkOperationResult):
                logger.debug(
                    "Adding verification metadata to result",
                    extra={
                        "device_name": device.name,
                        "function": func.__name__,
                        "result_type": type(result).__name__,
                    },
                )
                _add_verification_metadata(result, all_results)

            logger.debug(
                "Capability verification completed successfully",
                extra={
                    "device_name": device.name,
                    "function": func.__name__,
                },
            )

            return result

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
    for _, value in kwargs.items():
        if isinstance(value, Device):
            return value

    return None


def _extract_gnmi_request_from_args(*args, **kwargs) -> Optional[GnmiRequest]:
    """
    Extract GnmiRequest object from function arguments.

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        GnmiRequest object if found, None otherwise
    """
    # Check positional arguments
    for arg in args:
        if isinstance(arg, GnmiRequest):
            return arg

    # Check keyword arguments for common parameter names
    for key in ["request", "gnmi_request", "params", "parameters"]:
        if key in kwargs and isinstance(kwargs[key], GnmiRequest):
            return kwargs[key]

    return None


def _create_capability_error_result(
    device: Optional[Device],
    operation_type: str,
    error_message: str,
) -> NetworkOperationResult:
    """
    Create a NetworkOperationResult for capability verification errors.

    Args:
        device: Device object (can be None)
        operation_type: Type of operation that failed
        error_message: Error message describing the failure

    Returns:
        NetworkOperationResult with error status
    """
    device_name = device.name if device else "unknown"
    device_ip = device.ip_address if device else "unknown"
    device_nos = device.nos if device else "unknown"
    full_message = (
        f"Capability verification failed for {operation_type}: {error_message}"
    )

    error_response = ErrorResponse(
        type="CAPABILITY_VERIFICATION_ERROR",
        message=full_message,
        details={
            "device_name": device_name,
            "operation_type": operation_type,
            "error_message": error_message,
        },
    )

    return NetworkOperationResult(
        device_name=device_name,
        ip_address=device_ip,
        nos=device_nos,
        operation_type=operation_type,
        status=OperationStatus.FAILED,
        data={},
        metadata={
            "capability_verification": {
                "verified": False,
                "error": error_message,
            }
        },
        error_response=error_response,
    )


def _add_verification_metadata(
    result: NetworkOperationResult,
    verification_results: Dict[OpenConfigModel, Any],
) -> None:
    """
    Add verification metadata to NetworkOperationResult.

    Args:
        result: NetworkOperationResult to add metadata to
        verification_results: Dictionary of verification results by model
    """
    if not hasattr(result, "metadata") or result.metadata is None:
        result.metadata = {}

    verification_metadata = {
        "verified": True,
        "models": {},
    }

    for model, model_result in verification_results.items():
        verification_metadata["models"][model.value] = {
            "status": model_result.status.value,
            "found_version": model_result.found_version,
            "required_version": model_result.required_version,
            "warning_message": model_result.warning_message,
        }

    result.metadata["capability_verification"] = verification_metadata
