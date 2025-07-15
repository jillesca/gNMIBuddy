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
)
from src.gnmi.error_handlers import (
    handle_timeout_error,
    handle_rpc_error,
    handle_connection_refused,
    handle_generic_error,
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
            return _create_response_from_raw_data(raw_response=raw_response)

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
    from src.utils.logging_config import configure_logging, get_logger

    configure_logging("DEBUG")
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
