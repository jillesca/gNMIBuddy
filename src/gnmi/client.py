#!/usr/bin/env python3
"""gNMI client module for interacting with network devices via gNMI"""
import os
import sys
import logging
from typing import Dict, Any, Union
import grpc
from pygnmi.client import gNMIclient

# Configure pygnmi logger to only show ERROR level messages
logging.getLogger("pygnmi.client").setLevel(logging.ERROR)

# Add parent directory to path when running as standalone for development
if __name__ == "__main__":
    sys.path.append(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


from src.schemas.models import Device
from src.inventory.file_handler import parse_json_file
from src.gnmi.parameters import GnmiRequest
from src.schemas.responses import (
    SuccessResponse,
    ErrorResponse,
    NetworkResponse,
    add_capability_verification_to_metadata,
)
from src.gnmi.error_handlers import (
    handle_timeout_error,
    handle_rpc_error,
    handle_connection_refused,
    handle_generic_error,
    handle_capability_error,
)
from src.services.capability_verification import (
    verify_openconfig_network_instance,
)
from src.utils.capability_cache import (
    is_device_verified,
    cache_verification_result,
)
from src.logging.config import get_logger


logger = get_logger(__name__)


def get_gnmi_data(device: Device, request: GnmiRequest) -> NetworkResponse:
    """
    Get data from a gNMI target using the GnmiRequest parameter object.

    Args:
        device: Device object containing device connection information
        request: GnmiRequest object containing the request parameters

    Returns:
        Union of SuccessResponse, ErrorResponse, or FeatureNotFoundResponse
    """
    logger.debug("gNMI request parameters: %s", request)

    # Check capability verification cache first
    if not is_device_verified(device.name):
        logger.info(
            f"Verifying openconfig-network-instance capability for device: {device.name}"
        )

        # Perform capability verification
        verification_result = verify_openconfig_network_instance(device)

        if not verification_result.get("is_supported", False):
            # Cache the failed verification result
            cache_verification_result(
                device.name,
                is_verified=False,
                verification_result=verification_result,
            )

            # Return error response for unsupported devices
            error_message = verification_result.get(
                "error_message",
                "Device does not support openconfig-network-instance model",
            )
            model_capability = verification_result.get("model_capability", {})

            if model_capability.get("status") == "NOT_FOUND":
                required_version = model_capability.get(
                    "required_version", "1.3.0"
                )
                model_name = model_capability.get(
                    "model_name", "openconfig-network-instance"
                )
                error_message = f"Required model '{model_name}' version {required_version} or higher is not supported on this device"

            return handle_capability_error(device, error_message)

        # Cache the successful verification result
        cache_verification_result(
            device.name,
            is_verified=True,
            verification_result=verification_result,
        )

        # Log appropriate message based on verification result
        model_capability = verification_result.get("model_capability", {})
        found_version = model_capability.get("found_version", "unknown")
        required_version = model_capability.get("required_version", "1.3.0")

        if verification_result.get("warning_message"):
            logger.warning(
                f"Device {device.name}: {verification_result['warning_message']}"
            )
        else:
            logger.info(
                f"Device {device.name}: openconfig-network-instance v{found_version} is supported (required: {required_version})"
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
        "show_diff": device.show_diff,
    }

    try:
        with gNMIclient(**gnmi_params) as gc:

            response_data = gc.get(**request)
            raw_response = _extract_gnmi_data(response=response_data)
            response = _create_response_from_raw_data(
                raw_response=raw_response
            )

            return response

    except grpc.FutureTimeoutError:
        return handle_timeout_error(device)
    except grpc.RpcError as e:
        return handle_rpc_error(device, e)
    except ConnectionRefusedError:
        return handle_connection_refused(device)
    except Exception as e:
        return handle_generic_error(device, e)


def _extract_gnmi_data(
    response: Dict[str, Any],
) -> Union[Dict[str, Any], None]:

    notifications = response.get("notification", [])

    if not notifications:
        logger.debug("No notifications found in gNMI response")
        return None

    updates = notifications[0].get("update", [])

    if not updates:
        logger.debug("No updates found in gNMI notification")
        return None

    result = {}
    result["data"] = updates

    if "timestamp" in notifications[0]:
        result["timestamp"] = notifications[0]["timestamp"]

    return result


def _create_response_from_raw_data(
    raw_response: Union[Dict[str, Any], None],
) -> Union[SuccessResponse, ErrorResponse]:
    if raw_response:
        data = raw_response.get("data", [])
        timestamp = raw_response.get("timestamp")
        return SuccessResponse(data=data, timestamp=timestamp)

    return ErrorResponse(
        type="NO_DATA", message="No data returned from device"
    )


if __name__ == "__main__":
    from pprint import pprint as pp
    from src.logging.config import get_logger

    logger = get_logger(__name__)

    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Path to sandbox.json (one level up from the gnmi directory)
    json_file_path = os.path.join(os.path.dirname(script_dir), "hosts.json")

    # Parse the JSON file to get device information
    devices = parse_json_file(json_file_path)

    device = Device(**devices[0])

    # Creating a GnmiRequest for an example query
    request = GnmiRequest(
        path=[
            "openconfig-interfaces:interfaces/interface[name=*]/state/admin-status",
            "openconfig-interfaces:interfaces/interface[name=*]/state/oper-status",
        ],
        encoding="json_ietf",
    )

    result = get_gnmi_data(device, request)

    pp(result)
