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


from src.inventory.models import Device
from src.inventory.file_handler import parse_json_file
from src.gnmi.parameters import GnmiRequest
from src.gnmi.responses import (
    GnmiDataResponse,
    GnmiError,
    GnmiFeatureNotFoundResponse,
)
from src.gnmi.error_handlers import (
    handle_timeout_error,
    handle_rpc_error,
    handle_connection_refused,
    handle_generic_error,
)
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def get_gnmi_data(device: Device, request: GnmiRequest) -> GnmiDataResponse:
    """
    Get data from a gNMI target using the GnmiRequest parameter object.

    Args:
        device: Device object containing device connection information
        request: GnmiRequest object containing the request parameters

    Returns:
        GnmiDataResponse object containing either the retrieved data or error information
    """
    logger.debug(f"gNMI request parameters: {request}")

    target = (device.ip_address, device.port)
    username = device.username
    password = device.password

    try:
        with gNMIclient(
            target=target, username=username, password=password, insecure=True
        ) as gc:

            result = gc.get(**request)
            raw_response = _extract_gnmi_data(response=result)
            return _create_response_from_raw_data(raw_response=raw_response)

    except grpc.FutureTimeoutError:
        error = handle_timeout_error(device)
        return GnmiDataResponse.error_response(error)
    except grpc.RpcError as e:
        result = handle_rpc_error(device, e)
        # Special handling for feature not found
        if isinstance(result, GnmiFeatureNotFoundResponse):
            return result
        return GnmiDataResponse.error_response(result)
    except ConnectionRefusedError:
        error = handle_connection_refused(device)
        return GnmiDataResponse.error_response(error)
    except Exception as e:
        result = handle_generic_error(device, e)
        # Special handling for feature not found
        if isinstance(result, GnmiFeatureNotFoundResponse):
            return result
        return GnmiDataResponse.error_response(result)


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
    result["response"] = updates

    if "timestamp" in notifications[0]:
        result["timestamp"] = notifications[0]["timestamp"]

    return result


def _create_response_from_raw_data(
    raw_response: Union[Dict[str, Any], None],
) -> GnmiDataResponse:
    if raw_response:
        return GnmiDataResponse.from_raw_response(raw_response)

    return GnmiDataResponse.error_response(
        GnmiError(type="NO_DATA", message="No data returned from device")
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

    device = Device.from_dict(devices[0])

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
