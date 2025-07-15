#!/usr/bin/env python3
"""
gNMI capability checker for gNMIBuddy.

Provides functionality to retrieve and parse device capabilities from gNMI
to determine supported models and versions.
"""

import json
from typing import Dict, Any, List, Union, Optional
import grpc
from pygnmi.client import gNMIclient

from src.schemas.models import Device
from src.schemas.capabilities import (
    CapabilityInfo,
    DeviceCapabilities,
    CapabilityError,
)
from src.schemas.responses import SuccessResponse, ErrorResponse
from src.logging.config import get_logger

logger = get_logger(__name__)

# OpenConfig models of interest for focused debugging
OPENCONFIG_MODELS_OF_INTEREST = [
    "openconfig-system",
    "openconfig-interfaces",
    "openconfig-network-instance",
]


def get_device_capabilities(
    device: Device,
) -> Union[SuccessResponse, ErrorResponse]:
    """
    Retrieve device capabilities via gNMI.

    This function connects to the device and retrieves the capabilities
    information, including supported models and their versions.

    Args:
        device: Device object containing connection information

    Returns:
        SuccessResponse with DeviceCapabilities data or ErrorResponse on failure
    """
    logger.info(
        f"Retrieving capabilities for device: {device.name} ({device.ip_address})"
    )

    gnmi_params = {
        "target": (device.ip_address, device.port),
        "username": device.username,
        "password": device.password,
        "insecure": device.insecure,
        "path_cert": device.path_cert,
        "path_key": device.path_key,
        "path_root": device.path_root,
        "override": device.override,
        "skip_verify": device.skip_verify,
        "gnmi_timeout": device.gnmi_timeout,
        "grpc_options": device.grpc_options,
    }

    try:
        with gNMIclient(**gnmi_params) as gc:
            # Get capabilities from the device
            capabilities_response = gc.capabilities()
            logger.debug(
                "Successfully retrieved capabilities response from %s",
                device.name,
            )

            # Parse the capabilities response
            if capabilities_response is not None:
                device_capabilities = _parse_capabilities_response(
                    device.name, capabilities_response
                )
            else:
                device_capabilities = None

            if device_capabilities:
                logger.info(
                    "Successfully retrieved capabilities for %s. "
                    "Found %d models.",
                    device.name,
                    len(device_capabilities.supported_models),
                )
                # Convert DeviceCapabilities to serializable format
                capabilities_dict = {
                    "device_name": device_capabilities.device_name,
                    "gnmi_version": device_capabilities.gnmi_version,
                    "supported_encodings": device_capabilities.supported_encodings,
                    "timestamp": device_capabilities.timestamp,
                    "raw_response": device_capabilities.raw_response,
                    "supported_models": [
                        {
                            "name": model.name,
                            "version": model.version,
                            "organization": model.organization,
                            "module": model.module,
                            "revision": model.revision,
                            "namespace": model.namespace,
                        }
                        for model in device_capabilities.supported_models
                    ],
                }
                return SuccessResponse(data=[capabilities_dict])
            else:
                error_msg = (
                    f"Failed to parse capabilities response for {device.name}"
                )
                logger.error(error_msg)
                return ErrorResponse(
                    type="CAPABILITIES_PARSE_ERROR",
                    message=error_msg,
                    details={
                        "device": device.name,
                        "raw_response": capabilities_response,
                    },
                )

    except grpc.FutureTimeoutError:
        error_msg = f"Timeout while retrieving capabilities from {device.name} ({device.ip_address}:{device.port})"
        logger.error(error_msg)
        return ErrorResponse(
            type="CAPABILITIES_TIMEOUT",
            message=error_msg,
            details={"device": device.name, "timeout": device.gnmi_timeout},
        )

    except grpc.RpcError as e:
        error_msg = f"gRPC error while retrieving capabilities from {device.name}: {str(e)}"
        logger.error(error_msg)

        # Extract more detailed error information
        error_details = {"device": device.name}
        try:
            status_code = getattr(e, "code", lambda: None)()
            details = getattr(e, "details", lambda: str(e))()
            if status_code:
                error_details["grpc_status"] = getattr(
                    status_code, "name", "UNKNOWN"
                )
                error_details["grpc_code"] = str(
                    getattr(status_code, "value", 0)
                )
            error_details["grpc_details"] = details
        except (AttributeError, TypeError):
            pass

        return ErrorResponse(
            type="CAPABILITIES_GRPC_ERROR",
            message=error_msg,
            details=error_details,
        )

    except ConnectionRefusedError:
        error_msg = f"Connection refused while retrieving capabilities from {device.name} ({device.ip_address}:{device.port})"
        logger.error(error_msg)
        return ErrorResponse(
            type="CAPABILITIES_CONNECTION_REFUSED",
            message=error_msg,
            details={
                "device": device.name,
                "address": f"{device.ip_address}:{device.port}",
            },
        )

    except Exception as e:
        error_msg = f"Unexpected error while retrieving capabilities from {device.name}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return ErrorResponse(
            type="CAPABILITIES_UNEXPECTED_ERROR",
            message=error_msg,
            details={
                "device": device.name,
                "error_type": type(e).__name__,
                "error_str": str(e),
            },
        )


