#!/usr/bin/env python3
"""gNMI client module for interacting with network devices via gNMI"""
import os
import sys
from typing import Dict, Any, Union
import grpc
from pygnmi.client import gNMIclient

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
from src.logging.config import get_logger, log_operation


logger = get_logger(__name__)


@log_operation("get_gnmi_data")
def get_gnmi_data(device: Device, request: GnmiRequest) -> NetworkResponse:
    """
    Get data from a gNMI target using the GnmiRequest parameter object.

    Args:
        device: Device object containing device connection information
        request: GnmiRequest object containing the request parameters

    Returns:
        Union of SuccessResponse, ErrorResponse, or FeatureNotFoundResponse
    """
    logger.debug(
        "Initiating gNMI request",
        extra={
            "device_name": device.name,
            "device_ip": device.ip_address,
            "paths": request.path,
            "encoding": request.encoding,
            "datatype": request.datatype,
        },
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

    logger.debug(
        "gNMI connection parameters configured",
        extra={
            "device_name": device.name,
            "target": f"{device.ip_address}:{device.port}",
            "timeout": device.gnmi_timeout,
            "insecure": device.insecure,
        },
    )

    try:
        logger.debug(
            "Establishing gNMI connection", extra={"device_name": device.name}
        )
        with gNMIclient(**gnmi_params) as gc:
            logger.debug(
                "gNMI connection established, executing request",
                extra={"device_name": device.name},
            )

            response_data = gc.get(**request)
            logger.debug(
                "gNMI request completed successfully",
                extra={
                    "device_name": device.name,
                    "response_keys": (
                        list(response_data.keys()) if response_data else None
                    ),
                },
            )

            raw_response = _extract_gnmi_data(response=response_data)
            response = _create_response_from_raw_data(
                raw_response=raw_response
            )

            logger.info(
                "gNMI data retrieval completed",
                extra={
                    "device_name": device.name,
                    "success": isinstance(response, SuccessResponse),
                    "data_points": (
                        len(response.data)
                        if isinstance(response, SuccessResponse)
                        and response.data
                        else 0
                    ),
                },
            )

            return response

    except grpc.FutureTimeoutError as e:
        logger.error(
            "gNMI request timed out",
            extra={
                "device_name": device.name,
                "timeout": device.gnmi_timeout,
                "error": str(e),
            },
        )
        return handle_timeout_error(device)
    except grpc.RpcError as e:
        logger.error(
            "gRPC error during gNMI request",
            extra={
                "device_name": device.name,
                "error_details": str(e),
            },
        )
        return handle_rpc_error(device, e)
    except ConnectionRefusedError as e:
        logger.error(
            "Connection refused by device",
            extra={
                "device_name": device.name,
                "device_ip": device.ip_address,
                "device_port": device.port,
                "error": str(e),
            },
        )
        return handle_connection_refused(device)
    except (ValueError, TypeError) as e:
        logger.error(
            "Invalid data or type error during gNMI request",
            extra={
                "device_name": device.name,
                "error_type": type(e).__name__,
                "error": str(e),
            },
        )
        return handle_generic_error(device, e)


def _extract_gnmi_data(
    response: Dict[str, Any],
) -> Union[Dict[str, Any], None]:
    """
    Extract useful data from gNMI response.

    Args:
        response: Raw gNMI response dictionary

    Returns:
        Extracted data dictionary or None if no data found
    """
    logger.debug(
        "Extracting data from gNMI response",
        extra={
            "response_keys": list(response.keys()) if response else None,
        },
    )

    notifications = response.get("notification", [])

    if not notifications:
        logger.debug("No notifications found in gNMI response")
        return None

    logger.debug(
        "Found notifications in gNMI response",
        extra={"notification_count": len(notifications)},
    )

    updates = notifications[0].get("update", [])

    if not updates:
        logger.debug("No updates found in gNMI notification")
        return None

    logger.debug(
        "Found updates in gNMI notification",
        extra={"update_count": len(updates)},
    )

    extracted_data = {}
    extracted_data["data"] = updates

    if "timestamp" in notifications[0]:
        extracted_data["timestamp"] = notifications[0]["timestamp"]
        logger.debug(
            "Timestamp extracted from gNMI response",
            extra={"timestamp": notifications[0]["timestamp"]},
        )

    logger.debug(
        "Data extraction completed",
        extra={"data_points": len(updates)},
    )

    return extracted_data


def _create_response_from_raw_data(
    raw_response: Union[Dict[str, Any], None],
) -> Union[SuccessResponse, ErrorResponse]:
    """
    Create a structured response from raw gNMI data.

    Args:
        raw_response: Raw extracted data from gNMI response

    Returns:
        Structured response object
    """
    if raw_response:
        data = raw_response.get("data", [])
        timestamp = raw_response.get("timestamp")

        logger.debug(
            "Creating success response from raw data",
            extra={
                "data_points": len(data),
                "has_timestamp": timestamp is not None,
            },
        )

        return SuccessResponse(data=data, timestamp=timestamp)

    logger.debug("Creating error response - no data returned from device")
    return ErrorResponse(
        type="NO_DATA", message="No data returned from device"
    )


if __name__ == "__main__":
    from pprint import pprint as pp

    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Path to sandbox.json (one level up from the gnmi directory)
    json_file_path = os.path.join(os.path.dirname(script_dir), "hosts.json")

    # Parse the JSON file to get device information
    devices = parse_json_file(json_file_path)

    test_device = Device(**devices[0])

    # Creating a GnmiRequest for an example query
    test_request = GnmiRequest(
        path=[
            "openconfig-interfaces:interfaces/interface[name=*]/state/admin-status",
            "openconfig-interfaces:interfaces/interface[name=*]/state/oper-status",
        ],
        encoding="json_ietf",
    )

    test_result = get_gnmi_data(test_device, test_request)

    pp(test_result)