def _parse_capabilities_response(
    device_name: str, response: Dict[str, Any]
) -> Optional[DeviceCapabilities]:
    """
    Parse gNMI capabilities response into DeviceCapabilities object.

    Args:
        device_name: Name of the device
        response: Raw capabilities response from gNMIclient

    Returns:
        DeviceCapabilities object or None if parsing fails
    """
    try:
        logger.debug(
            "Parsing capabilities response for device: %s", device_name
        )
        logger.debug("Raw response keys: %s", list(response.keys()))

        # Extract gNMI version
        gnmi_version = response.get("gNMI_version", "unknown")

        # Extract supported encodings
        supported_encodings = response.get("supported_encodings", [])

        # Extract supported models
        supported_models = []
        models_data = response.get("supported_models", [])

        logger.debug("Found %d models in raw response", len(models_data))

        # Log first few models for structure verification
        if models_data:
            logger.debug("Sample models from raw response:")
            for i, model in enumerate(models_data[:3]):
                logger.debug("  Model %d: %s", i + 1, model)

        # Track OpenConfig models during parsing
        openconfig_models_found = []

        for model_data in models_data:
            try:
                capability_info = _parse_model_capability(model_data)
                if capability_info:
                    supported_models.append(capability_info)

                    # Log specific models of interest during parsing
                    if capability_info.name in OPENCONFIG_MODELS_OF_INTEREST:
                        openconfig_models_found.append(capability_info)
                        logger.debug(
                            "Parsed OpenConfig model: %s v%s",
                            capability_info.name,
                            capability_info.version,
                        )

            except Exception as e:
                logger.warning(
                    "Failed to parse model capability: %s, error: %s",
                    model_data,
                    str(e),
                )
                continue

        logger.debug(
            "Successfully parsed %d models into CapabilityInfo objects",
            len(supported_models),
        )

        # Enhanced logging for OpenConfig models
        if openconfig_models_found:
            logger.debug(
                "Found %d OpenConfig models of interest during parsing:",
                len(openconfig_models_found),
            )
            for model in openconfig_models_found:
                logger.debug(
                    "  - %s v%s (%s)",
                    model.name,
                    model.version,
                    model.organization,
                )
        else:
            logger.debug(
                "No OpenConfig models of interest found during parsing"
            )

        # Filter and log only OpenConfig models of interest for debugging
        relevant_models = [
            model
            for model in supported_models
            if model.name in OPENCONFIG_MODELS_OF_INTEREST
        ]

        if relevant_models:
            logger.debug(
                "Found %d OpenConfig models of interest:", len(relevant_models)
            )
            for model in relevant_models:
                logger.debug(
                    "  - %s v%s (%s)",
                    model.name,
                    model.version,
                    model.organization,
                )
        else:
            logger.debug("No OpenConfig models of interest found")

        return DeviceCapabilities(
            device_name=device_name,
            gnmi_version=gnmi_version,
            supported_models=supported_models,
            supported_encodings=supported_encodings,
            raw_response=response,
        )

    except Exception as e:
        logger.error(
            "Failed to parse capabilities response for %s: %s",
            device_name,
            str(e),
        )
        logger.debug("Raw response: %s", response)
        return None


def _parse_model_capability(
    model_data: Dict[str, Any],
) -> Optional[CapabilityInfo]:
    """
    Parse a single model capability from the capabilities response.

    Args:
        model_data: Model data from capabilities response

    Returns:
        CapabilityInfo object or None if parsing fails
    """
    try:
        # Extract required fields
        name = model_data.get("name", "")
        version = model_data.get("version", "")
        organization = model_data.get("organization", "")

        if not name:
            logger.warning("Model capability missing name: %s", model_data)
            return None

        # Extract optional fields
        module = model_data.get("module")
        revision = model_data.get("revision")
        namespace = model_data.get("namespace")

        return CapabilityInfo(
            name=name,
            version=version,
            organization=organization,
            module=module,
            revision=revision,
            namespace=namespace,
        )

    except Exception as e:
        logger.warning(
            "Failed to parse model capability %s: %s", model_data, str(e)
        )
        return None


def extract_capabilities_from_response(
    response: SuccessResponse,
) -> Optional[DeviceCapabilities]:
    """
    Extract DeviceCapabilities from a SuccessResponse containing capabilities data.

    Args:
        response: SuccessResponse from get_device_capabilities

    Returns:
        DeviceCapabilities object or None if extraction fails
    """
    if not response.data:
        logger.warning("No data in capabilities response")
        return None

    try:
        # The data should contain a single dictionary with capabilities
        capabilities_dict = response.data[0]

        # Reconstruct the DeviceCapabilities object
        device_capabilities = DeviceCapabilities(
            device_name=capabilities_dict.get("device_name", ""),
            gnmi_version=capabilities_dict.get("gnmi_version", "unknown"),
            supported_encodings=capabilities_dict.get(
                "supported_encodings", []
            ),
            raw_response=capabilities_dict.get("raw_response"),
        )

        # Reconstruct the supported models
        models_data = capabilities_dict.get("supported_models", [])
        for model_data in models_data:
            # Check if model_data is already a CapabilityInfo object or a dict
            if isinstance(model_data, CapabilityInfo):
                capability_info = model_data
            else:
                capability_info = CapabilityInfo(
                    name=model_data.get("name", ""),
                    version=model_data.get("version", ""),
                    organization=model_data.get("organization", ""),
                    module=model_data.get("module"),
                    revision=model_data.get("revision"),
                    namespace=model_data.get("namespace"),
                )
            device_capabilities.supported_models.append(capability_info)

        return device_capabilities

    except Exception as e:
        logger.error(
            "Failed to extract capabilities from response: %s", str(e)
        )
        logger.debug("Exception details:", exc_info=True)
        return None


def create_capability_error(
    error_type: str, message: str, model_name: Optional[str] = None, **details
) -> CapabilityError:
    """
    Create a CapabilityError object with the given parameters.

    Args:
        error_type: Type of capability error
        message: Human-readable error message
        model_name: Name of the model that caused the error (optional)
        **details: Additional error details

    Returns:
        CapabilityError object
    """
    return CapabilityError(
        error_type=error_type,
        message=message,
        model_name=model_name,
        details=details,
    )


def log_capabilities_summary(device_capabilities: DeviceCapabilities) -> None:
    """
    Log a summary of device capabilities for debugging.

    Args:
        device_capabilities: DeviceCapabilities object to summarize
    """
    logger.info(
        f"Device capabilities summary for {device_capabilities.device_name}:"
    )
    logger.info(f"  gNMI version: {device_capabilities.gnmi_version}")
    logger.info(
        f"  Supported encodings: {device_capabilities.supported_encodings}"
    )
    logger.info(
        f"  Number of supported models: {len(device_capabilities.supported_models)}"
    )

    # Log some key models if available
    key_models = [
        "openconfig-network-instance",
        "openconfig-interfaces",
        "openconfig-routing-policy",
    ]
    for model_name in key_models:
        model = device_capabilities.find_model(model_name)
        if model:
            logger.info(
                f"  {model_name}: v{model.version} ({model.organization})"
            )


if __name__ == "__main__":
    # Test the capability checking functionality
    import os
    import sys
    from pprint import pprint

    # Add parent directory to path for testing
    sys.path.append(
        os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
    )

    from src.inventory.file_handler import parse_json_file

    # Get test device (adjust path as needed)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(
        os.path.dirname(os.path.dirname(script_dir)), "xrd_sandbox.json"
    )

    if os.path.exists(json_file_path):
        devices = parse_json_file(json_file_path)
        if devices:
            device = Device(**devices[0])

            print(f"Testing capabilities for device: {device.name}")
            result = get_device_capabilities(device)

            if isinstance(result, SuccessResponse):
                capabilities = extract_capabilities_from_response(result)
                if capabilities:
                    log_capabilities_summary(capabilities)
                    print(
                        f"\nFound {len(capabilities.supported_models)} models:"
                    )
                    for model in capabilities.supported_models[
                        :5
                    ]:  # Show first 5 models
                        print(
                            f"  - {model.name} v{model.version} ({model.organization})"
                        )
                else:
                    print("Failed to extract capabilities")
            else:
                print(f"Error: {result}")
    else:
        print(f"Test file not found: {json_file_path}")
